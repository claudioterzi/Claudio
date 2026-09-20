"""
R3∞ MVP — nodo singolo.
ID documenti = SHA-256 del contenuto (content-addressed).
Sync e integrity check delegati a sync.py esterno.

RRR control plane:
- activation events are signed by a separate controller key;
- nodes keep only the trusted verification key;
- the latest valid signed counter is authoritative locally;
- sync.py relays the same signed event to peers.
"""

import hashlib
import logging
import os
import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import nacl.encoding
import nacl.signing
from fastapi import Body, FastAPI, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse

try:
    from .rrr_control import POLICY as RRR_POLICY, POLICY_SHA256 as RRR_POLICY_SHA256, PROTOCOL as RRR_PROTOCOL, RRRControlError, verify_event
except ImportError:  # Railway single-file image
    from rrr_control import POLICY as RRR_POLICY, POLICY_SHA256 as RRR_POLICY_SHA256, PROTOCOL as RRR_PROTOCOL, RRRControlError, verify_event

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_DIR   = Path(os.getenv("R3_DATA_DIR", "data"))
DB_PATH    = DATA_DIR / "r3.db"
API_TOKEN  = os.getenv("R3_API_TOKEN", "changeme")
NODE_ID    = os.getenv("R3_NODE_ID", "node-a")
SIGNING_KEY_HEX = os.getenv("R3_SIGNING_KEY_HEX", "")
CONTROL_VERIFY_KEY_HEX = os.getenv("R3_CONTROL_VERIFY_KEY_HEX", "").strip()
REQUIRE_RRR_ACTIVE = os.getenv("R3_REQUIRE_RRR_ACTIVE", "true").strip().lower() in {"1", "true", "yes"}
ALLOW_TEST_SHUTDOWN = os.getenv("R3_ALLOW_TEST_SHUTDOWN", "").strip().lower() in {"1", "true", "yes"}

DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(DATA_DIR / "r3.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("r3")

# ---------------------------------------------------------------------------
# Ed25519 — generata una volta, persistita su disco
# ---------------------------------------------------------------------------

_KEY_FILE = DATA_DIR / "signing.key"

def _load_signing_key() -> nacl.signing.SigningKey:
    if SIGNING_KEY_HEX:
        return nacl.signing.SigningKey(bytes.fromhex(SIGNING_KEY_HEX))
    if _KEY_FILE.exists():
        return nacl.signing.SigningKey(_KEY_FILE.read_bytes())
    key = nacl.signing.SigningKey.generate()
    _KEY_FILE.write_bytes(bytes(key))
    _KEY_FILE.chmod(0o600)
    log.info("Nuova chiave di firma generata → %s", _KEY_FILE)
    return key

SIGNING_KEY   = _load_signing_key()
VERIFY_KEY_HEX = SIGNING_KEY.verify_key.encode(nacl.encoding.HexEncoder).decode()

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c

def _init_db() -> None:
    with _conn() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id          TEXT PRIMARY KEY,
                filename    TEXT NOT NULL,
                sha256      TEXT NOT NULL,
                signature   TEXT NOT NULL,
                size        INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL,
                deleted     INTEGER DEFAULT 0
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                event  TEXT NOT NULL,
                detail TEXT,
                ts     TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS protocol_events (
                event_id     TEXT PRIMARY KEY,
                protocol     TEXT NOT NULL,
                policy_sha256 TEXT NOT NULL DEFAULT '',
                action       TEXT NOT NULL,
                scope        TEXT NOT NULL,
                counter      INTEGER NOT NULL UNIQUE,
                issued_at    TEXT NOT NULL,
                nonce        TEXT NOT NULL UNIQUE,
                issuer       TEXT NOT NULL,
                signature    TEXT NOT NULL,
                received_at  TEXT NOT NULL,
                source_node  TEXT
            )
        """)
        columns = {
            row[1]
            for row in db.execute("PRAGMA table_info(protocol_events)").fetchall()
        }
        if "policy_sha256" not in columns:
            db.execute(
                "ALTER TABLE protocol_events "
                "ADD COLUMN policy_sha256 TEXT NOT NULL DEFAULT ''"
            )

_init_db()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc_path(doc_id: str) -> Path:
    return DATA_DIR / "docs" / doc_id

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _sign(data: bytes) -> str:
    return SIGNING_KEY.sign(data).signature.hex()

def _audit_db(db: sqlite3.Connection, event: str, detail: str = "") -> None:
    db.execute(
        "INSERT INTO audit_log (event, detail, ts) VALUES (?, ?, ?)",
        (event, detail, datetime.now(timezone.utc).isoformat()),
    )


def _audit(event: str, detail: str = "") -> None:
    with _conn() as db:
        _audit_db(db, event, detail)

def _check_token(authorization: Optional[str]) -> None:
    if not API_TOKEN or API_TOKEN == "changeme":
        raise HTTPException(status_code=503, detail="Token del nodo non configurato")
    expected = f"Bearer {API_TOKEN}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Token non valido")

def _rrr_latest() -> dict[str, Any] | None:
    with _conn() as db:
        row = db.execute(
            """SELECT event_id, protocol, policy_sha256, action, scope, counter, issued_at,
                      nonce, issuer, signature, received_at, source_node
               FROM protocol_events
               WHERE protocol = ?
               ORDER BY counter DESC
               LIMIT 1""",
            (RRR_PROTOCOL,),
        ).fetchone()
    return dict(row) if row else None

def _apply_rrr_event(event: dict[str, Any], source_node: str = "") -> tuple[str, dict[str, Any]]:
    if not CONTROL_VERIFY_KEY_HEX:
        raise HTTPException(
            status_code=503,
            detail="Controller RRR non configurato: R3_CONTROL_VERIFY_KEY_HEX assente",
        )
    try:
        payload = verify_event(event, CONTROL_VERIFY_KEY_HEX)
    except RRRControlError as exc:
        raise HTTPException(status_code=422, detail=f"Evento RRR non valido: {exc}") from exc

    event_id = str(event["event_id"])
    signature = str(event["signature"])
    received_at = datetime.now(timezone.utc).isoformat()

    # Ordering check + insert + audit are one serialized transaction.
    # This prevents a concurrent stale writer from being acknowledged after a
    # newer event has already committed.
    db = _conn()
    try:
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            """SELECT event_id, protocol, policy_sha256, action, scope, counter,
                      issued_at, nonce, issuer, signature, received_at, source_node
               FROM protocol_events
               WHERE protocol = ?
               ORDER BY counter DESC
               LIMIT 1""",
            (RRR_PROTOCOL,),
        ).fetchone()
        latest = dict(row) if row else None

        if latest and latest["event_id"] == event_id:
            db.execute("COMMIT")
            return "already_applied", latest
        if latest and payload["counter"] < latest["counter"]:
            db.execute("ROLLBACK")
            raise HTTPException(status_code=409, detail="Evento RRR obsoleto")
        if latest and payload["counter"] == latest["counter"]:
            db.execute("ROLLBACK")
            raise HTTPException(status_code=409, detail="Conflitto RRR: stesso counter, evento diverso")

        try:
            db.execute(
                """INSERT INTO protocol_events
                   (event_id, protocol, policy_sha256, action, scope, counter, issued_at,
                    nonce, issuer, signature, received_at, source_node)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event_id,
                    payload["protocol"],
                    payload["policy_sha256"],
                    payload["action"],
                    payload["scope"],
                    payload["counter"],
                    payload["issued_at"],
                    payload["nonce"],
                    payload["issuer"],
                    signature,
                    received_at,
                    source_node or None,
                ),
            )
        except sqlite3.IntegrityError as exc:
            db.execute("ROLLBACK")
            raise HTTPException(status_code=409, detail="Replay/conflitto evento RRR") from exc

        _audit_db(
            db,
            "rrr_event",
            f"event_id={event_id} action={payload['action']} counter={payload['counter']} "
            f"policy_sha256={payload['policy_sha256']} issuer={payload['issuer']} "
            f"source_reported={source_node or 'unknown'}",
        )
        db.execute("COMMIT")
    except HTTPException:
        raise
    except Exception:
        try:
            db.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        db.close()

    current = _rrr_latest()
    assert current is not None
    return "applied", current

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title=f"R3∞ {NODE_ID}", version="0.2.0")


