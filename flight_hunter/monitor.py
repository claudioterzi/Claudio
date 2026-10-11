"""Monitor 24/7 — la «versione evoluta»: gira, salva i minimi, avvisa.

Uso:
    python3 -m flight_hunter.monitor cacce.json [--intervallo 3600]

cacce.json:
    [
      {"origine": "MXP", "destinazione": "TIA", "mese": "2026-09"},
      {"origine": "Roma", "destinazione": "Marrakech", "mese": "2026-10", "bagaglio": true}
    ]

Avvisi: stampa su stdout sempre; se FLIGHT_HUNTER_WEBHOOK è impostata,
POSTa il messaggio in JSON ({"text": ...} — compatibile Slack/Discord/ntfy).

Va eseguito su una macchina sempre accesa (Raspberry, VPS, PC): il deploy
Vercel del progetto è serverless e non può tenere un processo vivo.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime

from .fonti import FonteRyanair
from .memoria import Memoria
from .motore import caccia

import os


def _avvisa(messaggio: str) -> None:
    print(messaggio, flush=True)
    webhook = os.environ.get("FLIGHT_HUNTER_WEBHOOK")
    if not webhook:
        return
    try:
        req = urllib.request.Request(
            webhook,
            data=json.dumps({"text": messaggio}).encode(),
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except OSError as e:
        print(f"(webhook non raggiungibile: {e})", file=sys.stderr)


def un_giro(cacce: list[dict], memoria: Memoria) -> None:
    for c in cacce:
        rotta = f"{c['origine'].upper()}-{c['destinazione'].upper()}"
        try:
            risultati = caccia(
                c["origine"], c["destinazione"], c["mese"],
                bagaglio=bool(c.get("bagaglio", False)),
                raggio_origine=float(c.get("raggio", 250)),
                top=1,
                fonte=FonteRyanair(),   # fonte nuova a ogni giro: cache fresca
            )
        except Exception as e:  # noqa: BLE001 — il monitor non deve mai morire
            print(f"[{rotta}] errore: {e}", file=sys.stderr)
            continue
        if not risultati:
            print(f"[{rotta} {c['mese']}] nessuna copertura dalle fonti attive "
                  "(rotta non servita o schedule non ancora pubblicato)", file=sys.stderr)
            continue
        migliore = risultati[0]
        vecchio = memoria.registra(rotta, c["mese"], migliore.voli[0].giorno, migliore.totale)
        if vecchio == float("inf"):
            _avvisa(f"[{rotta} {c['mese']}] prima rilevazione: {migliore.totale:.2f}€ "
                    f"({migliore.tipo}, {migliore.voli[0].giorno})")
        elif vecchio is not None:
            consiglio = memoria.consiglio(rotta, c["mese"], migliore.totale)
            _avvisa(f"★ [{rotta} {c['mese']}] NUOVO MINIMO {migliore.totale:.2f}€ "
                    f"(era {vecchio:.2f}€) — {migliore.tipo}, {migliore.voli[0].giorno}. "
                    f"Consiglio: {consiglio.azione.upper()} — {consiglio.motivo}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="flight_hunter.monitor")
    ap.add_argument("config", help="file JSON con la lista delle cacce")
    ap.add_argument("--intervallo", type=int, default=3600,
                    help="secondi tra un giro e l'altro (default 3600 = 1h)")
    ap.add_argument("--una-volta", action="store_true", help="un giro solo, poi esci")
    args = ap.parse_args(argv)

    with open(args.config, encoding="utf-8") as f:
        cacce = json.load(f)

    memoria = Memoria()
    while True:
        print(f"— giro delle {datetime.now():%H:%M:%S} ({len(cacce)} cacce) —", flush=True)
        un_giro(cacce, memoria)
        if args.una_volta:
            return 0
        time.sleep(args.intervallo)


if __name__ == "__main__":
    sys.exit(main())
