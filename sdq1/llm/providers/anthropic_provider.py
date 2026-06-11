"""Provider Anthropic (Claude)."""

from __future__ import annotations

import os
from typing import Any

from .base import ProviderBase

try:
    import anthropic
    _OK = True
except ImportError:
    _OK = False


class AnthropicProvider(ProviderBase):
    nome = "anthropic"

    def _inizializza(self) -> bool:
        if not _OK:
            return False
        key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            return False
        self.api_key = key
        self._client = anthropic.Anthropic(
            api_key=key, timeout=self.opts.get("timeout_secondi", 60)
        )
        return True

    def _completa_impl(self, sistema: str, utente: str) -> tuple[str, dict[str, Any]]:
        resp = self._client.messages.create(
            model=self.modello,
            max_tokens=self.opts.get("max_token", 4096),
            temperature=self.opts.get("temperatura", 0.7),
            system=sistema,
            messages=[{"role": "user", "content": utente}],
        )
        testo = "".join(b.text for b in resp.content if b.type == "text")
        return testo, {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "stop_reason": resp.stop_reason,
        }
