#!/usr/bin/env python3
"""R3 remote restart proof — Issue #86.

Captures a node's identity/state fingerprint, then verifies it after each
restart. Stdlib only, so it runs anywhere with Python 3.10+.

    # 1. baseline (optionally seed a preregistered document first)
    R3_API_TOKEN=... python scripts/r3_restart_proof.py capture \
        --base-url https://r3-external-node-a-production.up.railway.app \
        --seed-file r3/continuity_registry_seed.json --out proof/node-a.0.json

    # 2. restart the node (Railway restart), wait for /health, then:
    R3_API_TOKEN=... python scripts/r3_restart_proof.py verify \
        --base-url ... --baseline proof/node-a.0.json \
        --previous proof/node-a.0.json --out proof/node-a.1.json

    # 3. restart again and verify with --previous proof/node-a.1.json

Acceptance (per node): two consecutive verify runs exit 0.
Exit code 0 = all checks pass, 1 = a persistence check failed, 2 = usage/transport error.

Falsifier: any of these after a restart means persistence is NOT solved —
storage_id changed or storage_id_created_this_boot is true; verify key changed;
latest RRR event / protocol event count changed without a new controller event;
document hash set changed or a document is missing/corrupt on disk;
process_boot_id unchanged (no real restart happened, so nothing was proven).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

# Fields that must be byte-identical across a restart.
STABLE_FIELDS = (
    "node_id",
    "verify_key",
    "storage_id",
    "rrr_event_id",
    "rrr_counter",
    "rrr_action",
    "protocol_event_count",
    "document_count",
    "document_set_sha256",
)


def _request(method: str, url: str, token: str | None, body: bytes | None = None,
             headers: dict[str, str] | None = None) -> tuple[int, Any]:
    req = urllib.request.Request(url, data=body, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw or b"null")
        except json.JSONDecodeError:
            return exc.code, raw.decode(errors="replace")


def _fingerprint(base: str, token: str) -> dict[str, Any]:
    code, data = _request("GET", f"{base}/state/fingerprint", token)
    if code != 200 or not isinstance(data, dict):
        raise SystemExit(f"ERROR: /state/fingerprint returned {code}: {data}")
    return data


def _ready(base: str) -> tuple[int, Any]:
    return _request("GET", f"{base}/ready", None)


def _seed(base: str, token: str, path: Path) -> dict[str, Any]:
    boundary = uuid.uuid4().hex
    payload = path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()
    code, data = _request(
        "POST", f"{base}/documents", token, body,
        {"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    if code != 200:
        raise SystemExit(f"ERROR: seeding {path} returned {code}: {data}")
    return data


def compare(baseline: dict[str, Any], current: dict[str, Any],
            previous: dict[str, Any] | None) -> list[str]:
    """Return the list of failed checks (empty list = pass)."""
    failures: list[str] = []
    for field in STABLE_FIELDS:
        if baseline.get(field) != current.get(field):
            failures.append(
                f"{field} changed: {baseline.get(field)!r} -> {current.get(field)!r}"
            )
    if current.get("storage_id_created_this_boot"):
        failures.append("storage_id was created on this boot: DATA_DIR did not survive")
    if current.get("documents_missing_or_corrupt"):
        failures.append(
            f"documents missing/corrupt on disk: {current['documents_missing_or_corrupt']}"
        )
    if not current.get("durable_state_detected"):
        failures.append("durable_state_detected is false (DATA_DIR is not a mount)")
    ref = previous or baseline
    if ref.get("process_boot_id") == current.get("process_boot_id"):
        failures.append("process_boot_id unchanged: no restart happened, nothing proven")
    return failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("capture", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--base-url", required=True)
        p.add_argument("--out", required=True, type=Path)
        if name == "capture":
            p.add_argument("--seed-file", type=Path, action="append", default=[])
        else:
            p.add_argument("--baseline", required=True, type=Path)
            p.add_argument("--previous", type=Path)
            p.add_argument("--require-ready", action="store_true",
                           help="also fail unless /ready returns 200")
    args = ap.parse_args(argv)

    token = os.environ.get("R3_API_TOKEN", "")
    if not token:
        print("ERROR: set R3_API_TOKEN in the environment", file=sys.stderr)
        return 2
    base = args.base_url.rstrip("/")

    seeded: list[dict[str, Any]] = []
    if args.cmd == "capture":
        for f in args.seed_file:
            seeded.append(_seed(base, token, f))

    fp = _fingerprint(base, token)
    ready_code, ready_body = _ready(base)
    record: dict[str, Any] = {
        "fingerprint": fp,
        "ready_status": ready_code,
        "ready_reasons": ready_body.get("reasons") if isinstance(ready_body, dict) else None,
        "seeded": seeded,
    }

    rc = 0
    if args.cmd == "verify":
        baseline = json.loads(args.baseline.read_text())["fingerprint"]
        previous = json.loads(args.previous.read_text())["fingerprint"] if args.previous else None
        failures = compare(baseline, fp, previous)
        if args.require_ready and ready_code != 200:
            failures.append(f"/ready returned {ready_code}: {record['ready_reasons']}")
        record["failures"] = failures
        record["result"] = "PASS" if not failures else "FAIL"
        rc = 0 if not failures else 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    summary = {
        "cmd": args.cmd,
        "node_id": fp.get("node_id"),
        "verify_key": fp.get("verify_key"),
        "storage_id": fp.get("storage_id"),
        "document_set_sha256": fp.get("document_set_sha256"),
        "rrr_event_id": fp.get("rrr_event_id"),
        "ready_status": ready_code,
        "result": record.get("result", "CAPTURED"),
        "failures": record.get("failures", []),
    }
    print(json.dumps(summary, indent=2))
    return rc


if __name__ == "__main__":
    sys.exit(main())
