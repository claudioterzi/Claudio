"""Controller: superficie d'ingresso (controller-service-repository).

Sottile: traduce richieste in chiamate al service. Riusabile da API o CLI.
"""
from __future__ import annotations

from ..services.r3_service import R3Service


class R3Controller:
    def __init__(self, service: R3Service | None = None):
        self.service = service or R3Service()

    def avvia(self, iterazioni: int = 10) -> dict:
        return {"ok": True, "risultato": self.service.avvia(iterazioni)}

    def ferma(self, motivo: str = "stop") -> dict:
        return {"ok": True, "risultato": self.service.ferma(motivo)}

    def stato(self) -> dict:
        return {"ok": True, "stato": self.service.stato()}
