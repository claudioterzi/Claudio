"""Local, ephemeral progress contract; no thread, network or persistent data writes."""
import json
import math
import os
import time
from pathlib import Path


class ProgressWriter:
    def __init__(self, path, run_id):
        self.path = Path(path)
        self.state = dict(run_id=run_id, seq=0, failures=0, successes=0, phase="working")

    def mark(self, phase="working", *, success=None):
        self.state["seq"] += 1
        self.state["phase"] = phase
        if success is not None:
            self.state["failures"] = 0 if success else self.state["failures"] + 1
            self.state["successes"] += int(success)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.state), encoding="utf-8")
        os.replace(temp, self.path)


class ProgressWatchdog:
    def __init__(self, path, run_id, *, timeout=180, startup=120, interval=300,
                 max_failures=3, clock=time.monotonic):
        if any(not math.isfinite(v) or v <= 0 for v in (timeout, startup, interval)):
            raise ValueError("progress time budgets must be finite and positive")
        if type(max_failures) is not int or max_failures < 1:
            raise ValueError("max_failures must be a positive integer")
        self.path, self.run_id = Path(path), run_id
        self.timeout, self.startup, self.interval = timeout, startup, interval
        self.max_failures, self.clock = max_failures, clock
        self.started = self.last_change = clock()
        self.seq, self.phase = 0, "working"

    def check(self):
        now = self.clock()
        try:
            raw = self.path.read_bytes()
            if len(raw) > 4096:
                raise ValueError("oversized progress record")
            state = json.loads(raw)
            if (not isinstance(state, dict) or state.get("run_id") != self.run_id
                    or state.get("phase") not in {"working", "idle"}
                    or any(type(state.get(k)) is not int or state[k] < 0
                           for k in ("seq", "failures", "successes"))):
                raise ValueError("invalid progress record")
        except FileNotFoundError:
            limit = self.startup if self.seq == 0 else self.timeout
            return "progress_missing" if now - self.last_change > limit else None
        except (OSError, ValueError, TypeError):
            return "progress_invalid"
        if state["seq"] < self.seq:
            return "progress_regressed"
        if state["seq"] > self.seq:
            self.seq, self.phase, self.last_change = state["seq"], state["phase"], now
        if state["failures"] >= self.max_failures:
            return "sync_repeated_failure"
        budget = self.timeout + (self.interval if self.phase == "idle" else 0)
        return "sync_progress_timeout" if now - self.last_change > budget else None


_writer = None


def configure_from_environment():
    global _writer
    path, run_id = os.getenv("R3_SYNC_PROGRESS_PATH"), os.getenv("R3_SYNC_PROGRESS_RUN_ID")
    _writer = ProgressWriter(path, run_id) if path and run_id else None
    if _writer:
        _writer.mark()


def note_progress(phase="working", *, success=None):
    if _writer:
        _writer.mark(phase, success=success)
