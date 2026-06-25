"""Modulo 4 — INTRUSION SCORE.

Formula pesata V2:
    INTRUSION SCORE = (
        Anomaly      × 0.25
      + Repetition   × 0.20
      + Independence × 0.20
      + Relevance    × 0.20
      + Convergence  × 0.15
    ) × 100

La formula pesata evita che un singolo fattore zero azzeri lo score intero.
"""

from __future__ import annotations

from dataclasses import dataclass

WEIGHTS = {
    "anomaly":      0.25,
    "repetition":   0.20,
    "independence": 0.20,
    "relevance":    0.20,
    "convergence":  0.15,
}

CLASSES = {
    (0,  20):  "Rumore",
    (21, 40):  "Pattern Debole",
    (41, 60):  "Traccia Interessante",
    (61, 80):  "Forte Convergenza",
    (81, 100): "Evento Intruso",
}


@dataclass
class IntrusionScore:
    anomaly:      float  # 0.0–1.0
    repetition:   float
    independence: float
    relevance:    float
    convergence:  float

    @property
    def score(self) -> int:
        raw = (
            self.anomaly      * WEIGHTS["anomaly"]
          + self.repetition   * WEIGHTS["repetition"]
          + self.independence * WEIGHTS["independence"]
          + self.relevance    * WEIGHTS["relevance"]
          + self.convergence  * WEIGHTS["convergence"]
        )
        return min(100, int(raw * 100))

    @property
    def classification(self) -> str:
        s = self.score
        for (lo, hi), label in CLASSES.items():
            if lo <= s <= hi:
                return label
        return "Rumore"

    def __str__(self) -> str:
        return (
            f"{self.score}/100 — {self.classification} "
            f"[A={self.anomaly:.2f} R={self.repetition:.2f} "
            f"I={self.independence:.2f} Rv={self.relevance:.2f} "
            f"C={self.convergence:.2f}]"
        )
