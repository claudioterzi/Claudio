"""Shared typed-judgment transport for R3 sisters.

Order of preference:
1. R3-JUDGE local candidate/active backend when explicitly enabled.
2. Hosted TypeSafe/Jev when a TypeSafe API key is configured.
3. Raise ``TypeSafeNotConfigured`` so existing deterministic callers keep control.

No typed-model result is factual authority. R3 metadata is attached to every
successful model response.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import httpx

from r3_judge import ORIGIN, PROTOCOL
from r3_judge.gate import gate_allows


class TypeSafeNotConfigured(RuntimeError):
    pass


class R3JudgeRejected(RuntimeError):
    pass


def _mode() -> str:
    value = os.getenv("R3_JUDGE_MODE", "off").strip().lower()
    return value if value in {"off", "candidate", "active"} else "off"


def configured() -> bool:
    return _mode() in {"candidate", "active"} or bool(os.getenv("TYPESAFE_API_KEY", "").strip())


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _falsifier(name: str, spec: Any, answer: Any) -> str:
    qtype = spec.get("type") if isinstance(spec, dict) else None
    if qtype == "noul" and isinstance(answer, dict):
        p_yes = answer.get("noul")
        side = "NO" if type(p_yes) in (int, float) and p_yes >= 0.5 else "YES"
        return (
            f"Falsify {name!r} by supplying authoritative or reproducible evidence that supports "
            f"the opposite ({side}) answer, then rerun the same rubric on the updated evidence."
        )
    if qtype == "choice" and isinstance(answer, dict):
        selected = answer.get("choice")
        return (
            f"Falsify {name!r}={selected!r} by producing direct evidence satisfying a competing "
            "criterion better than the selected one, then rerun with the same option set."
        )
    if qtype == "score" and isinstance(answer, dict):
        selected = answer.get("score")
        return (
            f"Falsify the score for {name!r} (current {selected!r}) with direct evidence that meets "
            "a materially different rubric level, then rerun without changing the rubric."
        )
    return (
        f"Falsify {name!r} by adding authoritative contradictory evidence and rerunning the same "
        "question without changing its acceptance criteria."
    )


def _decorate(
    result: dict[str, Any],
    *,
    state: Any,
    questions: dict[str, Any],
    provider: str,
    calibration_status: str,
    mode: str,
) -> dict[str, Any]:
    answers = result.get("answers")
    if not isinstance(answers, dict):
        raise ValueError("Invalid typed-judgment response")
    result = dict(result)
    existing = result.get("x_r3") if isinstance(result.get("x_r3"), dict) else {}
    result["x_r3"] = {
        **existing,
        "protocol": PROTOCOL,
        "origin": ORIGIN,
        "provider": provider,
        "mode": mode,
        "epistemic_class": "IPOTESI",
        "factual_authority": False,
        "calibration_status": calibration_status,
        "probability_semantics": "model_score_not_probability_of_truth",
        "evidence_group_sha256": _canonical_hash(state),
        "request_sha256": _canonical_hash({"state": state, "questions": questions}),
        "independent_confirmation": False,
        "independence_rule": (
            "Judgments from sisters that share the same evidence_group_sha256 count as one evidence "
            "group, not as independent confirmations."
        ),
        "falsification": {
            name: _falsifier(name, spec, answers.get(name))
            for name, spec in questions.items()
        },
        "decisions": {
            name: {
                "epistemic_class": "IPOTESI",
                "factual_authority": False,
                "falsification": _falsifier(name, spec, answers.get(name)),
            }
            for name, spec in questions.items()
        },
    }
    return result


def _post_system_one(
    *,
    endpoint: str,
    key: str,
    state: Any,
    questions: dict[str, Any],
    model: str,
    timeout: float,
) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    request_timeout = httpx.Timeout(timeout, connect=min(float(timeout), 0.75))
    with httpx.Client(timeout=request_timeout, follow_redirects=False) as client:
        response = client.post(
            endpoint.rstrip("/") + "/v1/systemone",
            headers=headers,
            json={"state": state, "questions": questions, "model": model},
        )
        response.raise_for_status()
        if len(response.content) > 131072:
            raise ValueError("Typed-judgment response too large")
        result = response.json()
    if not isinstance(result, dict) or not isinstance(result.get("answers"), dict):
        raise ValueError("Invalid typed-judgment response")
    return result


def _try_local(
    state: Any,
    questions: dict[str, Any],
    *,
    model: str | None,
    base_url: str | None,
    timeout: float,
) -> dict[str, Any]:
    mode = _mode()
    if mode == "off":
        raise R3JudgeRejected("R3-JUDGE local backend is disabled")

    endpoint = (base_url or os.getenv("R3_JUDGE_BASE_URL", "http://127.0.0.1:8017")).rstrip("/")
    local_key = os.getenv("R3_JUDGE_API_KEY", "").strip()
    requested_model = (os.getenv("R3_JUDGE_MODEL", "").strip() or model or "rizzo-latest")
    if requested_model.startswith("jev-"):
        requested_model = os.getenv("R3_JUDGE_MODEL", "rizzo-latest").strip() or "rizzo-latest"

    result = _post_system_one(
        endpoint=endpoint,
        key=local_key,
        state=state,
        questions=questions,
        model=requested_model,
        timeout=timeout,
    )
    if mode == "active" and not gate_allows(result):
        raise R3JudgeRejected("R3-JUDGE active mode requires a passing gate for this model/fingerprint")
    return _decorate(
        result,
        state=state,
        questions=questions,
        provider="r3_local_rizzo_candidate" if mode == "candidate" else "r3_local_judge",
        calibration_status="uncalibrated",
        mode=mode,
    )


def system_one(state, questions, *, api_key=None, model=None, base_url=None, timeout=8):
    """Return a typed judgment without ever turning it into factual authority.

    ``base_url`` keeps its historical meaning for hosted TypeSafe.  The local R3
    endpoint is configured separately with ``R3_JUDGE_BASE_URL`` to avoid ever
    sending hosted credentials to localhost or vice versa.
    """
    local_error: Exception | None = None
    if _mode() in {"candidate", "active"}:
        try:
            return _try_local(state, questions, model=model, base_url=None, timeout=timeout)
        except (httpx.HTTPError, ValueError, R3JudgeRejected, OSError) as exc:
            local_error = exc

    key = (api_key if api_key is not None else os.getenv("TYPESAFE_API_KEY", "")).strip()
    if key:
        endpoint = (base_url or os.getenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai")).rstrip("/")
        result = _post_system_one(
            endpoint=endpoint,
            key=key,
            state=state,
            questions=questions,
            model=model or os.getenv("TYPESAFE_MODEL", "jev-latest"),
            timeout=timeout,
        )
        return _decorate(
            result,
            state=state,
            questions=questions,
            provider="typesafe_jev",
            calibration_status="provider_defined",
            mode="hosted",
        )

    if local_error is not None:
        raise TypeSafeNotConfigured(f"No adopted/available typed backend ({type(local_error).__name__})") from local_error
    raise TypeSafeNotConfigured("No typed-judgment backend is configured")
