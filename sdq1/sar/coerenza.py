"""Livello 6 — Indice di Coerenza.

Confronta ciò che il soggetto dice con ciò che fa,
ciò che vuole con ciò che ripete,
ciò che sente con ciò che costruisce.

Più la distanza cresce → più nasce frammentazione.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CoppiaCoerenza:
    """Una coppia interno/esterno da confrontare."""
    dimensione: str    # es. "dici / fai", "vuoi / ripeti"
    interno: str       # dichiarazione/intenzione
    esterno: str       # comportamento/risultato osservato
    distanza: float = 0.5   # 0.0 = perfetta coerenza, 1.0 = massima frammentazione
    nota: str = ""


class IndiceCoerenza:
    """Accumula coppie interno/esterno e calcola l'indice aggregato."""

    DIMENSIONI_STANDARD = [
        ("dici / fai",        "ciò che dichiari di essere",  "ciò che fai concretamente"),
        ("vuoi / ripeti",     "ciò che desideri",             "ciò che continui a ripetere"),
        ("senti / costruisci","ciò che senti dentro",         "ciò che stai costruendo fuori"),
    ]

    def __init__(self):
        self._coppie: list[CoppiaCoerenza] = []

    def aggiungi(
        self,
        dimensione: str,
        interno: str,
        esterno: str,
        distanza: float = 0.5,
        nota: str = "",
    ) -> CoppiaCoerenza:
        c = CoppiaCoerenza(dimensione=dimensione, interno=interno,
                           esterno=esterno, distanza=distanza, nota=nota)
        self._coppie.append(c)
        return c

    def indice_globale(self) -> float:
        """0.0 = massima coerenza, 1.0 = massima frammentazione."""
        if not self._coppie:
            return 0.0
        return sum(c.distanza for c in self._coppie) / len(self._coppie)

    def zone_critiche(self, soglia: float = 0.6) -> list[CoppiaCoerenza]:
        return [c for c in self._coppie if c.distanza >= soglia]

    def interpretazione(self) -> str:
        idx = self.indice_globale()
        if idx < 0.25:
            return "Alta coerenza: le parole e le azioni sono allineate."
        elif idx < 0.5:
            return "Coerenza moderata: alcune tensioni tra intenzione e comportamento."
        elif idx < 0.75:
            return "Frammentazione significativa: distanza notevole tra interno ed esterno."
        else:
            return "Frammentazione critica: l'identità dichiarata e quella vissuta divergono."

    def esporta(self) -> dict[str, Any]:
        return {
            "indice_globale":  round(self.indice_globale(), 3),
            "interpretazione": self.interpretazione(),
            "coppie":          len(self._coppie),
            "zone_critiche":   [
                {"dimensione": c.dimensione, "distanza": c.distanza, "nota": c.nota}
                for c in self.zone_critiche()
            ],
        }
