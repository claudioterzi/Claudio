"""Shared provider-neutral System One transport for R³.

The wire format is the TypeSafe-compatible POST /v1/systemone schema used by
hosted Jev and local/open CLM.  Existing callers default to Jev/TypeSafe;
CLM is opt-in and never creates a second semantic-policy stack.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

import httpx


class TypeSafeNotConfigured(RuntimeError):
    """Historical compatibility name for an unavailable System One provider."""


def _provider_name(provider=None):
    value = str(provider or os.getenv("R3_SYSTEM_ONE_PROVIDER", "typesafe")).strip().lower()
    if value in {"jev", "typesafe"}:
        return "typesafe"
    if value == "clm":
        return "clm"
    raise ValueError("provider must be typesafe/jev or clm")


def _is_loopback(url):
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return host in {"127.0.0.1", "localhost", "::1"}


def configured(provider=None, *, base_url=None, api_key=None):
    selected = _provider_name(provider)
    if selected == "typesafe":
        key = api_key if api_key is not None else os.getenv("TYPESAFE_API_KEY", "")
        return bool(str(key).strip())

    endpoint = (base_url or os.getenv("CLM_BASE_URL", "http://127.0.0.1:8700")).rstrip("/")
    key = api_key if api_key is not None else os.getenv("CLM_API_KEY", "")
    # An unauthenticated CLM endpoint is accepted only on loopback.  Remote CLM
    # deployments must provide an API key so adding CLM cannot weaken the
    # existing credential boundary by accident.
    return bool(str(key).strip()) or _is_loopback(endpoint)


def system_one(
    state,
    questions,
    *,
    api_key=None,
    model=None,
    base_url=None,
    timeout=8,
    provider=None,
):
    """Call one TypeSafe-compatible System One endpoint.

    provider="typesafe" (default) preserves the existing Jev behavior.
    provider="clm" speaks the same wire schema to clm-serve.
    """
    selected = _provider_name(provider)

    if selected == "typesafe":
        key = (api_key if api_key is not None else os.getenv("TYPESAFE_API_KEY", "")).strip()
        if not key:
            raise TypeSafeNotConfigured("TypeSafe/Jev is not configured")
        endpoint = (base_url or os.getenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai")).rstrip("/")
        request_model = model or os.getenv("TYPESAFE_MODEL", "jev-latest")
    else:
        endpoint = (base_url or os.getenv("CLM_BASE_URL", "http://127.0.0.1:8700")).rstrip("/")
        key = (api_key if api_key is not None else os.getenv("CLM_API_KEY", "")).strip()
        if not key and not _is_loopback(endpoint):
            raise TypeSafeNotConfigured("Remote CLM requires CLM_API_KEY")
        request_model = model or os.getenv("CLM_MODEL", "clm-latest")

    headers = {"Authorization": "Bearer " + key} if key else {}
    # No redirects or automatic retries: credentials remain at the configured
    # endpoint and one decision request has a bounded inference budget.
    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        response = client.post(
            endpoint + "/v1/systemone",
            headers=headers,
            json={"state": state, "questions": questions, "model": request_model},
        )
        response.raise_for_status()
        if len(response.content) > 131072:
            raise ValueError("System One response too large")
        result = response.json()
        if selected == "clm":
            latency = response.headers.get("X-CLM-Latency-Ms")
            if latency is not None:
                try:
                    result["latency_ms"] = float(latency)
                except (TypeError, ValueError):
                    pass

    if not isinstance(result, dict) or not isinstance(result.get("answers"), dict):
        raise ValueError("Invalid System One response")
    return result
