"""
R3∞ MVP — nodo singolo.
ID documenti = SHA-256 del contenuto (content-addressed).
Sync e integrity check delegati a sync.py esterno.
"""

import hashlib
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import nacl.encoding
import nacl.signing
from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_DIR   = Path(os.getenv("R3_DATA_DIR", "data"))
DB_PATH    = DATA_DIR / "r3.db"
API_TOKEN  = os.getenv("R3_API_TOKEN", "changeme")
NODE_ID    = os.getenv("R3_NODE_ID", "node-a")
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

def _audit(event: str, detail: str = "") -> None:
    with _conn() as db:
        db.execute(
            "INSERT INTO audit_log (event, detail, ts) VALUES (?, ?, ?)",
            (event, detail, datetime.now(timezone.utc).isoformat()),
        )

def _check_token(authorization: Optional[str]) -> None:
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Token non valido")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title=f"R3∞ {NODE_ID}", version="0.1.0")


# Health check — senza auth (usato da load balancer / monitor esterno)
@app.get("/health")
def health():
    return {"status": "healthy", "node_id": NODE_ID}


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
    return {
        "node_id":    NODE_ID,
        "documents":  count,
        "storage_bytes": storage,
        "verify_key": VERIFY_KEY_HEX,
        "ts":         datetime.now(timezone.utc).isoformat(),
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
