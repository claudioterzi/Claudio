"""Memoria vettoriale leggera in pure-Python con backend JAX opzionale.

Usa rappresentazione TF su n-grammi di caratteri + similarità coseno.
Quando JAX è disponibile e lo store supera JAX_THRESHOLD documenti,
la ricerca usa batch matrix multiply JIT-compilato (più veloce su store grandi).
"""

from __future__ import annotations

import logging
import math
import threading
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

try:
    from sdq1.core.jax_engine import (
        JAX_AVAILABLE, build_vocab_and_matrix, counter_to_vec, _cosine_batch
    )
except ImportError:
    JAX_AVAILABLE = False

JAX_THRESHOLD = 100  # attiva backend JAX sopra questa soglia


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
    """Storage in-memory con ricerca per similarità coseno.

    Usa backend puro-Python sotto JAX_THRESHOLD documenti;
    sopra quella soglia attiva batch cosine JIT via JAX (se disponibile).
    """

    def __init__(self, soglia_similarita: float = 0.55, max_risultati: int = 5):
        self.soglia = soglia_similarita
        self.max_risultati = max_risultati
        self._ricordi: dict[str, Ricordo] = {}
        self._jax_vocab: dict[str, int] | None = None
        self._jax_matrix = None
        self._jax_ids: list[str] = []      # ordine righe della matrice
        self._jax_dirty: bool = True
        self._lock = threading.Lock()

    def aggiungi(self, testo: str, metadata: dict[str, Any] | None = None) -> str:
        rid = uuid.uuid4().hex[:12]
        self._ricordi[rid] = Ricordo(
            id=rid,
            testo=testo,
            metadata=metadata or {},
            creato_at=time.time(),
            _vettore=_vettore(testo),
        )
        self._jax_dirty = True
        return rid

    def _rebuild_jax(self) -> None:
        """Ricostruisce vocabolario e matrice densa per il backend JAX."""
        ids = list(self._ricordi.keys())
        counters = [dict(self._ricordi[i]._vettore) for i in ids]
        self._jax_vocab, self._jax_matrix = build_vocab_and_matrix(counters)
        self._jax_ids = ids
        self._jax_dirty = False

    def cerca(
        self, query: str, k: int | None = None, soglia: float | None = None
    ) -> list[RisultatoRicerca]:
        if not self._ricordi:
            return []
        k = k or self.max_risultati
        soglia = self.soglia if soglia is None else soglia

        # Backend JAX: attivo sopra soglia se disponibile
        if JAX_AVAILABLE and len(self._ricordi) >= JAX_THRESHOLD:
            with self._lock:
                if self._jax_dirty:
                    self._rebuild_jax()
            qv = counter_to_vec(dict(_vettore(query)), self._jax_vocab)
            scores = _cosine_batch(qv, self._jax_matrix)
            scores_list = scores.tolist()
            risultati = [
                RisultatoRicerca(ricordo=self._ricordi[rid], similarita=s)
                for rid, s in zip(self._jax_ids, scores_list)
                if s >= soglia
            ]
        else:
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
