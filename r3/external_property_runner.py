from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[1]
TOKEN = os.environ["R3_API_TOKEN"]
NODE_A = os.environ["R3_NODE_A_URL"].rstrip("/")
NODE_B = os.environ["R3_NODE_B_URL"].rstrip("/")
WAIT_RESTART_SECONDS = int(os.getenv("R3_WAIT_RESTART_SECONDS", "300"))
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def log(event: str, **fields) -> None:
    print(json.dumps({"event": event, **fields}, sort_keys=True), flush=True)


def wait_health(url: str, *, want_up: bool, timeout: int) -> dict | None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            r = httpx.get(f"{url}/health", timeout=2)
            last = {"status_code": r.status_code, "body": r.text[:200]}
            up = r.status_code == 200
        except Exception as exc:
            last = {"error": type(exc).__name__, "detail": str(exc)[:200]}
            up = False
        if up == want_up:
            if up:
                return httpx.get(f"{url}/health", timeout=2).json()
            return None
        time.sleep(1)
    raise AssertionError(f"health state timeout url={url} want_up={want_up} last={last}")


def hashes(url: str) -> set[str]:
    r = httpx.get(f"{url}/sync/hashes", headers=HEADERS, timeout=10)
    r.raise_for_status()
    return {row["id"] for row in r.json().get("documents", [])}


def download(url: str, doc_id: str) -> bytes:
    r = httpx.get(f"{url}/documents/{doc_id}", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.content


def receive(url: str, name: str, data: bytes) -> dict:
    r = httpx.post(
        f"{url}/sync/receive",
        headers=HEADERS,
        files={"file": (name, data, "application/json")},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def upload(url: str, name: str, data: bytes) -> dict:
    r = httpx.post(
        f"{url}/documents",
        headers=HEADERS,
        files={"file": (name, data, "application/json")},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def copy_missing(src: str, dst: str) -> None:
    src_ids = hashes(src)
    dst_ids = hashes(dst)
    for doc_id in src_ids - dst_ids:
        data = download(src, doc_id)
        actual = hashlib.sha256(data).hexdigest()
        if actual != doc_id:
            raise AssertionError(f"hash mismatch while copying {doc_id}: {actual}")
        receive(dst, doc_id, data)


def main() -> int:
    health_a = wait_health(NODE_A, want_up=True, timeout=90)
    health_b = wait_health(NODE_B, want_up=True, timeout=90)
    log("nodes_up", node_a=health_a, node_b=health_b)

    payload = (ROOT / "sdq1_master.json").read_bytes()
    doc_id = hashlib.sha256(payload).hexdigest()

    up = upload(NODE_A, "sdq1_master.json", payload)
    if up["id"] != doc_id:
        raise AssertionError("node A returned unexpected content ID")

    copy_missing(NODE_A, NODE_B)
    if doc_id not in hashes(NODE_B):
        raise AssertionError("node B missing canonical object after sync")
    if hashlib.sha256(download(NODE_B, doc_id)).hexdigest() != doc_id:
        raise AssertionError("node B content hash mismatch before failover")

    shutdown = httpx.post(f"{NODE_A}/test/shutdown", headers=HEADERS, timeout=10)
    shutdown.raise_for_status()
    log("shutdown_requested", response=shutdown.json())

    wait_health(NODE_A, want_up=False, timeout=60)

    b_after = download(NODE_B, doc_id)
    b_after_hash = hashlib.sha256(b_after).hexdigest()
    if b_after_hash != doc_id:
        raise AssertionError("node B failed exact-object service while A was down")

    log(
        "external_failover_phase1_pass",
        document_sha256=doc_id,
        node_a_unavailable=True,
        node_b_served_exact_object=True,
        node_b_sha256=b_after_hash,
    )

    log("awaiting_node_a_restart", timeout_seconds=WAIT_RESTART_SECONDS)
    health_a2 = wait_health(NODE_A, want_up=True, timeout=WAIT_RESTART_SECONDS)
    log("node_a_restarted", node_a=health_a2)

    copy_missing(NODE_B, NODE_A)
    ids_a = hashes(NODE_A)
    ids_b = hashes(NODE_B)
    if ids_a != ids_b:
        raise AssertionError(f"hash-set divergence after recovery: A={sorted(ids_a)} B={sorted(ids_b)}")
    if doc_id not in ids_a:
        raise AssertionError("recovered A still missing canonical object")
    if hashlib.sha256(download(NODE_A, doc_id)).hexdigest() != doc_id:
        raise AssertionError("recovered A content hash mismatch")

    log(
        "external_failover_recovery_pass",
        document_sha256=doc_id,
        same_hash_sets=True,
        node_a_restored_from_node_b=True,
        provider_scope="RAILWAY_SEPARATE_SERVICES_SAME_PROVIDER",
        different_provider_proof=False,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        log("external_property_failed", error=type(exc).__name__, detail=str(exc))
        raise
