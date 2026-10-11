from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# The real wrapper is materialized from a digest-pinned environment payload and
# is not available in this repository.  This fixture models only the observed
# consumer contract: import the canonical package, then mount its ``app``
# attribute before installing a legacy catch-all.
SYNTHETIC_OBSERVED_WRAPPER = '''
from fastapi import FastAPI
import typesafe_sister

app = FastAPI()
WRAPPER_MOUNTED_APP = typesafe_sister.app
app.mount("/typesafe", WRAPPER_MOUNTED_APP)

@app.api_route("/{path:path}", methods=["GET", "POST"])
async def legacy_catch_all(path: str):
    return {"legacy": path}
'''

PROBE = r'''
import importlib
import json
import socket

from fastapi.testclient import TestClient

network_attempts = []
original_connect = socket.socket.connect

def refuse_network(sock, address):
    network_attempts.append(repr(address))
    raise AssertionError("network egress forbidden by startup compatibility test")

socket.socket.connect = refuse_network

import jev_gateway
import letta_bridge_v2
import typesafe_legacy
import typesafe_sister

client_module = importlib.import_module("typesafe_sister.client")
typesafe_legacy.R3_API_TOKEN = "TEST_R3_TOKEN"
provider_calls = []

def forbidden_provider(*args, **kwargs):
    provider_calls.append("unauthorized")
    raise AssertionError("unauthorized request reached provider")

typesafe_legacy.system_one = forbidden_provider
client = TestClient(jev_gateway.app)
payload = {
    "state": {"ready": True},
    "questions": {"present": {"type": "noul", "instructions": "present?"}},
}
missing = client.post("/jev/judge", json=payload)
wrong = client.post(
    "/jev/judge",
    headers={"Authorization": "Bearer WRONG"},
    json=payload,
)
calls_before_valid = list(provider_calls)

def mocked_provider(*args, **kwargs):
    provider_calls.append("authorized")
    return {
        "model": "mocked-system-one",
        "answers": {"present": {"type": "noul", "noul": 0.75}},
        "_r3_provider": "mocked",
    }

typesafe_legacy.system_one = mocked_provider
valid = client.post(
    "/jev/judge",
    headers={"Authorization": "Bearer TEST_R3_TOKEN"},
    json=payload,
)
legacy = client.get("/legacy-path")

routes = list(jev_gateway.app.router.routes)
route_paths = [str(getattr(route, "path", "")) for route in routes]
jev_indexes = [
    index for index, route in enumerate(routes)
    if (
        str(getattr(route, "path", "")).startswith("/jev/")
        or str(getattr(getattr(route, "include_context", None), "prefix", "")) == "/jev"
    )
]
catch_indexes = [
    index for index, route in enumerate(routes)
    if getattr(route, "path", None) == "/{path:path}"
]

print(json.dumps({
    "gateway_imported": True,
    "wrapper_identity_matches": letta_bridge_v2.WRAPPER_MOUNTED_APP is typesafe_legacy.app,
    "canonical_package_preserved": hasattr(typesafe_sister, "__path__"),
    "canonical_client_imported": client_module.__name__ == "typesafe_sister.client",
    "canonical_client_inside_layout": str(client_module.__file__).startswith(str(__import__("pathlib").Path.cwd())),
    "jev_route_count": len(jev_indexes),
    "route_paths": route_paths,
    "catch_all_count": len(catch_indexes),
    "jev_before_catch_all": bool(jev_indexes and catch_indexes and max(jev_indexes) < min(catch_indexes)),
    "missing_token_status": missing.status_code,
    "wrong_token_status": wrong.status_code,
    "provider_calls_before_valid": calls_before_valid,
    "valid_status": valid.status_code,
    "valid_provider": valid.json().get("provider"),
    "provider_calls": provider_calls,
    "legacy_status": legacy.status_code,
    "legacy_body": legacy.json(),
    "network_attempts": network_attempts,
}, sort_keys=True))
'''


class TypeSafeOneRuntimeStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.layout = Path(cls.tempdir.name)
        shutil.copy2(ROOT / "r3" / "typesafe_sister.py", cls.layout / "typesafe_legacy.py")
        shutil.copy2(ROOT / "r3" / "jev_gateway.py", cls.layout / "jev_gateway.py")
        shutil.copytree(ROOT / "typesafe_sister", cls.layout / "typesafe_sister")
        (cls.layout / "letta_bridge_v2.py").write_text(
            SYNTHETIC_OBSERVED_WRAPPER,
            encoding="utf-8",
        )
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(cls.layout), value]
            if (value := env.get("PYTHONPATH"))
            else [str(cls.layout)]
        )
        env.pop("R3_API_TOKEN", None)
        proc = subprocess.run(
            [sys.executable, "-c", PROBE],
            cwd=cls.layout,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        cls.exit_code = proc.returncode
        cls.stderr = proc.stderr
        cls.result = json.loads(proc.stdout.splitlines()[-1]) if proc.stdout.strip() else {}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tempdir.cleanup()

    def test_dockerfile_copy_layout_matches_probe(self):
        dockerfile = (ROOT / "Dockerfile.r3-typesafe-one-runtime").read_text(encoding="utf-8")
        self.assertIn("COPY r3/typesafe_sister.py ./typesafe_legacy.py", dockerfile)
        self.assertIn("COPY r3/jev_gateway.py ./jev_gateway.py", dockerfile)
        self.assertIn("COPY typesafe_sister ./typesafe_sister", dockerfile)

    def test_gateway_imports_in_fresh_process_with_expected_app_identity(self):
        self.assertEqual(self.exit_code, 0, self.stderr)
        self.assertTrue(self.result["gateway_imported"])
        self.assertTrue(self.result["wrapper_identity_matches"])

    def test_canonical_package_and_client_remain_importable(self):
        self.assertTrue(self.result["canonical_package_preserved"])
        self.assertTrue(self.result["canonical_client_imported"])
        self.assertTrue(self.result["canonical_client_inside_layout"])

    def test_jev_routes_precede_legacy_catch_all(self):
        self.assertGreater(self.result["jev_route_count"], 0)
        self.assertEqual(self.result["catch_all_count"], 1)
        self.assertTrue(self.result["jev_before_catch_all"])

    def test_missing_and_wrong_tokens_fail_before_provider(self):
        self.assertEqual(self.result["missing_token_status"], 401)
        self.assertEqual(self.result["wrong_token_status"], 401)
        self.assertEqual(self.result["provider_calls_before_valid"], [])

    def test_authenticated_mocked_request_preserves_contract_without_egress(self):
        self.assertEqual(self.result["valid_status"], 200)
        self.assertEqual(self.result["valid_provider"], "mocked")
        self.assertEqual(self.result["provider_calls"], ["authorized"])
        self.assertEqual(self.result["network_attempts"], [])

    def test_legacy_catch_all_remains_available(self):
        self.assertEqual(self.result["legacy_status"], 200)
        self.assertEqual(self.result["legacy_body"], {"legacy": "legacy-path"})


if __name__ == "__main__":
    unittest.main()
