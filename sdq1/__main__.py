"""Entry point SDQ-1.

Esempi:
    python -m sdq1 "Ciao, come va?"
    python -m sdq1 --verbose "spiegami il sistema"
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from .agents import costruisci_agenti
from .agents import implementazioni
from .config import carica_config
from .llm.client import ClaudeClient
from .memory.store import MemoriaVettoriale
from .orchestrator.gerarchico import OrchestratoreGerarchico
from .persistence.store import crea_store


def costruisci_sistema(verbose: bool = False):
    livello = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=livello, format="%(levelname)s [%(name)s] %(message)s")

    config = carica_config()

    # Memoria condivisa + seed
    memoria = MemoriaVettoriale(
        soglia_similarita=config.memoria.get("soglia_similarita", 0.45),
        max_risultati=config.memoria.get("max_risultati_recupero", 5),
    )
    for s in config.memoria.get("seed", []) or []:
        memoria.aggiungi(s, metadata={"origine": "seed"})

    # LLM factory (un client per modello, riutilizzato)
    cache: dict[str, ClaudeClient] = {}

    def llm_factory(modello: str) -> ClaudeClient:
        if modello not in cache:
            mc = dict(config.modello)
            mc["nome"] = modello
            cache[modello] = ClaudeClient(
                modello=modello,
                temperatura=mc.get("temperatura", 0.7),
                max_token=mc.get("max_token", 4096),
                timeout_secondi=mc.get("timeout_secondi", 60),
            )
        return cache[modello]

    implementazioni.imposta_runtime(
        llm_factory=llm_factory,
        memoria=memoria,
        pattern_blocco=config.sicurezza.get("pattern_blocco", []),
    )

    agenti = costruisci_agenti(config)
    stato = crea_store(config.redis)
    orch = OrchestratoreGerarchico(config, agenti, stato=stato)
    return orch, memoria, stato


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="sdq1")
    parser.add_argument("testo", nargs="*", help="Messaggio in ingresso")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--solo-output", action="store_true",
                        help="Stampa solo la risposta finale")
    args = parser.parse_args(argv[1:])

    testo = " ".join(args.testo) or "Ciao SDQ-1, sei attivo?"

    orch, memoria, stato = costruisci_sistema(verbose=args.verbose)
    esecuzione = orch.esegui({"testo": testo})

    if args.solo_output:
        if esecuzione.interrotta:
            print(f"[interrotto] {esecuzione.motivo_interruzione}")
        else:
            finale = (esecuzione.output_finale or {}).get("risposta_finale", "")
            print(finale or "(nessuna risposta)")
        return 0

    risultato = {
        "esecuzione_id": esecuzione.id,
        "input": esecuzione.input_iniziale,
        "passi": [
            {
                "agente": p.mittente,
                "successo": p.successo,
                "output_keys": list(p.output.keys()),
                "via_api": p.metadata.get("via_api"),
                "errore": p.errore,
            }
            for p in esecuzione.passi
        ],
        "interrotta": esecuzione.interrotta,
        "motivo_interruzione": esecuzione.motivo_interruzione,
        "durata_secondi": esecuzione.durata_secondi,
        "risposta_finale": (esecuzione.output_finale or {}).get("risposta_finale"),
        "memoria_size": memoria.dimensione(),
        "persistenza": stato.__class__.__name__,
    }
    print(json.dumps(risultato, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
