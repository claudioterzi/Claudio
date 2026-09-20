"""Falsifier for a stale RRR peer rejoining after a newer activation.

P5/P6 scope: two independent local OS processes with separate SQLite stores.
The stale node initiates synchronization itself. The test falsifies the claim
that an older valid signed state can win merely because that stale peer is the
sync initiator. It is not evidence of multi-host/provider partition behavior.
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
            "R3_NODE_ID": "rrr-stale-peer-sync-test",
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


def test_stale_b_initiates_rejoin_sync_but_newer_a_wins(tmp_path: Path) -> None:
    token = "r3-rrr-stale-peer-rejoin-test-token"
    controller = nacl.signing.SigningKey.generate()
    signing_hex = controller.encode().hex()
    verify_hex = controller.verify_key.encode().hex()

    port_a, port_b = _free_port(), _free_port()
    url_a, url_b = f"http://127.0.0.1:{port_a}", f"http://127.0.0.1:{port_b}"
    data_a, data_b = tmp_path / "node-a", tmp_path / "node-b"
    sync_dir = tmp_path / "sync-client"

    proc_a = proc_b = None
    try:
        proc_a = _spawn_node(
            port=port_a,
            node_id="rrr-node-a-stale-peer",
            data_dir=data_a,
            token=token,
            controller_verify_key=verify_hex,
        )
        proc_b = _spawn_node(
            port=port_b,
            node_id="rrr-node-b-stale-peer",
            data_dir=data_b,
            token=token,
            controller_verify_key=verify_hex,
        )
        assert _wait_health(url_a)["node_id"] == "rrr-node-a-stale-peer"
        assert _wait_health(url_b)["node_id"] == "rrr-node-b-stale-peer"

        # B has a valid but older controller state before going offline.
        older = sign_event(
            "deactivate",
            signing_hex,
            issuer="Claudio Terzi",
            counter=399,
            issued_at="2026-09-20T06:20:00+00:00",
            nonce="stale-peer-deactivation-0001",
        )
        old_applied = _post_event(url_b, token, older)
        old_applied.raise_for_status()
        state_b_old = _status(url_b, token)
        assert state_b_old["active"] is False
        assert state_b_old["event_id"] == older["event_id"]
        assert state_b_old["counter"] == 399

        _stop(proc_b)
        proc_b = None

        # While B is offline, the controller gives A one newer activation.
        activation = sign_event(
            "activate",
            signing_hex,
            issuer="Claudio Terzi",
            counter=400,
            issued_at="2026-09-20T06:21:00+00:00",
            nonce="stale-peer-activation-0001",
        )
        activated = _post_event(url_a, token, activation)
        activated.raise_for_status()
        state_a_before = _status(url_a, token)
        assert state_a_before["active"] is True
        assert state_a_before["event_id"] == activation["event_id"]
        assert state_a_before["counter"] == 400
        assert state_a_before["event"]["source_node"] == "test-controller"

        # B rejoins from the SAME store and is demonstrably stale before sync.
        proc_b = _spawn_node(
            port=port_b,
            node_id="rrr-node-b-stale-peer",
            data_dir=data_b,
            token=token,
            controller_verify_key=verify_hex,
        )
        _wait_health(url_b)
        pre_sync_b = _status(url_b, token)
        assert pre_sync_b["active"] is False
        assert pre_sync_b["event_id"] == older["event_id"]
        assert pre_sync_b["counter"] == 399

        # Crucial falsifier: the STALE node B initiates sync toward newer A.
        # Counter ordering must cause B to pull A's signed event, not push 399.
        relay = _sync(local_url=url_b, peer_url=url_a, token=token, data_dir=sync_dir)

        state_a_after = _status(url_a, token)
        caught_up_b = _status(url_b, token)
        assert state_a_after["active"] is True
        assert state_a_after["event_id"] == activation["event_id"]
        assert state_a_after["counter"] == 400
        assert state_a_after["event"]["source_node"] == "test-controller"

        assert caught_up_b["active"] is True
        assert caught_up_b["event_id"] == activation["event_id"] == state_a_after["event_id"]
        assert caught_up_b["counter"] == state_a_after["counter"] == 400
        assert caught_up_b["event"]["issuer"] == "Claudio Terzi"
        assert caught_up_b["event"]["source_node"] == "rrr-stale-peer-sync-test"

        # Direct replay of B's older valid event must still be rejected by A.
        downgrade = _post_event(url_a, token, older)
        assert downgrade.status_code == 409
        final_a = _status(url_a, token)
        assert final_a["active"] is True
        assert final_a["event_id"] == activation["event_id"]
        assert final_a["counter"] == 400

        print(
            {
                "property": "R3_RRR_STALE_PEER_REJOIN_NO_DOWNGRADE",
                "backend": "LOCAL_TWO_PROCESS_SEPARATE_SQLITE",
                "older_event_id": older["event_id"],
                "activation_event_id": activation["event_id"],
                "stale_b_counter_before_sync": pre_sync_b["counter"],
                "authoritative_a_counter_before_sync": state_a_before["counter"],
                "stale_node_initiated_sync": True,
                "same_newer_event_id_after_sync": caught_up_b["event_id"] == state_a_after["event_id"],
                "a_not_downgraded_by_stale_sync_initiator": state_a_after["event_id"] == activation["event_id"],
                "direct_old_event_rejected": downgrade.status_code == 409,
                "controller_issuer_preserved": caught_up_b["event"]["issuer"],
                "relay_source_preserved": caught_up_b["event"]["source_node"],
                "relay_stdout": relay.stdout.strip(),
                "relay_stderr": relay.stderr.strip(),
                "external_multi_host_proof": False,
            }
        )
    finally:
        _stop(proc_a)
        _stop(proc_b)
