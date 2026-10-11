"""Shared server-side System One transport for R3∞.

The canonical layer is provider-neutral. It can use the hosted TypeSafe/Jev API or
an open/self-hosted Contrastive Language Model (CLM) endpoint exposing the
TypeSafe-compatible /v1/systemone contract.  Callers keep the same policy layer
and never gain action authority from a model score.
"""
from __future__ import annotations

import os
import hashlib
import json
from typing import Any

from r3_judge import ORIGIN, PROTOCOL
from r3_judge.gate import gate_allows

import httpx


class SystemOneNotConfigured(RuntimeError):
    pass


class SystemOneCapabilityUnavailable(RuntimeError):
    pass


# Backwards-compatible import used by older modules/tests.
TypeSafeNotConfigured = SystemOneNotConfigured


def _clean(value):
    return str(value or "").strip()


def _resolve_backend(*, provider=None, api_key=None, model=None, base_url=None):
    requested = _clean(provider or os.getenv("R3_SYSTEMONE_PROVIDER", "auto")).lower()
    requested = {"r3-clm": "r3_clm", "internal": "r3_clm"}.get(requested, requested)
    if requested not in {"auto", "clm", "typesafe", "r3_clm"}:
        raise ValueError("Unsupported System One provider")
    if requested == "r3_clm":
        # Internal deterministic baseline: local, network-free, never auto-selected.
        from typesafe_sister.r3_clm import MODEL_ID
        return {"provider": "r3_clm", "base_url": "local", "model": MODEL_ID, "api_key": ""}

    generic_url = _clean(base_url or os.getenv("R3_SYSTEMONE_BASE_URL", ""))
    generic_model = _clean(model or os.getenv("R3_SYSTEMONE_MODEL", ""))
    generic_key = _clean(api_key if api_key is not None else os.getenv("R3_SYSTEMONE_API_KEY", ""))

    clm_url = _clean(os.getenv("CLM_BASE_URL", ""))
    clm_key = _clean(os.getenv("CLM_API_KEY", ""))
    clm_model = _clean(os.getenv("CLM_MODEL", "clm-latest")) or "clm-latest"

    ts_url = _clean(os.getenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai")) or "https://api.typesafe.ai"
    ts_key = _clean(os.getenv("TYPESAFE_API_KEY", ""))
    ts_model = _clean(os.getenv("TYPESAFE_MODEL", "jev-latest")) or "jev-latest"

    selected = requested
    if requested == "auto":
        hint_model = generic_model.lower()
        if hint_model.startswith("clm"):
            selected = "clm"
        elif hint_model.startswith("jev"):
            selected = "typesafe"
        elif generic_url and "typesafe.ai" not in generic_url.lower():
            selected = "clm"
        elif clm_url:
            # CLM is the preferred candidate when an endpoint is deliberately configured.
            selected = "clm"
        elif ts_key:
            selected = "typesafe"
        else:
            raise SystemOneNotConfigured("No System One backend is configured")

    if selected == "clm":
        endpoint = generic_url or clm_url
        if not endpoint:
            # Local CLM is opt-in: this default is used only when provider=clm explicitly.
            if requested == "clm":
                endpoint = "http://127.0.0.1:8700"
            else:
                raise SystemOneNotConfigured("CLM endpoint is not configured")
        return {
            "provider": "clm",
            "base_url": endpoint.rstrip("/"),
            "model": generic_model or clm_model,
            # CLM supports an optional API key. Local/self-hosted deployments may omit it.
            "api_key": generic_key or clm_key,
        }

    key = generic_key or ts_key
    if not key:
        raise SystemOneNotConfigured("TypeSafe/Jev is not configured")
    return {
        "provider": "typesafe",
        "base_url": (generic_url or ts_url).rstrip("/"),
        "model": generic_model or ts_model,
        "api_key": key,
    }


def _provider_backend_info(*, provider=None, model=None, base_url=None):
    """Return safe backend metadata without exposing credentials."""
    try:
        cfg = _resolve_backend(provider=provider, model=model, base_url=base_url)
    except SystemOneNotConfigured:
        return {
            "configured": False,
            "provider": None,
            "model": None,
            "base_url": None,
        }
    return {
        "configured": True,
        "provider": cfg["provider"],
        "model": cfg["model"],
        "base_url": cfg["base_url"],
    }


def configured():
    return backend_info()["configured"]


def _post_json(path, payload, *, provider=None, api_key=None, model=None, base_url=None, timeout=8):
    cfg = _resolve_backend(provider=provider, api_key=api_key, model=model, base_url=base_url)
    headers = {}
    if cfg["api_key"]:
        headers["Authorization"] = "Bearer " + cfg["api_key"]

    # No redirects or automatic retries: credentials stay at the configured endpoint
    # and one planning request has a bounded inference budget.
    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        response = client.post(cfg["base_url"] + path, headers=headers, json=payload)
        response.raise_for_status()
        if len(response.content) > 131072:
            raise ValueError("System One response too large")
        result = response.json()

    if not isinstance(result, dict):
        raise ValueError("Invalid System One response")
    result["_r3_provider"] = cfg["provider"]
    return result


def _provider_system_one(state, questions, *, api_key=None, model=None, base_url=None, provider=None, timeout=8):
    cfg = _resolve_backend(provider=provider, api_key=api_key, model=model, base_url=base_url)
    if cfg["provider"] == "r3_clm":
        from typesafe_sister.r3_clm import system_one_local
        result = dict(system_one_local(state, questions))
        result["_r3_provider"] = "r3_clm"
        return result
    result = _post_system_one(endpoint=cfg["base_url"], key=cfg["api_key"],
                              state=state, questions=questions, model=cfg["model"], timeout=timeout)
    result["_r3_provider"] = cfg["provider"]
    if not isinstance(result.get("answers"), dict):
        raise ValueError("Invalid System One response")
    return result


def rank(context, question, answers, *, api_key=None, model=None, base_url=None, provider=None, timeout=8):
    """Rank free-form candidate actions using CLM's native /v1/rank primitive.

    Jev remains supported for typed Choice/Score/Noul calls; native rank is a CLM
    capability and is intentionally not emulated here so callers can distinguish
    real backend capabilities from approximations.
    """
    cfg = _resolve_backend(provider=provider, api_key=api_key, model=model, base_url=base_url)
    if cfg["provider"] != "clm":  # r3_clm has no native rank either
        raise SystemOneCapabilityUnavailable("Native rank requires a CLM backend")
    result = _post_json(
        "/v1/rank",
        {"context": context, "question": question, "answers": list(answers)},
        provider=cfg["provider"],
        api_key=cfg["api_key"],
        model=cfg["model"],
        base_url=cfg["base_url"],
        timeout=timeout,
    )
    ranked = result.get("ranked")
    if not isinstance(ranked, list):
        raise ValueError("Invalid CLM rank response")
    return result


class R3JudgeRejected(RuntimeError):
    pass


def _mode() -> str:
    value = os.getenv("R3_JUDGE_MODE", "off").strip().lower()
    return value if value in {"off", "candidate", "active"} else "off"

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

def _post_system_one(*, endpoint, key, state, questions, model, timeout):
    """Compatibility adapter onto the single canonical bounded HTTP transport."""
    result = _post_json("/v1/systemone", {"state": state, "questions": questions, "model": model},
                        provider="typesafe" if "typesafe.ai" in endpoint.lower() else "clm",
                        api_key=key, model=model, base_url=endpoint,
                        timeout=httpx.Timeout(timeout, connect=min(float(timeout), 0.75)))
    if not isinstance(result.get("answers"), dict):
        raise ValueError("Invalid typed-judgment response")
    return result


def backend_info(*, provider=None, model=None, base_url=None):
    requested = _clean(provider or os.getenv("R3_SYSTEMONE_PROVIDER", "auto")).lower()
    if requested == "auto" and _mode() in {"candidate", "active"}:
        return {"configured": True, "provider": "r3_local_rizzo_candidate" if _mode() == "candidate" else "r3_local_judge",
                "model": os.getenv("R3_JUDGE_MODEL", "rizzo-latest"),
                "base_url": os.getenv("R3_JUDGE_BASE_URL", "http://127.0.0.1:8017")}
    return _provider_backend_info(provider=provider, model=model, base_url=base_url)


def system_one(state, questions, *, api_key=None, model=None, base_url=None, provider=None, timeout=8):
    """Explicit provider selection wins; opt-in R3-JUDGE keeps advisory metadata and gated fallback."""
    requested = _clean(provider or os.getenv("R3_SYSTEMONE_PROVIDER", "auto")).lower()
    local_error = None
    if requested == "auto" and _mode() in {"candidate", "active"}:
        try:
            result = _try_local(state, questions, model=model, base_url=None, timeout=timeout)
            result["_r3_provider"] = result["x_r3"]["provider"]
            return result
        except (httpx.HTTPError, ValueError, R3JudgeRejected, OSError) as exc:
            local_error = exc
    try:
        result = _provider_system_one(state, questions, api_key=api_key, model=model,
                                      base_url=base_url, provider=provider, timeout=timeout)
    except SystemOneNotConfigured as exc:
        if local_error is not None:
            raise SystemOneNotConfigured("No adopted/available typed backend") from local_error
        raise
    actual = result.get("_r3_provider", "unknown")
    return _decorate(result, state=state, questions=questions,
                     provider="typesafe_jev" if actual == "typesafe" else actual,
                     calibration_status="provider_defined", mode="hosted" if actual == "typesafe" else actual)
