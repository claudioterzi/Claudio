"""R3-PEER-RECEIPT/1: authenticated, replay-safe advisory receipts.

Bounded extension to the existing RRR Ed25519/SQLite node. No provider
activation, consensus, commands, or permission elevation is inferred here.
The host must provision trusted public keys out-of-band and authenticate callers
before issuing challenges or returning private checkpoint references.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import secrets
import sqlite3
import time
from typing import Any, Mapping

PROTOCOL = "R3-PEER-RECEIPT/1"
KINDS = frozenset({"HEARTBEAT", "PROVIDER_RUN", "CHECKPOINT"})
CLASSES = frozenset({"PUBLIC", "PRIVATE", "SEALED"})
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX128 = re.compile(r"^[0-9a-f]{128}$")
SAFE_ID = re.compile(r"^[a-zA-Z0-9._:-]{1,96}$")
VAULT_REF = re.compile(r"^vault://[a-zA-Z0-9._/-]{1,192}$")
MAX_BYTES = 8192
CHALLENGE_TTL = 120
RECENT_SECONDS = 90
GENESIS = "0" * 64
FIELDS = frozenset({"protocol", "node_id", "kind", "challenge", "issued_at", "payload"})


class ReceiptError(ValueError):
    """Receipt cannot be trusted or written."""


def canonical(data: Any) -> bytes:
    try:
        return json.dumps(data, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError) as exc:
        raise ReceiptError("invalid JSON") from exc


def _verify_ed25519(key_hex: str, raw: bytes, signature_hex: str) -> None:
    try:
        public_key = bytes.fromhex(key_hex)
        signature = bytes.fromhex(signature_hex)
        if len(public_key) != 32 or len(signature) != 64:
            raise ValueError("wrong key/signature length")
    except (TypeError, ValueError) as exc:
        raise ReceiptError("invalid key or signature encoding") from exc
    try:
        import nacl.signing
        import nacl.exceptions
        nacl.signing.VerifyKey(public_key).verify(raw, signature)
    except ImportError:
        # Equivalent Ed25519 verifier for tests/hosts without PyNaCl.
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
        try:
            Ed25519PublicKey.from_public_bytes(public_key).verify(signature, raw)
        except (InvalidSignature, ValueError) as exc:
            raise ReceiptError("signature verification failed") from exc
    except (nacl.exceptions.BadSignatureError, ValueError) as exc:
        raise ReceiptError("signature verification failed") from exc


def _validate_body(body: Any) -> None:
    if not isinstance(body, dict) or set(body) != FIELDS:
        raise ReceiptError("unsupported envelope fields")
    if body["protocol"] != PROTOCOL:
        raise ReceiptError("protocol mismatch")
    if not isinstance(body["node_id"], str) or not SAFE_ID.fullmatch(body["node_id"]):
        raise ReceiptError("invalid node_id")
    if not isinstance(body["kind"], str) or body["kind"] not in KINDS:
        raise ReceiptError("unsupported kind")
    if not isinstance(body["challenge"], str) or not re.fullmatch(r"[a-f0-9]{48}", body["challenge"]):
        raise ReceiptError("invalid challenge")
    if not isinstance(body["issued_at"], int) or isinstance(body["issued_at"], bool):
        raise ReceiptError("issued_at must be an integer epoch")
    payload = body["payload"]
    if not isinstance(payload, dict):
        raise ReceiptError("payload must be an object")
    if body["kind"] == "HEARTBEAT":
        if set(payload) != {"runtime_id", "boot_id"}:
            raise ReceiptError("heartbeat payload invalid")
        for key in ("runtime_id", "boot_id"):
            if not isinstance(payload[key], str) or not SAFE_ID.fullmatch(payload[key]):
                raise ReceiptError("invalid heartbeat identity")
    if body["kind"] == "PROVIDER_RUN":
        if set(payload) != {"provider", "model", "request_sha256", "response_sha256", "runtime_id"}:
            raise ReceiptError("provider run payload invalid")
        for key in ("request_sha256", "response_sha256"):
            if not isinstance(payload[key], str) or not HEX64.fullmatch(payload[key]):
                raise ReceiptError("invalid digest")
        for key in ("provider", "model", "runtime_id"):
            if not isinstance(payload[key], str) or not SAFE_ID.fullmatch(payload[key]):
                raise ReceiptError("invalid provider field")
    if body["kind"] == "CHECKPOINT":
        if set(payload) != {"classification", "sha256", "ref", "readers", "text"}:
            raise ReceiptError("checkpoint payload invalid")
        cls = payload["classification"]
        if not isinstance(cls, str) or cls not in CLASSES or not isinstance(payload["sha256"], str) or not HEX64.fullmatch(payload["sha256"]):
            raise ReceiptError("checkpoint classification/digest invalid")
        readers = payload["readers"]
        if not isinstance(readers, list) or len(readers) > 16 or len(readers) != len(set(map(str, readers))) or not all(isinstance(x, str) and SAFE_ID.fullmatch(x) for x in readers):
            raise ReceiptError("invalid checkpoint readers")
        if cls == "PUBLIC":
            if payload["ref"] is not None or not isinstance(payload["text"], str) or len(payload["text"]) > 1024:
                raise ReceiptError("public checkpoint must contain bounded text only")
            if hashlib.sha256(payload["text"].encode("utf-8")).hexdigest() != payload["sha256"]:
                raise ReceiptError("public checkpoint digest mismatch")
        else:
            if payload["text"] is not None or not isinstance(payload["ref"], str) or not VAULT_REF.fullmatch(payload["ref"]):
                raise ReceiptError("private checkpoint must contain only an opaque vault reference")


def _digest(prev: str, body: dict[str, Any], signature: str) -> str:
    return hashlib.sha256(bytes.fromhex(prev) + canonical(body) + bytes.fromhex(signature)).hexdigest()


class PeerReceiptJournal:
    """Trusted key registry is host policy, NEVER model-supplied data.

    `trusted` maps a node ID to {"verify_key": Ed25519 hex,
    "scopes": ["HEARTBEAT", "PROVIDER_RUN", "CHECKPOINT"], "active": bool}.
    The caller must authenticate before exposing issue_challenge or checkpoint
    content, including when running behind an existing R3 bearer-protected API.
    """

    def __init__(self, path: str | Path, trusted: Mapping[str, Mapping[str, Any]]):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.trusted = dict(trusted)
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS peer_challenges (
                nonce TEXT PRIMARY KEY, node_id TEXT NOT NULL, kind TEXT NOT NULL,
                created_at INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0)""")
            db.execute("""CREATE TABLE IF NOT EXISTS peer_receipts (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, node_id TEXT NOT NULL,
                kind TEXT NOT NULL, body TEXT NOT NULL, signature TEXT NOT NULL,
                previous_hash TEXT NOT NULL, hash TEXT NOT NULL UNIQUE,
                accepted_at INTEGER NOT NULL)""")
        if self.path.exists():
            self.path.chmod(0o600)

    @contextmanager
    def _db(self):
        db = sqlite3.connect(str(self.path), timeout=10)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _trusted(self, node_id: str, kind: str) -> Mapping[str, Any]:
        policy = self.trusted.get(node_id)
        if not policy or policy.get("active") is not True or kind not in policy.get("scopes", ()):
            raise ReceiptError("node not authorized for requested scope")
        key = policy.get("verify_key")
        if not isinstance(key, str) or not HEX64.fullmatch(key):
            raise ReceiptError("trusted public key missing")
        return policy

    def issue_challenge(self, node_id: str, kind: str, *, now: int | None = None) -> dict[str, Any]:
        self._trusted(node_id, kind)
        stamp = int(time.time()) if now is None else now
        nonce = secrets.token_hex(24)
        with self._db() as db:
            db.execute("DELETE FROM peer_challenges WHERE created_at < ?", (stamp - CHALLENGE_TTL,))
            outstanding = db.execute("SELECT COUNT(*) FROM peer_challenges WHERE node_id=? AND used=0", (node_id,)).fetchone()[0]
            if outstanding >= 16:
                raise ReceiptError("too many open challenges")
            db.execute("INSERT INTO peer_challenges(nonce,node_id,kind,created_at) VALUES(?,?,?,?)",
                       (nonce, node_id, kind, stamp))
        return {"protocol": PROTOCOL, "node_id": node_id, "kind": kind,
                "challenge": nonce, "expires_at": stamp + CHALLENGE_TTL}

    def accept(self, envelope: dict[str, Any], *, now: int | None = None) -> dict[str, Any]:
        if not isinstance(envelope, dict) or set(envelope) != FIELDS | {"signature"}:
            raise ReceiptError("invalid signed envelope")
        signature = envelope["signature"]
        if not isinstance(signature, str) or not HEX128.fullmatch(signature):
            raise ReceiptError("invalid signature encoding")
        body = {k: v for k, v in envelope.items() if k != "signature"}
        if len(canonical(body)) > MAX_BYTES:
            raise ReceiptError("receipt too large")
        _validate_body(body)
        key = self._trusted(body["node_id"], body["kind"])["verify_key"]
        _verify_ed25519(key, canonical(body), signature)
        if not self.audit()["ok"]:
            raise ReceiptError("existing ledger integrity failure")
        stamp = int(time.time()) if now is None else now
        if abs(stamp - body["issued_at"]) > CHALLENGE_TTL:
            raise ReceiptError("stale or future-dated receipt")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            challenge = db.execute("SELECT * FROM peer_challenges WHERE nonce=?",
                                   (body["challenge"],)).fetchone()
            if (challenge is None or challenge["node_id"] != body["node_id"] or
                challenge["kind"] != body["kind"] or challenge["used"] != 0 or
                not 0 <= stamp - challenge["created_at"] <= CHALLENGE_TTL):
                raise ReceiptError("unknown, expired, or consumed challenge")
            db.execute("UPDATE peer_challenges SET used=1 WHERE nonce=? AND used=0", (body["challenge"],))
            previous = db.execute("SELECT hash FROM peer_receipts ORDER BY seq DESC LIMIT 1").fetchone()
            previous_hash = previous[0] if previous else GENESIS
            event_hash = _digest(previous_hash, body, signature)
            db.execute("""INSERT INTO peer_receipts(node_id,kind,body,signature,previous_hash,hash,accepted_at)
                          VALUES(?,?,?,?,?,?,?)""",
                       (body["node_id"], body["kind"], canonical(body).decode(), signature,
                        previous_hash, event_hash, stamp))
            seq = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"seq": seq, "hash": event_hash, "state": "SIGNED_NODE_RECEIPT",
                "provider_state": "UNVERIFIED", "execution_authority": False}

    def audit(self) -> dict[str, Any]:
        previous = GENESIS
        count = 0
        with self._db() as db:
            rows = db.execute("SELECT * FROM peer_receipts ORDER BY seq").fetchall()
        for row in rows:
            try:
                body = json.loads(row["body"])
                _validate_body(body)
                _verify_ed25519(self.trusted[row["node_id"]]["verify_key"], canonical(body), row["signature"])
                if row["previous_hash"] != previous or row["hash"] != _digest(previous, body, row["signature"]):
                    raise ReceiptError("hash chain mismatch")
            except (ReceiptError, KeyError, ValueError, TypeError) as exc:
                return {"ok": False, "count": count, "reason": str(exc), "head": previous}
            previous = row["hash"]
            count += 1
        return {"ok": True, "count": count, "head": previous}

    def view(self, actor: str, *, authenticated: bool) -> list[dict[str, Any]]:
        """Read checkpoint records only for an authenticated host principal.

        `actor='OWNER'` is reserved for the authenticated controller, never
        accepted from request JSON directly. For others, the caller must prove
        the peer's identity before setting `authenticated=True`.
        """
        if not authenticated:
            raise ReceiptError("authenticated principal required")
        if actor != "OWNER":
            self._trusted(actor, "CHECKPOINT")
        if not self.audit()["ok"]:
            raise ReceiptError("audit chain invalid")
        visible: list[dict[str, Any]] = []
        with self._db() as db:
            rows = db.execute("SELECT node_id,body,hash FROM peer_receipts WHERE kind='CHECKPOINT' ORDER BY seq").fetchall()
        for row in rows:
            p = json.loads(row["body"])["payload"]
            cls = p["classification"]
            if cls == "PUBLIC" or actor == "OWNER" or actor == row["node_id"] or actor in p["readers"]:
                visible.append({"writer": row["node_id"], "hash": row["hash"], "checkpoint": p})
        return visible

    def status(self, *, now: int | None = None) -> dict[str, Any]:
        stamp = int(time.time()) if now is None else now
        chain = self.audit()
        if not chain["ok"]:
            return {"state": "WATCH_BLOCKED", "audit": chain, "nodes": {}}
        with self._db() as db:
            rows = db.execute("SELECT node_id,MAX(accepted_at) AS ts FROM peer_receipts WHERE kind='HEARTBEAT' GROUP BY node_id").fetchall()
        beats = {row["node_id"]: row["ts"] for row in rows}
        nodes = {}
        for node_id, p in self.trusted.items():
            ts = beats.get(node_id)
            nodes[node_id] = {
                "state": "UNVERIFIED" if ts is None else ("SIGNED_RECENT" if 0 <= stamp-ts <= RECENT_SECONDS and p.get("active") is True else "STALE"),
                "last_signed_heartbeat": ts,
                "provider_execution": "UNVERIFIED",
            }
        return {"state": "LOCAL_READY", "audit": chain, "nodes": nodes}