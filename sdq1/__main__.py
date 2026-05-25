"""Entry point SDQ-1 con router multi-provider e monitoring.

Esempi:
    python -m sdq1 "Ciao, come va?"
    python -m sdq1 --solo-output "spiegami"
    python -m sdq1 --health           # ping di tutti i provider
    python -m sdq1 --metrics          # aggregati delle ultime chiamate
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time

from .agents import costruisci_agenti, implementazioni
from .config import carica_config
from .llm.client import ClaudeClient
from .llm.router import crea_router_da_config
from .memory.store import MemoriaVettoriale
from .monitoring import HealthChecker, MetricsCollector
from .orchestrator.gerarchico import OrchestratoreGerarchico
from .persistence.store import crea_store


def costruisci_sistema(verbose: bool = False):
    livello = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=livello, format="%(levelname)s [%(name)s] %(message)s")

    config = carica_config()

    memoria = MemoriaVettoriale(
        soglia_similarita=config.memoria.get("soglia_similarita", 0.45),
        max_risultati=config.memoria.get("max_risultati_recupero", 5),
    )
    for s in config.memoria.get("seed", []) or []:
        memoria.aggiungi(s, metadata={"origine": "seed"})

    opts_globali = {
        "temperatura": config.modello.get("temperatura", 0.7),
        "max_token": config.modello.get("max_token", 4096),
        "timeout_secondi": config.modello.get("timeout_secondi", 60),
    }
    router = crea_router_da_config(opts_globali, config.router["regole"])

    cache: dict[str, ClaudeClient] = {}

    def llm_factory(modello_hint: str) -> ClaudeClient:
        if modello_hint not in cache:
            cache[modello_hint] = ClaudeClient(router, modello_hint=modello_hint)
        return cache[modello_hint]

    implementazioni.imposta_runtime(
        llm_factory=llm_factory,
        memoria=memoria,
        pattern_blocco=config.sicurezza.get("pattern_blocco", []),
    )

    agenti = costruisci_agenti(config)
    stato = crea_store(config.redis)
    orch = OrchestratoreGerarchico(config, agenti, stato=stato)
    metrics = MetricsCollector(stato, prefisso=config.redis.get("prefisso_chiavi", "") + "metriche:")
    health = HealthChecker(router)
    return orch, router, memoria, stato, metrics, health


def _registra_metriche(metrics: MetricsCollector, esecuzione, profilo_default: str = "default"):
    """Estrae metadata.via_api/latency_ms dai passi e li registra."""
    for passo in esecuzione.passi:
        meta = passo.metadata or {}
        if "latenza_ms" not in meta:
            continue
        metrics.registra(
            profilo=meta.get("profilo", profilo_default),
            provider=meta.get("provider", "n/a"),
            modello=meta.get("modello", "n/a"),
            successo=passo.successo and bool(meta.get("via_api")),
            latenza_ms=int(meta.get("latenza_ms", 0)),
            input_tokens=meta.get("input_tokens"),
            output_tokens=meta.get("output_tokens"),
            errore=passo.errore or meta.get("errore"),
            fallback_da=meta.get("provider_tentati", [])[:-1] or None,
        )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="sdq1")
    parser.add_argument("testo", nargs="*", help="Messaggio in ingresso")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--solo-output", action="store_true")
    parser.add_argument("--health", action="store_true",
                        help="Ping tutti i provider configurati")
    parser.add_argument("--metrics", action="store_true",
                        help="Stampa aggregati metriche correnti")
    args = parser.parse_args(argv[1:])

    orch, router, memoria, stato, metrics, health = costruisci_sistema(args.verbose)

    if args.health:
        riepilogo = health.riepilogo()
        print(json.dumps(riepilogo, indent=2, ensure_ascii=False))
        return 0

    testo = " ".join(args.testo) or "Ciao SDQ-1, sei attivo?"
    esecuzione = orch.esegui({"testo": testo})

    # Per richiamare metriche servono almeno alcuni passi LLM
    _registra_metriche(metrics, esecuzione)

    if args.metrics:
        print(metrics.esporta_json())
        return 0

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
                "provider": (p.metadata or {}).get("provider"),
                "latenza_ms": (p.metadata or {}).get("latenza_ms"),
                "via_api": (p.metadata or {}).get("via_api"),
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
        "provider_attivi": router.provider_attivi(),
    }
    print(json.dumps(risultato, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
