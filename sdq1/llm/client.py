"""Wrapper Claude con fallback deterministico se SDK/chiave assenti."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)

try:
    import anthropic
    _SDK_OK = True
except ImportError:
    _SDK_OK = False


@dataclass
class RispostaLLM:
    testo: str
    modello: str
    via_api: bool
    metadata: dict[str, Any]


class ClaudeClient:
    def __init__(
        self,
        modello: str,
        temperatura: float = 0.7,
        max_token: int = 4096,
        timeout_secondi: int = 60,
        api_key: str | None = None,
    ):
        self.modello = modello
        self.temperatura = temperatura
        self.max_token = max_token
        self.timeout = timeout_secondi
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.disponibile = bool(self.api_key) and _SDK_OK
        self._client = None
        if self.disponibile:
            self._client = anthropic.Anthropic(
                api_key=self.api_key, timeout=timeout_secondi
            )
            log.info("ClaudeClient: API reale attiva (%s)", modello)
        else:
            log.warning(
                "ClaudeClient: fallback STUB (sdk=%s, key=%s)",
                _SDK_OK,
                bool(self.api_key),
            )

    def completa(self, sistema: str, utente: str) -> RispostaLLM:
        if not self.disponibile:
            return self._stub(sistema, utente)
        try:
            resp = self._client.messages.create(
                model=self.modello,
                max_tokens=self.max_token,
                temperature=self.temperatura,
                system=sistema,
                messages=[{"role": "user", "content": utente}],
            )
            testo = "".join(
                blocco.text for blocco in resp.content if blocco.type == "text"
            )
            return RispostaLLM(
                testo=testo,
                modello=self.modello,
                via_api=True,
                metadata={
                    "input_tokens": resp.usage.input_tokens,
                    "output_tokens": resp.usage.output_tokens,
                    "stop_reason": resp.stop_reason,
                },
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("Chiamata Claude fallita, fallback stub: %s", exc)
            return self._stub(sistema, utente, errore=str(exc))

    def _stub(
        self, sistema: str, utente: str, errore: str | None = None
    ) -> RispostaLLM:
        eco = utente.strip().replace("\n", " ")[:160]
        return RispostaLLM(
            testo=f"[stub:{self.modello}] {eco}",
            modello=self.modello,
            via_api=False,
            metadata={
                "stub": True,
                "sistema_len": len(sistema),
                "errore": errore,
            },
        )


def crea_client_da_config(modello_cfg: dict[str, Any], modello: str | None = None) -> ClaudeClient:
    return ClaudeClient(
        modello=modello or modello_cfg["nome"],
        temperatura=modello_cfg.get("temperatura", 0.7),
        max_token=modello_cfg.get("max_token", 4096),
        timeout_secondi=modello_cfg.get("timeout_secondi", 60),
    )
