"""Runtime gates for streaming partial transcripts."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time
from typing import Any, Callable, Mapping

from .decider import Decision, ReflexDecider
from .executor import ExecutionResult, execute


STATIC_RISK = {
    "none": 0.0,
    "open_app": 0.10,
    "open_folder": 0.10,
    "dictate": 0.15,
    "set_volume": 0.10,
    "mute": 0.10,
    "unmute": 0.10,
    "screenshot": 0.20,
    "youtube": 0.20,
    "close_app": 1.00,
}
TARGET_REQUIRED = {"open_app", "close_app", "open_folder"}


@dataclass(frozen=True)
class Outcome:
    stance: str
    decision: Decision
    executed: bool
    detail: str
    signature: str


def _signature(decision: Decision) -> str:
    payload = {
        "action": decision.action,
        "target": decision.target,
        "volume": decision.volume,
        "text": decision.text_payload,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


class ReflexRuntime:
    """Evaluate partial transcripts and fire only after deterministic gates."""

    def __init__(
        self,
        config: Mapping[str, Any],
        *,
        decider: ReflexDecider | None = None,
        executor: Callable[[Decision, Mapping[str, Any]], ExecutionResult] = execute,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.config = dict(config)
        self.decider = decider or ReflexDecider(self.config)
        self.executor = executor
        self.clock = clock
        self.last_signature = ""
        self.last_fire_at = -1e12

    def evaluate(
        self,
        transcript: str,
        *,
        execute_actions: bool = False,
        allow_destructive: bool = False,
    ) -> Outcome:
        text = (transcript or "").strip()
        empty = Decision(provider=self.decider.backend)
        if len(text) < int(self.config.get("min_chars", 6)):
            return Outcome("FERMO", empty, False, "fragment too short", "")

        decision = self.decider.decide(text)
        signature = _signature(decision)
        wait_threshold = float(self.config.get("wait_threshold", 0.55))
        fire_threshold = float(self.config.get("fire_threshold", 0.80))
        destructive_threshold = float(self.config.get("destructive_threshold", 0.75))
        cooldown_seconds = float(self.config.get("cooldown_ms", 400)) / 1000.0

        if decision.complete < wait_threshold:
            return Outcome("FERMO", decision, False, "below wait threshold", signature)
        if decision.complete < fire_threshold or decision.action == "none":
            return Outcome("ATTESA", decision, False, "below fire threshold", signature)
        if decision.action in TARGET_REQUIRED and decision.target == "none":
            return Outcome("ATTESA", decision, False, "target unresolved", signature)

        effective_risk = max(float(decision.destructive), STATIC_RISK.get(decision.action, 1.0))
        if effective_risk >= destructive_threshold and not allow_destructive:
            return Outcome("BLOCCO", decision, False, f"risk={effective_risk:.2f}", signature)

        now = self.clock()
        if signature == self.last_signature and (now - self.last_fire_at) < cooldown_seconds:
            return Outcome("FERMO", decision, False, "duplicate within cooldown", signature)

        if not execute_actions or bool(self.config.get("dry_run", True)):
            self.last_signature = signature
            self.last_fire_at = now
            return Outcome("SCATTO", decision, False, "dry-run", signature)

        result = self.executor(decision, self.config)
        if result.ok:
            self.last_signature = signature
            self.last_fire_at = now
            return Outcome("SCATTO", decision, True, result.detail, signature)
        return Outcome("BLOCCO", decision, False, result.detail, signature)
