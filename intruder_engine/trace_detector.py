"""Modulo 3 — TRACE DETECTOR.

Rileva ricorrenze, convergenze, anomalie, accelerazioni.
Wrappa sdq1/sar/rilevatore_intruso.py per input reale.
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# Importa il rilevatore base se disponibile
_RILEVATORE_PATH = Path(__file__).parent.parent / "sdq1" / "sar"
if str(_RILEVATORE_PATH) not in sys.path:
    sys.path.insert(0, str(_RILEVATORE_PATH.parent.parent))

try:
    from sdq1.sar.rilevatore_intruso import Evento, RilevatorIntruso, Traccia
    _BASE_AVAILABLE = True
except ImportError:
    _BASE_AVAILABLE = False


def detect_recurrences(
    contents: list[tuple[str, str]],  # (source, text)
    min_count: int = 3,
    top_n: int = 20,
) -> list[tuple[str, int, set[str]]]:
    """Conta termini ricorrenti su più fonti.

    Returns: lista di (termine, conteggio, fonti) ordinata per frequenza.
    """
    term_counts: Counter[str] = Counter()
    term_sources: dict[str, set[str]] = defaultdict(set)

    for source, text in contents:
        words = text.lower().split()
        seen_in_doc: set[str] = set()
        for word in words:
            word = word.strip(".,;:!?\"'()")
            if len(word) > 4:  # filtra stopwords brevi
                term_counts[word] += 1
                term_sources[word].add(source)
                seen_in_doc.add(word)

    results = [
        (term, count, term_sources[term])
        for term, count in term_counts.most_common(top_n * 3)
        if count >= min_count and len(term_sources[term]) > 1
    ]
    return sorted(results, key=lambda x: x[1], reverse=True)[:top_n]


def detect_with_base_rilevatore(
    eventi: list[Any],
    temi_attivi: list[str],
    soglia: int = 21,
) -> list[Any]:
    """Usa il RilevatorIntruso base di SDQ-1 se disponibile."""
    if not _BASE_AVAILABLE:
        return []
    rilevatore = RilevatorIntruso(temi_attivi=temi_attivi)
    return rilevatore.analizza(eventi, soglia_minima=soglia)
