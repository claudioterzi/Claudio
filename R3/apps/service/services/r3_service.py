"""Service: orchestra il core R³∞ e persiste via repository."""
from __future__ import annotations

from r3_core import RaffaelloCore, carica_preset

from ..repositories.stato_repository import StatoRepository


class R3Service:
    """Logica applicativa: avvia il motore, esegue passi, salva lo stato."""

    def __init__(self, repo: StatoRepository | None = None, preset: str = "equilibrio"):
        self.repo = repo or StatoRepository()
        self.core = RaffaelloCore(carica_preset(preset))

    def avvia(self, iterazioni: int = 10) -> dict:
        self.core.loop(iterazioni)
        riassunto = self.core.riassunto()
        self.repo.salva(riassunto)
        return riassunto

    def ferma(self, motivo: str = "stop richiesto") -> dict:
        self.core.kill(motivo)
        riassunto = self.core.riassunto()
        self.repo.salva(riassunto)
        return riassunto

    def stato(self) -> dict:
        return self.repo.carica()
