"""Shared server-side System One transport for R3∞.

The canonical layer is provider-neutral. It can use the hosted TypeSafe/Jev API or
an open/self-hosted Contrastive Language Model (CLM) endpoint exposing the
TypeSafe-compatible /v1/systemone contract.  Callers keep the same policy layer
and never gain action authority from a model score.
"""
from __future__ import annotations

import os

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
    if requested not in {"auto", "clm", "typesafe"}:
        raise ValueError("Unsupported System One provider")

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


def backend_info(*, provider=None, model=None, base_url=None):
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


def system_one(state, questions, *, api_key=None, model=None, base_url=None, provider=None, timeout=8):
    cfg = _resolve_backend(provider=provider, api_key=api_key, model=model, base_url=base_url)
    result = _post_json(
        "/v1/systemone",
        {"state": state, "questions": questions, "model": cfg["model"]},
        provider=cfg["provider"],
        api_key=cfg["api_key"],
        model=cfg["model"],
        base_url=cfg["base_url"],
        timeout=timeout,
    )
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
    if cfg["provider"] != "clm":
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
