"""Modello del costo REALE — dove i comparatori barano per omissione.

Il prezzo del biglietto è solo una parte. Qui si sommano: bagagli, tratte via
terra per il posizionamento, notti forzate, e un margine di rischio per i
self-transfer (biglietti separati = nessuna protezione se perdi la coincidenza).
Tutte stime prudenziali, parametrizzabili.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParametriCosto:
    bagaglio_stiva: float = 30.0      # € per tratta-biglietto low cost
    notte: float = 35.0               # € ostello/guesthouse per notte forzata
    terra_eur_km: float = 0.09        # € al km per bus/treno regionale
    terra_minimo: float = 8.0         # € minimo di una tratta via terra
    margine_self_transfer: float = 15.0  # € accantonati per ogni coincidenza fai-da-te
    ore_minime_scalo: float = 3.0     # sotto questa soglia il rischio sale


def costo_terra(km: float, p: ParametriCosto = ParametriCosto()) -> float:
    """Stima bus/treno per il posizionamento verso un altro aeroporto."""
    if km < 1:
        return 0.0
    return round(max(p.terra_minimo, km * p.terra_eur_km), 2)


def ore_terra(km: float) -> float:
    """Tempo stimato del trasferimento via terra (media 75 km/h porta a porta)."""
    return round(km / 75.0, 1) if km >= 1 else 0.0
