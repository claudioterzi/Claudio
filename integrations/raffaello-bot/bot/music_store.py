"""Additive music queue on the existing SQLite connection and storage path."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
import time
import uuid
from urllib.parse import urlparse

from bot import db
from bot.music_auth import MusicError, is_owner

SCHEMA = """
CREATE TABLE IF NOT EXISTS music_requests (
 id TEXT PRIMARY KEY, requester INTEGER NOT NULL, client_id TEXT NOT NULL,
 fingerprint TEXT NOT NULL, story TEXT NOT NULL, genre TEXT NOT NULL,
 mood TEXT NOT NULL, language TEXT NOT NULL, personal_voice INTEGER NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('requested','writing','awaiting_suno','ready','kept','discarded','error')),
 title TEXT NOT NULL DEFAULT '', lyrics TEXT NOT NULL DEFAULT '', style_prompt TEXT NOT NULL DEFAULT '',
 suno_url TEXT NOT NULL DEFAULT '', playback_confirmed INTEGER NOT NULL DEFAULT 0,
 personal_voice_confirmed INTEGER NOT NULL DEFAULT 0,
 verified_by INTEGER, verified_at INTEGER, created INTEGER NOT NULL, updated INTEGER NOT NULL,
 error_code TEXT NOT NULL DEFAULT '', claim_id TEXT, lock_until INTEGER NOT NULL DEFAULT 0,
 attempts INTEGER NOT NULL DEFAULT 0, delivery_state TEXT NOT NULL DEFAULT 'none',
 delivery_claim TEXT, delivery_until INTEGER NOT NULL DEFAULT 0,
 message_id INTEGER, delivered_at INTEGER, owner_notice_state TEXT NOT NULL DEFAULT 'pending',
 owner_notice_claim TEXT, owner_notice_until INTEGER NOT NULL DEFAULT 0, UNIQUE(requester, client_id)
);
CREATE INDEX IF NOT EXISTS music_requests_requester ON music_requests(requester, created);
CREATE TABLE IF NOT EXISTS music_quota (
 requester INTEGER NOT NULL, period INTEGER NOT NULL, calls INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY(requester, period)
);
CREATE TABLE IF NOT EXISTS music_generation_quota (
 owner INTEGER NOT NULL, period INTEGER NOT NULL, calls INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY(owner, period)
);
"""


def init():
    with db.connect() as conn:
        conn.executescript(SCHEMA)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(music_requests)")}
        for name, kind in {"owner_notice_state": "TEXT NOT NULL DEFAULT 'pending'", "owner_notice_claim": "TEXT", "owner_notice_until": "INTEGER NOT NULL DEFAULT 0", "personal_voice_confirmed": "INTEGER NOT NULL DEFAULT 0"}.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE music_requests ADD COLUMN {name} {kind}")


def _text(value, maximum, required=False):
    if not isinstance(value, str) or len(value) > maximum or any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise MusicError("Controlla il testo e la sua lunghezza.")
    value = value.strip()
    if required and not value:
        raise MusicError("Racconta la canzone che desideri.")
    return value


def request_id(value):
    try:
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F-]{36}", value):
            raise ValueError("bad uuid")
        parsed = uuid.UUID(value)
        if not parsed.int or str(parsed) != value.lower():
            raise ValueError("non-canonical uuid")
        return str(parsed)
    except (ValueError, TypeError) as exc:
        raise MusicError("Identificativo della richiesta non valido.") from exc


def _iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None


def present(row):
    row = dict(row)
    return {key: row[key] for key in ("id", "story", "genre", "mood", "language", "state", "title", "lyrics", "style_prompt", "suno_url", "error_code")} | {
        "requester_id": row["requester"], "personal_voice": bool(row["personal_voice"]),
        "playback_confirmed": bool(row["playback_confirmed"]),
        "personal_voice_confirmed": bool(row["personal_voice_confirmed"]),
        "voice_verification": "owner_sample_confirmation" if row["personal_voice_confirmed"] else None,
        "voice_sample_label": "My Voice - Apr 30" if row["personal_voice_confirmed"] else None,
        "verification": "owner_playback_confirmation" if row["playback_confirmed"] else None,
        "verified_by": row["verified_by"], "verified_at": _iso(row["verified_at"]),
        "created_at": _iso(row["created"]), "updated_at": _iso(row["updated"]),
        "delivery": {"state": row["delivery_state"], "message_id": row["message_id"],
                     "delivered_at": _iso(row["delivered_at"])},
        "owner_notice": {"state": row["owner_notice_state"]},
    }


def _find(conn, rid, actor=None):
    row = conn.execute("SELECT * FROM music_requests WHERE id=?", (request_id(rid),)).fetchone()
    if row is None or (actor is not None and row["requester"] != actor and not is_owner(actor)):
        raise MusicError("Richiesta non disponibile per questo account.", 404, "not_found")
    return row


def recover_expired(now=None):
    now = int(time.time()) if now is None else now
    with db.connect() as conn:
        conn.execute("UPDATE music_requests SET state='error',error_code='preparation_interrupted',claim_id=NULL,updated=? WHERE state='writing' AND lock_until<=?", (now, now))
        # A crash after Telegram accepted a message is not proof that it was unsent.
        conn.execute("UPDATE music_requests SET delivery_state='uncertain',delivery_claim=NULL WHERE delivery_state='sending' AND delivery_until<=?", (now,))
        conn.execute("UPDATE music_requests SET owner_notice_state='error',owner_notice_claim=NULL WHERE owner_notice_state='sending' AND owner_notice_until<=?", (now,))


def recover_after_restart():
    """The sole Studio process restarts; old in-flight workers cannot still own a claim."""
    with db.connect() as conn:
        conn.execute("UPDATE music_requests SET state='error',error_code='preparation_interrupted',claim_id=NULL,lock_until=0,updated=? WHERE state='writing'", (int(time.time()),))
        conn.execute("UPDATE music_requests SET delivery_state='uncertain',delivery_claim=NULL,delivery_until=0 WHERE delivery_state='sending'")
        conn.execute("UPDATE music_requests SET owner_notice_state='error',owner_notice_claim=NULL,owner_notice_until=0 WHERE owner_notice_state='sending'")


def get(actor, rid):
    with db.connect() as conn:
        return present(_find(conn, rid, actor))


def internal(rid):
    with db.connect() as conn:
        return dict(_find(conn, rid))


def list_requests(actor, library=False):
    with db.connect() as conn:
        if library:
            rows = conn.execute("SELECT * FROM music_requests WHERE requester=? AND state IN ('ready','kept') ORDER BY created DESC LIMIT 100", (actor,))
        elif is_owner(actor):
            rows = conn.execute("SELECT * FROM music_requests ORDER BY created DESC LIMIT 100")
        else:
            rows = conn.execute("SELECT * FROM music_requests WHERE requester=? ORDER BY created DESC LIMIT 100", (actor,))
        return [present(row) for row in rows]


def create(actor, body):
    allowed = {"story", "genre", "mood", "language", "client_id", "personal_voice"}
    if set(body) - allowed:
        raise MusicError("La richiesta contiene campi non supportati.")
    content = {
        "story": _text(body.get("story"), 1800, True),
        "genre": _text(body.get("genre", "pop"), 80, True),
        "mood": _text(body.get("mood", ""), 80),
        "language": _text(body.get("language", "it"), 24, True),
        "personal_voice": body.get("personal_voice", False),
    }
    if type(content["personal_voice"]) is not bool:
        raise MusicError("La scelta della voce non è valida.")
    if content["personal_voice"] and not is_owner(actor):
        raise MusicError("La voce personale è disponibile soltanto a Claudio.", 403, "owner_required")
    client_id = request_id(body.get("client_id"))
    fingerprint = hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    now = int(time.time())
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        old = conn.execute("SELECT * FROM music_requests WHERE requester=? AND client_id=?", (actor, client_id)).fetchone()
        if old:
            if old["fingerprint"] != fingerprint:
                raise MusicError("Questo invio identifica già una richiesta diversa.", 409, "idempotency_conflict")
            return present(old)
        period = now // 3600
        conn.execute("DELETE FROM music_quota WHERE period<?", (period - 24,))
        conn.execute("INSERT OR IGNORE INTO music_quota VALUES (?,?,0)", (actor, period))
        quota = conn.execute("SELECT calls FROM music_quota WHERE requester=? AND period=?", (actor, period)).fetchone()[0]
        if quota >= 3:
            raise MusicError("Hai già inviato tre richieste in quest'ora. Riprova più tardi.", 429, "quota_reached")
        rid = str(uuid.uuid4())
        conn.execute("INSERT INTO music_requests (id,requester,client_id,fingerprint,story,genre,mood,language,personal_voice,state,created,updated) VALUES (?,?,?,?,?,?,?,?,?,'requested',?,?)", (rid, actor, client_id, fingerprint, content["story"], content["genre"], content["mood"], content["language"], int(content["personal_voice"]), now, now))
        conn.execute("UPDATE music_quota SET calls=calls+1 WHERE requester=? AND period=?", (actor, period))
        return present(_find(conn, rid))


def claim_prepare(actor, rid):
    if not is_owner(actor):
        raise MusicError("La preparazione è riservata a Claudio.", 403, "owner_required")
    now = int(time.time())
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = _find(conn, rid, actor)
        if row["state"] == "writing" and row["lock_until"] > now:
            return None
        if row["state"] not in ("requested", "error", "writing"):
            return None
        if row["attempts"] >= 3:
            raise MusicError("Sono stati eseguiti tre tentativi. Claudio può controllare la richiesta.", 429, "attempt_limit")
        period = now // 3600
        conn.execute("DELETE FROM music_generation_quota WHERE period<?", (period - 24,))
        conn.execute("INSERT OR IGNORE INTO music_generation_quota VALUES (?,?,0)", (actor, period))
        quota = conn.execute("SELECT calls FROM music_generation_quota WHERE owner=? AND period=?", (actor, period)).fetchone()[0]
        if quota >= 3:
            raise MusicError("Sono state avviate tre preparazioni in quest'ora. Riprova più tardi.", 429, "generation_quota_reached")
        claim = str(uuid.uuid4())
        conn.execute("UPDATE music_requests SET state='writing',claim_id=?,lock_until=?,attempts=attempts+1,error_code='',updated=? WHERE id=?", (claim, now + 300, now, rid))
        conn.execute("UPDATE music_generation_quota SET calls=calls+1 WHERE owner=? AND period=?", (actor, period))
        return claim


def finish_prepare(rid, claim, lyrics=None, style=None):
    lyrics = _text(lyrics, 7000, True) if lyrics is not None else None
    style = _text(style or "", 1000) if lyrics else ""
    with db.connect() as conn:
        conn.execute("UPDATE music_requests SET state=?,lyrics=?,style_prompt=?,error_code=?,claim_id=NULL,lock_until=0,updated=? WHERE id=? AND state='writing' AND claim_id=?", ("awaiting_suno" if lyrics else "error", lyrics or "", style, "" if lyrics else "generation_failed", int(time.time()), rid, claim))


def suno_url(value):
    if not isinstance(value, str) or len(value) > 160:
        raise MusicError("Inserisci il link Suno della canzone.")
    try:
        parsed = urlparse(value.strip())
        match = re.fullmatch(r"/song/([0-9a-fA-F-]{36})", parsed.path)
        if parsed.scheme != "https" or parsed.netloc not in ("suno.com", "www.suno.com") or parsed.query or parsed.fragment or not match:
            raise ValueError("bad url")
        return "https://suno.com/song/" + request_id(match[1])
    except ValueError as exc:
        raise MusicError("Usa un link https://suno.com/song/ seguito dall'identificativo della canzone.") from exc


def record_result(actor, rid, body):
    if not is_owner(actor):
        raise MusicError("Questa operazione è riservata a Claudio.", 403, "owner_required")
    if set(body) - {"title", "suno_url", "playback_confirmed", "personal_voice_confirmed"}:
        raise MusicError("Il risultato contiene campi non supportati.")
    title = _text(body.get("title"), 140, True)
    url = suno_url(body.get("suno_url"))
    if body.get("playback_confirmed") is not True:
        raise MusicError("Ascolta il brano in Suno e conferma la riproduzione prima di consegnarlo.", 409, "playback_required")
    voice_confirmed = body.get("personal_voice_confirmed", False)
    if type(voice_confirmed) is not bool:
        raise MusicError("La conferma della voce non è valida.")
    now = int(time.time())
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = _find(conn, rid, actor)
        if row["personal_voice"] and not voice_confirmed:
            raise MusicError("Conferma di aver applicato il campione My Voice - Apr 30 in Suno.", 409, "personal_voice_confirmation_required")
        if voice_confirmed and not row["personal_voice"]:
            raise MusicError("Questa richiesta non prevede la voce personale.")
        if row["state"] in ("ready", "kept") and row["title"] == title and row["suno_url"] == url:
            return present(row)
        if row["state"] not in ("requested", "error", "awaiting_suno"):
            raise MusicError("Attendi la preparazione in corso prima di collegare il risultato Suno.", 409, "invalid_transition")
        conn.execute("UPDATE music_requests SET state='ready',title=?,suno_url=?,playback_confirmed=1,personal_voice_confirmed=?,verified_by=?,verified_at=?,delivery_state='pending',updated=? WHERE id=?", (title, url, int(voice_confirmed), actor, now, now, rid))
        return present(_find(conn, rid))


def decide(actor, rid, keep):
    if not is_owner(actor):
        raise MusicError("Conserva e Scarta sono riservati a Claudio.", 403, "owner_required")
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = _find(conn, rid, actor)
        target = "kept" if keep else "discarded"
        if row["state"] == target:
            return present(row)
        if keep and row["state"] != "ready":
            raise MusicError("Puoi conservare soltanto un brano pronto.", 409, "invalid_transition")
        conn.execute("UPDATE music_requests SET state=?,claim_id=NULL,lock_until=0,updated=? WHERE id=?", (target, int(time.time()), rid))
        return present(_find(conn, rid))


def claim_delivery(rid):
    now = int(time.time())
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = _find(conn, rid)
        if row["state"] not in ("ready", "kept") or row["delivery_state"] not in ("pending", "error", "uncertain"):
            return None
        claim = str(uuid.uuid4())
        conn.execute("UPDATE music_requests SET delivery_state='sending',delivery_claim=?,delivery_until=? WHERE id=?", (claim, now + 120, rid))
        return claim


def complete_delivery(rid, claim, message_id=None, uncertain=False):
    with db.connect() as conn:
        state = "sent" if message_id else ("uncertain" if uncertain else "error")
        conn.execute("UPDATE music_requests SET delivery_state=?,message_id=?,delivered_at=?,delivery_claim=NULL WHERE id=? AND delivery_claim=?", (state, message_id, int(time.time()) if message_id else None, rid, claim))


def claim_owner_notice(rid):
    now = int(time.time())
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = _find(conn, rid)
        if row["owner_notice_state"] not in ("pending", "error") or row["state"] in ("ready", "kept", "discarded"):
            return None
        claim = str(uuid.uuid4())
        conn.execute("UPDATE music_requests SET owner_notice_state='sending',owner_notice_claim=?,owner_notice_until=? WHERE id=?", (claim, now + 120, rid))
        return claim


def complete_owner_notice(rid, claim, sent):
    with db.connect() as conn:
        conn.execute("UPDATE music_requests SET owner_notice_state=?,owner_notice_claim=NULL WHERE id=? AND owner_notice_claim=?", ("sent" if sent else "error", rid, claim))


def pending_notices():
    with db.connect() as conn:
        return [row["id"] for row in conn.execute("SELECT id FROM music_requests WHERE owner_notice_state IN ('pending','error') AND state NOT IN ('ready','kept','discarded') ORDER BY created LIMIT 20")]
