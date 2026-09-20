"""Universal advisory TypeSafe/Jev layer for every R3 project.

This module never authorizes an external action. It returns typed judgments that
Raffaello/application code may use as a second opinion under P5/P6.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math

from typesafe_sister.client import TypeSafeNotConfigured, system_one
from typesafe_sister.policy import (
    UNIVERSAL_FOCUS,
    UNIVERSAL_POLICY_VERSION,
    UNIVERSAL_SCORE_LEVELS,
    universal_questions,
)

LOGGER = logging.getLogger("r3.typesafe_universal")
MAX_STATE_BYTES = 64 * 1024


def _probability(value):
    if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Invalid probability")
    return float(value)


def _distribution(values, expected_keys):
    if not isinstance(values, dict) or set(values) != set(expected_keys):
        raise ValueError("Invalid probability distribution")
    result = {str(key): _probability(values[key]) for key in values}
    if abs(sum(result.values()) - 1.0) > 0.02:
        raise ValueError("Probability distribution does not sum to one")
    return result


def _choice(answer):
    if not isinstance(answer, dict) or answer.get("type") != "choice":
        raise ValueError("Invalid choice answer")
    value = answer.get("choice")
    if value not in UNIVERSAL_FOCUS:
        raise ValueError("Unknown focus choice")
    return {
        "value": value,
        "confidence": _probability(answer.get("confidence")),
        "probabilities": _distribution(answer.get("probabilities"), UNIVERSAL_FOCUS),
    }


def _score(answer, levels):
    if not isinstance(answer, dict) or answer.get("type") != "score":
        raise ValueError("Invalid score answer")
    value = answer.get("score")
    if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= len(levels) - 1:
        raise ValueError("Invalid score value")
    keys = [str(i) for i in range(len(levels))]
    probabilities = _distribution(answer.get("probabilities"), keys)
    legend = answer.get("legend")
    if not isinstance(legend, dict) or set(legend) != set(keys):
        raise ValueError("Invalid score legend")
    return {
        "score": float(value),
        "confidence": _probability(answer.get("confidence")),
        "probabilities": probabilities,
        "legend": {key: str(legend[key])[:500] for key in keys},
    }


def _noul(answer):
    if not isinstance(answer, dict) or answer.get("type") != "noul":
        raise ValueError("Invalid noul answer")
    return _probability(answer.get("noul"))


def assess_project_state(project_id, state, *, context=None, timeout=8):
    """Return bounded advisory judgments for any project state.

    Callers decide how to use the result. In particular, no TypeSafe output is
    permission to spend, publish, send, delete, deploy, merge or otherwise change
    external state.
    """
    project = str(project_id or "general").strip()[:120] or "general"
    payload = {"project": project, "state": state}
    if context is not None:
        payload["context"] = context

    try:
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return {"status": "invalid_state", "policy_version": UNIVERSAL_POLICY_VERSION}

    if len(canonical.encode("utf-8")) > MAX_STATE_BYTES:
        return {"status": "state_too_large", "policy_version": UNIVERSAL_POLICY_VERSION}

    questions = universal_questions()
    try:
        result = system_one(payload, questions, timeout=timeout)
        answers = result["answers"]
        if not isinstance(answers, dict) or set(answers) != set(questions):
            raise ValueError("Incomplete TypeSafe answers")

        focus = _choice(answers["focus"])
        scores = {
            key: _score(answers[key], levels)
            for key, levels in UNIVERSAL_SCORE_LEVELS.items()
        }
        flags = {
            key: _noul(answers[key])
            for key in ("contradiction", "missing_critical_input", "unsupported_claim", "freshness_needed", "external_side_effect")
        }
        return {
            "status": "evaluated",
            "provider": "typesafe",
            "model": str(result.get("model", "jev-latest"))[:100],
            "project": project,
            "focus": focus,
            "scores": scores,
            "flags": flags,
            "policy_version": UNIVERSAL_POLICY_VERSION,
            "input_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        }
    except TypeSafeNotConfigured:
        return {"status": "not_configured", "policy_version": UNIVERSAL_POLICY_VERSION}
    except Exception as exc:
        LOGGER.warning(json.dumps({
            "event": "typesafe_universal_unavailable",
            "error_class": type(exc).__name__,
            "project": project,
        }))
        return {"status": "unavailable", "policy_version": UNIVERSAL_POLICY_VERSION}
