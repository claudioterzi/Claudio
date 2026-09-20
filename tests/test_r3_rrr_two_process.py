"""Behavioral two-process proof for signed RRR propagation.

Scope: two independent local OS processes, separate SQLite stores, one signed
controller event, HTTP relay through r3.sync. This is not a multi-host/provider
proof.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import nacl.signing

from r3.rrr_control import sign_event


ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_health(base_url: str, timeout: float = 20.0) -> dict:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(f"{base_url}/health", timeout=1.0)
            if response.status_code == 200:
                return response.json()
        except Exception as exc:  # pragma: no cover - diagnostic only
            last_error = exc
        time.sleep(0.15)
    raise AssertionError(f"health timeout for {base_url}; last_error={last_error!r}")


def _spawn_node(
    *,
    port: int,
    node_id: str,
    data_dir: Path,
    token: str,
    controller_verify_key: str,
) -> subprocess.Popen:
    data_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "R3_DATA_DIR": str(data_dir),
            "R3_API_TOKEN": token,
            "R3_NODE_ID": node_id,
            "R3_CONTROL_VERIFY_KEY_HEX": controller_verify_key,
            "R3_SIGNING_KEY_HEX": nacl.signing.SigningKey.generate().encode().hex(),
            "PYTHONPATH": str(ROOT),
        }
    )
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "r3.node:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _stop(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _sync(
    *,
    local_url: str,
    peer_url: str,
    token: str,
    data_dir: Path,
    controller_verify_key: str,
) -> subprocess.CompletedProcess:
    data_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "R3_LOCAL_URL": local_url,
            "R3_PEERS": peer_url,
            "R3_API_TOKEN": token,
            "R3_CONTROL_VERIFY_KEY_HEX": controller_verify_key,
            "R3_DATA_DIR": str(data_dir),
            "R3_NODE_ID": "rrr-sync-test",
            "PYTHONPATH": str(ROOT),
        }
    )
    return subprocess.run(
        [sys.executable, "-m", "r3.sync"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _status(url: str, token: str) -> dict:
    response = httpx.get(f"{url}/protocol/rrr/status", headers=_headers(token), timeout=5)
    response.raise_for_status()
    return response.json()


def _post_event(url: str, token: str, event: dict) -> httpx.Response:
    return httpx.post(
        f"{url}/protocol/rrr/event",
        headers={**_headers(token), "X-R3-Source-Node": "test-controller"},
        json=event,
        timeout=5,
    )


def test_rrr_activation_reaches_late_peer_and_rejects_downgrade(tmp_path: Path) -> None:
    token = "r3-rrr-local-test-token"
    controller = nacl.signing.SigningKey.generate()
    signing_hex = controller.encode().hex()
    verify_hex = controller.verify_key.encode().hex()

    port_a, port_b = _free_port(), _free_port()
    url_a, url_b = f"http://127.0.0.1:{port_a}", f"http://127.0.0.1:{port_b}"
    data_a, data_b = tmp_path / "node-a", tmp_path / "node-b"
    sync_dir = tmp_path / "sync-client"

    proc_a = proc_b = None
    try:
        # A is online. B intentionally does not exist yet.
        proc_a = _spawn_node(
            port=port_a,
            node_id="rrr-node-a",
            data_dir=data_a,
            token=token,
            controller_verify_key=verify_hex,
        )
        assert _wait_health(url_a)["node_id"] == "rrr-node-a"

        activation = sign_event(
            "activate",
            signing_hex,
            issuer="Claudio Terzi",
            counter=200,
            issued_at="2026-09-20T03:40:00+00:00",
            nonce="activate-late-peer-0001",
        )
        applied = _post_event(url_a, token, activation)
        applied.raise_for_status()
        assert applied.json()["status"] == "applied"

        state_a = _status(url_a, token)
        assert state_a["active"] is True
        assert state_a["event_id"] == activation["event_id"]
        assert state_a["counter"] == 200

        # Late/new B joins after the activation was already issued.
        proc_b = _spawn_node(
            port=port_b,
            node_id="rrr-node-b",
            data_dir=data_b,
            token=token,
            controller_verify_key=verify_hex,
        )
        assert _wait_health(url_b)["node_id"] == "rrr-node-b"
        before = _status(url_b, token)
        assert before["active"] is False
        assert before["event_id"] is None

        relay = _sync(local_url=url_a, peer_url=url_b, token=token, data_dir=sync_dir)
        after = _status(url_b, token)
        assert after["active"] is True
        assert after["event_id"] == activation["event_id"]
        assert after["counter"] == 200

        # A valid but older signed event cannot downgrade B.
        stale = sign_event(
            "deactivate",
            signing_hex,
            issuer="Claudio Terzi",
            counter=199,
            issued_at="2026-09-20T03:41:00+00:00",
            nonce="stale-deactivate-0001",
        )
        stale_response = _post_event(url_b, token, stale)
        assert stale_response.status_code == 409
        after_stale = _status(url_b, token)
        assert after_stale["active"] is True
        assert after_stale["event_id"] == activation["event_id"]

        # Equal counter + different signed event is a conflict, never auto-picked.
        conflict = sign_event(
            "deactivate",
            signing_hex,
            issuer="Claudio Terzi",
            counter=200,
            issued_at="2026-09-20T03:42:00+00:00",
            nonce="same-counter-conflict-0001",
        )
        conflict_response = _post_event(url_b, token, conflict)
        assert conflict_response.status_code == 409
        after_conflict = _status(url_b, token)
        assert after_conflict["event_id"] == activation["event_id"]

        print(
            {
                "property": "R3_RRR_LATE_PEER_PROPAGATION",
                "backend": "LOCAL_TWO_PROCESS_SEPARATE_SQLITE",
                "activation_event_id": activation["event_id"],
                "same_event_id_on_a_and_b": state_a["event_id"] == after["event_id"],
                "late_peer_inherited_active": after["active"],
                "stale_downgrade_rejected": stale_response.status_code == 409,
                "same_counter_conflict_rejected": conflict_response.status_code == 409,
                "relay_stdout": relay.stdout.strip(),
                "relay_stderr": relay.stderr.strip(),
                "external_multi_host_proof": False,
            }
        )
    finally:
        _stop(proc_a)
        _stop(proc_b)
