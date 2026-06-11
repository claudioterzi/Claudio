"""Livello 4 — Memoria Evolutiva.

Salva decisioni, stati emotivi, previsioni, errori, trasformazioni.
Cerca pattern ricorrenti nel tempo per rivelare la struttura
comportamentale sottostante.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ..memory.vss import VectorStateStore


CATEGORIE = frozenset({
    "decisione",
    "stato_emotivo",
    "previsione",
    "errore",
    "trasformazione",
    "relazione",
    "conflitto",
    "successo",
    "paura",
    "desiderio",
})


@dataclass
class EntrataMemo:
    id: str
    categoria: str
    testo: str
    intensita: float
    timestamp: float
    tag: list[str] = field(default_factory=list)
    pattern_collegati: list[str] = field(default_factory=list)


@dataclass
class PatternRicorrente:
    trigger: str
    sequenza: list[str]
    frequenza: int = 1
    ultima_occorrenza: float = field(default_factory=time.time)

    def descrivi(self) -> str:
        return f"Ogni volta che '{self.trigger}':\n" + "\n↓\n".join(self.sequenza)


class MemoriaEvolutiva:
    """Accumula osservazioni e identifica pattern comportamentali nel tempo."""

    def __init__(self, vss: VectorStateStore | None = None, soggetto: str = "utente"):
        self._vss = vss
        self._soggetto = soggetto
        self._entrate: dict[str, EntrataMemo] = {}
        self._pattern: list[PatternRicorrente] = []

    def registra(
        self,
        testo: str,
        categoria: str = "stato_emotivo",
        intensita: float = 0.5,
        tag: list[str] | None = None,
    ) -> EntrataMemo:
        if categoria not in CATEGORIE:
            categoria = "stato_emotivo"
        eid = uuid.uuid4().hex[:8]
        entrata = EntrataMemo(
            id=eid, categoria=categoria, testo=testo,
            intensita=intensita, timestamp=time.time(), tag=tag or [],
        )
        self._entrate[eid] = entrata
        if self._vss:
            self._vss.scrivi(testo, run_id="sar_globale",
                             agente_id="SAR-MEM", chiave=eid)
        self._aggiorna_pattern(entrata)
        return entrata

    def _aggiorna_pattern(self, entrata: EntrataMemo) -> None:
        for p in self._pattern:
            if entrata.testo.lower() in p.trigger.lower() or p.trigger.lower() in entrata.testo.lower():
                p.frequenza += 1
                p.ultima_occorrenza = entrata.timestamp
                entrata.pattern_collegati.append(p.trigger)

    def aggiungi_pattern(self, trigger: str, sequenza: list[str]) -> PatternRicorrente:
        p = PatternRicorrente(trigger=trigger, sequenza=sequenza)
        self._pattern.append(p)
        return p

    def cerca_simili(self, query: str, top_k: int = 5) -> list[EntrataMemo]:
        if self._vss:
            testi = self._vss.cerca_nel_run(query, run_id="sar_globale", top_k=top_k)
            risultati = []
            for e in self._entrate.values():
                if e.testo in testi:
                    risultati.append(e)
            return risultati[:top_k]
        q = query.lower()
        scored = [
            (e, sum(1 for w in q.split() if w in e.testo.lower()))
            for e in self._entrate.values()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:top_k] if _ > 0]

    def pattern_attivi(self) -> list[PatternRicorrente]:
        return sorted(self._pattern, key=lambda p: p.frequenza, reverse=True)

    def cronologia(self, categoria: str | None = None) -> list[EntrataMemo]:
        entrate = list(self._entrate.values())
        if categoria:
            entrate = [e for e in entrate if e.categoria == categoria]
        return sorted(entrate, key=lambda e: e.timestamp)

    def esporta(self) -> dict[str, Any]:
        return {
            "soggetto": self._soggetto,
            "entrate": len(self._entrate),
            "pattern_attivi": [
                {"trigger": p.trigger, "sequenza": p.sequenza, "frequenza": p.frequenza}
                for p in self.pattern_attivi()
            ],
            "per_categoria": {
                cat: sum(1 for e in self._entrate.values() if e.categoria == cat)
                for cat in CATEGORIE
                if any(e.categoria == cat for e in self._entrate.values())
            },
        }
