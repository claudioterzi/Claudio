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

    # Mapping modello-hint -> profilo router
    PROFILI_PER_MODELLO = {
        "claude-opus-4-7": "ragionamento",
        "claude-sonnet-4-6": "default",
        "claude-haiku-4-5": "veloce",
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

    def completa(self, sistema: str, utente: str) -> RispostaLLM:
        esito = self.router.chiama(sistema, utente, profilo=self.profilo)
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
            },
        )
