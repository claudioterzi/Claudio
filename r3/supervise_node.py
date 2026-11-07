"""Keep the node and its sync loop in one supervised service lifecycle.

A child exiting unexpectedly fails the service, allowing the configured platform
restart policy to recover both. No secrets or child command lines are logged.
"""
from __future__ import annotations

import os
import ctypes
import math
from pathlib import Path
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


def _enable_subreaper():
    """Adopt orphan descendants on Linux; preserve caller's previous setting."""
    if sys.platform != "linux":
        return None
    libc = ctypes.CDLL(None, use_errno=True)
    previous = ctypes.c_int()
    if libc.prctl(37, ctypes.byref(previous), 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_GET_CHILD_SUBREAPER")
    if libc.prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_SET_CHILD_SUBREAPER")
    return libc, previous.value


def _adopted_pids(children):
    known = {child.pid for child in children}
    # /proc can be mounted from an ancestor namespace, and some kernels omit
    # task/children. PPid and NSpid in status give a portable Linux enumeration.
    own = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines()
               if ':' in line)
    proc_parent = int(own['Pid'])
    depth = len(own['NSpid'].split()) - 1
    adopted = set()
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = dict(line.split(':', 1) for line in (entry / 'status').read_text().splitlines()
                          if ':' in line)
            if int(fields['PPid']) != proc_parent:
                continue
            pid = int(fields['NSpid'].split()[depth])
        except (FileNotFoundError, ProcessLookupError):
            continue
        if pid not in known:
            adopted.add(pid)
    return adopted


def _reap_adopted(children):
    # Never waitpid(-1): Popen owns the status of each direct child.
    for child in children:
        child.poll()
    if sys.platform != "linux":
        return set()
    live = set()
    for pid in _adopted_pids(children):
        try:
            # An unreaped child retains its PID even after exit. With this dedicated
            # single reaper, PID reuse cannot race the subsequent signal.
            if os.waitpid(pid, os.WNOHANG)[0] == 0:
                live.add(pid)
        except ChildProcessError:
            pass
    return live


def _signal_adopted(children, signum, already=None):
    live = _reap_adopted(children)
    for pid in live:
        if already is not None and pid in already:
            continue
        try:
            os.kill(pid, signum)
        except ProcessLookupError:
            pass
        if already is not None:
            already.add(pid)
    return live


def _cleanup_children(children, grace_seconds):
    for child in children:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    terminated = set()
    deadline = time.monotonic() + grace_seconds
    while True:
        live = _signal_adopted(children, signal.SIGTERM, terminated)
        groups = any(_group_alive(child.pid) for child in children)
        if not live and not groups:
            return True
        if time.monotonic() >= deadline:
            break
        time.sleep(.05)
    for child in children:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    # Leaders can die and expose another generation of orphan descendants. Keep
    # collecting and killing adopted children, bounded even for uninterruptible IO.
    deadline = time.monotonic() + 1.0
    while True:
        live = _signal_adopted(children, signal.SIGKILL)
        leaders_alive = any(child.poll() is None for child in children)
        if not live and not leaders_alive and not _adopted_pids(children):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(.02)


def supervise(commands: Sequence[Sequence[str]], *, grace_seconds: float = 5.0,
              progress_check=None, failure_delay_seconds: float = 0.0) -> int:
    if not commands or any(not command for command in commands):
        raise ValueError('At least one non-empty child command is required')
    if not math.isfinite(grace_seconds) or grace_seconds < 0:
        raise ValueError('grace_seconds must be finite and nonnegative')
    if not math.isfinite(failure_delay_seconds) or not 0 <= failure_delay_seconds <= 60:
        raise ValueError('failure_delay_seconds must be between 0 and 60')
    subreaper = _enable_subreaper()
    children: list[subprocess.Popen] = []
    stopping = False
    failed = False

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
        last_tick = time.monotonic()
        while not stopping:
            now = time.monotonic()
            if now - last_tick > 1.0:
                owner = getattr(progress_check, "__self__", None)
                if owner is not None and hasattr(owner, "resume"):
                    owner.resume()
            last_tick = now
            _reap_adopted(children)
            for index, child in enumerate(children):
                code = child.poll()
                if code is not None:
                    failed = True
                    print(f'R3_CHILD_EXIT child={index} returncode={code}', flush=True)
                    return 1  # even a clean child exit leaves the service incomplete
            if progress_check is not None:
                reason = progress_check()
                if reason:
                    failed = True
                    print(f'R3_SYNC_UNHEALTHY reason={reason}', flush=True)
                    return 1
            time.sleep(0.1)
        return 0
    except OSError as exc:
        failed = True
        print(f'R3_CHILD_START_OR_RUNTIME_ERROR type={type(exc).__name__}', flush=True)
        return 1
    finally:
        cleanup_ok = False
        try:
            cleanup_ok = _cleanup_children(children, grace_seconds)
            if failed and not stopping and failure_delay_seconds:
                print(f'R3_FAILURE_COOLDOWN seconds={failure_delay_seconds}', flush=True)
                deadline = time.monotonic() + failure_delay_seconds
                while not stopping and time.monotonic() < deadline:
                    _reap_adopted(children)
                    time.sleep(min(.1, max(0, deadline - time.monotonic())))
        finally:
            try:
                if subreaper is not None:
                    libc, old = subreaper
                    libc.prctl(36, old, 0, 0, 0)
            finally:
                for sig, handler in previous.items():
                    signal.signal(sig, handler)
        if not cleanup_ok:
            print('R3_CLEANUP_INCOMPLETE', flush=True)
            return 1


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
            ], progress_check=watchdog.check,
               failure_delay_seconds=float(os.environ.get('R3_FAILURE_DELAY_SECONDS', '5')))
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == '__main__':
    raise SystemExit(main())
