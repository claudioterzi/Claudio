"""Legge le risposte di Claudio arrivate da Telegram (bot/inbox.jsonl).

Lato progetto: usato a ogni «avanza» per vedere cosa Claudio ha risposto sul
bot. Un puntatore (`bot/.inbox_letti`) ricorda quante voci sono già state lette,
così mostra solo le NUOVE — e il puntatore, committato, sopravvive tra sessioni.

    python -m bot.leggi_inbox          # mostra solo le risposte nuove
    python -m bot.leggi_inbox --tutto  # mostra tutto lo storico
    python -m bot.leggi_inbox --segna  # segna come lette le nuove (aggiorna il puntatore)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_BOT = Path(__file__).resolve().parent
INBOX = _BOT / "inbox.jsonl"
PUNTATORE = _BOT / ".inbox_letti"


def _voci() -> list[dict]:
    if not INBOX.exists():
        return []
    out = []
    for riga in INBOX.read_text(encoding="utf-8").splitlines():
        riga = riga.strip()
        if riga:
            try:
                out.append(json.loads(riga))
            except json.JSONDecodeError:
                pass
    return out


def _letti() -> int:
    try:
        return int(PUNTATORE.read_text().strip())
    except (OSError, ValueError):
        return 0


def main(argv: list[str]) -> int:
    args = argv[1:]
    voci = _voci()
    letti = 0 if "--tutto" in args else _letti()
    nuove = voci[letti:]

    if not voci:
        print("Inbox vuota. (Nessuna risposta da Telegram, o il ponte non ha ancora pushato.)")
        return 0
    if not nuove and "--tutto" not in args:
        print(f"Nessuna risposta nuova. ({len(voci)} totali, già lette.)")
        return 0

    etichetta = "TUTTE le risposte" if "--tutto" in args else "Risposte NUOVE da Claudio (Telegram)"
    print(f"=== {etichetta}: {len(nuove)} ===")
    for v in nuove:
        print(f"[{v.get('ts','?')}] {v.get('testo','')}")

    if "--segna" in args:
        PUNTATORE.write_text(str(len(voci)), encoding="utf-8")
        print(f"\n(segnate come lette: puntatore = {len(voci)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
