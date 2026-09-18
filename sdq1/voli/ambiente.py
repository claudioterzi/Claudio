"""Ambiente e segreti per la caccia voli.

`python -m sdq1.voli` non passa da `sdq1/__main__.py` (che carica il .env), quindi
qui carichiamo il .env da soli. `sdq1.notifiche.invia` di main legge poi
TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID dall'ambiente.
"""

from __future__ import annotations

import os
from pathlib import Path


def carica_env() -> None:
    """Carica un `.env` dalla root del repo, se presente (l'ambiente vince)."""
    root = Path(__file__).resolve().parent.parent.parent  # .../Claudio
    env = root / ".env"
    if not env.is_file():
        return
    try:
        for riga in env.read_text(encoding="utf-8").splitlines():
            riga = riga.strip()
            if not riga or riga.startswith("#") or "=" not in riga:
                continue
            chiave, _, valore = riga.partition("=")
            chiave = chiave.strip()
            valore = valore.strip().strip('"').strip("'")
            if chiave and chiave not in os.environ:
                os.environ[chiave] = valore
    except OSError:
        pass


def telegram_pronto() -> bool:
    """True se i segreti Telegram sono disponibili nell'ambiente."""
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


# Carica il .env al primo import del package voli.
carica_env()
