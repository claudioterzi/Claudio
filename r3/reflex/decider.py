"""Typed System One decision layer for bounded desktop reflexes.

The TypeSafe transport is the canonical shared client in typesafe_sister.client.
No TypeSafe output is authority or factual evidence; it is advisory classification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping

from typesafe_sister.client import configured, system_one
from typesafe_sister.policy import R3_REFLEX_ACTIONS, r3_reflex_questions


_OPEN = re.compile(r"\b(apri|aprire|abre|open|avvia|lancia)\b", re.I)
_CLOSE = re.compile(r"\b(chiudi|chiudere|cierra|close|esci)\b", re.I)
_VOLUME = re.compile(r"\b(volume|audio)\b.*?(\d{1,3})", re.I)
_MUTE = re.compile(r"\b(muta|mute|silenzio)\b", re.I)
_UNMUTE = re.compile(r"\b(smuta|unmute|riattiva audio)\b", re.I)
_DICTATE = re.compile(r"\b(scrivi|detta|dettare|type|pega)\b", re.I)
_SCREENSHOT = re.compile(r"\b(screenshot|cattura schermo|foto schermo)\b", re.I)
_YOUTUBE = re.compile(r"\b(youtube|metti un video)\b", re.I)
_FOLDER = re.compile(r"\b(cartella|folder|download|documenti|desktop)\b", re.I)


@dataclass
class Decision:
    complete: float = 0.0
    action: str = "none"
    target: str = "none"
    destructive: float = 0.0
    action_probs: dict[str, float] = field(default_factory=dict)
    target_probs: dict[str, float] = field(default_factory=dict)
    volume: float | None = None
    text_payload: str = ""
    provider: str = "demo"
    model: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def _bounded_probability(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError("invalid probability")
    if not 0.0 <= number <= 1.0:
        raise ValueError("probability outside [0,1]")
    return number


def _choice(answer: Any, allowed: set[str]) -> tuple[str, dict[str, float]]:
    if not isinstance(answer, dict) or answer.get("type") != "choice":
        raise ValueError("invalid choice")
    value = answer.get("choice")
    if value not in allowed:
        raise ValueError("choice outside closed catalog")
    raw_probs = answer.get("probabilities") or {}
    probs = {}
    if isinstance(raw_probs, dict):
        for key, probability in raw_probs.items():
            if key in allowed:
                probs[str(key)] = _bounded_probability(probability)
    return str(value), probs


def _noul(answer: Any) -> float:
    if not isinstance(answer, dict) or answer.get("type") != "noul":
        raise ValueError("invalid noul")
    return _bounded_probability(answer.get("noul"))


def _match_target(text: str, catalog: Mapping[str, str]) -> tuple[str, float]:
    low = text.lower()
    best = "none"
    best_len = 0
    for name in catalog:
        key = str(name).lower()
        if key in low and len(key) > best_len:
            best = str(name)
            best_len = len(key)
    if best == "none":
        return "none", 0.15
    return best, min(0.95, 0.45 + best_len / 20.0)


def _demo_decide(transcript: str, apps: Mapping[str, str], folders: Mapping[str, str]) -> Decision:
    text = (transcript or "").strip()
    words = len(text.split())
    catalog = {**apps, **folders}

    def base(action: str, target: str = "none", complete: float = 0.0) -> Decision:
        static_risk = 0.90 if action == "close_app" else 0.05
        return Decision(
            complete=complete,
            action=action,
            target=target,
            destructive=static_risk,
            action_probs={action: complete, "none": max(0.0, 1.0 - complete)},
            provider="demo",
        )

    if not text:
        return base("none", complete=0.02)

    target, target_confidence = _match_target(text, catalog)

    volume_match = _VOLUME.search(text)
    if volume_match:
        requested = int(volume_match.group(2))
        decision = base("set_volume", complete=0.90 if requested <= 100 else 0.40)
        decision.volume = float(min(requested, 100))
        return decision
    if _UNMUTE.search(text):
        return base("unmute", complete=0.88)
    if _MUTE.search(text):
        return base("mute", complete=0.88)
    if _SCREENSHOT.search(text):
        return base("screenshot", complete=0.90)
    if _YOUTUBE.search(text):
        decision = base("youtube", complete=0.84 if words >= 2 else 0.40)
        decision.text_payload = text
        return decision
    if _DICTATE.search(text):
        decision = base("dictate", complete=0.70 if words >= 3 else 0.35)
        match = _DICTATE.search(text)
        decision.text_payload = text[match.end():].strip(" :,-") if match else ""
        return decision
    if _CLOSE.search(text):
        return base("close_app", target, 0.82 if target != "none" else (0.55 if words >= 2 else 0.20))
    if _FOLDER.search(text) and _OPEN.search(text):
        return base("open_folder", target, 0.83 if target != "none" else 0.50)
    if _OPEN.search(text):
        if target != "none":
            complete = max(target_confidence, 0.82)
        elif words <= 2:
            complete = 0.07
        else:
            complete = 0.67
        return base("open_app", target, complete)

    return base("none", complete=min(0.25, words * 0.04))


def _typed_decide(
    transcript: str,
    apps: Mapping[str, str],
    folders: Mapping[str, str],
    *,
    model: str | None,
    timeout: int,
) -> Decision:
    targets = [*apps.keys(), *folders.keys()]
    questions = r3_reflex_questions(targets)
    state = {
        "transcript": transcript,
        "installed_apps": list(apps.keys()),
        "known_folders": list(folders.keys()),
        "epistemic_rule": (
            "The typed result is advisory only. It cannot authorize execution, "
            "prove a fact, or expand the closed target catalog."
        ),
    }
    result = system_one(state, questions, model=model, timeout=timeout)
    answers = result.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(questions):
        raise ValueError("incomplete TypeSafe answer set")

    action, action_probs = _choice(answers["action"], set(R3_REFLEX_ACTIONS))
    target, target_probs = _choice(answers["target"], set(targets) | {"none"})
    decision = Decision(
        complete=_noul(answers["complete"]),
        action=action,
        target=target,
        destructive=_noul(answers["destructive"]),
        action_probs=action_probs,
        target_probs=target_probs,
        provider="typesafe",
        model=str(result.get("model") or model or "jev-latest"),
        raw=answers,
    )

    volume_match = _VOLUME.search(transcript)
    if volume_match:
        decision.volume = float(min(int(volume_match.group(2)), 100))
    if action == "dictate":
        match = _DICTATE.search(transcript)
        decision.text_payload = transcript[match.end():].strip(" :,-") if match else transcript
    elif action == "youtube":
        decision.text_payload = transcript
    return decision


class ReflexDecider:
    """Choose one action from a closed catalog.

    backend="auto" uses TypeSafe only when the canonical client is configured.
    If a configured TypeSafe call fails, the decision fails closed; it never
    invents a live Jev result by silently substituting the demo classifier.
    """

    def __init__(self, config: Mapping[str, Any]):
        self.config = dict(config)
        self.apps = dict(self.config.get("apps") or {})
        self.folders = dict(self.config.get("folders") or {})
        wanted = str(self.config.get("backend", "auto")).lower()
        if wanted == "auto":
            self.backend = "typesafe" if configured() else "demo"
        elif wanted in {"demo", "typesafe"}:
            self.backend = wanted
        else:
            raise ValueError("backend must be auto, demo or typesafe")

    def decide(self, transcript: str) -> Decision:
        if self.backend == "demo":
            return _demo_decide(transcript, self.apps, self.folders)
        try:
            return _typed_decide(
                transcript,
                self.apps,
                self.folders,
                model=self.config.get("model"),
                timeout=int(self.config.get("typesafe_timeout_seconds", 8)),
            )
        except Exception as exc:
            return Decision(
                complete=0.0,
                action="none",
                provider="typesafe_unavailable",
                raw={"error_class": type(exc).__name__},
            )
