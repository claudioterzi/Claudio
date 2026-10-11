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
    from .sync_progress import configure_from_environment, note_progress
except ImportError:
    from sync_progress import configure_from_environment, note_progress

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
# Peers may use their own bearer token (e.g. a Railway reference variable to the
# peer service's R3_API_TOKEN). Empty → same token as the local node.
PEER_TOKEN        = os.getenv("R3_PEER_TOKEN", "").strip()
SYNC_START_DELAY  = int(os.getenv("R3_SYNC_START_DELAY", "0"))
# Replication proof: each cycle writes one canary on each side, syncs, then
# verifies by download+hash that each canary reached the other node.
SYNC_CANARY       = os.getenv("R3_SYNC_CANARY", "").strip().lower() in {"1", "true", "yes"}
# Canaries are permanent content-addressed documents; run the receipt cycle
# every N sync cycles to bound growth (1 = every cycle).
SYNC_CANARY_EVERY = max(1, int(os.getenv("R3_SYNC_CANARY_EVERY", "1")))
_CYCLE = 0

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


def _headers(node_url: str) -> dict[str, str]:
    """Local node uses R3_API_TOKEN; peers use R3_PEER_TOKEN when set."""
    if PEER_TOKEN and node_url != LOCAL_URL:
        return {"Authorization": f"Bearer {PEER_TOKEN}", "X-R3-Source-Node": NODE_ID}
    return HEADERS

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get_hashes(node_url: str) -> dict[str, dict]:
    """Restituisce {id: {sha256, size, uploaded_at}} per un nodo."""
    resp = httpx.get(f"{node_url}/sync/hashes", headers=_headers(node_url), timeout=30)
    resp.raise_for_status()
    note_progress()
    return {d["id"]: d for d in resp.json().get("documents", [])}


def _pull_doc(src_url: str, doc_id: str) -> bytes:
    resp = httpx.get(f"{src_url}/documents/{doc_id}", headers=_headers(src_url), timeout=120)
    resp.raise_for_status()
    note_progress()
    return resp.content


def _push_doc(dst_url: str, doc_id: str, data: bytes, filename: str) -> None:
    resp = httpx.post(
        f"{dst_url}/sync/receive",
        headers=_headers(dst_url),
        files={"file": (filename, data)},
        timeout=120,
    )
    resp.raise_for_status()
    note_progress()


def _get_rrr_status(node_url: str) -> dict[str, Any]:
    resp = httpx.get(f"{node_url}/protocol/rrr/status", headers=_headers(node_url), timeout=15)
    resp.raise_for_status()
    note_progress()
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
        headers=_headers(dst_url),
        json=event,
        timeout=15,
    )
    resp.raise_for_status()
    note_progress()
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError("invalid RRR acknowledgement")
    return data


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _local_doc_ok(doc_id: str) -> bool:
    path = DATA_DIR / "docs" / doc_id
    try:
        return path.exists() and _sha256(path.read_bytes()) == doc_id
    except OSError:
        return False


def _repair_doc_from_peers(doc_id: str) -> str | None:
    """Ripara un ID preciso dalla prima replica che dimostra lo stesso hash."""
    for peer in PEER_URLS:
        try:
            data = _pull_doc(peer, doc_id)
            actual = _sha256(data)
            if actual != doc_id:
                log.warning(
                    "Replica non integra per %s da %s: got=%s",
                    doc_id[:12],
                    peer,
                    actual[:12],
                )
                continue
            _push_doc(LOCAL_URL, doc_id, data, doc_id)
            if _local_doc_ok(doc_id):
                log.info("Repair %s completato da %s", doc_id[:12], peer)
                return peer
            log.warning("Repair %s da %s non verificato localmente", doc_id[:12], peer)
        except Exception as exc:
            log.warning("Repair fallito %s da %s: %s", doc_id[:12], peer, exc)
    return None

# ---------------------------------------------------------------------------
# RRR propagation
# ---------------------------------------------------------------------------

