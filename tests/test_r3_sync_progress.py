import importlib
import os
import signal
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

from r3.sync_progress import ProgressWatchdog, ProgressWriter


def setup(tmp_path):
    now = [0.0]
    path = tmp_path / "progress.json"
    writer = ProgressWriter(path, "run")
    watcher = ProgressWatchdog(path, "run", timeout=5, startup=10, interval=20,
                               max_failures=3, clock=lambda: now[0])
    return now, writer, watcher


def test_startup_and_hung_work(tmp_path):
    now, writer, watcher = setup(tmp_path)
    now[0] = 9
    assert watcher.check() is None
    writer.mark()
    assert watcher.check() is None
    now[0] = 15
    assert watcher.check() == "sync_progress_timeout"


def test_idle_empty_success_is_healthy_then_expires(tmp_path):
    now, writer, watcher = setup(tmp_path)
    writer.mark("idle", success=True)
    assert watcher.check() is None
    now[0] = 24
    assert watcher.check() is None
    now[0] = 26
    assert watcher.check() == "sync_progress_timeout"


def test_repeated_failures_even_when_advancing(tmp_path):
    now, writer, watcher = setup(tmp_path)
    for i in range(3):
        now[0] += 1
        writer.mark("idle", success=False)
        assert watcher.check() == ("sync_repeated_failure" if i == 2 else None)


def test_transient_failure_resets_after_success(tmp_path):
    _, writer, watcher = setup(tmp_path)
    for success in (False, False, True, False):
        writer.mark("idle", success=success)
        assert watcher.check() is None


def test_stale_run_and_missing_record_rejected(tmp_path):
    now, writer, watcher = setup(tmp_path)
    now[0] = 11
    assert watcher.check() == "progress_missing"
    writer.state["run_id"] = "previous-run"
    writer.mark()
    assert watcher.check() == "progress_invalid"


def test_sync_returns_failures_not_just_normal_return(tmp_path):
    with patch.dict(os.environ, {"R3_DATA_DIR": str(tmp_path)}):
        from r3 import sync
        sync = importlib.reload(sync)
    with patch.object(sync, "sync_rrr_with_peer", return_value=True), \
         patch.object(sync, "_get_hashes", return_value={}):
        assert sync.sync_with_peer("http://unused.invalid") is True
    with patch.object(sync, "sync_rrr_with_peer", return_value=True), \
         patch.object(sync, "_get_hashes", side_effect=RuntimeError("offline")):
        assert sync.sync_with_peer("http://unused.invalid") is False
    with patch.object(sync, "PEER_URLS", ["http://unused.invalid"]), \
         patch.object(sync, "SYNC_CANARY", False), \
         patch.object(sync, "sync_with_peer", return_value=False):
        assert sync.run_once() is False


def test_watchdog_failure_stops_and_reaps_real_children(tmp_path):
    from r3.supervise_node import supervise
    from unittest.mock import Mock
    real_popen = subprocess.Popen
    children = []
    def spawn(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        children.append(child)
        return child
    check = Mock(side_effect=[None, "sync_repeated_failure"])
    with patch("r3.supervise_node.subprocess.Popen", side_effect=spawn):
        result = supervise([[sys.executable, "-c", "import time; time.sleep(30)"]]*2,
                           grace_seconds=.2, progress_check=check)
    assert result == 1
    for child in children:
        assert child.poll() is not None
        with pytest.raises(ProcessLookupError):
            os.kill(child.pid, 0)


@pytest.mark.parametrize("mode,reason", [("hang", "sync_progress_timeout"),
                                         ("fail", "sync_repeated_failure")])
def test_real_writer_hang_and_failed_cycles(tmp_path, mode, reason, capsys):
    from r3.supervise_node import supervise
    path = tmp_path / "progress.json"
    code = ("import time\nfrom r3.sync_progress import ProgressWriter\n"
            f"w=ProgressWriter({str(path)!r}, 'run')\nw.mark()\n")
    if mode == "hang":
        code += "time.sleep(30)\n"
    else:
        code += "while True:\n w.mark('idle', success=False)\n time.sleep(.1)\n"
    watcher = ProgressWatchdog(path, "run", timeout=.4, startup=2, interval=.1)
    assert supervise([[sys.executable, "-c", code]], grace_seconds=.2,
                     progress_check=watcher.check) == 1
    assert reason in capsys.readouterr().out
