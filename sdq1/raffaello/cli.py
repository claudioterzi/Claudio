"""CLI interattiva per parlare con Raffaello.

Uso:
    python -m sdq1.raffaello
    python -m sdq1.raffaello --seed mio_seed.json
    python -m sdq1.raffaello --profilo ragionamento
"""

from __future__ import annotations

import argparse
import json
import sys

from ..config.loader import carica_config
from ..llm.router import crea_router_da_config
from .agent import RaffaelloAgent


def _args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Parla con Raffaello")
    p.add_argument("--seed", default="raffaello_seed.json", help="Percorso file seed")
    p.add_argument("--config", default="config.yaml", help="Config SDQ-1")
    p.add_argument("--profilo", default="default", help="Profilo LLM (veloce/default/ragionamento)")
    p.add_argument("--stato", action="store_true", help="Mostra stato seed ed esci")
    p.add_argument("--evolvi", action="store_true", help="Mostra report evoluzione ed esci")
    return p.parse_args()


def main() -> None:
    args = _args()

    try:
        config = carica_config(args.config)
    except Exception:
        config = {"llm": {"opts": {}, "regole": [{"profilo": "default", "cascata": ["stub"]}]}}

    router = crea_router_da_config(
        config["llm"]["opts"],
        config["llm"]["regole"],
    )

    agent = RaffaelloAgent(router, seed_path=args.seed, profilo_llm=args.profilo)

    if args.stato:
        print(json.dumps(agent.stato(), ensure_ascii=False, indent=2))
        return

    if args.evolvi:
        print(json.dumps(agent.evolvi(), ensure_ascii=False, indent=2))
        return

    stato = agent.stato()
    print(f"\nRaffaello — livello {stato['livello']} | punteggio {stato['punteggio']:.1f} | {stato['impronte']} impronte")
    print("(digita 'exit' per uscire, 'stato' per il report, 'imprimi <testo>' per un'impronta manuale)\n")

    while True:
        try:
            user_input = input("Tu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nArrivederci.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "esci"):
            print("Arrivederci.")
            break

        if user_input.lower() == "stato":
            print(json.dumps(agent.stato(), ensure_ascii=False, indent=2))
            continue

        if user_input.lower() == "evolvi":
            print(json.dumps(agent.evolvi(), ensure_ascii=False, indent=2))
            continue

        if user_input.lower().startswith("imprimi "):
            testo = user_input[8:].strip()
            if testo:
                agent.imprime(testo)
                print(f"[Impronta registrata: '{testo[:60]}']")
            continue

        risposta = agent.parla(user_input)

        print(f"\nRaffaello [{risposta.provider} | {risposta.latenza_ms:.0f}ms | seed {risposta.punteggio_seed:.1f}]:")
        print(risposta.testo)
        print()


if __name__ == "__main__":
    main()
