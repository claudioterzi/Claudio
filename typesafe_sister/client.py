"""Shared server-side TypeSafe transport for the sister API and the website."""
from __future__ import annotations

import os

import httpx


class TypeSafeNotConfigured(RuntimeError):
    pass


def configured():
    return bool(os.getenv('TYPESAFE_API_KEY', '').strip())


def system_one(state, questions, *, api_key=None, model=None, base_url=None, timeout=8):
    key = (api_key if api_key is not None else os.getenv('TYPESAFE_API_KEY', '')).strip()
    if not key:
        raise TypeSafeNotConfigured('TypeSafe is not configured')
    endpoint = (base_url or os.getenv('TYPESAFE_BASE_URL', 'https://api.typesafe.ai')).rstrip('/')
    # No redirects or automatic retries: credentials stay at the configured endpoint
    # and one planning request has a bounded inference budget.
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
