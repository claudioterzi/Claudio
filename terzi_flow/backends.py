"""Judge adapters for TERZI.

No credential is embedded here.  Hosted Jev uses the existing R³ TypeSafe
transport; local Rizzo uses its Jev-compatible /v1/systemone endpoint.
"""
from __future__ import annotations

import os
from typing import Any, Mapping

import httpx

from typesafe_sister.client import system_one as hosted_system_one


def jev(
    state: Any,
    questions: Mapping[str, Any],
    *,
    model: str | None = None,
    timeout: float = 12,
):
    """Hosted Jev/TypeSafe route through the existing R³ client."""
    return hosted_system_one(
        state,
        questions,
        model=model or os.getenv("TYPESAFE_MODEL", "jev-latest"),
        timeout=timeout,
    )


def rizzo_local(
    state: Any,
    questions: Mapping[str, Any],
    *,
    base_url: str | None = None,
    model: str = "rizzo-latest",
    timeout: float = 30,
):
    """Call a local Rizzo Flow server without sending hosted credentials."""
    endpoint = (base_url or os.getenv("RIZZO_BASE_URL", "http://127.0.0.1:8017")).rstrip("/")
    headers = {"Content-Type": "application/json"}
    key = os.getenv("RIZZO_API_KEY", "").strip()
    if key:
        headers["Authorization"] = "Bearer " + key
    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        response = client.post(
            endpoint + "/v1/systemone",
            headers=headers,
            json={"state": state, "questions": questions, "model": model},
        )
        response.raise_for_status()
        if len(response.content) > 131072:
            raise ValueError("Rizzo response too large")
        result = response.json()
    if not isinstance(result, dict) or not isinstance(result.get("answers"), dict):
        raise ValueError("Invalid Rizzo response")
    return result
