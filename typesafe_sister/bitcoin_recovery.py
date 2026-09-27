"""Jev forensic information-gain advisory for the Bitcoin Cannes recovery case.

This module reuses the canonical TypeSafe/Jev transport and universal questions.
It never authorizes account access, fund movement, credential use, contact with
third parties, or any other external action.
"""
from __future__ import annotations

import hashlib
import json
import logging

from typesafe_sister.client import TypeSafeNotConfigured, system_one
from typesafe_sister.policy import (
    BITCOIN_RECOVERY_FOCUS,
    BITCOIN_RECOVERY_SCORE_LEVELS,
    UNIVERSAL_POLICY_VERSION,
    UNIVERSAL_SCORE_LEVELS,
    bitcoin_recovery_questions,
)
from typesafe_sister.universal import (
    MAX_STATE_BYTES,
    _choice,
    _distribution,
    _noul,
    _probability,
    _score,
)

LOGGER = logging.getLogger("r3.bitcoin_recovery")
POLICY_VERSION = "r3-jev-bitcoin-recovery-v1"


def _recovery_choice(answer):
    if not isinstance(answer, dict) or answer.get("type") != "choice":
        raise ValueError("Invalid recovery focus answer")
    value = answer.get("choice")
    if value not in BITCOIN_RECOVERY_FOCUS:
        raise ValueError("Unknown recovery focus")
    return {
        "value": value,
        "confidence": _probability(answer.get("confidence")),
        "probabilities": _distribution(answer.get("probabilities"), BITCOIN_RECOVERY_FOCUS),
    }


def assess_bitcoin_recovery(state, *, context=None, timeout=8):
    """Return universal + forensic typed judgments for one evidence-graph state."""
    payload = {
        "project": "bitcoin-cannes-recovery",
        "state": state,
        "epistemic_contract": {
            "facts": "observed/provider/documentary evidence only",
            "memories": "testimony until independently corroborated",
            "no_ownership_inference_from_inactivity": True,
            "authorized_sources_only": True,
        },
    }
    if context is not None:
        payload["context"] = context

    try:
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return {"status": "invalid_state", "policy_version": POLICY_VERSION}

    if len(canonical.encode("utf-8")) > MAX_STATE_BYTES:
        return {"status": "state_too_large", "policy_version": POLICY_VERSION}

    questions = bitcoin_recovery_questions()
    try:
        result = system_one(payload, questions, timeout=timeout)
        answers = result["answers"]
        if not isinstance(answers, dict) or set(answers) != set(questions):
            raise ValueError("Incomplete TypeSafe answers")

        universal_scores = {
            key: _score(answers[key], levels)
            for key, levels in UNIVERSAL_SCORE_LEVELS.items()
        }
        universal_flags = {
            key: _noul(answers[key])
            for key in (
                "contradiction",
                "missing_critical_input",
                "unsupported_claim",
                "freshness_needed",
                "external_side_effect",
            )
        }
        forensic_scores = {
            key: _score(answers[key], levels)
            for key, levels in BITCOIN_RECOVERY_SCORE_LEVELS.items()
        }

        return {
            "status": "evaluated",
            "provider": "typesafe",
            "model": str(result.get("model", "jev-latest"))[:100],
            "project": "bitcoin-cannes-recovery",
            "universal": {
                "focus": _choice(answers["focus"]),
                "scores": universal_scores,
                "flags": universal_flags,
                "policy_version": UNIVERSAL_POLICY_VERSION,
            },
            "forensic": {
                "next_focus": _recovery_choice(answers["recovery_next_focus"]),
                "scores": forensic_scores,
                "flags": {
                    "ownership_inference_risk": _noul(answers["ownership_inference_risk"]),
                    "branch_exhausted": _noul(answers["branch_exhausted"]),
                },
            },
            "policy_version": POLICY_VERSION,
            "input_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "epistemic_note": "typed_model_judgment_not_independent_factual_evidence",
        }
    except TypeSafeNotConfigured:
        return {"status": "not_configured", "policy_version": POLICY_VERSION}
    except Exception as exc:
        LOGGER.warning(json.dumps({
            "event": "bitcoin_recovery_jev_unavailable",
            "error_class": type(exc).__name__,
        }))
        return {"status": "unavailable", "policy_version": POLICY_VERSION}
