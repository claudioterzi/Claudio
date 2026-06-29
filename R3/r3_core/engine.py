"""RAFFAELLO CORE — loop, stato, kill switch.

Il motore centrale R³∞: a ogni passo valuta la scacchiera quantica, esegue il
Protocollo Rosso e aggiorna lo stato. Il kill switch interrompe immediatamente
il loop: è la garanzia di controllo umano (coerente con i limiti non negoziabili).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import ConfigR3, carica_preset
from .protocol_rosso import ProtocolloRosso
from .scacchiera import ScacchieraQuantica


class KillSwitchAttivato(Exception):
    """Sollevata internamente quando il kill switch ferma il motore."""


@dataclass
class StatoCore:
    iterazione: int = 0
    energia: float = 0.0
    ultima_sintesi: str = ""
    collassi: int = 0
    fermato: bool = False
    motivo_stop: str = ""


class RaffaelloCore:
    """Motore centrale. `passo()` = un'iterazione; `loop()` = R3 continuo."""

    def __init__(self, config: ConfigR3 | None = None):
        self.config = config or carica_preset("equilibrio")
        self.scacchiera = ScacchieraQuantica(self.config.n_scacchiera, self.config.seed)
        self.rosso = ProtocolloRosso()
        self.stato = StatoCore()
        self._kill = False

    # --- kill switch -------------------------------------------------------
    def kill(self, motivo: str = "kill switch") -> None:
        """Attiva il kill switch: il prossimo controllo del loop si ferma."""
        self._kill = True
        self.stato.fermato = True
        self.stato.motivo_stop = motivo

    @property
    def attivo(self) -> bool:
        return not self.stato.fermato

    def _verifica_kill(self) -> None:
        if self.config.kill_switch_attivo and self._kill:
            raise KillSwitchAttivato(self.stato.motivo_stop or "kill")

    # --- ciclo -------------------------------------------------------------
    def passo(self) -> StatoCore:
        """Una iterazione del motore."""
        self._verifica_kill()
        self.scacchiera.perturba()
        energia = self.scacchiera.valuta()
        finale = self.rosso.esegui({"osservazione": "scacchiera", "energia": energia})
        nodo = self.scacchiera.collassa(self.config.soglia_collasso)
        if nodo is not None:
            self.stato.collassi += 1
        self.stato.iterazione += 1
        self.stato.energia = energia
        self.stato.ultima_sintesi = finale.get("sintesi", "")
        return self.stato

    def loop(self, n: int | None = None) -> StatoCore:
        """R3 continuo: ripete `passo()` fino a n (o max_iterazioni) o kill switch."""
        limite = min(n or self.config.max_iterazioni, self.config.max_iterazioni)
        try:
            for _ in range(limite):
                self.passo()
        except KillSwitchAttivato as exc:
            self.stato.fermato = True
            self.stato.motivo_stop = str(exc)
        return self.stato

    def riassunto(self) -> dict:
        return {
            "qstp": self.config.qstp_versione,
            "preset": self.config.preset,
            "iterazione": self.stato.iterazione,
            "energia": round(self.stato.energia, 4),
            "collassi": self.stato.collassi,
            "fermato": self.stato.fermato,
            "motivo_stop": self.stato.motivo_stop,
            "scacchiera": f"{self.config.n_scacchiera}x{self.config.n_scacchiera}",
        }
