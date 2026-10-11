"""Flight Hunter — motore di ricerca del miglior risultato verificabile.

Contratto Raffaello:
    - non si ferma al primo prezzo e non confonde la tariffa nuda con il costo reale;
    - usa solo fonti/API consentite, senza scraping fragile o contrario ai ToS;
    - confronta tutte le fonti attive disponibili;
    - espande in modo intelligente aeroporti vicini, hub, split ticketing e
      posizionamento via terra;
    - valuta tariffa, bagagli, notti, trasferimenti, rischio e — quando noto — tempo;
    - può ottimizzare per costo reale minimo oppure per miglior equilibrio;
    - conserva le osservazioni perché le ricerche future possano migliorare;
    - dichiara sempre il perimetro cercato: “migliore trovato” non significa
      “ottimo globale provato” se una fonte o una combinazione non è osservabile.

Strategie che violano i contratti di trasporto (hidden city, throwaway,
fuel dump) non sono implementate.

Uso:
    from flight_hunter import caccia
    risultati = caccia("MXP", "TIA", "2026-09", bagaglio=False)

    # CLI: python3 -m flight_hunter MXP TIA --mese 2026-09
"""
from .aeroporti import AEROPORTI, cerca_aeroporto, piu_vicino, vicini
from .categorie import CATEGORIE, tipi_di
from .costi import ParametriCosto
from .fonti import FonteKiwi, FonteRyanair, FonteTravelpayouts, fonti_disponibili
from .memoria import Memoria
from .motore import Itinerario, MetaPossibile, caccia, occasioni, ovunque
from .oracolo import Responso, consulta

__all__ = [
    "AEROPORTI", "cerca_aeroporto", "piu_vicino", "vicini",
    "CATEGORIE", "tipi_di",
    "ParametriCosto", "FonteRyanair", "FonteKiwi", "FonteTravelpayouts",
    "fonti_disponibili", "Memoria",
    "Itinerario", "MetaPossibile", "caccia", "occasioni", "ovunque",
    "Responso", "consulta",
]
