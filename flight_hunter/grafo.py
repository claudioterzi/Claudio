"""Il grafo — la rete della fonte esplorata con Dijkstra pigro.

Non si cercano voli: si costruisce il grafo dei collegamenti e si cerca il
percorso a costo minimo. La rete NON viene scaricata tutta (200 aeroporti =
200 richieste): un nodo si espande — una richiesta di mappa tariffe — solo
quando la frontiera più economica lo raggiunge. Dijkstra decide quali
richieste fare: è la potatura portata al livello del grafo.

Gli archi sono le tariffe minime del mese; ogni coincidenza aggiunge una
penalità stimata (rischio + probabile notte). I percorsi trovati sono
CANDIDATI: il motore li verifica poi sui calendari con gli orari reali.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass

from .aeroporti import Aeroporto
from .costi import ParametriCosto, costo_terra
from .fonti import Fonte

PENALITA_TRATTA = 25.0   # € stimati per coincidenza (margine rischio + mezza notte)


@dataclass(frozen=True)
class Percorso:
    scali: tuple[str, ...]   # sequenza IATA, estremi inclusi
    stima: float             # tariffe minime + penalità + terra iniziale

    def __str__(self) -> str:
        return " → ".join(self.scali) + f"  (~{self.stima:.0f}€ stimati)"


def esplora(origini: list[tuple[Aeroporto, float]], desti: set[str],
            dal: str, al: str, fonte: Fonte,
            parametri: ParametriCosto | None = None,
            max_espansioni: int = 18, max_tratte: int = 3,
            top: int = 6) -> list[Percorso]:
    """Percorsi a costo minimo stimato dalle origini a una delle destinazioni.

    max_espansioni limita le richieste HTTP (una per nodo espanso).
    Aeroporti fuori dal database curato restano attraversabili: per il grafo
    serve solo il codice, non le coordinate.
    """
    p = parametri or ParametriCosto()
    mappe: dict[str, dict[str, float]] = {}

    def mappa_di(iata: str) -> dict[str, float]:
        if iata not in mappe:
            mappe[iata] = fonte.mappa_tariffe(iata, dal, al)
        return mappe[iata]

    heap: list[tuple[float, int, str, tuple[str, ...]]] = []
    migliori: dict[tuple[str, int], float] = {}
    for a, km in origini:
        costo = costo_terra(km, p)
        heapq.heappush(heap, (costo, 0, a.iata, (a.iata,)))
        migliori[(a.iata, 0)] = costo

    risultati: list[Percorso] = []
    visti: set[tuple[str, ...]] = set()

    while heap and len(risultati) < top:
        stima, tratte, iata, percorso = heapq.heappop(heap)
        if stima > migliori.get((iata, tratte), float("inf")):
            continue

        if iata in desti and tratte > 0:
            if percorso not in visti:
                visti.add(percorso)
                risultati.append(Percorso(percorso, round(stima, 2)))
            continue

        if tratte >= max_tratte:
            continue
        if iata not in mappe and len(mappe) >= max_espansioni:
            continue

        for arrivo, prezzo in mappa_di(iata).items():
            if arrivo in percorso:          # niente cicli
                continue
            penalita = PENALITA_TRATTA if tratte > 0 else 0.0
            nuova = stima + prezzo + penalita
            chiave = (arrivo, tratte + 1)
            if nuova < migliori.get(chiave, float("inf")):
                migliori[chiave] = nuova
                heapq.heappush(heap, (nuova, tratte + 1, arrivo, percorso + (arrivo,)))

    return risultati
