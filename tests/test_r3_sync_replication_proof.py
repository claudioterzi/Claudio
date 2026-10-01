"""Two-process proof for the A<->B replication receipt (R3_SYNC_CANARY).

Scope: two local OS processes with separate stores and DIFFERENT bearer tokens,
one r3.sync run using R3_PEER_TOKEN. Not a multi-host/provider proof; the
production proof is the R3_SYNC_RECEIPT stream in the platform logs.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import nacl.signing

try:
    from tests.test_r3_rrr_two_process import ROOT, _free_port, _spawn_node, _stop, _wait_health
except ImportError:  # pytest rootdir/sys.path variants
    from test_r3_rrr_two_process import ROOT, _free_port, _spawn_node, _stop, _wait_health


def _receipts(stderr: str) -> list[dict]:
    out = []
    for line in stderr.splitlines():
        if "R3_SYNC_RECEIPT " in line:
            out.append(json.loads(line.split("R3_SYNC_RECEIPT ", 1)[1]))
    return out


def _run_sync(local_url: str, local_token: str, peer_url: str, peer_token: str,
              data_dir: Path) -> list[dict]:
    data_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({
        "R3_LOCAL_URL": local_url,
        "R3_PEERS": peer_url,
        "R3_API_TOKEN": local_token,
        "R3_PEER_TOKEN": peer_token,
        "R3_SYNC_CANARY": "true",
        "R3_DATA_DIR": str(data_dir),
        "R3_NODE_ID": "sync-proof-test",
        "PYTHONPATH": str(ROOT),
    })
    proc = subprocess.run(
        [sys.executable, "-m", "r3.sync"], cwd=ROOT, env=env,
        capture_output=True, text=True, timeout=60, check=True,
    )
    return _receipts(proc.stderr + proc.stdout)


def _hashes(url: str, token: str) -> set[str]:
    r = httpx.get(f"{url}/sync/hashes", headers={"Authorization": f"Bearer {token}"}, timeout=5)
    r.raise_for_status()
    return {d["id"] for d in r.json()["documents"]}


def test_canary_receipt_proves_both_directions_with_distinct_tokens(tmp_path: Path) -> None:
    ctrl = nacl.signing.SigningKey.generate().verify_key.encode().hex()
    port_a, port_b = _free_port(), _free_port()
    url_a, url_b = f"http://127.0.0.1:{port_a}", f"http://127.0.0.1:{port_b}"
    tok_a, tok_b = "TOKEN_A_only", "TOKEN_B_only"
    a = b = None
    try:
        a = _spawn_node(port=port_a, node_id="a", data_dir=tmp_path / "a", token=tok_a,
                        controller_verify_key=ctrl)
        b = _spawn_node(port=port_b, node_id="b", data_dir=tmp_path / "b", token=tok_b,
                        controller_verify_key=ctrl)
        _wait_health(url_a)
        _wait_health(url_b)

        # Pre-existing document only on B must also end up on A.
        r = httpx.post(f"{url_b}/documents", headers={"Authorization": f"Bearer {tok_b}"},
                       files={"file": ("only-b.txt", b"only on B")}, timeout=5)
        r.raise_for_status()
        only_b = r.json()["id"]

        receipts = _run_sync(url_a, tok_a, url_b, tok_b, tmp_path / "sync")
        assert len(receipts) == 1
        rc = receipts[0]
        assert rc["pass"] is True, rc
        assert rc["local_to_peer_arrived"] and rc["peer_to_local_arrived"]
        assert rc["sets_equal"] is True
        assert only_b in _hashes(url_a, tok_a)
        assert rc["canary_local_to_peer"] in _hashes(url_b, tok_b)
        assert rc["canary_peer_to_local"] in _hashes(url_a, tok_a)

        # Second cycle: new canaries, still passing, sets grow by exactly 2.
        rc2 = _run_sync(url_a, tok_a, url_b, tok_b, tmp_path / "sync")[0]
        assert rc2["pass"] is True, rc2
        assert rc2["canary_local_to_peer"] != rc["canary_local_to_peer"]
        assert rc2["local_count"] == rc["local_count"] + 2
    finally:
        _stop(a)
        _stop(b)


def test_receipt_fails_visibly_when_peer_is_unreachable_or_rejects(tmp_path: Path) -> None:
    ctrl = nacl.signing.SigningKey.generate().verify_key.encode().hex()
    port_a, port_b = _free_port(), _free_port()
    url_a, url_b = f"http://127.0.0.1:{port_a}", f"http://127.0.0.1:{port_b}"
    a = b = None
    try:
        a = _spawn_node(port=port_a, node_id="a", data_dir=tmp_path / "a", token="TA",
                        controller_verify_key=ctrl)
        b = _spawn_node(port=port_b, node_id="b", data_dir=tmp_path / "b", token="TB",
                        controller_verify_key=ctrl)
        _wait_health(url_a)
        _wait_health(url_b)

        wrong_token = _run_sync(url_a, "TA", url_b, "WRONG", tmp_path / "s1")[0]
        assert wrong_token["pass"] is False
        assert "error" in wrong_token

        _stop(b)
        b = None
        peer_down = _run_sync(url_a, "TA", url_b, "TB", tmp_path / "s2")[0]
        assert peer_down["pass"] is False
    finally:
        _stop(a)
        _stop(b)
