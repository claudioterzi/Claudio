"""Keep the node and its sync loop in one supervised service lifecycle.

A child exiting unexpectedly fails the service, allowing the configured platform
restart policy to recover both. No secrets or child command lines are logged.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import tempfile
import uuid
from collections.abc import Sequence

from .sync_progress import ProgressWatchdog


def _group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def supervise(commands: Sequence[Sequence[str]], *, grace_seconds: float = 5.0,
              progress_check=None) -> int:
    if not commands or any(not command for command in commands):
        raise ValueError('At least one non-empty child command is required')
    children: list[subprocess.Popen] = []
    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        for command in commands:
            # Check before and right after each start: a SIGTERM that arrives during
            # start-up must not be followed by starting another child. A child started
            # in the residual window is still registered and reaped below. Signals are
            # deliberately NOT blocked here: children would inherit the blocked mask and
            # then ignore SIGTERM (observed in the isolated harness, 2026-10-05).
            if stopping:
                break
            children.append(subprocess.Popen(command, start_new_session=True))
            if stopping:
                break
        while not stopping:
            for index, child in enumerate(children):
                code = child.poll()
                if code is not None:
                    print(f'R3_CHILD_EXIT child={index} returncode={code}', flush=True)
                    return 1  # even a clean child exit leaves the service incomplete
            if progress_check is not None:
                reason = progress_check()
                if reason:
                    print(f'R3_SYNC_UNHEALTHY reason={reason}', flush=True)
                    return 1
            time.sleep(0.1)
        return 0
    finally:
        # Terminate entire process groups, including descendants, on every path.
        for child in children:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        # Grace applies to whole process groups, not only to the leaders: a worker
        # still finishing a write keeps its group alive until the deadline.
        deadline = time.monotonic() + grace_seconds
        while time.monotonic() < deadline:
            for child in children:
                child.poll()  # reap exited leaders so they do not pin the group
            if not any(_group_alive(child.pid) for child in children):
                break
            time.sleep(0.05)
        for child in children:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        for child in children:
            child.wait()
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def main() -> int:
    port = int(os.environ.get('PORT', '8000'))
    if not 1 <= port <= 65535:
        raise ValueError('PORT must be between 1 and 65535')
    os.environ['R3_LOCAL_URL'] = f'http://127.0.0.1:{port}'
    interval = int(os.environ.get('R3_SYNC_INTERVAL', '300'))
    delay = int(os.environ.get('R3_SYNC_START_DELAY', '0'))
    if delay < 0:
        raise ValueError('R3_SYNC_START_DELAY must be nonnegative')
    keys = ('R3_SYNC_PROGRESS_PATH', 'R3_SYNC_PROGRESS_RUN_ID')
    previous = {key: os.environ.get(key) for key in keys}
    with tempfile.TemporaryDirectory(prefix='r3-sync-progress-') as directory:
        run_id = uuid.uuid4().hex
        path = os.path.join(directory, 'progress.json')
        watchdog = ProgressWatchdog(
            path, run_id, interval=interval,
            timeout=float(os.environ.get('R3_SYNC_PROGRESS_TIMEOUT', '180')),
            startup=float(os.environ.get('R3_SYNC_STARTUP_TIMEOUT', '120')) + delay,
            max_failures=int(os.environ.get('R3_SYNC_MAX_FAILURES', '3')),
        )
        os.environ[keys[0]], os.environ[keys[1]] = path, run_id
        try:
            return supervise([
                [sys.executable, '-m', 'uvicorn', 'r3.node:app', '--host', '0.0.0.0', '--port', str(port)],
                [sys.executable, '-m', 'r3.sync', '--loop'],
            ], progress_check=watchdog.check)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == '__main__':
    raise SystemExit(main())
