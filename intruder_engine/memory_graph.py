"""Modulo 2 — MEMORY GRAPH.

Mappa dinamica di entità e relazioni pesate (NetworkX + SQLite).
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

try:
    import networkx as nx
    _NX = True
except ImportError:
    _NX = False

from .db import Entity, Relationship, Session


ENTITY_PATTERNS: dict[str, list[str]] = {
    "date":    [r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", r"\b\d{4}-\d{2}-\d{2}\b"],
    "number":  [r"\b\d+(?:[.,]\d+)?\b"],
}


def extract_entities_simple(text: str) -> list[tuple[str, str]]:
    """Estrazione semplice di entità senza NER completo (V1)."""
    found: list[tuple[str, str]] = []
    for etype, patterns in ENTITY_PATTERNS.items():
        for pat in patterns:
            for m in re.finditer(pat, text):
                found.append((etype, m.group()))
    return found


class MemoryGraph:
    """Grafo in-memory con persistenza SQLite."""

    def __init__(self, session: Session):
        self.session = session
        self._graph = nx.DiGraph() if _NX else None
        self._weights: dict[tuple[str, str], float] = defaultdict(float)
        self._load()

    def _load(self) -> None:
        for rel in self.session.query(Relationship).all():
            src = rel.source.name
            tgt = rel.target.name
            self._weights[(src, tgt)] = rel.weight
            if self._graph is not None:
                self._graph.add_edge(src, tgt, weight=rel.weight)

    def add_event_entities(self, entities: list[tuple[str, str]], boost: float = 1.0) -> None:
        """Aggiunge entità da un evento e aggiorna i pesi delle relazioni."""
        names = []
        for etype, name in entities:
            ent = self.session.query(Entity).filter_by(name=name).first()
            if not ent:
                ent = Entity(type=etype, name=name)
                self.session.add(ent)
                self.session.flush()
            names.append(name)

        for i, a in enumerate(names):
            for b in names[i+1:]:
                self._weights[(a, b)] += boost
                self._weights[(b, a)] += boost
                if self._graph is not None:
                    self._graph.add_edge(a, b, weight=self._weights[(a, b)])
                    self._graph.add_edge(b, a, weight=self._weights[(b, a)])

        self.session.commit()

    def top_entities(self, n: int = 20) -> list[tuple[str, float]]:
        """Le N entità con maggiore connessione totale."""
        totals: dict[str, float] = defaultdict(float)
        for (a, _), w in self._weights.items():
            totals[a] += w
        return sorted(totals.items(), key=lambda x: x[1], reverse=True)[:n]

    def neighbors(self, name: str) -> list[tuple[str, float]]:
        if self._graph is None:
            return [(b, w) for (a, b), w in self._weights.items() if a == name]
        if name not in self._graph:
            return []
        return [(nb, self._graph[name][nb].get("weight", 1.0))
                for nb in self._graph.neighbors(name)]
