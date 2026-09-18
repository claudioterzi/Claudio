"""Configurazione da variabili d'ambiente. Nessun segreto in codice."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

TELEGRAM_BOT_TOKEN = (
    os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    or os.getenv("BOT_TOKEN", "").strip()
)
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "protocollo.db"))
PERSISTENCE_PATH = os.getenv(
    "PERSISTENCE_PATH", str(BASE_DIR / "protocollo.persistence")
)
CONVERSATION_TIMEOUT = int(os.getenv("CONVERSATION_TIMEOUT", "1800"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Ponte verso SDQ-1 a sei agenti, quando esiste.
# Vuota = risponde il nucleo locale (classificatore del Protocollo).
# Piena = /ask inoltra al motore esterno; se il ponte cade, lo dichiara.
SDQ1_URL = os.getenv("SDQ1_URL", "").strip()
SDQ1_TIMEOUT = float(os.getenv("SDQ1_TIMEOUT", "8"))

# Network Event v1 (twin Supereroe) — never gates crisis / anti-×3.
NODE_ID = (os.getenv("NODE_ID") or "protocollo-rosso").strip() or "protocollo-rosso"
NETWORK_SECRET = os.getenv("NETWORK_SECRET", "").strip()
NETWORK_PEERS = os.getenv("NETWORK_PEERS", "").strip()


def require_token() -> str:
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN.startswith("123456789"):
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN mancante o di esempio. "
            "Copia .env.example in .env e incolla il token di @BotFather."
        )
    return TELEGRAM_BOT_TOKEN
