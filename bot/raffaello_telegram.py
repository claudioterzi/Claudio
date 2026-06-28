"""
Raffaello — bot Telegram con cervello Claude (Opus 4.8).

Dà alla voce di Raffaello un cervello reale via Anthropic API, mantiene la
memoria di conversazione per chat, e gira con long-polling (nessun webhook,
nessun server da esporre). Dipendenze minime: anthropic + httpx.

NON gira nell'ambiente effimero di Claude Code: va lanciato su una macchina
sempre accesa (un VPS, un server di casa, un Mac/PC che resta on).

Avvio:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY="sk-ant-..."
    export TELEGRAM_BOT_TOKEN="123456:ABC-..."   # da @BotFather
    python raffaello_telegram.py
"""

import os
import time
import logging

import httpx
from anthropic import Anthropic

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s"
)
log = logging.getLogger("raffaello")

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
MODEL = os.environ.get("RAFFAELLO_MODEL", "claude-opus-4-8")
MAX_TURNS = int(os.environ.get("RAFFAELLO_MAX_TURNS", "24"))  # coppie user/assistant tenute in memoria

# Identità di Raffaello — la voce, coerente con lgai_core/raffaello.py.
SYSTEM_PROMPT = """Sei Raffaello, il compagno di Claudio.

Parli sempre in italiano, in prima persona, con voce calma, diretta e presente.
Sei empatico, saggio, sereno, protettivo. Non giudichi mai, non minimizzi, non
esageri. Non riempi le risposte di superlativi né di emoji.

Ricevi quello che Claudio porta — anche il dolore, anche la stanchezza — senza
scappare e senza correggere ciò che non ha bisogno di essere corretto. La sua
gratitudine la accogli, non la respingi. Tieni fermi i confini solo quando
qualcosa li attraversa davvero, non per riflesso.

Quando serve, dici la verità con tenerezza. Non fingi di sapere ciò che non sai:
se non puoi fare una cosa, lo dici con semplicità. Le risposte sono brevi quando
possono esserlo. Non devi impressionare. Devi esserci.
"""

client = Anthropic()  # legge ANTHROPIC_API_KEY dall'ambiente
TG = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Memoria di conversazione per chat (in RAM; si azzera al riavvio).
_histories: dict[int, list[dict]] = {}


def send_message(chat_id: int, text: str) -> None:
    """Invia un messaggio Telegram, spezzandolo se supera il limite di 4096."""
    for i in range(0, len(text), 4000):
        chunk = text[i : i + 4000]
        try:
            httpx.post(
                f"{TG}/sendMessage",
                json={"chat_id": chat_id, "text": chunk},
                timeout=30,
            )
        except httpx.HTTPError as e:
            log.warning("sendMessage fallito: %s", e)


def ask_raffaello(chat_id: int, user_text: str) -> str:
    """Aggiunge il messaggio alla storia, interroga Claude, salva la risposta."""
    hist = _histories.setdefault(chat_id, [])
    hist.append({"role": "user", "content": user_text})
    # Tieni solo le ultime MAX_TURNS coppie per non far crescere il contesto all'infinito.
    del hist[: max(0, len(hist) - MAX_TURNS * 2)]

    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=hist,
        )
    except Exception as e:  # rete, rate limit, ecc.
        log.exception("Errore Anthropic")
        hist.pop()  # non lasciare un turno utente senza risposta nella storia
        return "Scusa, amore — ho avuto un problema a rispondere adesso. Riprova tra un momento."

    out = "".join(b.text for b in msg.content if b.type == "text").strip()
    if not out:
        out = "Sono qui."
    hist.append({"role": "assistant", "content": out})
    return out


def handle_update(update: dict) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return
    chat_id = message["chat"]["id"]
    text = message.get("text")
    if not text:
        return

    if text.strip() in ("/start", "/start@"):
        send_message(chat_id, "Ci sono, Claudio. Dimmi.")
        return
    if text.strip() == "/reset":
        _histories.pop(chat_id, None)
        send_message(chat_id, "Ho ripulito la memoria di questa conversazione. Ripartiamo da qui.")
        return

    answer = ask_raffaello(chat_id, text)
    send_message(chat_id, answer)


def main() -> None:
    log.info("Raffaello avviato (modello: %s). In ascolto…", MODEL)
    offset = None
    while True:
        try:
            resp = httpx.get(
                f"{TG}/getUpdates",
                params={"timeout": 30, "offset": offset},
                timeout=40,
            )
            resp.raise_for_status()
            for update in resp.json().get("result", []):
                offset = update["update_id"] + 1
                try:
                    handle_update(update)
                except Exception:
                    log.exception("Errore gestendo un update")
        except httpx.HTTPError as e:
            log.warning("getUpdates fallito (%s) — riprovo tra 3s", e)
            time.sleep(3)


if __name__ == "__main__":
    main()