def sync_rrr_with_peer(peer_url: str) -> bool:
    try:
        local_raw = _get_rrr_status(LOCAL_URL)
        peer_raw = _get_rrr_status(peer_url)
        local = _trusted_rrr_view(local_raw)
        peer = _trusted_rrr_view(peer_raw)
        direction = replication_direction(local, peer)

        if direction in {"none", "equal"}:
            return True
        if direction == "conflict":
            log.error(
                "RRR conflict con %s: local counter/event=%r/%r peer=%r/%r; nessuna risoluzione automatica",
                peer_url,
                local.get("counter"),
                local.get("event_id"),
                peer.get("counter"),
                peer.get("event_id"),
            )
            return False

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
            return True

        event = _wire_rrr_event(peer_raw)
        ack = _push_rrr_event(LOCAL_URL, event)
        log.info(
            "RRR relay ← %s event=%s counter=%s ack=%s",
            peer_url,
            str(event.get("event_id", ""))[:12],
            event.get("counter"),
            ack.get("status"),
        )
        return True
    except Exception as exc:
        # RRR propagation is independent from document replication; one failure
        # must not silently disable the other path.
        log.warning("RRR sync fallito con %s: %s", peer_url, exc)
        return False

# ---------------------------------------------------------------------------
# Document sync logic
# ---------------------------------------------------------------------------

def sync_with_peer(peer_url: str) -> bool:
    log.info("Sync → %s", peer_url)

    # The signed RRR state is relayed independently before document sync.
    ok = sync_rrr_with_peer(peer_url)

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
                    ok = False
                    continue
                _push_doc(LOCAL_URL, doc_id, data, peer_docs[doc_id].get("filename", doc_id))
                log.info("Pull  %s  da %s", doc_id[:12], peer_url)
            except Exception as e:
                ok = False
                log.warning("Pull fallito %s da %s: %s", doc_id[:12], peer_url, e)

        # Cosa abbiamo noi che manca al peer → push
        for doc_id in local_ids - peer_ids:
            try:
                data = _pull_doc(LOCAL_URL, doc_id)
                _push_doc(peer_url, doc_id, data, local_docs[doc_id].get("filename", doc_id))
                log.info("Push  %s  su %s", doc_id[:12], peer_url)
            except Exception as e:
                ok = False
                log.warning("Push fallito %s su %s: %s", doc_id[:12], peer_url, e)

    except Exception as e:
        ok = False
        log.error("Sync fallito con %s: %s", peer_url, e)
    return bool(ok)


# ---------------------------------------------------------------------------
# Integrity check
# ---------------------------------------------------------------------------

def integrity_check() -> list[str]:
    """Verifica e prova a riparare; restituisce solo gli ID ancora non integri."""
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

    corrupted: list[str] = []
    for row in rows:
        note_progress()
        doc_id = row["id"]
        path = DATA_DIR / "docs" / doc_id
        if not path.exists():
            log.error("File mancante: id=%s", doc_id)
            corrupted.append(doc_id)
            continue
        try:
            actual = _sha256(path.read_bytes())
        except OSError:
            log.error("File non leggibile: id=%s", doc_id)
            corrupted.append(doc_id)
            continue
        if actual != row["sha256"] or actual != doc_id:
            log.error("Corruzione rilevata: id=%s", doc_id)
            corrupted.append(doc_id)

    if not corrupted:
        log.info("Integrity OK: %d documenti verificati", len(rows))
        return []

    log.warning(
        "%d documenti corrotti/mancanti → repair mirato da replica sana",
        len(corrupted),
    )
    for doc_id in corrupted:
        _repair_doc_from_peers(doc_id)

    remaining = [doc_id for doc_id in corrupted if not _local_doc_ok(doc_id)]
    repaired = len(corrupted) - len(remaining)
    if repaired:
        log.info("Integrity repair: %d/%d recuperati", repaired, len(corrupted))
    if remaining:
        log.error("Integrity non risolta: %d documenti", len(remaining))
    return remaining

# ---------------------------------------------------------------------------
# Replication proof (canary + receipt)
# ---------------------------------------------------------------------------

def _canary_bytes(origin: str, cycle_ts: str) -> bytes:
    return f"R3_SYNC_CANARY v1 origin={origin} ts={cycle_ts}\n".encode()


def _arrived(node_url: str, doc_id: str) -> bool:
    """True only if node_url lists doc_id AND serves bytes with that exact hash."""
    try:
        if doc_id not in _get_hashes(node_url):
            return False
        return _sha256(_pull_doc(node_url, doc_id)) == doc_id
    except Exception as exc:
        log.warning("Verifica canarino %s su %s fallita: %s", doc_id[:12], node_url, exc)
        return False


