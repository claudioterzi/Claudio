"""Signed network control events for Protocollo Rosso Rosso Rosso (RRR).

The control event is deliberately tiny and transport-independent:
- one canonical issuer signs an activation/deactivation event;
- every R3 node verifies the same public key;
- a monotonically increasing signed counter prevents replay/downgrade;
- the event can be replicated by peers without trusting the transport.

No private signing key is stored by R3 nodes. The controller keeps it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import nacl.exceptions
import nacl.signing

SCHEMA = "r3-rrr-event/1"
PROTOCOL = "RRR-JEV/1.0"
SCOPE = "network"
VALID_ACTIONS = {"activate", "deactivate"}
PAYLOAD_FIELDS = (
    "schema",
    "protocol",
    "policy_sha256",
    "action",
    "scope",
    "counter",
    "issued_at",
    "nonce",
    "issuer",
)

POLICY: dict[str, Any] = {
    "protocol": PROTOCOL,
    "name": "Protocollo Rosso Rosso Rosso",
    "activation_phrase": "ROSSO ROSSO ROSSO",
    "required_on_join": True,
    "role": "network_epistemic_policy",
    "rules": {
        "epistemic_states": ["FATTO", "INTERPRETAZIONE", "IPOTESI"],
        "p5": "Una fonte non conferma se stessa; l'indipendenza si misura sull'origine causale.",
        "p6": "Conservare provenienza, nodo, versione, evidenza e hash quando disponibili.",
        "falsification": "Prima della conferma cercare una prova capace di indebolire o falsificare l'ipotesi.",
        "resonance": "La convergenza genera CANDIDATE, non TRUE.",
        "divergence": "Conservare il disaccordo e il test capace di discriminarlo.",
        "high_impact": "Preferire analisi, simulazione, test, verifica e azioni reversibili con rollback.",
    },
    "output_contract": [
        "FATTI",
        "INTERPRETAZIONI",
        "IPOTESI",
        "P5_CHECK",
        "P6_CHECK",
        "FALSIFIER",
        "RISCHI",
        "TEST",
        "ESITO",
        "CONFIDENZA",
        "NEXT_ACTION",
    ],
}


class RRRControlError(ValueError):
    """A signed RRR event is malformed or cannot be verified."""


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


POLICY_SHA256 = hashlib.sha256(_canonical_bytes(POLICY)).hexdigest()


def _counter_db_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    configured = os.getenv("R3_CONTROL_COUNTER_DB", "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".r3" / "rrr_control.db"


def _next_counter(path: str | Path | None = None) -> int:
    """Return a controller-local monotonic counter, durable across restarts.

    SQLite BEGIN IMMEDIATE serializes concurrent controller processes that share
    the same counter DB.  Wall-clock nanoseconds are only a floor; a backwards
    clock step cannot reduce the signed counter.
    """
    db_path = _counter_db_path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(db_path), timeout=10, isolation_level=None)
    try:
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            """CREATE TABLE IF NOT EXISTS controller_counter (
                   singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                   value INTEGER NOT NULL
               )"""
        )
        row = db.execute(
            "SELECT value FROM controller_counter WHERE singleton = 1"
        ).fetchone()
        last = int(row[0]) if row else 0
        candidate = max(time.time_ns(), last + 1)
        db.execute(
            """INSERT INTO controller_counter (singleton, value)
               VALUES (1, ?)
               ON CONFLICT(singleton) DO UPDATE SET value = excluded.value""",
            (candidate,),
        )
        db.execute("COMMIT")
        return candidate
    except Exception:
        try:
            db.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        db.close()


def canonical_payload(event: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise RRRControlError("event must be an object")

    try:
        payload = {field: event[field] for field in PAYLOAD_FIELDS}
    except KeyError as exc:
        raise RRRControlError(f"missing field: {exc.args[0]}") from exc

    if payload["schema"] != SCHEMA:
        raise RRRControlError("unsupported schema")
    if payload["protocol"] != PROTOCOL:
        raise RRRControlError("unsupported protocol")
    if payload["policy_sha256"] != POLICY_SHA256:
        raise RRRControlError("policy hash mismatch")
    if payload["action"] not in VALID_ACTIONS:
        raise RRRControlError("unsupported action")
    if payload["scope"] != SCOPE:
        raise RRRControlError("scope must be network")
    if type(payload["counter"]) is not int or payload["counter"] <= 0:
        raise RRRControlError("counter must be a positive integer")
    if not isinstance(payload["nonce"], str) or len(payload["nonce"]) < 16:
        raise RRRControlError("nonce is too short")
    if not isinstance(payload["issuer"], str) or not payload["issuer"].strip():
        raise RRRControlError("issuer is required")
    if not isinstance(payload["issued_at"], str):
        raise RRRControlError("issued_at is required")
    try:
        issued = datetime.fromisoformat(payload["issued_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise RRRControlError("issued_at is not ISO-8601") from exc
    if issued.tzinfo is None:
        raise RRRControlError("issued_at must include a timezone")

    return payload


def event_id_for(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def sign_event(
    action: str,
    signing_key_hex: str,
    *,
    issuer: str = "Claudio Terzi",
    counter: int | None = None,
    issued_at: str | None = None,
    nonce: str | None = None,
) -> dict[str, Any]:
    if action not in VALID_ACTIONS:
        raise RRRControlError("unsupported action")
    if not signing_key_hex:
        raise RRRControlError("R3_CONTROL_SIGNING_KEY_HEX is required")

    try:
        key = nacl.signing.SigningKey(bytes.fromhex(signing_key_hex))
    except (ValueError, TypeError) as exc:
        raise RRRControlError("invalid Ed25519 signing key") from exc

    payload = canonical_payload(
        {
            "schema": SCHEMA,
            "protocol": PROTOCOL,
            "policy_sha256": POLICY_SHA256,
            "action": action,
            "scope": SCOPE,
            "counter": counter if counter is not None else _next_counter(),
            "issued_at": issued_at or datetime.now(timezone.utc).isoformat(),
            "nonce": nonce or secrets.token_urlsafe(24),
            "issuer": issuer,
        }
    )
    raw = _canonical_bytes(payload)
    return {
        **payload,
        "event_id": event_id_for(payload),
        "signature": key.sign(raw).signature.hex(),
    }


def verify_event(event: dict[str, Any], verify_key_hex: str) -> dict[str, Any]:
    if not verify_key_hex:
        raise RRRControlError("R3_CONTROL_VERIFY_KEY_HEX is required")

    payload = canonical_payload(event)
    expected_id = event_id_for(payload)
    if event.get("event_id") != expected_id:
        raise RRRControlError("event_id mismatch")

    signature = event.get("signature")
    if not isinstance(signature, str):
        raise RRRControlError("signature is required")
    try:
        verify_key = nacl.signing.VerifyKey(bytes.fromhex(verify_key_hex))
        verify_key.verify(_canonical_bytes(payload), bytes.fromhex(signature))
    except (ValueError, TypeError, nacl.exceptions.BadSignatureError) as exc:
        raise RRRControlError("invalid signature") from exc

    return payload


def public_key_from_signing_key(signing_key_hex: str) -> str:
    try:
        key = nacl.signing.SigningKey(bytes.fromhex(signing_key_hex))
    except (ValueError, TypeError) as exc:
        raise RRRControlError("invalid Ed25519 signing key") from exc
    return key.verify_key.encode().hex()


def replication_direction(local: dict[str, Any], peer: dict[str, Any]) -> str:
    """Choose how to relay an already-signed event between two R3 nodes.

    Cryptographic validity is still checked by the receiving node. Equal
    counters with different event IDs are a hard conflict and are never
    auto-resolved.
    """
    local_event = local.get("event")
    peer_event = peer.get("event")

    if not local_event and not peer_event:
        return "none"
    if local_event and not peer_event:
        return "local_to_peer"
    if peer_event and not local_event:
        return "peer_to_local"

    local_counter = local.get("counter")
    peer_counter = peer.get("counter")
    if type(local_counter) is not int or type(peer_counter) is not int:
        return "conflict"
    if local_counter > peer_counter:
        return "local_to_peer"
    if peer_counter > local_counter:
        return "peer_to_local"
    if local.get("event_id") == peer.get("event_id"):
        return "equal"
    return "conflict"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "X-R3-Source-Node": "rrr-controller"}


def _targets() -> list[str]:
    urls = [os.getenv("R3_LOCAL_URL", "http://localhost:8000")]
    urls.extend(u.strip() for u in os.getenv("R3_PEERS", "").split(",") if u.strip())
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        clean = url.rstrip("/")
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result


def _post_event(url: str, event: dict[str, Any], token: str) -> dict[str, Any]:
    response = httpx.post(
        f"{url}/protocol/rrr/event",
        headers=_headers(token),
        json=event,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def _get_status(url: str, token: str) -> dict[str, Any]:
    response = httpx.get(
        f"{url}/protocol/rrr/status",
        headers=_headers(token),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R3∞ RRR signed network control")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("activate", help="Activate RRR across configured R3 peers")
    sub.add_parser("deactivate", help="Deactivate RRR across configured R3 peers")
    sub.add_parser("status", help="Read RRR status from configured R3 peers")
    sub.add_parser("public-key", help="Print the public verification key for the configured signing key")
    args = parser.parse_args(argv)

    token = os.getenv("R3_API_TOKEN", "")
    if args.command == "public-key":
        signing_key = os.getenv("R3_CONTROL_SIGNING_KEY_HEX", "")
        try:
            print(public_key_from_signing_key(signing_key))
            return 0
        except RRRControlError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    if not token or token == "changeme":
        print("ERROR: configure R3_API_TOKEN before using network control", file=sys.stderr)
        return 2

    targets = _targets()
    if args.command == "status":
        failures = 0
        for url in targets:
            try:
                status = _get_status(url, token)
                print(json.dumps({"url": url, **status}, ensure_ascii=False, sort_keys=True))
            except Exception as exc:
                failures += 1
                print(json.dumps({"url": url, "status": "unreachable", "error": type(exc).__name__}))
        return 1 if failures else 0

    signing_key = os.getenv("R3_CONTROL_SIGNING_KEY_HEX", "")
    issuer = os.getenv("R3_CONTROL_ISSUER", "Claudio Terzi")
    try:
        event = sign_event(args.command, signing_key, issuer=issuer)
    except RRRControlError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    failures = 0
    acknowledgements = []
    for url in targets:
        try:
            result = _post_event(url, event, token)
            acknowledgements.append({"url": url, "ack": result.get("status"), "node_id": result.get("node_id")})
        except Exception as exc:
            failures += 1
            acknowledgements.append({"url": url, "ack": "unreachable", "error": type(exc).__name__})

    print(json.dumps(
        {
            "command": args.command,
            "protocol": PROTOCOL,
            "policy_sha256": POLICY_SHA256,
            "event_id": event["event_id"],
            "counter": event["counter"],
            "acknowledgements": acknowledgements,
            "propagation_note": "Any reachable node that accepted the signed event can relay it to peers during normal R3 sync.",
        },
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
