"""sdq1.voli — Caccia autonoma agli errori di prezzo voli.

Agenti (Protocollo Rosso Rosso Rosso) che interrogano direttamente il motore di
prenotazione, valutano i prezzi contro soglie per rotta, e scrivono note su
Telegram quando trovano error fare o promo forti.

  ScoutVoli       → cerca il prezzo reale di una rotta (motore Node/Playwright)
  ValutatoreVoli  → classifica: error_fare / promo_forte / normale
  CronistaVoli    → invia la nota su Telegram (o dry-run)
  Cacciatore      → orchestratore su una matrice di rotte
"""

from .agenti import CronistaVoli, EsitoScout, ScoutVoli, ValutatoreVoli, Valutazione
from .caccia import Cacciatore, RisultatoCaccia
from .rotte import ROTTE, Rotta, rotte_per_tag

__all__ = [
    "ScoutVoli",
    "EsitoScout",
    "ValutatoreVoli",
    "Valutazione",
    "CronistaVoli",
    "Cacciatore",
    "RisultatoCaccia",
    "ROTTE",
    "Rotta",
    "rotte_per_tag",
]
