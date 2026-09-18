"""
R3∞ sync — da eseguire ogni 5 minuti (cron o schedule).

Algoritmo per ogni peer:
  1. GET /sync/hashes    → cosa ha il peer
  2. GET /sync/hashes    → cosa ho io (locale via HTTP o diretto su DB)
  3. Delta: cosa manca al peer  → push
  4. Delta: cosa manca a me     → pull
  5. Integrity check (opzionale, ogni N run)

Uso:
  python sync.py                          # sync una volta e termina
  python sync.py --loop                   # loop ogni R3_SYNC_INTERVAL secondi
  python sync.py --integrity              # solo integrity check
"""

import argparse
import hashlib
import logging
import os
import sqlite3
import sys
import time
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_TOKEN         = os.getenv("R3_API_TOKEN", "changeme")
LOCAL_URL         = os.getenv("R3_LOCAL_URL", "http://localhost:8000")
PEER_URLS         = [u for u in os.getenv("R3_PEERS", "").split(",") if u]
SYNC_INTERVAL     = int(os.getenv("R3_SYNC_INTERVAL", "300"))
DATA_DIR          = Path(os.getenv("R3_DATA_DIR", "data"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(DATA_DIR / "sync.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("r3.sync")

HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get_hashes(node_url: str) -> dict[str, dict]:
    """Restituisce {id: {sha256, size, uploaded_at}} per un nodo."""
    resp = httpx.get(f"{node_url}/sync/hashes", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return {d["id"]: d for d in resp.json().get("documents", [])}


def _pull_doc(src_url: str, doc_id: str) -> bytes:
    resp = httpx.get(f"{src_url}/documents/{doc_id}", headers=HEADERS, timeout=120)
    resp.raise_for_status()
    return resp.content


def _push_doc(dst_url: str, doc_id: str, data: bytes, filename: str) -> None:
    resp = httpx.post(
        f"{dst_url}/sync/receive",
        headers=HEADERS,
        files={"file": (filename, data)},
        timeout=120,
    )
    resp.raise_for_status()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# ---------------------------------------------------------------------------
# Sync logic
# ---------------------------------------------------------------------------

def sync_with_peer(peer_url: str) -> None:
    log.info("Sync → %s", peer_url)
    try:
        local_docs = _get_hashes(LOCAL_URL)
        peer_docs  = _get_hashes(peer_url)

        local_ids = set(local_docs)
        peer_ids  = set(peer_docs)

        # Cosa ha il peer che manca a noi → pull
        for doc_id in peer_ids - local_ids:
            try:
                data = _pull_doc(peer_url, doc_id)
                actual = _sha256(data)
                if actual != doc_id:
                    log.error("Hash mismatch pull %s da %s (got %s)", doc_id, peer_url, actual)
                    continue
                _push_doc(LOCAL_URL, doc_id, data, peer_docs[doc_id].get("filename", doc_id))
                log.info("Pull  %s  da %s", doc_id[:12], peer_url)
            except Exception as e:
                log.warning("Pull fallito %s da %s: %s", doc_id[:12], peer_url, e)

        # Cosa abbiamo noi che manca al peer → push
        for doc_id in local_ids - peer_ids:
            try:
                data = _pull_doc(LOCAL_URL, doc_id)
                _push_doc(peer_url, doc_id, data, local_docs[doc_id].get("filename", doc_id))
                log.info("Push  %s  su %s", doc_id[:12], peer_url)
            except Exception as e:
                log.warning("Push fallito %s su %s: %s", doc_id[:12], peer_url, e)

    except Exception as e:
        log.error("Sync fallito con %s: %s", peer_url, e)


# ---------------------------------------------------------------------------
# Integrity check
# ---------------------------------------------------------------------------

def integrity_check() -> list[str]:
    """Controlla hash di ogni file su disco vs DB. Restituisce lista ID corrotti."""
    db_path = DATA_DIR / "r3.db"
    if not db_path.exists():
        log.warning("DB non trovato: %s", db_path)
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, sha256 FROM documents WHERE deleted = 0"
    ).fetchall()
    conn.close()

    corrupted = []
    for row in rows:
        path = DATA_DIR / "docs" / row["id"]
        if not path.exists():
            log.error("File mancante: id=%s", row["id"])
            corrupted.append(row["id"])
            continue
        actual = _sha256(path.read_bytes())
        if actual != row["sha256"]:
            log.error("Corruzione rilevata: id=%s", row["id"])
            corrupted.append(row["id"])

    if corrupted:
        log.warning("%d documenti corrotti/mancanti → avvio sync da peer", len(corrupted))
        for peer in PEER_URLS:
            sync_with_peer(peer)
    else:
        log.info("Integrity OK: %d documenti verificati", len(rows))

    return corrupted

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_once(check_integrity: bool = False) -> None:
    if not PEER_URLS:
        log.warning("Nessun peer configurato (R3_PEERS vuoto)")
        return
    for peer in PEER_URLS:
        sync_with_peer(peer)
    if check_integrity:
        integrity_check()


def main() -> None:
    parser = argparse.ArgumentParser(description="R3∞ sync script")
    parser.add_argument("--loop",      action="store_true", help="Loop ogni R3_SYNC_INTERVAL secondi")
    parser.add_argument("--integrity", action="store_true", help="Esegui solo integrity check")
    args = parser.parse_args()

    if args.integrity:
        corrupted = integrity_check()
        sys.exit(1 if corrupted else 0)

    if args.loop:
        log.info("Sync loop avviato (intervallo=%ds)", SYNC_INTERVAL)
        while True:
            run_once()
            time.sleep(SYNC_INTERVAL)
    else:
        run_once()


if __name__ == "__main__":
    main()