# Liveness: process is up. This deliberately does not claim network readiness.
@app.get("/health")
def health():
    return {"status": "healthy", "node_id": NODE_ID}


def _readiness_state() -> dict[str, Any]:
    latest = _rrr_latest()
    active = bool(latest and latest["action"] == "activate")
    reasons: list[str] = []
    if not API_TOKEN or API_TOKEN == "changeme":
        reasons.append("api_token_not_configured")
    if not CONTROL_VERIFY_KEY_HEX:
        reasons.append("rrr_controller_key_not_configured")
    if REQUIRE_RRR_ACTIVE and not active:
        reasons.append("rrr_not_active")
    return {
        "ready": not reasons,
        "node_id": NODE_ID,
        "protocol": RRR_PROTOCOL,
        "policy_sha256": RRR_POLICY_SHA256,
        "rrr_active": active,
        "rrr_event_id": latest["event_id"] if latest else None,
        "reasons": reasons,
    }


# Readiness: a node may be alive while still quarantined from active network use.
@app.get("/ready")
def ready():
    state = _readiness_state()
    return JSONResponse(status_code=200 if state["ready"] else 503, content=state)


# Stato nodo — con auth
@app.get("/status")
def status(authorization: Optional[str] = Header(None)):
    _check_token(authorization)
    with _conn() as db:
        count = db.execute(
            "SELECT COUNT(*) FROM documents WHERE deleted = 0"
        ).fetchone()[0]
        storage = sum(f.stat().st_size for f in (DATA_DIR / "docs").glob("*")) \
            if (DATA_DIR / "docs").exists() else 0
    rrr = _rrr_latest()
    readiness = _readiness_state()
    return {
        "node_id":    NODE_ID,
        "documents":  count,
        "storage_bytes": storage,
        "verify_key": VERIFY_KEY_HEX,
        "rrr_active": bool(rrr and rrr["action"] == "activate"),
        "rrr_protocol": RRR_PROTOCOL,
        "rrr_policy_sha256": RRR_POLICY_SHA256,
        "rrr_event_id": rrr["event_id"] if rrr else None,
        "network_ready": readiness["ready"],
        "readiness_reasons": readiness["reasons"],
        "ts":         datetime.now(timezone.utc).isoformat(),
    }


# Canonical machine-readable policy. Public by design: no secret material.
@app.get("/protocol/rrr/policy")
def rrr_policy():
    return {**RRR_POLICY, "policy_sha256": RRR_POLICY_SHA256}


# RRR network state — authenticated because it exposes control-plane metadata.
@app.get("/protocol/rrr/status")
def rrr_status(authorization: Optional[str] = Header(None)):
    _check_token(authorization)
    latest = _rrr_latest()
    return {
        "node_id": NODE_ID,
        "protocol": RRR_PROTOCOL,
        "policy_sha256": RRR_POLICY_SHA256,
        "active": bool(latest and latest["action"] == "activate"),
        "controller_configured": bool(CONTROL_VERIFY_KEY_HEX),
        "counter": latest["counter"] if latest else None,
        "event_id": latest["event_id"] if latest else None,
        "event": latest,
        "source_node_trust": "bearer_transport_reported_not_controller_authenticated",
    }


@app.post("/protocol/rrr/event")
def rrr_event(
    event: dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None),
    x_r3_source_node: Optional[str] = Header(None),
):
    _check_token(authorization)
    state, current = _apply_rrr_event(event, x_r3_source_node or "")
    return {
        "status": state,
        "node_id": NODE_ID,
        "active": current["action"] == "activate",
        "protocol": current["protocol"],
        "counter": current["counter"],
        "event_id": current["event_id"],
    }


