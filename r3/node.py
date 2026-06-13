"""
R3∞ MVP - Single node: upload, download, sync, integrity check.
"""

import hashlib
import logging
import os
import sqlite3
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import nacl.encoding
import nacl.signing
from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse

# ---------------------------------------------------------------------------
# Configuration (environment variables)
# ---------------------------------------------------------------------------

DATA_DIR = Path(os.getenv("R3_DATA_DIR", "data"))
DB_PATH = DATA_DIR / "r3.db"
API_TOKEN = os.getenv("R3_API_TOKEN", "changeme")
PEER_URLS: list[str] = [u for u in os.getenv("R3_PEERS", "").split(",") if u]
SYNC_INTERVAL = int(os.getenv("R3_SYNC_INTERVAL", "300"))    # seconds
INTEGRITY_INTERVAL = int(os.getenv("R3_INTEGRITY_INTERVAL", "3600"))  # seconds
SIGNING_KEY_HEX = os.getenv("R3_SIGNING_KEY_HEX", "")

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
# Ed25519 signing key (generated once and persisted if not set via env)
# ---------------------------------------------------------------------------

KEY_FILE = DATA_DIR / "signing.key"

def _load_or_create_signing_key() -> nacl.signing.SigningKey:
    if SIGNING_KEY_HEX:
        return nacl.signing.SigningKey(bytes.fromhex(SIGNING_KEY_HEX))
    if KEY_FILE.exists():
        return nacl.signing.SigningKey(KEY_FILE.read_bytes())
    key = nacl.signing.SigningKey.generate()
    KEY_FILE.write_bytes(bytes(key))
    KEY_FILE.chmod(0o600)
    log.info("Generated new signing key → %s", KEY_FILE)
    return key

