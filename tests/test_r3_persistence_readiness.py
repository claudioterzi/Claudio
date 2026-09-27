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
