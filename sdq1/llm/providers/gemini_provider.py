"""Provider Google Gemini (via HTTP diretto — nessuna dipendenza SDK)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .base import ProviderBase

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(ProviderBase):
    nome = "gemini"

    def _inizializza(self) -> bool:
        key = self.api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            return False
        self.api_key = key
        return True

    def _completa_impl(self, sistema: str, utente: str) -> tuple[str, dict[str, Any]]:
        url = f"{_BASE}/{self.modello}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": sistema}]},
            "contents": [{"parts": [{"text": utente}]}],
            "generationConfig": {
                "temperature": self.opts.get("temperatura", 0.7),
                "maxOutputTokens": self.opts.get("max_token", 4096),
            },
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=int(self.opts.get("timeout_s", 60))) as r:
                resp = json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"Gemini HTTP {e.code}: {body[:300]}") from e

        testo = resp["candidates"][0]["content"]["parts"][0]["text"]
        meta: dict[str, Any] = {}
        if "usageMetadata" in resp:
            u = resp["usageMetadata"]
            meta["input_tokens"] = u.get("promptTokenCount", 0)
            meta["output_tokens"] = u.get("candidatesTokenCount", 0)
        return testo, meta
