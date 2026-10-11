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
# consumer contract: import the canonical package, then mount its ``app``.
# Both paths are explicit: / is the observed Railway mount; /typesafe is the
# earlier synthetic scenario, retained only as an alternate-mount control.
SYNTHETIC_OBSERVED_WRAPPER = '''
from fastapi import FastAPI
import typesafe_sister

app = FastAPI()
WRAPPER_MOUNTED_APP = typesafe_sister.app

# Literal consumer call observed in Railway /app/letta_bridge_v2.py:282.
# This remains a bounded synthetic fixture, not a copy of the full wrapper.
@app.get("/health")
def wrapper_health():
    base = dict(typesafe_sister.health())
    base["wrapper_health_delegated"] = True
    return base

app.mount("/typesafe", WRAPPER_MOUNTED_APP)

@app.api_route("/{path:path}", methods=["GET", "POST"])
async def legacy_catch_all(path: str):
    return {"legacy": path}
'''

PROBE = r'''
import importlib
import json
import socket
import threading

from fastapi.testclient import TestClient

network_attempts = []
original_connect = socket.socket.connect
original_socketpair = socket.socketpair
socketpair_context = threading.local()

def local_socketpair(*args, **kwargs):
    # Windows implements socketpair with a loopback connect. Scope the exemption
    # to this standard-library operation in the calling thread; all other
    # connects, including ordinary loopback/provider requests, remain forbidden.
    socketpair_context.active = True
    try:
        return original_socketpair(*args, **kwargs)
    finally:
        socketpair_context.active = False

def refuse_network(sock, address):
    if (
        getattr(socketpair_context, "active", False)
        and isinstance(address, tuple)
        and address[0] in ("127.0.0.1", "::1")
    ):
        return original_connect(sock, address)
    network_attempts.append(repr(address))
    raise AssertionError("network egress forbidden by startup compatibility test")

socket.socket.connect = refuse_network
socket.socketpair = local_socketpair

guard_negative_controls = 0
with socket.socket() as guard_socket:
    for internal_pair, address in (
        (False, ("127.0.0.1", 1)),
        (False, ("192.0.2.1", 443)),
        (True, ("192.0.2.1", 443)),
    ):
        socketpair_context.active = internal_pair
        try:
            refuse_network(guard_socket, address)
        except AssertionError:
            guard_negative_controls += 1
        else:
            raise AssertionError("egress guard negative control unexpectedly allowed")
        finally:
            socketpair_context.active = False
network_attempts.clear()

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
wrapper_health = client.get("/health")
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

root_probe = None
if any(getattr(route, "path", None) == "" for route in jev_gateway.app.router.routes):
    health = client.get("/health")
    jev_health = client.get("/jev/health")
    jev_provider_calls = list(provider_calls)
    provider_calls.clear()
    typesafe_legacy.system_one = forbidden_provider
    root_missing = client.post("/judge", json=payload)
    root_wrong = client.post(
        "/judge", headers={"Authorization": "Bearer WRONG"}, json=payload,
    )
    root_unauthorized_calls = list(provider_calls)
    typesafe_legacy.R3_API_TOKEN = ""
    unconfigured = [
        client.post(path, json=payload).status_code
        for path in ("/judge", "/jev/judge")
    ]
    typesafe_legacy.R3_API_TOKEN = "TEST_R3_TOKEN"
    typesafe_legacy.system_one = mocked_provider
    root_valid = client.post(
        "/judge", headers={"Authorization": "Bearer TEST_R3_TOKEN"}, json=payload,
    )
    root_probe = {
        "health_status": health.status_code,
        "jev_health_status": jev_health.status_code,
        "health_service": health.json().get("service"),
        "jev_health_service": jev_health.json().get("service"),
        "missing_status": root_missing.status_code,
        "wrong_status": root_wrong.status_code,
        "unauthorized_calls": root_unauthorized_calls,
        "unconfigured_statuses": unconfigured,
        "valid_status": root_valid.status_code,
        "valid_body_matches_jev": root_valid.json() == valid.json(),
        "provider_calls": list(provider_calls),
        "unused_alternate_mount_status": client.get("/typesafe/health").status_code,
    }
    provider_calls[:] = jev_provider_calls

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
root_mount_indexes = [
    index for index, route in enumerate(routes)
    if getattr(route, "path", None) == ""
]

print(json.dumps({
    "gateway_imported": True,
    "wrapper_health_status": wrapper_health.status_code,
    "wrapper_health_delegated": wrapper_health.json().get("wrapper_health_delegated"),
    "wrapper_identity_matches": letta_bridge_v2.WRAPPER_MOUNTED_APP is typesafe_legacy.app,
    "canonical_package_preserved": hasattr(typesafe_sister, "__path__"),
    "canonical_client_imported": client_module.__name__ == "typesafe_sister.client",
    "canonical_client_inside_layout": str(client_module.__file__).startswith(str(__import__("pathlib").Path.cwd())),
    "jev_route_count": len(jev_indexes),
    "route_paths": route_paths,
    "root_probe": root_probe,
    "catch_all_count": len(catch_indexes),
    "jev_before_catch_all": bool(jev_indexes and catch_indexes and max(jev_indexes) < min(catch_indexes)),
    "jev_before_root_mount": bool(jev_indexes and root_mount_indexes and max(jev_indexes) < min(root_mount_indexes)),
    "missing_token_status": missing.status_code,
    "wrong_token_status": wrong.status_code,
    "provider_calls_before_valid": calls_before_valid,
    "valid_status": valid.status_code,
    "valid_provider": valid.json().get("provider"),
    "provider_calls": provider_calls,
    "legacy_status": legacy.status_code,
    "legacy_body": legacy.json(),
    "network_attempts": network_attempts,
    "guard_negative_controls": guard_negative_controls,
}, sort_keys=True))
'''


