"""OmniRoute gateway provider for SDQ-1/R³∞.

OmniRoute exposes an OpenAI-compatible API and can dynamically route across its
own connected provider pool. This adapter treats OmniRoute as a transport/router
only: R³∞ still owns authority, provenance, P5/P6, verification and fallback.

Environment:
    OMNIROUTE_BASE_URL=http://127.0.0.1:20128/v1
    OMNIROUTE_API_KEY=...                 # recommended, required for remote
    OMNIROUTE_LOCAL_NO_AUTH=1             # optional explicit loopback-only mode
"""
from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

from .base import ProviderBase

try:
    from openai import OpenAI
    _OK = True
except ImportError:
    _OK = False


_DEFAULT_BASE_URL = "http://127.0.0.1:20128/v1"
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class OmniRouteProvider(ProviderBase):
    """OpenAI-compatible OmniRoute gateway.

    Availability means only that the adapter is configured locally. It does not
    prove that OmniRoute is running or that any upstream provider is connected.
    """

    nome = "omniroute"

    def _inizializza(self) -> bool:
        if not _OK:
            return False

        base_url = (os.getenv("OMNIROUTE_BASE_URL") or _DEFAULT_BASE_URL).strip().rstrip("/")
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False

        key = (self.api_key or os.getenv("OMNIROUTE_API_KEY") or "").strip()
        local_no_auth = os.getenv("OMNIROUTE_LOCAL_NO_AUTH", "").strip().lower() in {
            "1", "true", "yes", "on"
        }

        if not key:
            if not (local_no_auth and parsed.hostname in _LOOPBACK_HOSTS):
                return False
            # OpenAI client requires a non-empty value even when the local
            # OmniRoute endpoint itself does not enforce Bearer auth.
            key = "omniroute-local-no-auth"

        self.api_key = key
        self.base_url = base_url
        self._client = OpenAI(
            api_key=key,
            base_url=base_url,
            timeout=self.opts.get("timeout_secondi", 60),
            max_retries=self.opts.get("max_retries", 1),
        )
        return True

    def _completa_impl(self, sistema: str, utente: str) -> tuple[str, dict[str, Any]]:
        resp = self._client.chat.completions.create(
            model=self.modello,
            max_tokens=self.opts.get("max_token", 4096),
            temperature=self.opts.get("temperatura", 0.7),
            messages=[
                {"role": "system", "content": sistema},
                {"role": "user", "content": utente},
            ],
        )
        if not resp.choices:
            raise RuntimeError("OmniRoute returned no choices")

        msg = resp.choices[0].message
        text = msg.content or ""
        resolved_model = getattr(resp, "model", None)

        metadata: dict[str, Any] = {
            "gateway": "omniroute",
            "requested_model": self.modello,
            "resolved_model": resolved_model,
            "finish_reason": resp.choices[0].finish_reason,
            "base_url": self.base_url,
        }
        if resp.usage:
            metadata["input_tokens"] = getattr(resp.usage, "prompt_tokens", None)
            metadata["output_tokens"] = getattr(resp.usage, "completion_tokens", None)
        return text, metadata