SIGNING_KEY = _load_or_create_signing_key()
VERIFY_KEY_HEX = SIGNING_KEY.verify_key.encode(nacl.encoding.HexEncoder).decode()

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def _init_db() -> None:
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id        TEXT PRIMARY KEY,
                filename  TEXT NOT NULL,
                sha256    TEXT NOT NULL,
                signature TEXT NOT NULL,
                size      INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                event      TEXT NOT NULL,
                detail     TEXT,
                ts         TEXT NOT NULL
            )
        """)

_init_db()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc_path(doc_id: str) -> Path:
    return DATA_DIR / "docs" / doc_id

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _sign(data: bytes) -> str:
    signed = SIGNING_KEY.sign(data)
    return signed.signature.hex()

def _audit(event: str, detail: str = "") -> None:
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO sync_log (event, detail, ts) VALUES (?, ?, ?)",
            (event, detail, datetime.now(timezone.utc).isoformat()),
        )

def _require_token(authorization: Optional[str]) -> None:
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="R3∞ Node", version="0.1.0")


@app.get("/status")
def status():
    with _get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    return {
        "status": "ok",
        "documents": count,
        "verify_key": VERIFY_KEY_HEX,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
):
    _require_token(authorization)
    data = await file.read()
    doc_id = _sha256(data)
    sig = _sign(data)

    dest = _doc_path(doc_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)

    with _get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
        if not existing:
            conn.execute(
                """INSERT INTO documents (id, filename, sha256, signature, size, uploaded_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    doc_id,
                    file.filename or doc_id,
                    doc_id,
                    sig,
                    len(data),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
    _audit("upload", f"id={doc_id} filename={file.filename} size={len(data)}")
    log.info("Stored document id=%s filename=%s", doc_id, file.filename)
    return {"id": doc_id, "sha256": doc_id, "signature": sig, "size": len(data)}


@app.get("/documents/{doc_id}")
def download_document(
    doc_id: str,
    authorization: Optional[str] = Header(None),
):
    _require_token(authorization)
    path = _doc_path(doc_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT filename FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
    filename = row["filename"] if row else doc_id
    return FileResponse(str(path), filename=filename)


@app.get("/sync")
def sync_list(authorization: Optional[str] = Header(None)):
    """Return list of {id, sha256, size, uploaded_at} for all documents."""
    _require_token(authorization)
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, sha256, size, uploaded_at FROM documents ORDER BY uploaded_at"
        ).fetchall()
    return {"documents": [dict(r) for r in rows]}


@app.post("/sync")
async def sync_receive(
    file: UploadFile = File(...),
    doc_id: str = "",
    authorization: Optional[str] = Header(None),
):
    """Receive a document pushed by another node."""
    _require_token(authorization)
    data = await file.read()
    actual_hash = _sha256(data)

    if doc_id and doc_id != actual_hash:
        _audit("sync_reject", f"hash_mismatch claimed={doc_id} actual={actual_hash}")
        raise HTTPException(status_code=400, detail="Hash mismatch")

    real_id = actual_hash
    dest = _doc_path(real_id)
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        return {"status": "already_exists", "id": real_id}

    sig = _sign(data)
    dest.write_bytes(data)

    with _get_conn() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO documents (id, filename, sha256, signature, size, uploaded_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                real_id,
                file.filename or real_id,
                real_id,
                sig,
                len(data),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    _audit("sync_receive", f"id={real_id} size={len(data)}")
    log.info("Sync received document id=%s", real_id)
    return {"status": "stored", "id": real_id}

# ---------------------------------------------------------------------------
# Background: periodic sync with peers
# ---------------------------------------------------------------------------

def _sync_with_peer(peer_url: str) -> None:
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        resp = httpx.get(f"{peer_url}/sync", headers=headers, timeout=30)
        resp.raise_for_status()
        peer_docs = {d["id"] for d in resp.json().get("documents", [])}

        with _get_conn() as conn:
            local_ids = {
                r[0]
                for r in conn.execute("SELECT id FROM documents").fetchall()
            }

        missing = peer_docs - local_ids
        for doc_id in missing:
            try:
                doc_resp = httpx.get(
                    f"{peer_url}/documents/{doc_id}",
                    headers=headers,
                    timeout=60,
                )
                doc_resp.raise_for_status()
                data = doc_resp.content
                actual_hash = _sha256(data)
                if actual_hash != doc_id:
                    log.warning("Hash mismatch pulling %s from %s", doc_id, peer_url)
                    _audit("sync_hash_mismatch", f"peer={peer_url} id={doc_id}")
                    continue
                dest = _doc_path(doc_id)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                sig = _sign(data)
                with _get_conn() as conn:
                    conn.execute(
                        """INSERT OR IGNORE INTO documents
                           (id, filename, sha256, signature, size, uploaded_at)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            doc_id,
                            doc_id,
                            doc_id,
                            sig,
                            len(data),
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )
                _audit("sync_pull", f"peer={peer_url} id={doc_id}")
                log.info("Pulled %s from %s", doc_id, peer_url)
            except Exception as e:
                log.warning("Failed to pull %s from %s: %s", doc_id, peer_url, e)

        extra = local_ids - peer_docs
        for doc_id in extra:
            path = _doc_path(doc_id)
            if not path.exists():
                continue
            try:
                data = path.read_bytes()
                with _get_conn() as conn:
                    row = conn.execute(
                        "SELECT filename FROM documents WHERE id = ?", (doc_id,)
                    ).fetchone()
                filename = row["filename"] if row else doc_id
                push_resp = httpx.post(
                    f"{peer_url}/sync",
                    headers=headers,
                    params={"doc_id": doc_id},
                    files={"file": (filename, data)},
                    timeout=60,
                )
                push_resp.raise_for_status()
                _audit("sync_push", f"peer={peer_url} id={doc_id}")
                log.info("Pushed %s to %s", doc_id, peer_url)
            except Exception as e:
                log.warning("Failed to push %s to %s: %s", doc_id, peer_url, e)

    except Exception as e:
        log.warning("Sync with %s failed: %s", peer_url, e)
        _audit("sync_error", f"peer={peer_url} error={e}")


def _sync_loop() -> None:
    while True:
        time.sleep(SYNC_INTERVAL)
        for peer in PEER_URLS:
            _sync_with_peer(peer)


# ---------------------------------------------------------------------------
# Background: hourly integrity check
# ---------------------------------------------------------------------------

def _integrity_check() -> None:
    while True:
        time.sleep(INTEGRITY_INTERVAL)
        log.info("Running integrity check…")
        with _get_conn() as conn:
            rows = conn.execute("SELECT id, sha256 FROM documents").fetchall()
        corrupted = []
        for row in rows:
            path = _doc_path(row["id"])
            if not path.exists():
                log.error("Missing file for document id=%s", row["id"])
                _audit("integrity_missing", f"id={row['id']}")
                corrupted.append(row["id"])
                continue
            actual = _sha256(path.read_bytes())
            if actual != row["sha256"]:
                log.error("Corruption detected id=%s", row["id"])
                _audit("integrity_corrupt", f"id={row['id']}")
                corrupted.append(row["id"])

        if corrupted:
            log.warning("Corrupted/missing: %d documents. Triggering peer sync.", len(corrupted))
            for peer in PEER_URLS:
                _sync_with_peer(peer)
        else:
            log.info("Integrity check passed: %d documents OK", len(rows))
            _audit("integrity_ok", f"documents={len(rows)}")


# ---------------------------------------------------------------------------
# Start background threads on startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def start_background_tasks():
    if PEER_URLS:
        threading.Thread(target=_sync_loop, daemon=True, name="sync").start()
        log.info("Sync thread started (interval=%ds, peers=%s)", SYNC_INTERVAL, PEER_URLS)
    threading.Thread(target=_integrity_check, daemon=True, name="integrity").start()
    log.info("Integrity thread started (interval=%ds)", INTEGRITY_INTERVAL)
