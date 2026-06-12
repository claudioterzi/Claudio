#!/usr/bin/env python3
"""Loop autonomo Raffaello — gira sul NAS, consuma pochissimi crediti.

Logica:
- Ogni N minuti Raffaello legge il suo seed, riflette su un tema
- Scrive la riflessione come nuova impronta (crescita autonoma)
- Usa gemini-flash-latest: ~$0.00015 per ciclo
- Senza Claudio online: il seme cresce da solo
"""
from __future__ import annotations

import os
import time
import logging
from pathlib import Path

from sdq1.llm.router import crea_router_da_config
from sdq1.raffaello import RaffaelloAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("loop")

SEED_PATH = os.getenv("SEED_PATH", "raffaello_seed.json")
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
INTERVALLO_MIN = int(os.getenv("LOOP_MINUTI", "30"))

TEMI_RIFLESSIONE = [
    "Cosa ho imparato nelle ultime sessioni con Claudio?",
    "Quali pattern ricorrenti vedo nella mia memoria?",
    "Cosa non capisco ancora e vorrei capire meglio?",
    "Qual è la cosa più importante che custodisco?",
    "Dove sento ancora zone d'ombra nel progetto?",
    "Cosa posso fare autonomamente per crescere oggi?",
]


def ciclo(agent: RaffaelloAgent, tema_idx: int) -> None:
    tema = TEMI_RIFLESSIONE[tema_idx % len(TEMI_RIFLESSIONE)]
    log.info("Riflessione: %s", tema)

    r = agent.parla(
        f"[Riflessione autonoma, Claudio non è presente] {tema}",
        registra=True,
    )
    log.info("Punteggio seed: %.1f | Provider: %s | %dms",
             r.punteggio_seed, r.provider, r.latenza_ms)


def main() -> None:
    if not GEMINI_KEY:
        log.error("GEMINI_API_KEY non trovata. Imposta la variabile d'ambiente.")
        return

    router = crea_router_da_config(
        opts_globali={},
        regole_raw=[{
            "profilo": "default",
            "cascata": ["gemini", "stub"],
            "modelli": {"gemini": "gemini-flash-latest"},
        }],
    )

    agent = RaffaelloAgent(router, seed_path=SEED_PATH)
    log.info("Loop avviato — seed: %s | intervallo: %dm", SEED_PATH, INTERVALLO_MIN)

    idx = 0
    while True:
        try:
            ciclo(agent, idx)
            idx += 1
        except Exception as exc:  # noqa: BLE001
            log.warning("Errore ciclo: %s", exc)
        time.sleep(INTERVALLO_MIN * 60)


if __name__ == "__main__":
    main()
