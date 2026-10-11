"""Contratto comune per tutti i provider LLM."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RispostaProvider:
    testo: str
    provider: str
    modello: str
    via_api: bool
    latenza_ms: int
    metadata: dict[str, Any] = field(default_factory=dict)
    errore: str | None = None


class ProviderBase(ABC):
    nome: str = "base"

    def __init__(self, modello: str, api_key: str | None, **opts):
        self.modello = modello
        self.api_key = api_key
        self.opts = opts
        self.disponibile = self._inizializza()

    @abstractmethod
    def _inizializza(self) -> bool:
        """Inizializza il client. Restituisce True se utilizzabile."""

    @abstractmethod
    def _completa_impl(self, sistema: str, utente: str) -> tuple[str, dict[str, Any]]:
        """Esegue la chiamata. Restituisce (testo, metadata)."""

    def completa(self, sistema: str, utente: str) -> RispostaProvider:
        if not self.disponibile:
            return RispostaProvider(
                testo="",
                provider=self.nome,
                modello=self.modello,
                via_api=False,
                latenza_ms=0,
                errore="provider non disponibile",
            )
        inizio = time.time()
        try:
            testo, meta = self._completa_impl(sistema, utente)
            return RispostaProvider(
                testo=testo,
                provider=self.nome,
                modello=self.modello,
                via_api=True,
                latenza_ms=int((time.time() - inizio) * 1000),
                metadata=meta,
            )
        except Exception as exc:  # noqa: BLE001
            return RispostaProvider(
                testo="",
                provider=self.nome,
                modello=self.modello,
                via_api=False,
                latenza_ms=int((time.time() - inizio) * 1000),
                errore=str(exc),
            )

    def ping(self) -> RispostaProvider:
        """Smoke test: chiamata minima per verificare connettività."""
        return self.completa("Sei un servizio di echo.", "ping")
