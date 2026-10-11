"""Compat shim: ClaudeClient ora avvolge il router multi-provider.

Mantenuto per non rompere `agents/implementazioni.py`. Il vero motore è
`sdq1.llm.router.LLMRouter`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .router import LLMRouter


@dataclass
class RispostaLLM:
    testo: str
    modello: str
    via_api: bool
    provider: str
    metadata: dict[str, Any]


class ClaudeClient:
    """Compat wrapper. Usa il router; il 'modello' diventa hint per profilo."""

    PROFILI_PER_MODELLO = {
        "claude-fable-5":            "ragionamento",
        "claude-opus-4-8":           "ragionamento",
        "claude-opus-4-7":           "ragionamento",
        "claude-sonnet-4-6":         "default",
        "claude-haiku-4-5-20251001": "veloce",
        "claude-haiku-4-5":          "veloce",
        # Gemini — flash = veloce, pro = default (ragionamento per 2.5-pro)
        "gemini-2.5-flash":          "veloce",
        "gemini-2.5-pro":            "default",
        "gemini-2.0-flash":          "veloce",
        "gemini-1.5-flash":          "veloce",
        "gemini-1.5-pro":            "default",
    }

    def __init__(self, router: LLMRouter, modello_hint: str | None = None):
        self.router = router
        self.modello_hint = modello_hint or "claude-sonnet-4-6"
        self.profilo = self.PROFILI_PER_MODELLO.get(self.modello_hint, "default")

    @property
    def modello(self) -> str:
        return self.modello_hint

    @property
    def disponibile(self) -> bool:
        return any(self.router.provider_attivi().values())

    def completa(
        self,
        sistema: str,
        utente: str,
        hedging: bool = False,
        provider_vincolo: str | None = None,
    ) -> RispostaLLM:
        esito = self.router.chiama(
            sistema, utente,
            profilo=self.profilo,
            hedging=hedging,
            provider_vincolo=provider_vincolo,
        )
        r = esito.risposta
        return RispostaLLM(
            testo=r.testo,
            modello=r.modello,
            via_api=r.via_api,
            provider=r.provider,
            metadata={
                **r.metadata,
                "latenza_ms": r.latenza_ms,
                "provider_tentati": esito.provider_usati,
                "profilo": esito.profilo,
                "errore": r.errore,
                "hedged": esito.hedged,
            },
        )
