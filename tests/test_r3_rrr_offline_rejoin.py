"""Falsifier for signed RRR propagation across an offline/rejoining peer.

P5/P6 scope: two independent local OS processes with separate SQLite stores.
This deliberately tests persisted absence, offline issuance, peer catch-up,
transport provenance, stale-event rejection, and persistence after restart.
It is not evidence of multi-host/provider or Internet partition behavior.
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
            "R3_NODE_ID": "rrr-rejoin-sync-test",
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


def test_offline_b_rejoins_catches_same_event_and_cannot_be_downgraded(tmp_path: Path) -> None:
    token = "r3-rrr-offline-rejoin-test-token"
    controller = nacl.signing.SigningKey.generate()
    signing_hex = controller.encode().hex()
    verify_hex = controller.verify_key.encode().hex()

    port_a, port_b = _free_port(), _free_port()
    url_a, url_b = f"http://127.0.0.1:{port_a}", f"http://127.0.0.1:{port_b}"
    data_a, data_b = tmp_path / "node-a", tmp_path / "node-b"
    sync_dir = tmp_path / "sync-client"

    proc_a = proc_b = None
    try:
        # Both nodes exist independently and begin with no RRR event.
        proc_a = _spawn_node(
            port=port_a,
            node_id="rrr-node-a-rejoin",
            data_dir=data_a,
            token=token,
            controller_verify_key=verify_hex,
        )
        proc_b = _spawn_node(
            port=port_b,
            node_id="rrr-node-b-rejoin",
            data_dir=data_b,
            token=token,
            controller_verify_key=verify_hex,
        )
        assert _wait_health(url_a)["node_id"] == "rrr-node-a-rejoin"
        assert _wait_health(url_b)["node_id"] == "rrr-node-b-rejoin"
        assert _status(url_a, token)["event_id"] is None
        assert _status(url_b, token)["event_id"] is None

        # B goes offline before the controller issues the activation to A.
        _stop(proc_b)
        proc_b = None

        activation = sign_event(
            "activate",
            signing_hex,
            issuer="Claudio Terzi",
            counter=300,
            issued_at="2026-09-20T05:35:00+00:00",
            nonce="offline-rejoin-activation-0001",
        )
        applied = _post_event(url_a, token, activation)
        applied.raise_for_status()
        assert applied.json()["status"] == "applied"
        state_a = _status(url_a, token)
        assert state_a["active"] is True
        assert state_a["event_id"] == activation["event_id"]
        assert state_a["counter"] == 300

        # B rejoins using the SAME persistent store. It must still be stale
        # before sync, proving catch-up is caused by peer relay rather than restart.
        proc_b = _spawn_node(
            port=port_b,
            node_id="rrr-node-b-rejoin",
            data_dir=data_b,
            token=token,
            controller_verify_key=verify_hex,
        )
        _wait_health(url_b)
        pre_sync_b = _status(url_b, token)
        assert pre_sync_b["active"] is False
        assert pre_sync_b["event_id"] is None

        relay = _sync(local_url=url_a, peer_url=url_b, token=token, data_dir=sync_dir)
        caught_up_b = _status(url_b, token)
        assert caught_up_b["active"] is True
        assert caught_up_b["event_id"] == activation["event_id"] == state_a["event_id"]
        assert caught_up_b["counter"] == state_a["counter"] == 300
        assert caught_up_b["event"]["issuer"] == "Claudio Terzi"
        assert caught_up_b["event"]["source_node"] == "rrr-rejoin-sync-test"

        # A validly signed older event cannot downgrade the rejoined peer.
        stale = sign_event(
            "deactivate",
            signing_hex,
            issuer="Claudio Terzi",
            counter=299,
            issued_at="2026-09-20T05:36:00+00:00",
            nonce="offline-rejoin-stale-0001",
        )
        stale_response = _post_event(url_b, token, stale)
        assert stale_response.status_code == 409
        after_stale = _status(url_b, token)
        assert after_stale["active"] is True
        assert after_stale["event_id"] == activation["event_id"]
        assert after_stale["counter"] == 300

        # Persisted convergence survives another B process restart.
        _stop(proc_b)
        proc_b = _spawn_node(
            port=port_b,
            node_id="rrr-node-b-rejoin",
            data_dir=data_b,
            token=token,
            controller_verify_key=verify_hex,
        )
        _wait_health(url_b)
        persisted_b = _status(url_b, token)
        assert persisted_b["active"] is True
        assert persisted_b["event_id"] == activation["event_id"]
        assert persisted_b["counter"] == 300
        assert persisted_b["event"]["issuer"] == "Claudio Terzi"
        assert persisted_b["event"]["source_node"] == "rrr-rejoin-sync-test"

        print(
            {
                "property": "R3_RRR_OFFLINE_REJOIN_CATCHUP",
                "backend": "LOCAL_TWO_PROCESS_SEPARATE_SQLITE",
                "activation_event_id": activation["event_id"],
                "b_was_stale_before_sync": pre_sync_b["event_id"] is None,
                "same_event_id_after_rejoin_sync": caught_up_b["event_id"] == state_a["event_id"],
                "controller_issuer_preserved": caught_up_b["event"]["issuer"],
                "relay_source_preserved": caught_up_b["event"]["source_node"],
                "stale_downgrade_rejected": stale_response.status_code == 409,
                "convergence_persisted_after_restart": persisted_b["event_id"] == activation["event_id"],
                "relay_stdout": relay.stdout.strip(),
                "relay_stderr": relay.stderr.strip(),
                "external_multi_host_proof": False,
            }
        )
    finally:
        _stop(proc_a)
        _stop(proc_b)
