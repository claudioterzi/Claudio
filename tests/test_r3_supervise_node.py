"""Process-only falsifiers: no provider, HTTP, database or production writes."""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from r3.supervise_node import supervise

ROOT = Path(__file__).resolve().parents[1]


def wait_for(predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.02)
    raise AssertionError('Timed out waiting for process condition')


def start_pair(tmp_path, exit_first=False):
    markers = [tmp_path / 'node.pid', tmp_path / 'sync.pid']
    commands = []
    for index, marker in enumerate(markers):
        code = f"import os,time;open({str(marker)!r},'w').write(str(os.getpid()));"
        code += 'time.sleep(.3)' if exit_first and index == 0 else 'time.sleep(60)'
        commands.append([sys.executable, '-c', code])
    harness = 'from r3.supervise_node import supervise;raise SystemExit(supervise(' + repr(commands) + ',grace_seconds=.5))'
    parent = subprocess.Popen([sys.executable, '-c', harness], cwd=ROOT)
    wait_for(lambda: all(marker.exists() for marker in markers))
    return parent, [int(marker.read_text()) for marker in markers]


def assert_reaped(pids):
    for pid in pids:
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)


@pytest.mark.parametrize('child_index', [0, 1])
def test_either_child_failure_stops_pair(tmp_path, child_index):
    parent, pids = start_pair(tmp_path)
    try:
        os.kill(pids[child_index], signal.SIGKILL)
        assert parent.wait(timeout=5) == 1
        assert_reaped(pids)
    finally:
        if parent.poll() is None:
            parent.kill(); parent.wait()


def test_service_stop_is_clean_and_reaps_children(tmp_path):
    parent, pids = start_pair(tmp_path)
    try:
        parent.terminate()
        assert parent.wait(timeout=5) == 0
        assert_reaped(pids)
    finally:
        if parent.poll() is None:
            parent.kill(); parent.wait()


def test_clean_child_exit_still_fails_incomplete_service(tmp_path):
    parent, pids = start_pair(tmp_path, exit_first=True)
    try:
        assert parent.wait(timeout=5) == 1
        assert_reaped(pids)
    finally:
        if parent.poll() is None:
            parent.kill(); parent.wait()


def test_invalid_commands_rejected():
    with pytest.raises(ValueError):
        supervise([])
    with pytest.raises(ValueError):
        supervise([[]])
