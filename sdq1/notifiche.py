"""Notifiche Telegram — bot Raffaello (SDQ-1).

Invia "note" nella chat Telegram di Claudio. Una nota = un messaggio che resta
nella chat come registro consultabile.

Segreti (mai in chiaro, letti solo dall'ambiente):
  TELEGRAM_BOT_TOKEN — token del bot (@BotFather)
  TELEGRAM_CHAT_ID   — id della chat di destinazione

Uso:
    from sdq1.notifiche import invia
    invia("🗒️ <b>Nota</b>\\n\\nContenuto.")

`invia()` restituisce True se l'invio è riuscito. Se i segreti non sono
configurati, non solleva: logga un avviso e restituisce False (così gli agenti
girano anche in dry-run senza credenziali).
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from pathlib import Path

log = logging.getLogger("sdq1.notifiche")

_API = "https://api.telegram.org/bot{token}/sendMessage"


def _carica_env() -> None:
    """Carica un file `.env` dalla root del repo, se presente.

    Legge solo chiavi non già impostate nell'ambiente (l'ambiente vince sempre).
    Nessuna dipendenza esterna, formato KEY=VALORE, righe `#` ignorate.
    """
    root = Path(__file__).resolve().parent.parent  # .../Claudio
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


_carica_env()


def configurato() -> bool:
    """True se token e chat_id sono presenti nell'ambiente."""
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def invia(testo: str, *, parse_mode: str = "HTML", timeout: float = 10.0) -> bool:
    """Invia una nota alla chat Telegram. Ritorna True se ok.

    Non solleva per credenziali mancanti o errori di rete: logga e ritorna False.
    """
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat:
        log.warning("Telegram non configurato (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID assenti) — nota non inviata.")
        return False

    payload = json.dumps(
        {"chat_id": chat, "text": testo, "parse_mode": parse_mode, "disable_web_page_preview": False}
    ).encode()
    req = urllib.request.Request(
        _API.format(token=token),
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ok = json.loads(r.read()).get("ok", False)
            if not ok:
                log.error("Telegram ha rifiutato la nota.")
            return bool(ok)
    except Exception as exc:  # rete, timeout, HTTP error
        log.error("Invio nota Telegram fallito: %s", exc)
        return False


if __name__ == "__main__":  # smoke test manuale
    import sys

    testo = " ".join(sys.argv[1:]) or "🗒️ <b>Nota di prova</b>\n\nsdq1.notifiche funziona. #nota #test"
    print("configurato:", configurato())
    print("inviata:", invia(testo))
