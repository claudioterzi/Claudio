"""
R3∞ sync — da eseguire ogni 5 minuti (cron o schedule).

Replica due classi di stato:
1. documenti content-addressed;
2. ultimo evento di controllo RRR firmato.

Per RRR il trasporto non è autorità: il nodo ricevente verifica sempre la firma
del controller e rifiuta replay/downgrade tramite il counter firmato.

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
from typing import Any

import httpx

try:
    from .rrr_control import (
        SCHEMA as RRR_SCHEMA,
        RRRControlError,
        replication_direction,
        verify_event,
    )
except ImportError:  # standalone execution
    from rrr_control import (
        SCHEMA as RRR_SCHEMA,
        RRRControlError,
        replication_direction,
        verify_event,
    )

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_TOKEN         = os.getenv("R3_API_TOKEN", "changeme")
LOCAL_URL         = os.getenv("R3_LOCAL_URL", "http://localhost:8000")
PEER_URLS         = [u for u in os.getenv("R3_PEERS", "").split(",") if u]
SYNC_INTERVAL     = int(os.getenv("R3_SYNC_INTERVAL", "300"))
DATA_DIR          = Path(os.getenv("R3_DATA_DIR", "data"))
NODE_ID           = os.getenv("R3_NODE_ID", "sync")
CONTROL_VERIFY_KEY_HEX = os.getenv("R3_CONTROL_VERIFY_KEY_HEX", "").strip()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(DATA_DIR / "sync.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("r3.sync")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "X-R3-Source-Node": NODE_ID,
}

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


def _get_rrr_status(node_url: str) -> dict[str, Any]:
    resp = httpx.get(f"{node_url}/protocol/rrr/status", headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError("invalid RRR status")
    return data


def _wire_rrr_event(status: dict[str, Any]) -> dict[str, Any]:
    """Rebuild the canonical signed event from node status for peer relay.

    protocol_events stores the verified signed payload fields but not the
    constant schema marker.  The relay therefore reconstructs the exact wire
    envelope for the currently supported schema and strips receive-local audit
    metadata such as received_at/source_node.  The destination still verifies
    event_id and Ed25519 signature over the canonical payload before accepting.
    """
    stored = status.get("event")
    if not isinstance(stored, dict):
        raise ValueError("RRR event missing")

    required = (
        "protocol",
        "policy_sha256",
        "action",
        "scope",
        "counter",
        "issued_at",
        "nonce",
        "issuer",
        "event_id",
        "signature",
    )
    missing = [field for field in required if field not in stored]
    if missing:
        raise ValueError(f"RRR event incomplete: {','.join(missing)}")

    return {
        "schema": RRR_SCHEMA,
        "protocol": stored["protocol"],
        "policy_sha256": stored["policy_sha256"],
        "action": stored["action"],
        "scope": stored["scope"],
        "counter": stored["counter"],
        "issued_at": stored["issued_at"],
        "nonce": stored["nonce"],
        "issuer": stored["issuer"],
        "event_id": stored["event_id"],
        "signature": stored["signature"],
    }


def _trusted_rrr_view(status: dict[str, Any]) -> dict[str, Any]:
    """Validate the signed event before its counter can influence sync direction."""
    if not status.get("event"):
        return {
            "event": None,
            "counter": None,
            "event_id": None,
        }
    if not CONTROL_VERIFY_KEY_HEX:
        raise RRRControlError(
            "R3_CONTROL_VERIFY_KEY_HEX is required to route a non-empty RRR state"
        )

    wire = _wire_rrr_event(status)
    payload = verify_event(wire, CONTROL_VERIFY_KEY_HEX)

    # Top-level status metadata is transport data. It must agree with the signed
    # payload/envelope before it is used for ordering.
    if status.get("counter") != payload["counter"]:
        raise RRRControlError("status counter disagrees with signed event")
    if status.get("event_id") != wire["event_id"]:
        raise RRRControlError("status event_id disagrees with signed event")

    return {
        "event": status["event"],
        "counter": payload["counter"],
        "event_id": wire["event_id"],
    }


def _push_rrr_event(dst_url: str, event: dict[str, Any]) -> dict[str, Any]:
    resp = httpx.post(
        f"{dst_url}/protocol/rrr/event",
        headers=HEADERS,
        json=event,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError("invalid RRR acknowledgement")
    return data


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# ---------------------------------------------------------------------------
# RRR propagation
# ---------------------------------------------------------------------------

def sync_rrr_with_peer(peer_url: str) -> None:
    try:
        local_raw = _get_rrr_status(LOCAL_URL)
        peer_raw = _get_rrr_status(peer_url)
        local = _trusted_rrr_view(local_raw)
        peer = _trusted_rrr_view(peer_raw)
        direction = replication_direction(local, peer)

        if direction in {"none", "equal"}:
            return
        if direction == "conflict":
            log.error(
                "RRR conflict con %s: local counter/event=%r/%r peer=%r/%r; nessuna risoluzione automatica",
                peer_url,
                local.get("counter"),
                local.get("event_id"),
                peer.get("counter"),
                peer.get("event_id"),
            )
            return

        if direction == "local_to_peer":
            event = _wire_rrr_event(local_raw)
            ack = _push_rrr_event(peer_url, event)
            log.info(
                "RRR relay → %s event=%s counter=%s ack=%s",
                peer_url,
                str(event.get("event_id", ""))[:12],
                event.get("counter"),
                ack.get("status"),
            )
            return

        event = _wire_rrr_event(peer_raw)
        ack = _push_rrr_event(LOCAL_URL, event)
        log.info(
            "RRR relay ← %s event=%s counter=%s ack=%s",
            peer_url,
            str(event.get("event_id", ""))[:12],
            event.get("counter"),
            ack.get("status"),
        )
    except Exception as exc:
        # RRR propagation is independent from document replication; one failure
        # must not silently disable the other path.
        log.warning("RRR sync fallito con %s: %s", peer_url, exc)

# ---------------------------------------------------------------------------
# Document sync logic
# ---------------------------------------------------------------------------

def sync_with_peer(peer_url: str) -> None:
    log.info("Sync → %s", peer_url)

    # The signed RRR state is relayed independently before document sync.
    sync_rrr_with_peer(peer_url)

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
