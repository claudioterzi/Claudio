"""Entry point dimostrativo per SDQ-1 Fase 1.

Esecuzione:
    python -m sdq1 "il tuo messaggio qui"
"""

from __future__ import annotations

import json
import logging
import sys

from .agents import costruisci_agenti
from .agents import implementazioni  # noqa: F401 — registra le implementazioni
from .config import carica_config
from .orchestrator.gerarchico import OrchestratoreGerarchico


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO)
    config = carica_config()
    agenti = costruisci_agenti(config)
    orch = OrchestratoreGerarchico(config, agenti)

    testo = " ".join(argv[1:]) if len(argv) > 1 else "Ciao SDQ-1, sei attivo?"
    esecuzione = orch.esegui({"testo": testo})

    risultato = {
        "input": esecuzione.input_iniziale,
        "passi": [
            {
                "agente": p.mittente,
                "successo": p.successo,
                "output": p.output,
                "errore": p.errore,
            }
            for p in esecuzione.passi
        ],
        "output_finale": esecuzione.output_finale,
        "interrotta": esecuzione.interrotta,
        "motivo_interruzione": esecuzione.motivo_interruzione,
    }
    print(json.dumps(risultato, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
