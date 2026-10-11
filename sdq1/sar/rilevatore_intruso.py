"""Rilevatore dell'Intruso — SDQ-1 SAR Layer.

Identifica pattern, coincidenze, ricorrenze e convergenze
statisticamente o semanticamente insolite nei dati del sistema.

NON cerca conferme di credenze.
NON genera superstizione.
NON assume entità soprannaturali.

TRACCIA = ANOMALIA × RIPETIZIONE × INDIPENDENZA × RILEVANZA × CONVERGENZA
Se uno dei fattori è assente: TRACCIA = 0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


CLASSI = {
    (0,  20):  "Rumore",
    (21, 40):  "Pattern Debole",
    (41, 60):  "Traccia Interessante",
    (61, 80):  "Forte Convergenza",
    (81, 100): "Evento Intruso",
}


@dataclass
class Evento:
    tipo: str
    elementi: list[str]
    fonte: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Traccia:
    tipo: str
    elementi_coinvolti: list[str]
    motivo: str
    spiegazione_razionale: str
    punteggio: int
    confidenza: float          # 0.0 - 1.0

    # Fattori componenti
    anomalia: float = 0.0
    ripetizione: float = 0.0
    indipendenza: float = 0.0
    rilevanza: float = 0.0
    convergenza: float = 0.0

    def classificazione(self) -> str:
        for (lo, hi), label in CLASSI.items():
            if lo <= self.punteggio <= hi:
                return label
        return "Rumore"

    def report(self) -> str:
        righe = [
            f"TIPO:                  {self.tipo}",
            f"CONFIDENZA:            {self.confidenza:.0%}",
            f"ELEMENTI COINVOLTI:    {', '.join(self.elementi_coinvolti)}",
            f"MOTIVO:                {self.motivo}",
            f"SPIEGAZIONE RAZIONALE: {self.spiegazione_razionale}",
            f"PUNTEGGIO INTRUSO:     {self.punteggio}/100 — {self.classificazione()}",
            f"  anomalia={self.anomalia:.2f}  ripetizione={self.ripetizione:.2f}  "
            f"indipendenza={self.indipendenza:.2f}  rilevanza={self.rilevanza:.2f}  "
            f"convergenza={self.convergenza:.2f}",
        ]
        return "\n".join(righe)


class RilevatorIntruso:
    """
    Osservatore delle tracce — non decide il significato,
    identifica soltanto le convergenze.
    """

    def __init__(self, temi_attivi: list[str] | None = None):
        self.temi_attivi = temi_attivi or []
        self._tracce: list[Traccia] = []

    def analizza(
        self,
        eventi: list[Evento],
        soglia_minima: int = 21,
    ) -> list[Traccia]:
        """Analizza una lista di eventi e restituisce le tracce rilevate."""
        self._tracce = []

        # Raggruppa per elemento
        indice: dict[str, list[Evento]] = {}
        for ev in eventi:
            for el in ev.elementi:
                indice.setdefault(el, []).append(ev)

        for elemento, occorrenze in indice.items():
            traccia = self._valuta(elemento, occorrenze, eventi)
            if traccia and traccia.punteggio >= soglia_minima:
                self._tracce.append(traccia)

        self._tracce.sort(key=lambda t: t.punteggio, reverse=True)
        return self._tracce

    def _valuta(
        self, elemento: str, occorrenze: list[Evento], tutti: list[Evento]
    ) -> Traccia | None:
        n = len(occorrenze)
        if n < 2:
            return None

        # RIPETIZIONE: quante volte compare (normalizzato su 10 come soglia alta)
        rip = min(1.0, (n - 1) / 4)

        # INDIPENDENZA: fonti distinte
        fonti = {ev.fonte for ev in occorrenze}
        ind = min(1.0, (len(fonti) - 1) / 3) if len(fonti) > 1 else 0.0
        if ind == 0.0:
            return None  # stessa fonte → non è traccia

        # ANOMALIA: elemento presente in proporzione insolita rispetto al totale eventi
        freq_attesa = 2 / max(len(tutti), 1)
        freq_reale = n / len(tutti)
        anom = min(1.0, (freq_reale / max(freq_attesa, 0.01)) / 5)

        # RILEVANZA: l'elemento è connesso ai temi attivi?
        rel = 0.0
        for tema in self.temi_attivi:
            if tema.lower() in elemento.lower() or elemento.lower() in tema.lower():
                rel = 1.0
                break
        if rel == 0.0:
            # Ricerca parziale
            for tema in self.temi_attivi:
                parole_tema = set(tema.lower().split())
                parole_el = set(elemento.lower().split())
                if parole_tema & parole_el:
                    rel = 0.6
                    break

        if rel == 0.0:
            return None  # non rilevante per i temi attivi

        # CONVERGENZA TEMPORALE: gli eventi sono ravvicinati?
        # Semplificato: se stesso batch → convergenza alta
        conv = 0.8 if n >= 2 else 0.4

        # PUNTEGGIO: prodotto normalizzato 0-100
        score_raw = anom * rip * ind * rel * conv
        punteggio = min(100, int(score_raw * 100 * 5))

        if punteggio == 0:
            return None

        tipo = (
            f"CONVERGENZA_{elemento.upper().replace(' ', '_')[:20]}"
        )

        return Traccia(
            tipo=tipo,
            elementi_coinvolti=[elemento] + [ev.tipo for ev in occorrenze],
            motivo=(
                f"'{elemento}' compare {n} volte in {len(fonti)} fonti distinte "
                f"({', '.join(sorted(fonti))})"
            ),
            spiegazione_razionale=(
                f"Presenza elevata in contesti multipli. "
                f"Possibile: tema centrale del sistema, bug ricorrente, "
                f"o segnale evolutivo da investigare."
            ),
            punteggio=punteggio,
            confidenza=round(ind * rel * conv, 2),
            anomalia=round(anom, 2),
            ripetizione=round(rip, 2),
            indipendenza=round(ind, 2),
            rilevanza=round(rel, 2),
            convergenza=round(conv, 2),
        )

    def stampa_report(self) -> str:
        if not self._tracce:
            return "Nessuna traccia rilevata. Punteggio < soglia minima."
        righe = [
            "═" * 60,
            "RILEVATORE DELL'INTRUSO — REPORT",
            f"Tracce rilevate: {len(self._tracce)}",
            "═" * 60,
        ]
        for i, t in enumerate(self._tracce, 1):
            righe.append(f"\n[{i}] {t.classificazione()}")
            righe.append(t.report())
            righe.append("─" * 60)
        return "\n".join(righe)
