"""Provider OpenAI + cugini API-compatibili (DeepSeek, Perplexity, Grok)."""

from __future__ import annotations

import os
from typing import Any

from .base import ProviderBase

try:
    from openai import OpenAI
    _OK = True
except ImportError:
    _OK = False


class _OpenAIBase(ProviderBase):
    env_var: str = "OPENAI_API_KEY"
    base_url: str | None = None

    def _inizializza(self) -> bool:
        if not _OK:
            return False
        key = self.api_key or os.getenv(self.env_var)
        if not key:
            return False
        self.api_key = key
        kwargs: dict[str, Any] = {
            "api_key": key,
            "timeout": self.opts.get("timeout_secondi", 60),
        }
        if self.base_url:
            kwargs["base_url"] = self.base_url
        self._client = OpenAI(**kwargs)
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
        msg = resp.choices[0].message
        testo = msg.content or ""
        return testo, {
            "input_tokens": resp.usage.prompt_tokens if resp.usage else None,
            "output_tokens": resp.usage.completion_tokens if resp.usage else None,
            "finish_reason": resp.choices[0].finish_reason,
        }


class OpenAIProvider(_OpenAIBase):
    nome = "openai"
    env_var = "OPENAI_API_KEY"


class DeepSeekProvider(_OpenAIBase):
    nome = "deepseek"
    env_var = "DEEPSEEK_API_KEY"
    base_url = "https://api.deepseek.com"


class PerplexityProvider(_OpenAIBase):
    nome = "perplexity"
    env_var = "PERPLEXITY_API_KEY"
    base_url = "https://api.perplexity.ai"


class GrokProvider(_OpenAIBase):
    nome = "grok"
    env_var = "XAI_API_KEY"
    base_url = "https://api.x.ai/v1"


class MiniMaxProvider(_OpenAIBase):
    """MiniMax (M-series) — API OpenAI-compatibile, quasi-frontiera a basso costo.

    Endpoint e nome-modello sono sovrascrivibili via env in caso MiniMax
    aggiorni le rotte, senza toccare il codice:
        MINIMAX_API_KEY    (obbligatorio)
        MINIMAX_BASE_URL   (default: https://api.minimax.io/v1)
    """
    nome = "minimax"
    env_var = "MINIMAX_API_KEY"
    base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
