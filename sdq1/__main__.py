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
import os
import sys
import time
from pathlib import Path


def _carica_dotenv() -> None:
    """Carica .env dalla root del progetto se presente, senza dipendenze esterne."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    with env_path.open() as f:
        for riga in f:
            riga = riga.strip()
            if not riga or riga.startswith("#") or "=" not in riga:
                continue
            chiave, _, valore = riga.partition("=")
            chiave = chiave.strip()
            valore = valore.strip().strip('"').strip("'")
            if chiave and chiave not in os.environ:
                os.environ[chiave] = valore


_carica_dotenv()

from .agents import costruisci_agenti, implementazioni
from .config import carica_config
from .llm.client import ClaudeClient
from .llm.router import crea_router_da_config
from .memory.store import MemoriaVettoriale
from .memory.vss import VectorStateStore
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

    vss = VectorStateStore(memoria)

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
        vss=vss,
        pattern_blocco=config.sicurezza.get("pattern_blocco", []),
    )

    agenti = costruisci_agenti(config)
    stato = crea_store(config.redis)
    orch = OrchestratoreGerarchico(config, agenti, stato=stato)
    metrics = MetricsCollector(stato, prefisso=config.redis.get("prefisso_chiavi", "") + "metriche:")
    health = HealthChecker(router)
    return orch, router, memoria, stato, metrics, health, vss


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
                        help="Ping tutti i provider configurati + stato circuit breaker")
    parser.add_argument("--metrics", action="store_true",
                        help="Stampa aggregati metriche correnti")
    parser.add_argument("--sim-to-real", action="store_true",
                        help="Genera script CadQuery dall'output WAVE-003")
    parser.add_argument("--conferma", action="store_true",
                        help="Scrive i file su disco (richiesto con --sim-to-real)")
    parser.add_argument("--sar", metavar="TENSIONE",
                        help="Ciclo SAR sulla tensione indicata, es. 'Controllo ↔ Fiducia'")
    parser.add_argument("--sar-stato", action="store_true",
                        help="Mostra stato SAR salvato su disco")
    parser.add_argument("--no-api", action="store_true",
                        help="Forza stub-only: zero chiamate API, zero spesa")
    args = parser.parse_args(argv[1:])

    orch, router, memoria, stato, metrics, health, vss = costruisci_sistema(args.verbose)

    # --no-api: disabilita tutti i provider reali, solo stub
    if args.no_api:
        from .llm.router import PROVIDER_REGISTRY
        from .llm.providers.stub_provider import StubProvider
        router._cache.clear()
        for name in list(PROVIDER_REGISTRY):
            if name != "stub":
                router._circuit[name] = time.time() + 86400  # aperto per 24h

    if args.sar_stato:
        from .sar import PersistenzaSAR, report_stato
        p = PersistenzaSAR(soggetto="Claudio")
        info = p.info()
        if not info["esiste"]:
            print("Nessuno stato SAR salvato. Usa --sar per avviare il primo ciclo.")
        else:
            from .sar import ScacchieraAutoRiflessiva
            sar_tmp = ScacchieraAutoRiflessiva(llm_fn=None, vss=vss, soggetto="Claudio")
            print(report_stato(sar_tmp.stato(), soggetto="Claudio"))
            print(f"File: {info['file_stato']}")
            print(f"Report salvati: {info['report']}")
        return 0

    if args.health:
        riepilogo = health.riepilogo()
        riepilogo["circuit_breaker"] = router.stato_circuit_breaker()
        riepilogo["vss_size"] = vss.dimensione()
        print(json.dumps(riepilogo, indent=2, ensure_ascii=False))
        return 0

    testo = " ".join(args.testo) or "Ciao SDQ-1, sei attivo?"
    esecuzione = orch.esegui({"testo": testo})

    _registra_metriche(metrics, esecuzione)

    if args.metrics:
        agg = json.loads(metrics.esporta_json())
        agg["vss_size"] = vss.dimensione()
        agg["circuit_breaker"] = router.stato_circuit_breaker()
        print(json.dumps(agg, indent=2, ensure_ascii=False))
        return 0

    if args.solo_output:
        if esecuzione.interrotta:
            print(f"[interrotto] {esecuzione.motivo_interruzione}")
        else:
            finale = (esecuzione.output_finale or {}).get("risposta_finale", "")
            print(finale or "(nessuna risposta)")
        return 0

    if args.sar:
        from .sar import ScacchieraAutoRiflessiva, report_ciclo

        def _llm(sistema: str, utente: str) -> str:
            return router.chiama(sistema, utente, profilo="default").risposta.testo

        sar = ScacchieraAutoRiflessiva(llm_fn=_llm, vss=vss, soggetto="Claudio")
        if testo:
            sar.osserva(testo, tag=["input"])
        report = sar.ciclo_completo(args.sar)
        print(report_ciclo(report, soggetto="Claudio"))
        azione = sar.genera_azione(report.get("sintesi", ""))
        print("AZIONE CONCRETA (Livello 9)\n" + "─" * 60)
        print(azione)
        return 0

    if args.sim_to_real:
        from .output.cad_bridge import CadBridge
        finale = (esecuzione.output_finale or {}).get("risposta_finale", "")
        bridge = CadBridge()
        esito_cad = bridge.elabora(finale, confermato=args.conferma)
        if not args.conferma:
            print("=== Script CadQuery generato (non scritto su disco) ===")
            print(esito_cad["script"])
            print("\n[ATTENZIONE] Per scrivere i file usa: --sim-to-real --conferma")
            print("[ATTENZIONE] Verifica sempre il toolpath prima di avviare la Pocket NC.")
        else:
            print(json.dumps(
                {k: v for k, v in esito_cad.items() if k != "script"},
                indent=2, ensure_ascii=False, default=str,
            ))
        return 0

    risposta_finale = (esecuzione.output_finale or {}).get("risposta_finale")
    risultato = {
        "esecuzione_id":       esecuzione.id,
        "input":               esecuzione.input_iniziale,
        "passi": [
            {
                "agente":     p.mittente,
                "successo":   p.successo,
                "provider":   (p.metadata or {}).get("provider"),
                "latenza_ms": (p.metadata or {}).get("latenza_ms"),
                "via_api":    (p.metadata or {}).get("via_api"),
                "hedged":     (p.metadata or {}).get("hedged", False),
                "errore":     p.errore,
            }
            for p in esecuzione.passi
        ],
        "interrotta":           esecuzione.interrotta,
        "motivo_interruzione":  esecuzione.motivo_interruzione,
        "durata_secondi":       esecuzione.durata_secondi,
        "risposta_finale":      risposta_finale,
        "vss_size":             vss.dimensione(),
        "vss_ptr_run":          len(vss.ptr_del_run(esecuzione.id)),
        "memoria_size":         memoria.dimensione(),
        "circuit_breaker":      router.stato_circuit_breaker(),
        "persistenza":          stato.__class__.__name__,
        "provider_attivi":      router.provider_attivi(),
    }
    print(json.dumps(risultato, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
