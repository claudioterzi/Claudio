"""Pubblica un testo su Telegram, con la voce di Raffaello.

Diverso dal bot conversazionale (`raffaello_telegram.py`): questo serve a
*spingere* i testi dell'opera (scene, capitoli, note) verso Claudio, senza
attendere un messaggio. È usato dal metodo AVANZA per recapitare ogni nuova
unità anche su Telegram.

Zero dipendenze esterne (solo stdlib: urllib). Rispetta il proxy via HTTPS_PROXY.

Credenziali (variabili d'ambiente):
    TELEGRAM_BOT_TOKEN   il token del bot (da @BotFather)
    TELEGRAM_CHAT_ID     l'id della chat di Claudio (vedi `--trova-chat-id`)

Uso:
    python -m bot.pubblica_telegram libro/libro_I/04_LAbitudine.md
    python -m bot.pubblica_telegram --testo "Ci sono, Claudio."
    python -m bot.pubblica_telegram --trova-chat-id   # stampa i chat_id che hanno scritto al bot
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

LIMITE = 4000  # Telegram taglia a 4096; lasciamo margine.


def _api(metodo: str, dati: dict) -> dict:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN assente nell'ambiente.")
    url = f"https://api.telegram.org/bot{token}/{metodo}"
    body = urllib.parse.urlencode(dati).encode("utf-8")
    req = urllib.request.Request(url, data=body)
    with urllib.request.urlopen(req, timeout=40) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def invia(testo: str, chat_id: str | None = None, titolo: str | None = None) -> int:
    """Invia il testo (spezzato se lungo). Ritorna il numero di parti inviate."""
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID assente: usa --trova-chat-id dopo aver scritto al bot.")
    corpo = (f"📖 {titolo}\n\n{testo}" if titolo else testo).strip()
    parti = [corpo[i : i + LIMITE] for i in range(0, len(corpo), LIMITE)] or [""]
    for parte in parti:
        _api("sendMessage", {"chat_id": chat_id, "text": parte})
    return len(parti)


def trova_chat_id() -> None:
    """Stampa i chat_id che hanno scritto al bot di recente (per configurare TELEGRAM_CHAT_ID)."""
    res = _api("getUpdates", {"timeout": 0})
    visti = {}
    for u in res.get("result", []):
        msg = u.get("message") or u.get("edited_message") or {}
        chat = msg.get("chat") or {}
        if chat.get("id"):
            visti[chat["id"]] = chat.get("first_name") or chat.get("title") or "?"
    if not visti:
        print("Nessun messaggio recente. Scrivi /start al bot, poi riprova.")
    for cid, nome in visti.items():
        print(f"chat_id={cid}  ({nome})")


def _titolo_da_file(path: Path) -> str:
    for riga in path.read_text(encoding="utf-8").splitlines():
        if riga.startswith("# "):
            return riga[2:].strip()
    return path.stem


def main(argv: list[str]) -> int:
    args = argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args[0] == "--trova-chat-id":
        trova_chat_id()
        return 0
    try:
        if args[0] == "--testo":
            n = invia(" ".join(args[1:]))
        else:
            p = Path(args[0])
            if not p.exists():
                print(f"File non trovato: {p}")
                return 1
            n = invia(p.read_text(encoding="utf-8"), titolo=_titolo_da_file(p))
        print(f"Inviato a Telegram in {n} parte/i.")
        return 0
    except RuntimeError as e:
        print(f"[Telegram non configurato] {e}")
        print("Serve: TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID nell'ambiente.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