# 1. Upload
@app.post("/documents")
async def upload(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
):
    _check_token(authorization)
    data   = await file.read()
    doc_id = _sha256(data)          # ID = hash del contenuto
    sig    = _sign(data)

    dest = _doc_path(doc_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)

    with _conn() as db:
        if not db.execute("SELECT 1 FROM documents WHERE id = ?", (doc_id,)).fetchone():
            db.execute(
                """INSERT INTO documents
                   (id, filename, sha256, signature, size, uploaded_at, deleted)
                   VALUES (?, ?, ?, ?, ?, ?, 0)""",
                (doc_id, file.filename or doc_id, doc_id, sig,
                 len(data), datetime.now(timezone.utc).isoformat()),
            )

    _audit("upload", f"id={doc_id} file={file.filename} size={len(data)}")
    log.info("Stored  id=%s  file=%s", doc_id, file.filename)
    return {"id": doc_id, "sha256": doc_id, "signature": sig, "size": len(data)}


# 2. Download
@app.get("/documents/{doc_id}")
def download(
    doc_id: str,
    authorization: Optional[str] = Header(None),
):
    _check_token(authorization)
    path = _doc_path(doc_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Documento non trovato")
    with _conn() as db:
        row = db.execute(
            "SELECT filename FROM documents WHERE id = ? AND deleted = 0", (doc_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    return FileResponse(str(path), filename=row["filename"])


# 3. Info documento
@app.get("/documents/{doc_id}/info")
def doc_info(
    doc_id: str,
    authorization: Optional[str] = Header(None),
):
    _check_token(authorization)
    with _conn() as db:
        row = db.execute(
            "SELECT * FROM documents WHERE id = ? AND deleted = 0", (doc_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    return dict(row)


# 4. Lista hash — usata da sync.py per confronto
@app.get("/sync/hashes")
def sync_hashes(authorization: Optional[str] = Header(None)):
    _check_token(authorization)
    with _conn() as db:
        rows = db.execute(
            "SELECT id, sha256, size, uploaded_at FROM documents WHERE deleted = 0"
        ).fetchall()
    return {
        "node_id":   NODE_ID,
        "documents": [dict(r) for r in rows],
    }


# 5. Ricevi documento da altro nodo
@app.post("/sync/receive")
async def sync_receive(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
):
    _check_token(authorization)
    data        = await file.read()
    actual_hash = _sha256(data)

    dest = _doc_path(actual_hash)
    if dest.exists():
        return {"status": "already_exists", "id": actual_hash}

    sig = _sign(data)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)

    with _conn() as db:
        db.execute(
            """INSERT OR IGNORE INTO documents
               (id, filename, sha256, signature, size, uploaded_at, deleted)
               VALUES (?, ?, ?, ?, ?, ?, 0)""",
            (actual_hash, file.filename or actual_hash, actual_hash, sig,
             len(data), datetime.now(timezone.utc).isoformat()),
        )

    _audit("sync_receive", f"id={actual_hash} size={len(data)}")
    log.info("Sync received  id=%s", actual_hash)
    return {"status": "stored", "id": actual_hash}


# ---------------------------------------------------------------------------
# Test-only process shutdown hook
# ---------------------------------------------------------------------------

@app.post("/test/shutdown")
def test_shutdown(authorization: Optional[str] = Header(None)):
    """
    Authenticated test hook used only by the external failover property test.

    Disabled by default. It exists to make process loss observable without
    adding a production control plane. Enabling it requires BOTH:
      1. R3_ALLOW_TEST_SHUTDOWN=true
      2. the normal Bearer token.

    It must never be described as a production failover mechanism.
    """
    _check_token(authorization)
    if not ALLOW_TEST_SHUTDOWN:
        raise HTTPException(status_code=404, detail="Test shutdown non abilitato")

    _audit("test_shutdown", f"node_id={NODE_ID}")
    log.warning("Authenticated external property test requested process shutdown")

    def _exit_process() -> None:
        os._exit(0)

    threading.Timer(0.35, _exit_process).start()
    return {"status": "shutting_down_for_test", "node_id": NODE_ID}
