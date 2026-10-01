"""Readiness and local restart tests for R3 durable state semantics."""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import nacl.signing


ROOT = Path(__file__).resolve().parents[1]


def _base_env(data_dir: str) -> dict[str, str]:
    controller = nacl.signing.SigningKey.generate()
    return {
        "R3_DATA_DIR": data_dir,
        "R3_API_TOKEN": "TEST_TOKEN",
        "R3_NODE_ID": "persistence-test",
        "R3_CONTROL_VERIFY_KEY_HEX": controller.verify_key.encode().hex(),
        "R3_SIGNING_KEY_HEX": nacl.signing.SigningKey.generate().encode().hex(),
        "R3_REQUIRE_RRR_ACTIVE": "false",
        "R3_REQUIRE_DURABLE_STATE": "true",
    }


def test_ready_fails_when_durable_state_is_not_detected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, _base_env(tmp), clear=False):
            import r3.node as node

            node = importlib.reload(node)
            with patch("r3.node.os.path.ismount", return_value=False):
                state = node._readiness_state()

        assert state["ready"] is False
        assert state["durable_state_required"] is True
        assert state["durable_state_detected"] is False
        assert "durable_state_not_detected" in state["reasons"]


def test_ready_accepts_detected_mount_when_other_gates_are_satisfied() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, _base_env(tmp), clear=False):
            import r3.node as node

            node = importlib.reload(node)
            with patch("r3.node.os.path.ismount", return_value=True):
                state = node._readiness_state()

        assert state["ready"] is True
        assert state["durable_state_detected"] is True
        assert state["reasons"] == []


def test_signing_identity_survives_fresh_process_restart_on_same_data_dir() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env.update(_base_env(tmp))
        env["R3_SIGNING_KEY_HEX"] = ""
        env["R3_REQUIRE_DURABLE_STATE"] = "false"
        env["PYTHONPATH"] = str(ROOT)

        code = (
            "import json; from r3 import node; "
            "print(json.dumps({'verify_key': node.VERIFY_KEY_HEX, "
            "'db_exists': node.DB_PATH.exists(), 'key_exists': node._KEY_FILE.exists()}))"
        )
        first = json.loads(
            subprocess.check_output([sys.executable, "-c", code], cwd=ROOT, env=env, text=True)
        )
        second = json.loads(
            subprocess.check_output([sys.executable, "-c", code], cwd=ROOT, env=env, text=True)
        )

        assert first["verify_key"] == second["verify_key"]
        assert first["db_exists"] and second["db_exists"]
        assert first["key_exists"] and second["key_exists"]


# ---------------------------------------------------------------------------
# Issue #86 — full-state restart contract (identity + storage + protocol + docs)
# ---------------------------------------------------------------------------

_FINGERPRINT_CODE = r"""
import json, sys
from unittest.mock import patch
from fastapi.testclient import TestClient
from r3 import node

client = TestClient(node.app)
auth = {"Authorization": "Bearer TEST_TOKEN"}
if sys.argv[1] == "seed":
    r = client.post("/documents", headers=auth,
                    files={"file": ("seed.txt", b"r3 preregistered seed #86")})
    assert r.status_code == 200, r.text
with patch("r3.node.os.path.ismount", return_value=True):
    fp = client.get("/state/fingerprint", headers=auth)
assert fp.status_code == 200, fp.text
print(json.dumps(fp.json()))
"""


def _boot(env: dict[str, str], mode: str) -> dict:
    out = subprocess.check_output(
        [sys.executable, "-c", _FINGERPRINT_CODE, mode], cwd=ROOT, env=env, text=True
    )
    return json.loads(out.strip().splitlines()[-1])


def _proof_compare():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import r3_restart_proof
    finally:
        sys.path.pop(0)
    return r3_restart_proof.compare


def test_full_state_survives_two_clean_restarts_on_same_data_dir() -> None:
    compare = _proof_compare()
    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env.update(_base_env(tmp))
        env["R3_SIGNING_KEY_HEX"] = ""  # identity must come from DATA_DIR
        env["PYTHONPATH"] = str(ROOT)

        baseline = _boot(env, "seed")
        assert baseline["document_count"] == 1
        assert baseline["storage_id_created_this_boot"] is True

        first = _boot(env, "read")
        second = _boot(env, "read")

        assert compare(baseline, first, None) == []
        assert compare(baseline, second, first) == []
        assert first["process_boot_id"] != second["process_boot_id"]
        assert second["storage_id_created_this_boot"] is False
        assert second["documents_missing_or_corrupt"] == []


def test_env_signing_key_alone_does_not_pass_restart_proof() -> None:
    """Same R3_SIGNING_KEY_HEX, lost DATA_DIR: identity matches, proof must FAIL."""
    compare = _proof_compare()
    pinned_key = nacl.signing.SigningKey.generate().encode().hex()
    with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
        env = os.environ.copy()
        env.update(_base_env(tmp_a))
        env["R3_SIGNING_KEY_HEX"] = pinned_key
        env["PYTHONPATH"] = str(ROOT)
        baseline = _boot(env, "seed")

        env["R3_DATA_DIR"] = tmp_b  # simulates ephemeral storage wiped on restart
        after = _boot(env, "read")

        assert after["verify_key"] == baseline["verify_key"]
        failures = compare(baseline, after, None)
        assert any(f.startswith("storage_id changed") for f in failures)
        assert any(f.startswith("document_set_sha256 changed") for f in failures)
        assert any("created on this boot" in f for f in failures)


def test_restart_proof_rejects_evidence_without_a_real_restart() -> None:
    compare = _proof_compare()
    snap = {
        "node_id": "n", "verify_key": "k", "storage_id": "s", "rrr_event_id": None,
        "rrr_counter": None, "rrr_action": None, "protocol_event_count": 0,
        "document_count": 0, "document_set_sha256": "x",
        "storage_id_created_this_boot": False, "documents_missing_or_corrupt": [],
        "durable_state_detected": True, "process_boot_id": "same",
    }
    assert any("no restart happened" in f for f in compare(snap, dict(snap), None))


def test_restart_proof_rejects_unmounted_data_dir() -> None:
    compare = _proof_compare()
    base = {
        "node_id": "n", "verify_key": "k", "storage_id": "s", "rrr_event_id": None,
        "rrr_counter": None, "rrr_action": None, "protocol_event_count": 0,
        "document_count": 0, "document_set_sha256": "x",
        "storage_id_created_this_boot": False, "documents_missing_or_corrupt": [],
        "durable_state_detected": True, "process_boot_id": "a",
    }
    cur = dict(base, process_boot_id="b", durable_state_detected=False)
    assert any("not a mount" in f for f in compare(base, cur, None))
