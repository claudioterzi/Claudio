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
from collections.abc import Sequence


def supervise(commands: Sequence[Sequence[str]], *, grace_seconds: float = 5.0) -> int:
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
            children.append(subprocess.Popen(command, start_new_session=True))
        while not stopping:
            for index, child in enumerate(children):
                code = child.poll()
                if code is not None:
                    print(f'R3_CHILD_EXIT child={index} returncode={code}', flush=True)
                    return 1  # even a clean child exit leaves the service incomplete
            time.sleep(0.1)
        return 0
    finally:
        # Terminate entire process groups, including descendants, on every path.
        for child in children:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + grace_seconds
        for child in children:
            try:
                child.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                pass
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
    return supervise([
        [sys.executable, '-m', 'uvicorn', 'r3.node:app', '--host', '0.0.0.0', '--port', str(port)],
        [sys.executable, '-m', 'r3.sync', '--loop'],
    ])


if __name__ == '__main__':
    raise SystemExit(main())
