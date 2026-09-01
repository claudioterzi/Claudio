"""Matrice di rotte e soglie per la caccia agli errori di prezzo.

Ogni rotta è un viaggio (di norma open-jaw o andata/ritorno) espresso come lista
di tratte. Il campo `soglia_eur` è il prezzo sotto il quale l'offerta è
considerata *notevole* e merita una nota su Telegram. Le soglie sono tarate su
prezzi "pieni" tipici dall'Europa occidentale: se il motore trova qualcosa di
molto più basso, è o una promo forte o una error fare.

Le date sono finestre di esempio: vanno aggiornate/ruotate nel tempo. Il formato
è quello che Google Flights accetta digitato (es. "February 15, 2027").
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rotta:
    id: str
    descrizione: str
    legs: tuple[dict[str, str], ...]
    soglia_eur: int
    tag: tuple[str, ...] = field(default_factory=tuple)


# Hub di partenza preferiti da Claudio: Bruxelles e Parigi (+ hub low-cost
# raggiungibili: Madrid, Lisbona). Destinazioni: Sud America, Brasile, Cuba.
ROTTE: tuple[Rotta, ...] = (
    Rotta(
        id="BRU-GRU-CDG",
        descrizione="Bruxelles → San Paolo, rientro Parigi (open-jaw)",
        legs=(
            {"from": "Brussels", "to": "Sao Paulo", "date": "February 15, 2027"},
            {"from": "Sao Paulo", "to": "Paris", "date": "March 1, 2027"},
        ),
        soglia_eur=400,
        tag=("brasile", "sanpaolo", "open-jaw"),
    ),
    Rotta(
        id="CDG-GRU-CDG",
        descrizione="Parigi ↔ San Paolo (andata/ritorno)",
        legs=(
            {"from": "Paris", "to": "Sao Paulo", "date": "February 15, 2027"},
            {"from": "Sao Paulo", "to": "Paris", "date": "March 1, 2027"},
        ),
        soglia_eur=400,
        tag=("brasile", "sanpaolo"),
    ),
    Rotta(
        id="LIS-GRU-FRA",
        descrizione="Lisbona → San Paolo, rientro Francoforte (rotta-madre error fare Iberia/TAP)",
        legs=(
            {"from": "Lisbon", "to": "Sao Paulo", "date": "February 15, 2027"},
            {"from": "Sao Paulo", "to": "Frankfurt", "date": "March 1, 2027"},
        ),
        soglia_eur=350,
        tag=("brasile", "sanpaolo", "rotta-madre"),
    ),
    Rotta(
        id="BRU-HAV-BRU",
        descrizione="Bruxelles ↔ L'Avana, Cuba",
        legs=(
            {"from": "Brussels", "to": "Havana", "date": "February 10, 2027"},
            {"from": "Havana", "to": "Brussels", "date": "February 24, 2027"},
        ),
        soglia_eur=450,
        tag=("cuba", "havana"),
    ),
    Rotta(
        id="CDG-HAV-CDG",
        descrizione="Parigi ↔ L'Avana, Cuba",
        legs=(
            {"from": "Paris", "to": "Havana", "date": "February 10, 2027"},
            {"from": "Havana", "to": "Paris", "date": "February 24, 2027"},
        ),
        soglia_eur=450,
        tag=("cuba", "havana"),
    ),
    Rotta(
        id="MAD-HAV-MAD",
        descrizione="Madrid ↔ L'Avana (hub low-cost raggiungibile da BRU/CDG)",
        legs=(
            {"from": "Madrid", "to": "Havana", "date": "February 10, 2027"},
            {"from": "Havana", "to": "Madrid", "date": "February 24, 2027"},
        ),
        soglia_eur=380,
        tag=("cuba", "havana", "hub"),
    ),
)


def rotte_per_tag(*tag: str) -> tuple[Rotta, ...]:
    """Filtra le rotte per uno o più tag (OR)."""
    if not tag:
        return ROTTE
    voluti = set(tag)
    return tuple(r for r in ROTTE if voluti & set(r.tag))
