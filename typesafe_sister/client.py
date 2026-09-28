"""Shared server-side System-One transport/router for R3.

Default behavior remains TypeSafe/Jev. The internal R3-CLM backend is opt-in and
uses the same typed contract, so callers do not create project-local judgment
engines. Shadow mode keeps Jev primary and records local A/B disagreement only.
"""
from __future__ import annotations

import os

import httpx


class TypeSafeNotConfigured(RuntimeError):
    pass


def _backend_name(explicit=None, *, api_key=None, base_url=None):
    if api_key is not None or base_url is not None:
        return "typesafe"
    value = str(explicit or os.getenv("R3_SYSTEM_ONE_BACKEND", "typesafe")).strip().lower()
    aliases = {"r3-clm": "r3_clm", "internal": "r3_clm"}
    value = aliases.get(value, value)
    if value not in {"typesafe", "r3_clm", "shadow"}:
        raise ValueError("R3_SYSTEM_ONE_BACKEND must be typesafe, r3_clm or shadow")
    return value


def configured(backend=None):
    selected = _backend_name(backend)
    if selected == "r3_clm":
        return True
    return bool(os.getenv('TYPESAFE_API_KEY', '').strip())


def _system_one_typesafe(state, questions, *, api_key=None, model=None, base_url=None, timeout=8):
    key = (api_key if api_key is not None else os.getenv('TYPESAFE_API_KEY', '')).strip()
    if not key:
        raise TypeSafeNotConfigured('TypeSafe is not configured')
    endpoint = (base_url or os.getenv('TYPESAFE_BASE_URL', 'https://api.typesafe.ai')).rstrip('/')
    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        response = client.post(endpoint + '/v1/systemone',
            headers={'Authorization': 'Bearer ' + key},
            json={'state': state, 'questions': questions,
                  'model': model or os.getenv('TYPESAFE_MODEL', 'jev-latest')})
        response.raise_for_status()
        if len(response.content) > 131072:
            raise ValueError('TypeSafe response too large')
        result = response.json()
    if not isinstance(result, dict) or not isinstance(result.get('answers'), dict):
        raise ValueError('Invalid TypeSafe response')
    return result


def system_one(state, questions, *, api_key=None, model=None, base_url=None, timeout=8, backend=None):
    """Single canonical typed System-One entry point."""
    selected = _backend_name(backend, api_key=api_key, base_url=base_url)
    if selected == "r3_clm":
        from typesafe_sister.r3_clm import system_one_local
        return system_one_local(state, questions)

    primary = _system_one_typesafe(state, questions, api_key=api_key, model=model,
                                   base_url=base_url, timeout=timeout)
    if selected != "shadow":
        return primary

    try:
        from typesafe_sister.r3_clm import compare_answer_sets, system_one_local
        candidate = system_one_local(state, questions)
        primary = dict(primary)
        primary["shadow"] = {"candidate_model": candidate.get("model"),
                             "candidate_provider": candidate.get("provider"),
                             "comparison": compare_answer_sets(primary, candidate),
                             "candidate_answers": candidate.get("answers"),
                             "authority": "observation_only"}
    except Exception as exc:
        primary = dict(primary)
        primary["shadow"] = {"status": "candidate_unavailable",
                             "error_class": type(exc).__name__,
                             "authority": "observation_only"}
    return primary
