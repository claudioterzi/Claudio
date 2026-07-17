"""Provider Google Gemini (via REST API — no SDK dipendency)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .base import ProviderBase

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(ProviderBase):
    nome = "gemini"

    def _inizializza(self) -> bool:
        key = self.api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            return False
        self.api_key = key
        return True

    def _completa_impl(self, sistema: str, utente: str) -> tuple[str, dict[str, Any]]:
        modello = self.modello or "gemini-2.5-flash"
        url = f"{_BASE_URL}/{modello}:generateContent?key={self.api_key}"

        gen = {
            "temperature": self.opts.get("temperatura", 0.7),
            "maxOutputTokens": self.opts.get("max_token", 4096),
        }
        # modalità JSON strutturata: Gemini garantisce output JSON valido,
        # senza preamboli né recinti markdown (usata dall'Atelier)
        if self.opts.get("json_mode"):
            gen["responseMimeType"] = "application/json"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": utente}]}],
            "generationConfig": gen,
        }
        if sistema:
            payload["systemInstruction"] = {"parts": [{"text": sistema}]}

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.opts.get("timeout", 60)) as r:
                resp = json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            raise RuntimeError(f"Gemini HTTP {e.code}: {body[:300]}") from e

        candidates = resp.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini: nessun candidato nella risposta: {resp}")

        testo = candidates[0]["content"]["parts"][0].get("text", "")
        meta: dict[str, Any] = {}
        usage = resp.get("usageMetadata", {})
        if usage:
            meta["input_tokens"] = usage.get("promptTokenCount", 0)
            meta["output_tokens"] = usage.get("candidatesTokenCount", 0)

        return testo, meta
