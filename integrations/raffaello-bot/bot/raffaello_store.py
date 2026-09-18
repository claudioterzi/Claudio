"""Owner-scoped dialogue and immutable Alpha readings. Claudio Terzi · C.Terzi.

Additive SQLite migration: no legacy table is rewritten. Tokens are stored hashed.
Every answer belongs to a frozen draft, never to a mutable 'current reading'.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import time
from pathlib import Path

from bot import db

LANGUAGE_CODES = frozenset({"it", "en", "fr", "es"})

SCHEMA = """
CREATE TABLE IF NOT EXISTS r3_readings (
 id TEXT PRIMARY KEY, owner INTEGER NOT NULL, source_id TEXT NOT NULL,
 fingerprint TEXT NOT NULL, snapshot TEXT NOT NULL, created INTEGER NOT NULL,
 UNIQUE(owner, source_id)
);
CREATE TABLE IF NOT EXISTS r3_dialogues (
 owner INTEGER PRIMARY KEY, thread TEXT NOT NULL, active_reading TEXT
);
CREATE TABLE IF NOT EXISTS r3_drafts (
 id TEXT PRIMARY KEY, owner INTEGER NOT NULL, client_id TEXT NOT NULL,
 thread TEXT NOT NULL, reading_id TEXT, question TEXT NOT NULL,
 status TEXT NOT NULL, answer TEXT, created INTEGER NOT NULL, updated INTEGER NOT NULL,
 language TEXT NOT NULL DEFAULT 'it',
 UNIQUE(owner, client_id)
);
CREATE INDEX IF NOT EXISTS r3_drafts_context ON r3_drafts(owner,thread,created);
CREATE TABLE IF NOT EXISTS r3_links (
 digest TEXT PRIMARY KEY, owner INTEGER NOT NULL, expires INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS r3_sessions (
 digest TEXT PRIMARY KEY, owner INTEGER NOT NULL, expires INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS r3_quota (
 owner INTEGER NOT NULL, period INTEGER NOT NULL, calls INTEGER NOT NULL,
 PRIMARY KEY(owner,period)
);
"""


class Problem(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def init():
    with db.connect() as conn:
        conn.executescript(SCHEMA)
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(r3_drafts)").fetchall()}
        if cols and "language" not in cols:
            conn.execute("ALTER TABLE r3_drafts ADD COLUMN language TEXT NOT NULL DEFAULT 'it'")


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _text(value, maximum, required=False):
    if not isinstance(value, str) or len(value) > maximum:
        raise Problem("Testo mancante o troppo lungo.")
    value = value.strip()
    if required and not value:
        raise Problem("Scrivi prima la domanda.")
    return value


def _language(value):
    raw = str(value or "it").strip().lower().replace("_", "-")
    code = raw.split("-", 1)[0]
    return code if code in LANGUAGE_CODES else "it"


def canonical_snapshot(raw):
    if not isinstance(raw, dict):
        raise Problem("Lettura non valida.")
    deck = json.loads((Path(__file__).parent / "data" / "alpha74.json").read_text())["carte"]
    by_name = {card["nome"]: card for card in deck}
    items = raw.get("carte")
    if not isinstance(items, list) or not 1 <= len(items) <= 7:
        raise Problem("Servono da una a sette carte già estratte.")
    cards, seen = [], set()
    for item in items:
        if not isinstance(item, dict):
            raise Problem("Carta non valida.")
        name = item.get("carta")
        card = by_name.get(name) if isinstance(name, str) else None
        axis, polarity = item.get("asse"), item.get("polarita")
        if not card or card["id"] in seen or axis not in ("nord", "est", "sud", "ovest") or polarity not in ("luce", "ombra"):
            raise Problem("Carta, direzione o polarità non valida: nessuna estrazione sostitutiva.")
        seen.add(card["id"])
        cards.append({"id": card["id"], "carta": card["nome"], "asse": axis, "polarita": polarity,
                      "posizione": _text(item.get("posizione", ""), 30, True),
                      "posizione_label": _text(item.get("posizione_label", ""), 50, True),
                      "significato_canonico": card[polarity][axis]})
    reading = raw.get("lettura")
    if not isinstance(reading, dict):
        raise Problem("Manca l'interpretazione della lettura.")
    interpretation = {key: _text(reading.get(key, ""), 6000) for key in ("messaggio", "nodo", "direzione", "domanda_finale")}
    if not interpretation["messaggio"]:
        raise Problem("Analizza prima la stesa sul sito.")
    history = raw.get("cronologia", [])
    if not isinstance(history, list) or len(history) > 100:
        raise Problem("Cronologia non valida.")
    imported = []
    for turn in history:
        if not isinstance(turn, dict):
            raise Problem("Cronologia non valida.")
        imported.append({"domanda": _text(turn.get("domanda", ""), 4000, True),
                         "risposta": _text(turn.get("risposta", ""), 8000, True), "origine": "sito-importato"})
    language = str(raw.get("lingua") or raw.get("language") or "it").strip().lower().replace("_", "-").split("-", 1)[0]
    if language not in {"it", "en", "fr", "es"}:
        language = "it"
    snapshot = {"versione": 1, "sistema": "Canone Alpha 74", "origine": "sito",
                "domanda": _text(raw.get("domanda", ""), 1800), "contesto": _text(raw.get("contesto", ""), 3200),
                "carte": cards, "lettura": interpretation, "cronologia": imported}
    # Italian remains the historical default, so old snapshots keep their exact
    # fingerprint; non-Italian readings carry the chosen language forward.
    if language != "it":
        snapshot["lingua"] = language
    return snapshot


def save_reading(owner, raw):
    snapshot = canonical_snapshot(raw)
    source_id = _text(raw.get("lettura_id", ""), 80, True)
    payload = _json(snapshot)
    fingerprint = _hash(payload)
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        old = conn.execute("SELECT * FROM r3_readings WHERE owner=? AND source_id=?", (owner, source_id)).fetchone()
        if old:
            if old["fingerprint"] != fingerprint:
                raise Problem("Questa lettura è già salvata. Le carte e il contesto restano invariati.", 409)
            return old["id"]
        rid = secrets.token_hex(16)
        conn.execute("INSERT INTO r3_readings VALUES (?,?,?,?,?,?)", (rid, owner, source_id, fingerprint, payload, int(time.time())))
        return rid


def reading(owner, rid):
    if not isinstance(rid, str) or not re.fullmatch(r"[a-f0-9]{32}", rid):
        raise Problem("Identificativo della lettura non valido.", 400)
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM r3_readings WHERE id=? AND owner=?", (rid, owner)).fetchone()
    if not row:
        raise Problem("Lettura non disponibile in questo account.", 404)
    return {"id": row["id"], "created": row["created"], "snapshot": json.loads(row["snapshot"]),
            "cronologia": history(owner, rid, limit=30)}


def readings(owner):
    with db.connect() as conn:
        rows = conn.execute("SELECT id,snapshot,created FROM r3_readings WHERE owner=? ORDER BY created DESC,rowid DESC LIMIT 30", (owner,)).fetchall()
    return [{"id": r["id"], "domanda": json.loads(r["snapshot"])["domanda"], "created": r["created"],
             "carte": [c["carta"] for c in json.loads(r["snapshot"])["carte"]]} for r in rows]


def current(owner):
    with db.connect() as conn:
        conn.execute("INSERT OR IGNORE INTO r3_dialogues VALUES (?,?,NULL)", (owner, secrets.token_hex(16)))
        return dict(conn.execute("SELECT * FROM r3_dialogues WHERE owner=?", (owner,)).fetchone())


def select(owner, rid=None):
    if rid:
        reading(owner, rid)
    current(owner)
    with db.connect() as conn:
        conn.execute("UPDATE r3_dialogues SET active_reading=?,thread=? WHERE owner=?", (rid, secrets.token_hex(16), owner))
        conn.execute("UPDATE r3_drafts SET status='superseded' WHERE owner=? AND status IN ('pending','failed')", (owner,))


def history(owner, thread, limit=8):
    with db.connect() as conn:
        rows = conn.execute("SELECT id,question,answer FROM r3_drafts WHERE owner=? AND thread=? AND status='done' ORDER BY updated DESC,rowid DESC LIMIT ?", (owner, thread, limit)).fetchall()
    return [{"id": r["id"], "domanda": r["question"], "risposta": json.loads(r["answer"])["risposta"], "origine": "raffaello"} for r in reversed(rows)]


def stage(owner, question, client_id, rid=None, use_current=False, language="it"):
    question = _text(question, 4000, True)
    client_id = _text(client_id, 100, True)
    language = _language(language)
    state = current(owner)
    if use_current:
        rid = state["active_reading"]
    if rid:
        reading(owner, rid)
    thread = rid or state["thread"]
    now = int(time.time())
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        old = conn.execute("SELECT * FROM r3_drafts WHERE owner=? AND client_id=?", (owner, client_id)).fetchone()
        if old:
            if old["question"] != question or old["reading_id"] != rid:
                raise Problem("Identificativo già usato per un'altra domanda.", 409)
            return dict(old)
        conn.execute("UPDATE r3_drafts SET status='superseded' WHERE owner=? AND status IN ('pending','failed')", (owner,))
        did = secrets.token_hex(16)
        conn.execute("INSERT INTO r3_drafts (id,owner,client_id,thread,reading_id,question,status,answer,created,updated,language) VALUES (?,?,?,?,?,?,'pending',NULL,?,?,?)", (did, owner, client_id, thread, rid, question, now, now, language))
    return draft(owner, did)


def draft(owner, did):
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM r3_drafts WHERE owner=? AND id=?", (owner, did)).fetchone()
    if not row:
        raise Problem("Domanda non disponibile in questo account.", 404)
    out = dict(row)
    if out["answer"]:
        out["answer"] = json.loads(out["answer"])
    return out


def claim(owner, did):
    now = int(time.time())
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM r3_drafts WHERE owner=? AND id=?", (owner, did)).fetchone()
        if not row:
            raise Problem("Domanda non disponibile.", 404)
        if row["status"] == "done":
            return json.loads(row["answer"])
        if row["status"] == "superseded":
            raise Problem("Usa Analizza sotto la domanda più recente.", 409)
        if row["status"] == "working" and row["updated"] > now - 180:
            raise Problem("Raffaello sta già analizzando questa domanda.", 409)
        # Serialize generations per owner across the HTTP and Telegram workers.
        busy = conn.execute("SELECT 1 FROM r3_drafts WHERE owner=? AND id<>? AND status='working' AND updated>?", (owner, did, now - 180)).fetchone()
        if busy:
            raise Problem("Attendi la risposta in corso prima di analizzare la successiva.", 409)
        period = now // 3600
        conn.execute("DELETE FROM r3_quota WHERE period<?", (period - 24,))
        conn.execute("INSERT OR IGNORE INTO r3_quota VALUES (?,?,0)", (owner, period))
        quota = conn.execute("SELECT calls FROM r3_quota WHERE owner=? AND period=?", (owner, period)).fetchone()[0]
        if quota >= 30:
            raise Problem("Hai raggiunto il limite di analisi per quest'ora. Riprova più tardi.", 429)
        conn.execute("UPDATE r3_quota SET calls=calls+1 WHERE owner=? AND period=?", (owner, period))
        conn.execute("UPDATE r3_drafts SET status='working',updated=? WHERE owner=? AND id=?", (now, owner, did))
    return None


def complete(owner, did, answer=None):
    with db.connect() as conn:
        conn.execute("UPDATE r3_drafts SET status=?,answer=?,updated=? WHERE owner=? AND id=? AND status='working'",
                     ("done" if answer else "failed", _json(answer) if answer else None, int(time.time()), owner, did))


def link_code(owner):
    code = secrets.token_hex(8).upper()
    now = int(time.time())
    with db.connect() as conn:
        conn.execute("DELETE FROM r3_links WHERE owner=? OR expires<?", (owner, now))
        conn.execute("INSERT INTO r3_links VALUES (?,?,?)", (_hash(code), owner, now + 600))
    return "-".join(code[i:i+4] for i in range(0, 16, 4))


def exchange(code):
    code = re.sub(r"[\s-]", "", _text(code, 40)).upper()
    token, now = secrets.token_urlsafe(32), int(time.time())
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT owner FROM r3_links WHERE digest=? AND expires>?", (_hash(code), now)).fetchone()
        if not row:
            raise Problem("Codice scaduto o già utilizzato. Richiedi /collega nel bot.", 401)
        conn.execute("DELETE FROM r3_links WHERE digest=?", (_hash(code),))
        conn.execute("DELETE FROM r3_sessions WHERE expires<?", (now,))
        conn.execute("INSERT INTO r3_sessions VALUES (?,?,?)", (_hash(token), row["owner"], now + 30*86400))
    return token, row["owner"]


def session_owner(token):
    if not isinstance(token, str) or not token or len(token) > 100:
        raise Problem("Collega prima il tuo account Telegram.", 401)
    with db.connect() as conn:
        row = conn.execute("SELECT owner FROM r3_sessions WHERE digest=? AND expires>?", (_hash(token), int(time.time()))).fetchone()
    if not row:
        raise Problem("Collegamento scaduto. Richiedi /collega nel bot.", 401)
    return row["owner"]


def revoke(owner):
    with db.connect() as conn:
        conn.execute("DELETE FROM r3_sessions WHERE owner=?", (owner,))
        conn.execute("DELETE FROM r3_links WHERE owner=?", (owner,))
