"""Scacchiera Quantica n=8 — nodi e valutazioni.

Una griglia n×n di nodi con un'ampiezza in [0,1]. La valutazione aggrega lo
stato; il collasso seleziona il nodo dominante quando supera la soglia.
Deterministica a parità di seed. Zero dipendenze.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class Nodo:
    riga: int
    colonna: int
    ampiezza: float  # [0,1]

    @property
    def coord(self) -> tuple[int, int]:
        return (self.riga, self.colonna)


class ScacchieraQuantica:
    """Scacchiera n×n di nodi quantici."""

    def __init__(self, n: int = 8, seed: int = 7):
        if n < 1:
            raise ValueError("n deve essere >= 1")
        self.n = n
        self._rng = random.Random(seed)
        self.nodi: list[Nodo] = [
            Nodo(r, c, self._rng.random())
            for r in range(n) for c in range(n)
        ]

    def valuta(self) -> float:
        """Energia media della scacchiera in [0,1]."""
        return sum(nd.ampiezza for nd in self.nodi) / len(self.nodi)

    def dominante(self) -> Nodo:
        """Il nodo con ampiezza massima."""
        return max(self.nodi, key=lambda nd: nd.ampiezza)

    def collassa(self, soglia: float) -> Nodo | None:
        """Collassa sul nodo dominante se supera la soglia, altrimenti None."""
        nd = self.dominante()
        return nd if nd.ampiezza >= soglia else None

    def perturba(self, intensita: float = 0.1) -> None:
        """Evolve lo stato: piccola perturbazione deterministica dei nodi."""
        for nd in self.nodi:
            delta = (self._rng.random() - 0.5) * 2 * intensita
            nd.ampiezza = min(1.0, max(0.0, nd.ampiezza + delta))

    def __len__(self) -> int:
        return len(self.nodi)
