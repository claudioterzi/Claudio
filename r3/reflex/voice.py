"""Windows microphone bridge for the R3 reflex candidate.

Windows System.Speech emits partial hypotheses and final recognitions. This
module adds a stability gate before an eligible reflex is allowed to execute.
"""
from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
from pathlib import Path
import platform
import subprocess
from typing import Iterator

from .cli import DEFAULT_CONFIG, load_config
from .decider import Decision
from .runtime import Outcome, ReflexRuntime


@dataclass(frozen=True)
class SpeechEvent:
    text: str
    confidence: float
    final: bool
    kind: str = "speech"


def parse_speech_event(line: str) -> SpeechEvent | None:
    try:
        payload = json.loads(line)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("type") in {"status", "rejected"}:
        return None
    if payload.get("type") == "error":
        raise RuntimeError(str(payload.get("message") or "Windows speech error"))
    text = str(payload.get("text") or "").strip()
    if not text:
        return None
    try:
        confidence = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    return SpeechEvent(
        text=text,
        confidence=confidence,
        final=bool(payload.get("final")),
        kind=str(payload.get("type") or "speech"),
    )


class VoiceReflexController:
    """Require stable repeated partials, while allowing a final result immediately."""

    def __init__(
        self,
        runtime: ReflexRuntime,
        *,
        stability_hits: int = 2,
        min_confidence: float = 0.20,
        execute_actions: bool = False,
        allow_destructive: bool = False,
    ):
        self.runtime = runtime
        self.stability_hits = max(1, int(stability_hits))
        self.min_confidence = max(0.0, min(1.0, float(min_confidence)))
        self.execute_actions = bool(execute_actions)
        self.allow_destructive = bool(allow_destructive)
        self.pending_signature = ""
        self.pending_hits = 0

    def _reset(self) -> None:
        self.pending_signature = ""
        self.pending_hits = 0

    def on_event(self, event: SpeechEvent) -> Outcome:
        if not event.final and event.confidence < self.min_confidence:
            self._reset()
            return Outcome(
                "FERMO",
                Decision(provider="windows_speech"),
                False,
                f"voice confidence {event.confidence:.2f} below threshold",
                "",
            )

        preview = self.runtime.evaluate(
            event.text,
            execute_actions=False,
            allow_destructive=self.allow_destructive,
        )
        if preview.stance != "SCATTO":
            self._reset()
            return preview

        if preview.signature == self.pending_signature:
            self.pending_hits += 1
        else:
            self.pending_signature = preview.signature
            self.pending_hits = 1

        if not event.final and self.pending_hits < self.stability_hits:
            return Outcome(
                "ATTESA",
                preview.decision,
                False,
                f"voice stability {self.pending_hits}/{self.stability_hits}",
                preview.signature,
            )

        outcome = self.runtime.evaluate(
            event.text,
            execute_actions=self.execute_actions,
            allow_destructive=self.allow_destructive,
        )
        if outcome.stance == "SCATTO":
            self._reset()
        return outcome


def iter_windows_speech(culture: str = "it-IT") -> Iterator[SpeechEvent]:
    if platform.system() != "Windows":
        raise RuntimeError("Windows System.Speech adapter requires Windows")
    script = Path(__file__).with_name("windows_speech.ps1")
    process = subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-Culture",
            culture,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    if process.stdout is None:
        raise RuntimeError("Windows speech stdout unavailable")
    try:
        for line in process.stdout:
            event = parse_speech_event(line.strip())
            if event is not None:
                yield event
        code = process.wait()
        if code:
            raise RuntimeError(f"Windows speech exited with code {code}")
    finally:
        if process.poll() is None:
            process.terminate()


def _print(event: SpeechEvent, outcome: Outcome) -> None:
    d = outcome.decision
    phase = "FINAL" if event.final else "PART"
    print(
        f"{phase:5} c={event.confidence:.2f} {outcome.stance:7} "
        f"complete={d.complete:.2f} action={d.action} target={d.target} "
        f"detail={outcome.detail} :: {event.text}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="R3 reflex Windows voice bridge")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--backend", choices=["auto", "demo", "typesafe"])
    parser.add_argument("--culture")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-destructive", action="store_true")
    parser.add_argument("--stability-hits", type=int)
    parser.add_argument("--min-confidence", type=float)
    args = parser.parse_args()

    config = load_config(args.config)
    if args.backend:
        config["backend"] = args.backend
    if args.execute:
        config["dry_run"] = False

    culture = args.culture or str(config.get("speech_culture", "it-IT"))
    controller = VoiceReflexController(
        ReflexRuntime(config),
        stability_hits=args.stability_hits or int(config.get("voice_stability_hits", 2)),
        min_confidence=(
            args.min_confidence
            if args.min_confidence is not None
            else float(config.get("voice_min_confidence", 0.20))
        ),
        execute_actions=args.execute,
        allow_destructive=args.allow_destructive,
    )

    print(
        "R3 voice reflex · Windows System.Speech · "
        f"culture={culture} execute={args.execute}"
    )
    for event in iter_windows_speech(culture):
        _print(event, controller.on_event(event))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
