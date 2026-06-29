"""Protocollo Rosso — Rivelazione · Direzione · Mutazione · Fusione.

Quattro fasi che trasformano uno stato (dict) in modo puro e tracciabile.
È il ciclo semantico del nodo Rosso: vedere → orientare → cambiare → integrare.
"""
from __future__ import annotations

from dataclasses import dataclass, field

RIVELAZIONE = "rivelazione"
DIREZIONE = "direzione"
MUTAZIONE = "mutazione"
FUSIONE = "fusione"
FASI = (RIVELAZIONE, DIREZIONE, MUTAZIONE, FUSIONE)


@dataclass
class EsitoFase:
    fase: str
    nota: str
    stato: dict


@dataclass
class ProtocolloRosso:
    """Esegue le quattro fasi in sequenza su uno stato."""
    log: list[EsitoFase] = field(default_factory=list)

    def _rivela(self, stato: dict) -> dict:
        s = dict(stato)
        s["rivelato"] = s.get("osservazione", "")
        return s

    def _dirige(self, stato: dict) -> dict:
        s = dict(stato)
        energia = float(s.get("energia", 0.0))
        s["direzione"] = "avanti" if energia >= 0.5 else "raccolta"
        return s

    def _muta(self, stato: dict) -> dict:
        s = dict(stato)
        s["mutazioni"] = int(s.get("mutazioni", 0)) + 1
        return s

    def _fonde(self, stato: dict) -> dict:
        s = dict(stato)
        s["fuso"] = True
        s["sintesi"] = f"{s.get('direzione', '?')}|mut={s.get('mutazioni', 0)}"
        return s

    def esegui(self, stato: dict) -> dict:
        """Applica le 4 fasi in ordine, registrando il log. Ritorna lo stato finale."""
        self.log.clear()
        passi = [
            (RIVELAZIONE, self._rivela, "ciò che c'è viene visto"),
            (DIREZIONE, self._dirige, "lo sguardo prende rotta"),
            (MUTAZIONE, self._muta, "qualcosa cambia"),
            (FUSIONE, self._fonde, "le parti si integrano"),
        ]
        for fase, fn, nota in passi:
            stato = fn(stato)
            self.log.append(EsitoFase(fase, nota, dict(stato)))
        return stato

    def fasi_eseguite(self) -> list[str]:
        return [e.fase for e in self.log]
