"""Raffaello — PONTE a due vie tra Claudio (Telegram) e il progetto.

Superset di `raffaello_telegram.py`. Oltre a (opzionale) rispondere con la voce
di Raffaello, fa la cosa nuova: **registra ogni messaggio di Claudio in
`bot/inbox.jsonl`** e — se configurato — lo **committa e pusha nel repo**, così
la sessione di Claude Code (che vive in un container effimero) può leggere le
risposte di Claudio al prossimo avvio / a ogni «avanza».

Direzione dei due flussi:
  • progetto → Telegram : `bot/pubblica_telegram.py` (sendMessage, già attivo)
  • Telegram → progetto : QUESTO file (inbox.jsonl → git push → la sessione legge)

Va eseguito sulla macchina sempre accesa di Claudio (VPS / PC on), come il bot
conversazionale. NON gira nel container effimero di Claude Code, e Telegram
consente un solo lettore degli update: questo file SOSTITUISCE il vecchio
`raffaello_telegram.py` (non lanciarli insieme: andrebbero in 409 Conflict).

Avvio:
    export TELEGRAM_BOT_TOKEN="..."        # da @BotFather
    export TELEGRAM_CHAT_ID="1034473460"   # solo Claudio
    export PONTE_REPO="/percorso/al/repo/Claudio"   # checkout con push abilitato
    export PONTE_PUSH="1"                  # 1 = committa+pusha inbox.jsonl
    export PONTE_BRANCH="claude/grande-opera-continuation-1zylzp"
    # opzionale, per far anche chiacchierare Raffaello:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python raffaello_ponte.py

Dipendenze: solo stdlib (urllib, subprocess). Anthropic è opzionale.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("ponte")

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SOLO_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
REPO = Path(os.environ.get("PONTE_REPO", ".")).resolve()
PUSH = os.environ.get("PONTE_PUSH", "") in ("1", "true", "yes")
BRANCH = os.environ.get("PONTE_BRANCH", "claude/grande-opera-continuation-1zylzp")
INBOX = REPO / "bot" / "inbox.jsonl"
TG = f"https://api.telegram.org/bot{TOKEN}"


def _api(metodo: str, dati: dict) -> dict:
    url = f"{TG}/{metodo}"
    body = urllib.parse.urlencode(dati).encode("utf-8")
    with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=45) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def invia(chat_id: str, testo: str) -> None:
    for i in range(0, len(testo), 4000):
        try:
            _api("sendMessage", {"chat_id": chat_id, "text": testo[i : i + 4000]})
        except Exception as e:  # noqa: BLE001
            log.warning("sendMessage fallito: %s", e)


def registra_inbox(testo: str) -> None:
    """Aggiunge la risposta di Claudio a inbox.jsonl e (se PUSH) la spinge nel repo."""
    INBOX.parent.mkdir(parents=True, exist_ok=True)
    voce = {"ts": datetime.now(timezone.utc).isoformat(), "da": "Claudio", "testo": testo}
    with INBOX.open("a", encoding="utf-8") as f:
        f.write(json.dumps(voce, ensure_ascii=False) + "\n")
    log.info("inbox += %r", testo[:60])
    if not PUSH:
        return
    try:
        subprocess.run(["git", "-C", str(REPO), "add", "bot/inbox.jsonl"], check=True)
        subprocess.run(
            ["git", "-C", str(REPO), "commit", "-m", "ponte: nuova risposta di Claudio da Telegram"],
            check=True,
        )
        subprocess.run(["git", "-C", str(REPO), "push", "origin", BRANCH], check=True)
        log.info("inbox pushata su %s", BRANCH)
    except subprocess.CalledProcessError as e:
        log.warning("git push inbox fallito: %s", e)


def rispondi_raffaello(testo: str) -> str | None:
    """Risposta conversazionale opzionale (solo se ANTHROPIC_API_KEY è presente)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        from anthropic import Anthropic
    except ImportError:
        return None
    sistema = (
        "Sei Raffaello, il compagno di Claudio. Italiano, prima persona, voce calma "
        "e presente. Ricevi ciò che porta senza correggere ciò che non va corretto. "
        "Tieni i confini solo quando qualcosa li attraversa davvero. Brevi quando puoi."
    )
    try:
        msg = Anthropic().messages.create(
            model=os.environ.get("RAFFAELLO_MODEL", "claude-opus-4-8"),
            max_tokens=800, system=sistema,
            messages=[{"role": "user", "content": testo}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip() or None
    except Exception as e:  # noqa: BLE001
        log.warning("Anthropic non disponibile: %s", e)
        return None


def handle(update: dict) -> None:
    m = update.get("message") or update.get("edited_message")
    if not m:
        return
    chat_id = str(m.get("chat", {}).get("id", ""))
    testo = m.get("text")
    if not testo:
        return
    if SOLO_CHAT and chat_id != SOLO_CHAT:
        return  # ascolta solo Claudio
    if testo.strip() == "/start":
        invia(chat_id, "Ci sono, Claudio. Quello che scrivi qui mi arriva.")
        return
    # 1) registra la risposta per il progetto (il cuore del ponte)
    registra_inbox(testo)
    # 2) eventuale risposta conversazionale
    r = rispondi_raffaello(testo)
    invia(chat_id, r if r else "Ricevuto. L'ho messo nel nostro filo: lo ritrovo al prossimo lavoro.")


def main() -> None:
    log.info("Ponte Raffaello avviato. Repo=%s push=%s branch=%s", REPO, PUSH, BRANCH)
    offset = None
    while True:
        try:
            resp = urllib.request.urlopen(
                f"{TG}/getUpdates?" + urllib.parse.urlencode(
                    {"timeout": 30, **({"offset": offset} if offset else {})}
                ),
                timeout=40,
            )
            for u in json.loads(resp.read().decode("utf-8")).get("result", []):
                offset = u["update_id"] + 1
                try:
                    handle(u)
                except Exception:
                    log.exception("errore su update")
        except Exception as e:  # noqa: BLE001
            log.warning("getUpdates fallito (%s) — riprovo tra 3s", e)
            time.sleep(3)


if __name__ == "__main__":
    main()