class TypeSafeOneRuntimeStartupTests(unittest.TestCase):
    mount_path = "/typesafe"

    @classmethod
    def setUpClass(cls) -> None:
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.layout = Path(cls.tempdir.name)
        shutil.copy2(ROOT / "r3" / "typesafe_sister.py", cls.layout / "typesafe_legacy.py")
        shutil.copy2(ROOT / "r3" / "jev_gateway.py", cls.layout / "jev_gateway.py")
        shutil.copytree(ROOT / "typesafe_sister", cls.layout / "typesafe_sister")
        (cls.layout / "letta_bridge_v2.py").write_text(
            SYNTHETIC_OBSERVED_WRAPPER.replace('app.mount("/typesafe",', f'app.mount("{cls.mount_path}",'),
            encoding="utf-8",
        )
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(cls.layout), value]
            if (value := env.get("PYTHONPATH"))
            else [str(cls.layout)]
        )
        env.pop("R3_API_TOKEN", None)
        # Health and mocked contracts must not inherit provider credentials or
        # endpoints from the host. No project/production configuration changes.
        for key in list(env):
            if key.startswith(("TYPESAFE_", "CLM_", "R3_SYSTEMONE_")):
                env.pop(key)
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
        self.assertEqual(self.result["wrapper_health_status"], 200)
        self.assertTrue(self.result["wrapper_health_delegated"])

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
        self.assertEqual(self.result["guard_negative_controls"], 3)

    def test_legacy_catch_all_remains_available(self):
        self.assertEqual(self.result["legacy_status"], 200)
        self.assertEqual(self.result["legacy_body"], {"legacy": "legacy-path"})


class TypeSafeRootMountStartupTests(TypeSafeOneRuntimeStartupTests):
    """Literal observed root mount, still a synthetic wrapper contract."""

    mount_path = "/"

    def test_legacy_catch_all_remains_available(self):
        # A root ASGI mount consumes unmatched paths before the later catch-all.
        # Do not promise the alternate fixture's 200 behavior for this topology.
        self.assertEqual(self.result["legacy_status"], 404)
        self.assertEqual(self.result["legacy_body"], {"detail": "Not Found"})

    def test_root_mount_is_present_and_jev_precedes_it(self):
        paths = self.result["route_paths"]
        self.assertIn("", paths)
        # FastAPI may retain an included router instead of flattening paths;
        # the probe uses the same public prefix metadata as the existing test.
        self.assertTrue(self.result["jev_before_root_mount"])

    def test_root_and_jev_health_use_existing_app(self):
        probe = self.result["root_probe"]
        self.assertEqual(probe["health_status"], 200)
        self.assertEqual(probe["jev_health_status"], 200)
        self.assertEqual(probe["health_service"], "r3-typesafe-sister")
        self.assertEqual(probe["jev_health_service"], "r3-typesafe-sister")

    def test_root_auth_rejects_missing_and_wrong_tokens_before_provider(self):
        probe = self.result["root_probe"]
        self.assertEqual(probe["missing_status"], 401)
        self.assertEqual(probe["wrong_status"], 401)
        self.assertEqual(probe["unauthorized_calls"], [])

    def test_unconfigured_auth_fails_closed_at_root_and_jev(self):
        self.assertEqual(self.result["root_probe"]["unconfigured_statuses"], [503, 503])

    def test_root_authenticated_mock_matches_jev_without_egress(self):
        probe = self.result["root_probe"]
        self.assertEqual(probe["valid_status"], 200)
        self.assertTrue(probe["valid_body_matches_jev"])
        self.assertEqual(probe["provider_calls"], ["authorized"])
        self.assertEqual(self.result["network_attempts"], [])

    def test_unobserved_alternate_mount_is_not_exposed(self):
        self.assertEqual(self.result["root_probe"]["unused_alternate_mount_status"], 404)


if __name__ == "__main__":
    unittest.main()
