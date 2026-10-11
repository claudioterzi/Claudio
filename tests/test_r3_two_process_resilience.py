from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_health(base_url: str, timeout: float = 20.0) -> dict:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base_url}/health", timeout=1.0)
            if r.status_code == 200:
                return r.json()
        except Exception as exc:  # pragma: no cover - diagnostic only
            last_error = exc
        time.sleep(0.15)
    raise AssertionError(f"health timeout for {base_url}; last_error={last_error!r}")


def _spawn_node(*, port: int, node_id: str, data_dir: Path, token: str) -> subprocess.Popen:
    data_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "R3_DATA_DIR": str(data_dir),
            "R3_API_TOKEN": token,
            "R3_NODE_ID": node_id,
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


def _sync(*, local_url: str, peer_url: str, token: str, data_dir: Path) -> subprocess.CompletedProcess:
    data_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "R3_LOCAL_URL": local_url,
            "R3_PEERS": peer_url,
            "R3_API_TOKEN": token,
            "R3_DATA_DIR": str(data_dir),
            "PYTHONPATH": str(ROOT),
        }
    )
    return subprocess.run(
        [sys.executable, str(ROOT / "r3" / "sync.py")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )


@pytest.mark.timeout(60)
def test_two_independent_processes_failover_and_resync(tmp_path: Path) -> None:
    """
    Property test for the current R3 MVP.

    This proves only two independent local OS processes with separate SQLite/data
    directories and independent HTTP servers. It MUST NOT be reported as a
    multi-host, multi-provider, or Internet/VPS proof.
    """
    token = "r3-test-token-not-a-production-secret"
    port_a, port_b = _free_port(), _free_port()
    url_a, url_b = f"http://127.0.0.1:{port_a}", f"http://127.0.0.1:{port_b}"
    data_a, data_b = tmp_path / "node-a", tmp_path / "node-b"
    sync_dir = tmp_path / "sync-client"

    proc_a = proc_b = None
    try:
        proc_a = _spawn_node(port=port_a, node_id="node-a-test", data_dir=data_a, token=token)
        proc_b = _spawn_node(port=port_b, node_id="node-b-test", data_dir=data_b, token=token)

        health_a = _wait_health(url_a)
        health_b = _wait_health(url_b)
        assert health_a["node_id"] == "node-a-test"
        assert health_b["node_id"] == "node-b-test"

        payload = (ROOT / "sdq1_master.json").read_bytes()
        expected_sha = hashlib.sha256(payload).hexdigest()
        headers = {"Authorization": f"Bearer {token}"}

        upload = httpx.post(
            f"{url_a}/documents",
            headers=headers,
            files={"file": ("sdq1_master.json", payload, "application/json")},
            timeout=10,
        )
        upload.raise_for_status()
        assert upload.json()["id"] == expected_sha

        first_sync = _sync(
            local_url=url_a,
            peer_url=url_b,
            token=token,
            data_dir=sync_dir,
        )

        hashes_b = httpx.get(f"{url_b}/sync/hashes", headers=headers, timeout=5)
        hashes_b.raise_for_status()
        ids_b = {d["id"] for d in hashes_b.json()["documents"]}
        assert expected_sha in ids_b

        downloaded_b = httpx.get(f"{url_b}/documents/{expected_sha}", headers=headers, timeout=5)
        downloaded_b.raise_for_status()
        assert downloaded_b.content == payload

        # Failover property: A is gone; B still serves the exact content-addressed object.
        _stop(proc_a)
        proc_a = None
        assert _wait_health(url_b)["status"] == "healthy"
        still_on_b = httpx.get(f"{url_b}/documents/{expected_sha}", headers=headers, timeout=5)
        still_on_b.raise_for_status()
        assert hashlib.sha256(still_on_b.content).hexdigest() == expected_sha

        # Restart A using its own persistent directory, then reconcile again.
        proc_a = _spawn_node(port=port_a, node_id="node-a-test", data_dir=data_a, token=token)
        _wait_health(url_a)
        second_sync = _sync(
            local_url=url_a,
            peer_url=url_b,
            token=token,
            data_dir=sync_dir,
        )

        hashes_a = httpx.get(f"{url_a}/sync/hashes", headers=headers, timeout=5)
        hashes_b2 = httpx.get(f"{url_b}/sync/hashes", headers=headers, timeout=5)
        hashes_a.raise_for_status()
        hashes_b2.raise_for_status()
        ids_a = {d["id"] for d in hashes_a.json()["documents"]}
        ids_b2 = {d["id"] for d in hashes_b2.json()["documents"]}
        assert ids_a == ids_b2 == {expected_sha}

        print(
            json.dumps(
                {
                    "property": "R3_TWO_PROCESS_FAILOVER_RESYNC",
                    "backend": "LOCAL_TWO_PROCESS_SEPARATE_SQLITE",
                    "node_a": health_a["node_id"],
                    "node_b": health_b["node_id"],
                    "document_sha256": expected_sha,
                    "failover_b_served_after_a_stop": True,
                    "resync_after_a_restart": True,
                    "same_hash_sets": True,
                    "first_sync_stdout": first_sync.stdout.strip(),
                    "first_sync_stderr": first_sync.stderr.strip(),
                    "second_sync_stdout": second_sync.stdout.strip(),
                    "second_sync_stderr": second_sync.stderr.strip(),
                    "external_multi_host_proof": False,
                },
                sort_keys=True,
            )
        )
    finally:
        _stop(proc_a)
        _stop(proc_b)
