"""Provider Google Gemini (via google-genai SDK)."""

from __future__ import annotations

import os
from typing import Any

from .base import ProviderBase

try:
    from google import genai
    from google.genai import types as genai_types
    _OK = True
except ImportError:
    _OK = False


class GeminiProvider(ProviderBase):
    nome = "gemini"

    def _inizializza(self) -> bool:
        if not _OK:
            return False
        key = self.api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            return False
        self.api_key = key
        self._client = genai.Client(api_key=key)
        return True

    def _completa_impl(self, sistema: str, utente: str) -> tuple[str, dict[str, Any]]:
        resp = self._client.models.generate_content(
            model=self.modello,
            contents=utente,
            config=genai_types.GenerateContentConfig(
                system_instruction=sistema,
                temperature=self.opts.get("temperatura", 0.7),
                max_output_tokens=self.opts.get("max_token", 4096),
            ),
        )
        testo = resp.text or ""
        meta: dict[str, Any] = {}
        if getattr(resp, "usage_metadata", None):
            meta["input_tokens"] = resp.usage_metadata.prompt_token_count
            meta["output_tokens"] = resp.usage_metadata.candidates_token_count
        return testo, meta
