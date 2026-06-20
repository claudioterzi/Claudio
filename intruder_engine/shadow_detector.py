"""Modulo 7 — SHADOW DETECTOR.

Non cerca ciò che appare. Cerca ciò che scompare.

Legge la frequenza storica di ogni entità e segnala quelle
che sono cadute sotto la soglia dopo essere state attive.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .db import Event, Session


@dataclass
class Absence:
    entity:          str
    days_absent:     int
    last_seen:       str
    historical_freq: float   # occorrenze/giorno nel periodo attivo
    score:           float   # 0.0–1.0 (quanto è anomala l'assenza)

    def __str__(self) -> str:
        return (
            f"'{self.entity}' assente da {self.days_absent} giorni "
            f"(ultima occorrenza: {self.last_seen[:10]}, "
            f"freq. storica: {self.historical_freq:.1f}/giorno)"
        )


class ShadowDetector:
    """Rileva entità che erano attive e sono scomparse."""

    def __init__(self, session: Session, absence_threshold_days: int = 14):
        self.session = session
        self.threshold = absence_threshold_days

    def detect(
        self,
        tracked_entities: list[str],
        lookback_days: int = 90,
    ) -> list[Absence]:
        """
        Per ogni entità tracciata, controlla se è assente da più di
        `threshold` giorni rispetto alla sua frequenza storica.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=lookback_days)
        absences: list[Absence] = []

        events = (
            self.session.query(Event)
            .filter(Event.timestamp >= cutoff.isoformat())
            .all()
        )
        content_all = [(e.timestamp, e.content.lower()) for e in events]

        for entity in tracked_entities:
            term = entity.lower()
            occurrences = [
                ts for ts, content in content_all if term in content
            ]
            if not occurrences:
                continue

            occurrences.sort()
            last_ts = occurrences[-1]
            last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            days_absent = (now - last_dt).days

            if days_absent < self.threshold:
                continue

            active_days = max(1, (last_dt - cutoff).days)
            freq = len(occurrences) / active_days

            score = min(1.0, days_absent / (self.threshold * 3) * freq)

            absences.append(Absence(
                entity=entity,
                days_absent=days_absent,
                last_seen=last_ts,
                historical_freq=round(freq, 2),
                score=round(score, 2),
            ))

        return sorted(absences, key=lambda a: a.score, reverse=True)
