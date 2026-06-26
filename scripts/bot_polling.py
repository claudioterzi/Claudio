"""Bot Raffaello — loop di polling continuo Telegram.

Avvio:
    python scripts/bot_polling.py

Ferma con Ctrl+C.
Polling ogni 5 secondi — legge messaggi, esegue comandi, risponde via Claude.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Aggiungi root del progetto al path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def _carica_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for riga in env_path.read_text(encoding="utf-8").splitlines():
        riga = riga.strip()
        if not riga or riga.startswith("#") or "=" not in riga:
            continue
        chiave, _, valore = riga.partition("=")
        chiave = chiave.strip()
        valore = valore.strip().strip('"').strip("'")
        if chiave and chiave not in os.environ:
            os.environ[chiave] = valore


_TZ = timezone(timedelta(hours=2))


def _ora() -> str:
    return datetime.now(_TZ).strftime("%H:%M:%S")


def main() -> None:
    _carica_dotenv()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN non trovato nel .env — impossibile avviare.")
        sys.exit(1)

    from sdq1.notifiche import esegui_comandi_e_chat, invia

    print(f"[{_ora()}] 🤖 Bot Raffaello — polling avviato (intervallo: 5s)")
    invia(f"🟢 <b>Raffaello online</b>  [{_ora()}]\nSistema SDQ-1 pronto. Scrivi /help per i comandi.")

    while True:
        try:
            n = esegui_comandi_e_chat()
            if n:
                print(f"[{_ora()}] Elaborati {n} messaggi")
        except KeyboardInterrupt:
            print(f"\n[{_ora()}] Bot fermato.")
            invia(f"🔴 <b>Raffaello offline</b>  [{_ora()}]")
            break
        except Exception as e:
            print(f"[{_ora()}] Errore polling: {e}")

        time.sleep(5)


if __name__ == "__main__":
    main()