def run_cycle_with_receipt(peer_url: str) -> dict[str, Any]:
    """One sync cycle with independent proof that data moved both ways.

    Before syncing, a unique canary is written ONLY to the local node and
    another ONLY to the peer. After sync_with_peer(), each canary must be
    downloadable from the opposite node with the exact hash. The receipt is
    logged as one R3_SYNC_RECEIPT line; any False field falsifies the claim
    that A<->B replication works for this cycle.
    """
    import json
    from datetime import datetime, timezone

    started = datetime.now(timezone.utc)
    cycle_ts = started.isoformat()
    receipt: dict[str, Any] = {"peer": peer_url, "cycle_ts": cycle_ts, "node_id": NODE_ID}
    try:
        local_canary = _canary_bytes(f"{NODE_ID}->peer", cycle_ts)
        peer_canary = _canary_bytes(f"peer->{NODE_ID}", cycle_ts)
        local_id, peer_id = _sha256(local_canary), _sha256(peer_canary)
        _push_doc(LOCAL_URL, local_id, local_canary, f"canary-{local_id[:12]}.txt")
        _push_doc(peer_url, peer_id, peer_canary, f"canary-{peer_id[:12]}.txt")
        receipt["canary_local_to_peer"] = local_id
        receipt["canary_peer_to_local"] = peer_id
        receipt["canary_local_to_peer_preabsent_on_peer"] = local_id not in _get_hashes(peer_url)
        receipt["canary_peer_to_local_preabsent_on_local"] = peer_id not in _get_hashes(LOCAL_URL)

        sync_ok = sync_with_peer(peer_url)

        receipt["local_to_peer_arrived"] = _arrived(peer_url, local_id)
        receipt["peer_to_local_arrived"] = _arrived(LOCAL_URL, peer_id)
        local_set, peer_set = set(_get_hashes(LOCAL_URL)), set(_get_hashes(peer_url))
        receipt["local_count"] = len(local_set)
        receipt["peer_count"] = len(peer_set)
        receipt["sets_equal"] = local_set == peer_set
        receipt["set_sha256"] = _sha256("\n".join(sorted(local_set)).encode())
        receipt["pass"] = all((
            sync_ok,
            receipt["canary_local_to_peer_preabsent_on_peer"],
            receipt["canary_peer_to_local_preabsent_on_local"],
            receipt["local_to_peer_arrived"],
            receipt["peer_to_local_arrived"],
            receipt["sets_equal"],
        ))
    except Exception as exc:
        receipt["pass"] = False
        receipt["error"] = f"{type(exc).__name__}: {exc}"[:300]
    receipt["duration_s"] = round(
        (datetime.now(timezone.utc) - started).total_seconds(), 2
    )
    log.info("R3_SYNC_RECEIPT %s", json.dumps(receipt, sort_keys=True))
    return receipt


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_once(check_integrity: bool = False) -> bool:
    global _CYCLE
    if not PEER_URLS:
        log.warning("Nessun peer configurato (R3_PEERS vuoto)")
        return False
    canary_cycle = SYNC_CANARY and _CYCLE % SYNC_CANARY_EVERY == 0
    _CYCLE += 1
    ok = True
    for peer in PEER_URLS:
        note_progress()
        if canary_cycle:
            peer_ok = run_cycle_with_receipt(peer).get("pass") is True
        else:
            peer_ok = sync_with_peer(peer) is True
        ok = peer_ok and ok
    if check_integrity:
        ok = not integrity_check() and ok
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description="R3∞ sync script")
    parser.add_argument("--loop",      action="store_true", help="Loop ogni R3_SYNC_INTERVAL secondi")
    parser.add_argument("--integrity", action="store_true", help="Esegui solo integrity check")
    args = parser.parse_args()

    if args.integrity:
        corrupted = integrity_check()
        sys.exit(1 if corrupted else 0)

    if args.loop:
        log.info(
            "Sync loop avviato (intervallo=%ds, canary=%s, peers=%d)",
            SYNC_INTERVAL, SYNC_CANARY, len(PEER_URLS),
        )
        if SYNC_START_DELAY:
            time.sleep(SYNC_START_DELAY)
        configure_from_environment()
        while True:
            note_progress()
            ok = False
            try:
                ok = run_once()
            except Exception as exc:  # the loop must survive one bad cycle
                log.error("Ciclo sync fallito: %s", exc)
            note_progress("idle", success=ok)
            time.sleep(SYNC_INTERVAL)
    else:
        run_once()


if __name__ == "__main__":
    main()
