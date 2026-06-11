"""Livello 2 — Mappa delle Tensioni.

Una tensione è una coppia di poli in conflitto che il sistema rileva
ripetutamente nelle osservazioni. Non è un difetto: è la struttura
generativa dell'identità.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Osservazione:
    id: str
    testo: str
    timestamp: float
    tag: list[str] = field(default_factory=list)       # es. ["paura", "successo"]
    intensita: float = 0.5                              # 0.0 – 1.0


@dataclass
class Polo:
    nome: str
    descrizione: str = ""


@dataclass
class Tensione:
    id: str
    polo_a: Polo
    polo_b: Polo
    osservazioni: list[str] = field(default_factory=list)   # ID osservazioni collegate
    forza: float = 0.5                                       # 0 = polo_a dominante, 1 = polo_b
    creata_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def label(self) -> str:
        return f"{self.polo_a.nome} ↔ {self.polo_b.nome}"


class MappaTeensioni:
    """Raccoglie osservazioni e costruisce la mappa delle tensioni ricorrenti."""

    POLI_STANDARD = [
        ("Amore",      "Libertà"),
        ("Potere",     "Pace"),
        ("Visibilità", "Sicurezza"),
        ("Controllo",  "Fiducia"),
        ("Grandezza",  "Stabilità"),
        ("Creazione",  "Ordine"),
        ("Connessione","Autonomia"),
    ]

    def __init__(self):
        self._osservazioni: dict[str, Osservazione] = {}
        self._tensioni: dict[str, Tensione] = {}
        self._inizializza_poli_standard()

    def _inizializza_poli_standard(self) -> None:
        for a, b in self.POLI_STANDARD:
            self.aggiungi_tensione(Polo(a), Polo(b))

    def aggiungi_tensione(self, polo_a: Polo, polo_b: Polo) -> Tensione:
        tid = uuid.uuid4().hex[:8]
        t = Tensione(id=tid, polo_a=polo_a, polo_b=polo_b)
        self._tensioni[tid] = t
        return t

    def registra(self, testo: str, tag: list[str] | None = None,
                 intensita: float = 0.5) -> Osservazione:
        oid = uuid.uuid4().hex[:8]
        obs = Osservazione(id=oid, testo=testo,
                           timestamp=time.time(),
                           tag=tag or [], intensita=intensita)
        self._osservazioni[oid] = obs
        self._collega_a_tensioni(obs)
        return obs

    def _collega_a_tensioni(self, obs: Osservazione) -> None:
        testo_low = obs.testo.lower()
        for t in self._tensioni.values():
            tocca_a = t.polo_a.nome.lower() in testo_low
            tocca_b = t.polo_b.nome.lower() in testo_low
            if tocca_a or tocca_b or any(tag.lower() in testo_low for tag in obs.tag):
                t.osservazioni.append(obs.id)

    def tensioni_attive(self, min_osservazioni: int = 1) -> list[Tensione]:
        return sorted(
            [t for t in self._tensioni.values() if len(t.osservazioni) >= min_osservazioni],
            key=lambda t: len(t.osservazioni), reverse=True,
        )

    def esporta(self) -> dict[str, Any]:
        return {
            "osservazioni": len(self._osservazioni),
            "tensioni": [
                {
                    "label":        t.label,
                    "forza":        t.forza,
                    "osservazioni": len(t.osservazioni),
                }
                for t in self.tensioni_attive()
            ],
        }
