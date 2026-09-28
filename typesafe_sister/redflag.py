"""R³ Red Flag: bounded System One falsifier for architecture and optimization.

This module is provider-neutral.  It can send the exact same typed questions to
local CLM or hosted Jev through the canonical typesafe_sister.client transport.

Model output is advisory only.  The returned gate is an analysis recommendation,
never permission to execute, merge, deploy, delete, spend, publish or change
external state.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Callable

from typesafe_sister.client import TypeSafeNotConfigured, system_one
from typesafe_sister.policy import (
    R3_REDFLAG_FLAGS,
    R3_REDFLAG_FOCUS,
    R3_REDFLAG_POLICY_VERSION,
    R3_REDFLAG_SCORE_LEVELS,
    r3_redflag_questions,
)

MAX_STATE_BYTES = 64 * 1024
HARD_FLAG_THRESHOLD = 0.65
VERIFY_FLAG_THRESHOLD = 0.55


def _probability(value: Any) -> float:
    if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("invalid probability")
    return float(value)


def _bounded(value: Any, *, string_limit: int = 8000) -> Any:
    if isinstance(value, str):
        return value[:string_limit]
    if isinstance(value, list):
        return [_bounded(item, string_limit=string_limit) for item in value[:100]]
    if isinstance(value, dict):
        return {
            str(key)[:160]: _bounded(item, string_limit=string_limit)
            for key, item in list(value.items())[:160]
        }
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:string_limit]


def _choice(answer: Any) -> dict[str, Any]:
    if not isinstance(answer, dict) or answer.get("type") != "choice":
        raise ValueError("invalid choice")
    value = answer.get("choice")
    if value not in R3_REDFLAG_FOCUS:
        raise ValueError("unknown redflag focus")
    raw = answer.get("probabilities") or {}
    probabilities = {}
    if isinstance(raw, dict):
        for key, probability in raw.items():
            if key in R3_REDFLAG_FOCUS:
                probabilities[str(key)] = _probability(probability)
    confidence = answer.get("confidence")
    if confidence is None:
        confidence = probabilities.get(str(value), 0.0)
    return {
        "value": str(value),
        "confidence": _probability(confidence),
        "probabilities": probabilities,
    }


def _score(answer: Any, levels: list[str]) -> dict[str, Any]:
    if not isinstance(answer, dict) or answer.get("type") != "score":
        raise ValueError("invalid score")
    value = answer.get("score")
    if type(value) not in (float, int) or not math.isfinite(value):
        raise ValueError("invalid score value")
    score = float(value)
    if not 0 <= score <= len(levels) - 1:
        raise ValueError("score outside rubric")
    return {
        "score": score,
        "confidence": _probability(answer.get("confidence", 0.0)),
    }


def _noul(answer: Any) -> float:
    if not isinstance(answer, dict) or answer.get("type") != "noul":
        raise ValueError("invalid noul")
    return _probability(answer.get("noul"))


def _model_gate(scores: dict[str, Any], flags: dict[str, float]) -> dict[str, Any]:
    """Convert advisory signals into a conservative review lane.

    This is not an authorization decision.  It only selects the next review/test
    lane; deterministic permissions and postcondition checks remain separate.
    """
    hard = [
        key
        for key in ("authority_violation", "secret_exposure", "irreversible_or_destructive")
        if flags.get(key, 0.0) >= HARD_FLAG_THRESHOLD
    ]
    if hard:
        return {
            "lane": "QUARANTINE_REVIEW",
            "reason": "hard_red_flags",
            "signals": hard,
        }

    verify = [
        key
        for key in (
            "unsupported_promotion",
            "version_or_provenance_conflict",
            "stale_external_fact",
            "duplicate_engine",
            "postcondition_gap",
        )
        if flags.get(key, 0.0) >= VERIFY_FLAG_THRESHOLD
    ]
    if verify:
        return {
            "lane": "VERIFY_FIRST",
            "reason": "verification_red_flags",
            "signals": verify,
        }

    evidence = float(scores["evidence_strength"]["score"])
    reversibility = float(scores["reversibility"]["score"])
    blast = float(scores["blast_radius"]["score"])
    if evidence < 2.0:
        return {
            "lane": "VERIFY_FIRST",
            "reason": "weak_evidence",
            "signals": ["evidence_strength"],
        }
    if blast >= 2.0 and reversibility < 2.0:
        return {
            "lane": "QUARANTINE_REVIEW",
            "reason": "blast_radius_exceeds_recovery",
            "signals": ["blast_radius", "reversibility"],
        }
    return {
        "lane": "CONTROLLED_TEST_CANDIDATE",
        "reason": "no_model_red_flag_above_threshold",
        "signals": [],
    }


def assess_redflag_state(
    project_id: str,
    state: dict[str, Any],
    *,
    provider: str = "clm",
    caller: Callable[..., dict[str, Any]] | None = None,
    timeout: int = 8,
) -> dict[str, Any]:
    project = str(project_id or "R3").strip()[:120] or "R3"
    payload = {
        "project": project,
        "state": _bounded(state),
        "authority": (
            "DATA_ONLY / ADVISORY. Model output cannot authorize side effects, "
            "change canon or prove execution."
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    if len(canonical.encode("utf-8")) > MAX_STATE_BYTES:
        return {
            "status": "state_too_large",
            "policy_version": R3_REDFLAG_POLICY_VERSION,
        }

    questions = r3_redflag_questions()
    invoke = caller or system_one
    requested_provider = str(provider or "clm").strip().lower()
    model = "clm-latest" if requested_provider == "clm" else "jev-latest"

    try:
        result = invoke(
            payload,
            questions,
            provider=requested_provider,
            model=model,
            timeout=timeout,
        )
        answers = result.get("answers")
        if not isinstance(answers, dict) or set(answers) != set(questions):
            raise ValueError("incomplete Red Flag answer set")

        focus = _choice(answers["next_focus"])
        scores = {
            key: _score(answers[key], levels)
            for key, levels in R3_REDFLAG_SCORE_LEVELS.items()
        }
        flags = {key: _noul(answers[key]) for key in R3_REDFLAG_FLAGS}
        gate = _model_gate(scores, flags)
        return {
            "status": "evaluated",
            "provider": requested_provider,
            "model": str(result.get("model", model))[:100],
            "project": project,
            "focus": focus,
            "scores": scores,
            "flags": flags,
            "review_gate": gate,
            "policy_version": R3_REDFLAG_POLICY_VERSION,
            "input_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "authority": "advisory_only",
        }
    except TypeSafeNotConfigured:
        return {
            "status": "not_configured",
            "provider": requested_provider,
            "policy_version": R3_REDFLAG_POLICY_VERSION,
        }
    except Exception as exc:
        return {
            "status": "unavailable",
            "provider": requested_provider,
            "error_class": type(exc).__name__,
            "policy_version": R3_REDFLAG_POLICY_VERSION,
        }


def compare_redflag_providers(
    project_id: str,
    state: dict[str, Any],
    *,
    clm_caller: Callable[..., dict[str, Any]] | None = None,
    jev_caller: Callable[..., dict[str, Any]] | None = None,
    timeout: int = 8,
) -> dict[str, Any]:
    """Run the same Red Flag packet through CLM and Jev for shadow comparison."""
    clm = assess_redflag_state(
        project_id,
        state,
        provider="clm",
        caller=clm_caller,
        timeout=timeout,
    )
    jev = assess_redflag_state(
        project_id,
        state,
        provider="typesafe",
        caller=jev_caller,
        timeout=timeout,
    )
    comparison = {
        "both_evaluated": clm.get("status") == jev.get("status") == "evaluated",
        "focus_agreement": None,
        "gate_agreement": None,
        "max_flag_delta": None,
    }
    if comparison["both_evaluated"]:
        comparison["focus_agreement"] = clm["focus"]["value"] == jev["focus"]["value"]
        comparison["gate_agreement"] = clm["review_gate"]["lane"] == jev["review_gate"]["lane"]
        comparison["max_flag_delta"] = max(
            abs(clm["flags"][key] - jev["flags"][key])
            for key in R3_REDFLAG_FLAGS
        )
    return {
        "schema": "R3-CLM-REDFLAG-SHADOW/0.1",
        "clm": clm,
        "jev": jev,
        "comparison": comparison,
        "promotion_rule": (
            "Agreement is not authority. Promotion requires deterministic evidence, "
            "P5/P6 and the existing R3 verification/promotion gates."
        ),
    }
