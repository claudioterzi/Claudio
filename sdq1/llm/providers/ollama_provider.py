"""Provider Ollama — modelli open-source in locale, costo zero.

Attivazione: avviare `ollama serve` e impostare OLLAMA_BASE_URL
(default: http://localhost:11434/v1). Nessuna API key necessaria.

Modelli consigliati (scaricabili con `ollama pull <nome>`):
  llama3.2        – uso generale, 3B, veloce
  mistral         – bilanciato, 7B
  phi4            – ragionamento, 14B
  gemma3          – istruzioni, 4B
  qwen2.5-coder   – codice
"""

from __future__ import annotations

import os
from typing import Any

from .base import ProviderBase

try:
    from openai import OpenAI
    _OK = True
except ImportError:
    _OK = False

_DEFAULT_URL = "http://localhost:11434/v1"


class OllamaProvider(ProviderBase):
    nome = "ollama"
    # Modelli locali: i token non costano — la compressione darebbe solo
    # latenza e rischio semantico a fronte di zero risparmio. Cfr. CLAUDE.md.
    _headroom_default = False

    def _inizializza(self) -> bool:
        if not _OK:
            return False
        base_url = os.getenv("OLLAMA_BASE_URL", _DEFAULT_URL)
        try:
            self._client = OpenAI(
                api_key="ollama",           # Ollama non richiede chiave reale
                base_url=base_url,
                timeout=self.opts.get("timeout_secondi", 120),
            )
            # Verifica che il server risponda
            self._client.models.list()
            return True
        except Exception:
            return False

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
        testo = resp.choices[0].message.content or ""
        return testo, {
            "input_tokens": resp.usage.prompt_tokens if resp.usage else None,
            "output_tokens": resp.usage.completion_tokens if resp.usage else None,
            "finish_reason": resp.choices[0].finish_reason,
        }
