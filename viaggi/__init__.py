"""Viaggi Low Cost — pianificatore di viaggi economici dall'Italia.

Zero dipendenze esterne, come il resto del progetto.

    from viaggi import DESTINAZIONI, pianifica
    proposte = pianifica(budget=300, giorni=4, mese=9, tipo="mare")
"""
from .destinazioni import DESTINAZIONI, Destinazione, MESI, TIPI
from .pianificatore import Proposta, pianifica

__all__ = [
    "DESTINAZIONI",
    "Destinazione",
    "MESI",
    "TIPI",
    "Proposta",
    "pianifica",
]
