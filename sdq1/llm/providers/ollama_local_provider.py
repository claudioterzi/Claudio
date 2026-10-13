"""Provider Ollama locale per modelli LLM installati localmente.

Comunica con Ollama via HTTP API (default: http://localhost:11434).
Zero costi, modelli locali, completamente offline.
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Any

from .base import ProviderBase

log = logging.getLogger(__name__)


class OllamaLocalProvider(ProviderBase):
    """Provider per modelli Ollama locali."""

    nome = "ollama_local"

    def __init__(self, modello: str, api_key: str | None = None, **opts):
        self.base_url = opts.get("base_url", "http://localhost:11434")
        self.modello = modello
        self.api_key = api_key
        self.opts = opts
        self.disponibile = self._inizializza()

    def _inizializza(self) -> bool:
        """Verifica che Ollama sia raggiungibile."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception as exc:
            log.warning("Ollama non raggiungibile a %s: %s", self.base_url, exc)
            return False

    def _completa_impl(self, sistema: str, utente: str) -> tuple[str, dict[str, Any]]:
        """
        Chiama Ollama via API per generare una risposta.

        Args:
            sistema: prompt di sistema
            utente: prompt dell'utente

        Returns:
            (testo_risposta, metadata)
        """
        payload = {
            "model": self.modello,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": utente},
            ],
            "stream": False,
            "temperature": 0.7,
        }

        try:
            payload_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=payload_bytes,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                testo = data.get("message", {}).get("content", "").strip()

                return testo, {
                    "ollama_model": self.modello,
                    "ollama_base_url": self.base_url,
                    "ollama_success": True,
                }

        except urllib.error.URLError as exc:
            if "timeout" in str(exc).lower():
                return "", {
                    "ollama_model": self.modello,
                    "ollama_success": False,
                    "errore": "timeout",
                }
            return "", {
                "ollama_model": self.modello,
                "ollama_success": False,
                "errore": f"connection_error: {str(exc)[:50]}",
            }
        except Exception as exc:
            return "", {
                "ollama_model": self.modello,
                "ollama_success": False,
                "errore": str(exc)[:100],
            }

    def completa(self, sistema: str, utente: str):
        """Override per marcare via_api=False (è locale)."""
        r = super().completa(sistema, utente)
        r.via_api = False
        return r
