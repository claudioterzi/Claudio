import sys
import time

import pytest

from r3.supervise_node import supervise
from r3.sync_progress import ProgressWatchdog, ProgressWriter


def test_failure_cooldown_is_bounded_and_still_nonzero():
    start = time.monotonic()
    assert supervise([[sys.executable, '-c', 'pass']], grace_seconds=.1,
                     failure_delay_seconds=.25) == 1
    assert .25 <= time.monotonic() - start < 3


def test_startup_failure_is_nonzero_with_cooldown():
    start = time.monotonic()
    assert supervise([['/nonexistent/r3-child']], grace_seconds=.1,
                     failure_delay_seconds=.25) == 1
    assert .25 <= time.monotonic() - start < 3


def test_invalid_cooldown_rejected_before_spawn():
    for value in (-1, 61, float('inf'), float('nan')):
        with pytest.raises(ValueError):
            supervise([['never-started']], failure_delay_seconds=value)


def test_repeated_suspension_cannot_mask_same_stalled_sequence(tmp_path):
    now = [0.]
    path = tmp_path / 'progress.json'
    writer = ProgressWriter(path, 'run')
    watcher = ProgressWatchdog(path, 'run', timeout=5, startup=10, interval=20,
                               clock=lambda: now[0])
    writer.mark()
    assert watcher.check() is None
    now[0] = 100
    watcher.resume()
    assert watcher.check() is None
    now[0] = 104
    watcher.resume()
    now[0] = 106
    assert watcher.check() == 'sync_progress_timeout'
