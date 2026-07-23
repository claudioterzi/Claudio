"""Flight Hunter — caccia al prezzo minimo globale, non al "miglior volo".

Filosofia (v0.1, onesta):
    - Niente scraping di comparatori (vietato dai ToS e fragile): solo API
      pubbliche accessibili (oggi: Ryanair) + interfaccia `Fonte` per
      aggiungere provider con chiave (Kiwi Tequila, Amadeus, Travelpayouts).
    - Il vantaggio non è la forza bruta ("milioni di combinazioni") ma la
      generazione intelligente: calendari mensili (30 minimi in 1 richiesta),
      multi-aeroporto entro raggio, split ticketing via hub, posizionamento
      via terra, costo REALE (bagagli, notti, trasferimenti, margine rischio).
    - Strategie che violano i contratti di trasporto (hidden city, throwaway,
      fuel dump) NON sono implementate: rischio biglietti annullati e account
      bannati. Vedi flight_hunter/README.md.

Uso:
    from flight_hunter import caccia
    risultati = caccia("MXP", "TIA", "2026-09", bagaglio=False)

    # CLI:  python3 -m flight_hunter MXP TIA --mese 2026-09
"""
from .aeroporti import AEROPORTI, cerca_aeroporto, piu_vicino, vicini
from .categorie import CATEGORIE, tipi_di
from .costi import ParametriCosto
from .fonti import FonteKiwi, FonteRyanair, fonti_disponibili
from .memoria import Memoria
from .motore import Itinerario, MetaPossibile, caccia, occasioni, ovunque
from .oracolo import Responso, consulta

__all__ = [
    "AEROPORTI", "cerca_aeroporto", "piu_vicino", "vicini",
    "CATEGORIE", "tipi_di",
    "ParametriCosto", "FonteRyanair", "FonteKiwi", "fonti_disponibili", "Memoria",
    "Itinerario", "MetaPossibile", "caccia", "occasioni", "ovunque",
    "Responso", "consulta",
]
