"""Mappatura comandi → azioni R3.

Traduce comandi operativi (anche da shell, es. `pytest -q`) nel rito R³∞
corrispondente. È il ponte tra il gesto quotidiano e il livello semantico.
"""
from __future__ import annotations

from .triggers import REGISTRO

# Comando testuale → nome del rito nel REGISTRO.
COMANDI: dict[str, str] = {
    "pytest -q": "Updater",     # verificare = ri-sincronizzare lo stato
    "rosso": "Rosso",
    "raffaello": "Raffaello",
    "updater": "Updater",
    "applica": "Applica",
    "git push": "Applica",      # pushare = applicare in modo inevitabile
}


def risolvi(comando: str) -> str | None:
    """Ritorna il nome del rito per un comando, o None se non mappato."""
    return COMANDI.get(comando.strip().lower())


def mappa_completa() -> dict[str, str]:
    """Solo i comandi che puntano a riti realmente registrati."""
    return {cmd: rito for cmd, rito in COMANDI.items() if rito in REGISTRO}
