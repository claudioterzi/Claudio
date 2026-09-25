"""R3 durable-state observability contract.

This module does not claim a filesystem is durable. It creates a stable,
non-secret marker in R3_DATA_DIR and evaluates externally frozen expectations.
A positive durability claim requires three exact matches after a fresh
container/redeploy: marker fingerprint, Ed25519 verify key, and a known
content-addressed canary document.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from pathlib import Path
from typing import Any

MARKER_FILENAME = "persistence.marker"
MARKER_BYTES = 32


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ensure_persistence_marker(data_dir: Path) -> dict[str, Any]:
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / MARKER_FILENAME
    created = False
    if not path.exists():
        payload = secrets.token_bytes(MARKER_BYTES)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        try:
            fd = os.open(path, flags, 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(fd, "wb") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            created = True
    raw = path.read_bytes()
    if len(raw) != MARKER_BYTES:
        raise RuntimeError(f"invalid persistence marker size: {len(raw)}")
    return {
        "sha256": _sha256(raw),
        "created": created,
        "size": len(raw),
    }


def evaluate_durability_expectations(
    *,
    marker_sha256: str,
    verify_key_hex: str,
    expected_marker_sha256: str,
    expected_verify_key_hex: str,
    expected_canary_doc_id: str,
    canary_ok: bool,
) -> dict[str, Any]:
    expected_marker_sha256 = (expected_marker_sha256 or "").strip().lower()
    expected_verify_key_hex = (expected_verify_key_hex or "").strip().lower()
    expected_canary_doc_id = (expected_canary_doc_id or "").strip().lower()

    marker_match = bool(expected_marker_sha256) and marker_sha256.lower() == expected_marker_sha256
    verify_key_match = bool(expected_verify_key_hex) and verify_key_hex.lower() == expected_verify_key_hex
    canary_match = bool(expected_canary_doc_id) and bool(canary_ok)
    expectation_complete = all(
        [expected_marker_sha256, expected_verify_key_hex, expected_canary_doc_id]
    )
    durability_verified = bool(
        expectation_complete and marker_match and verify_key_match and canary_match
    )
    return {
        "expectation_complete": expectation_complete,
        "marker_match": marker_match,
        "verify_key_match": verify_key_match,
        "canary_match": canary_match,
        "durability_verified": durability_verified,
    }
