"""Memoria vettoriale leggera in pure-Python.

Usa rappresentazione TF su n-grammi di caratteri + similarità coseno.
Non richiede numpy né sentence-transformers; sostituibile in produzione
con MiniLM + Qdrant senza cambiare l'interfaccia pubblica.
"""

from __future__ import annotations

import math
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


def _shingle(testo: str, n: int = 3) -> list[str]:
    t = " " + testo.lower().strip() + " "
    return [t[i : i + n] for i in range(len(t) - n + 1)] if len(t) >= n else [t]


def _vettore(testo: str) -> Counter:
    return Counter(_shingle(testo))


def _coseno(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    comune = set(a) & set(b)
    num = sum(a[k] * b[k] for k in comune)
    den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(
        sum(v * v for v in b.values())
    )
    return num / den if den else 0.0


@dataclass
class Ricordo:
    id: str
    testo: str
    metadata: dict[str, Any]
    creato_at: float
    _vettore: Counter = field(repr=False, default_factory=Counter)


@dataclass
class RisultatoRicerca:
    ricordo: Ricordo
    similarita: float


class MemoriaVettoriale:
    """Storage in-memory con ricerca per similarità coseno."""

    def __init__(self, soglia_similarita: float = 0.55, max_risultati: int = 5):
        self.soglia = soglia_similarita
        self.max_risultati = max_risultati
        self._ricordi: dict[str, Ricordo] = {}

    def aggiungi(self, testo: str, metadata: dict[str, Any] | None = None) -> str:
        rid = uuid.uuid4().hex[:12]
        self._ricordi[rid] = Ricordo(
            id=rid,
            testo=testo,
            metadata=metadata or {},
            creato_at=time.time(),
            _vettore=_vettore(testo),
        )
        return rid

    def cerca(
        self, query: str, k: int | None = None, soglia: float | None = None
    ) -> list[RisultatoRicerca]:
        if not self._ricordi:
            return []
        k = k or self.max_risultati
        soglia = self.soglia if soglia is None else soglia
        qv = _vettore(query)
        risultati = [
            RisultatoRicerca(ricordo=r, similarita=_coseno(qv, r._vettore))
            for r in self._ricordi.values()
        ]
        risultati = [r for r in risultati if r.similarita >= soglia]
        risultati.sort(key=lambda r: r.similarita, reverse=True)
        return risultati[:k]

    def dimensione(self) -> int:
        return len(self._ricordi)

    def esporta(self) -> list[dict]:
        return [
            {"testo": r.testo, "metadata": r.metadata, "creato_at": r.creato_at}
            for r in self._ricordi.values()
        ]

    def svuota(self) -> None:
        self._ricordi.clear()
