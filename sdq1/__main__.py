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
from datetime import datetime, timezone, timedelta
from pathlib import Path

_TZ_BRUSSELS = timezone(timedelta(hours=2))  # CEST; in inverno passare a +1


def _ora_brussels() -> tuple[str, str]:
    """Restituisce (data, ora) nel fuso orario di Bruxelles (CEST = UTC+2)."""
    now = datetime.now(_TZ_BRUSSELS)
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")


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

import threading

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
    parser.add_argument("--backup", action="store_true",
                        help="Salva snapshot completo dello stato in output/backups/")
    parser.add_argument("--restore", metavar="FILE",
                        help="Ripristina backup da FILE")
    parser.add_argument("--lista-backup", action="store_true",
                        help="Elenca i backup disponibili")
    parser.add_argument("--watchdog", action="store_true",
                        help="Avvia monitor continuo dei nodi (blocca il processo)")
    parser.add_argument("--intervallo", type=float, default=120.0,
                        help="Secondi tra i ping del watchdog (default: 120)")
    parser.add_argument("--contatto", action="store_true",
                        help="Registra un contatto reale in output/contatti.jsonl (criterio H2)")
    parser.add_argument("--tipo", default="",
                        help="Tipo contatto: lettore, cliente, uso, condivisione, ...")
    parser.add_argument("--nota", default="",
                        help="Descrizione del contatto")
    parser.add_argument("--verifica", default="",
                        help="Come è verificabile (link, nome, messaggio, ecc.)")
    parser.add_argument("--persona", default="",
                        help="Nome/identificatore della persona (per contare persone distinte)")
    parser.add_argument("--no-umano", action="store_true",
                        help="Marca il contatto come evento di sistema, non umano")
    parser.add_argument("--economia", action="store_true",
                        help="Solo Gemini (free tier) + DeepSeek (low cost), niente Anthropic/OpenAI")
    parser.add_argument("--locale", action="store_true",
                        help="Priorità a Ollama locale (costo zero), fallback Gemini")
    parser.add_argument("--simula", action="store_true",
                        help="Esegui simulazioni parallele degli scenari futuri")
    parser.add_argument("--scenari", nargs="*", metavar="ID",
                        help="ID scenari da simulare (default: tutti). Es: ALPHA BETA GAMMA")
    parser.add_argument("--genera", metavar="TIPO",
                        help="Genera contenuto: canzone | immagine | video | traduzione")
    parser.add_argument("--tema", default="",
                        help="Tema / descrizione del contenuto da generare")
    parser.add_argument("--genere", default="pop",
                        help="Genere musicale (per --genera canzone)")
    parser.add_argument("--lingua", default="italiano",
                        help="Lingua (per --genera canzone o traduzione)")
    parser.add_argument("--stile", default="",
                        help="Stile artistico (per --genera immagine)")
    parser.add_argument("--formato", default="reel",
                        help="Formato video: reel | youtube | tiktok | spot | pitch")
    parser.add_argument("--da", default="it", help="Lingua sorgente (per traduzione)")
    parser.add_argument("--a", default="en", help="Lingua destinazione (per traduzione)")
    parser.add_argument("--modello-target", default="Claude / GPT-4",
                        help="Modello AI per cui ottimizzare il prompt")
    parser.add_argument("--strumenti", nargs="*", metavar="TOOL",
                        help="Tool disponibili per l'agente (es. search_web send_email)")
    parser.add_argument("--autonomia", default="semi-autonomo",
                        help="Livello autonomia agente: supervisionato | semi-autonomo | completamente_autonomo")
    args = parser.parse_args(argv[1:])

    if args.watchdog:
        from .watchdog import Watchdog
        wd = Watchdog(health, router, intervallo_s=args.intervallo)
        print(f"Watchdog avviato — ping ogni {args.intervallo}s — log: output/health_log.jsonl")
        print("Ctrl+C per fermare.")
        try:
            wd.avvia()
        except KeyboardInterrupt:
            wd.ferma()
            print("\nWatchdog fermato.")
        return 0

    if args.contatto:
        _contatti = Path("output/contatti.jsonl")
        _contatti.parent.mkdir(parents=True, exist_ok=True)
        if not args.nota or not args.verifica:
            print("Uso: sdq1 --contatto --tipo <tipo> --nota <descrizione> --verifica <come_verificabile>")
            print("Esempio: sdq1 --contatto --tipo lettore --nota 'Marco ha letto il README' --verifica 'github star claudioterzi/Claudio'")
            return 1
        _data, _ora = _ora_brussels()
        voce: dict = {
            "data": _data,
            "ora": _ora,
            "tz": "Europe/Brussels",
            "tipo": args.tipo or "generico",
            "umano": not args.no_umano,
            "nota": args.nota,
            "verifica": args.verifica,
        }
        if args.persona:
            voce["persona"] = args.persona
        with _contatti.open("a", encoding="utf-8") as f:
            f.write(json.dumps(voce, ensure_ascii=False) + "\n")
        righe = [r for r in _contatti.read_text(encoding="utf-8").splitlines() if r]
        totale = len(righe)
        umani = [json.loads(r) for r in righe if json.loads(r).get("umano", True)]
        persone = len({v.get("persona", v.get("nota", ""))[:40] for v in umani})
        print(json.dumps({"registrato": voce, "totale_voci": totale, "contatti_umani": len(umani), "persone_distinte_stimate": persone}, indent=2, ensure_ascii=False))
        print(f"\n[H2] Persone reali raggiunte: ~{persone} | Voci totali: {totale}")
        return 0

    if args.lista_backup:
        from .backup import lista_backup
        bk = lista_backup()
        if not bk:
            print("Nessun backup trovato in output/backups/")
        else:
            print(json.dumps(bk, indent=2, ensure_ascii=False))
        return 0

    if args.restore:
        from .backup import ripristina_backup
        esito = ripristina_backup(args.restore)
        print(json.dumps(esito, indent=2, ensure_ascii=False))
        return 0

    orch, router, memoria, stato, metrics, health, vss = costruisci_sistema(args.verbose)

    # Startup: aggiorna circuit breaker in base allo stato reale dei provider
    threading.Thread(
        target=health.aggiorna_circuit_breaker, daemon=True
    ).start()

    # --locale: priorità Ollama, blocca tutti i cloud provider costosi
    if args.locale:
        _cloud_costosi = {"anthropic", "openai", "perplexity", "deepseek"}
        for name in _cloud_costosi:
            router._circuit[name] = time.time() + 86400

    # --economia: solo Gemini (free) e DeepSeek (cheap), blocca provider costosi
    if args.economia:
        _costosi = {"anthropic", "openai", "perplexity"}
        for name in _costosi:
            router._circuit[name] = time.time() + 86400

    # --no-api: disabilita tutti i provider reali, solo stub
    if args.no_api:
        from .llm.router import PROVIDER_REGISTRY
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
        # Aggiorna anche il circuit breaker con i risultati del ping
        azioni_cb = health.aggiorna_circuit_breaker()
        riepilogo["circuit_breaker"] = router.stato_circuit_breaker()
        riepilogo["circuit_breaker_azioni"] = azioni_cb
        riepilogo["vss_size"] = vss.dimensione()
        riepilogo["cache_risposte"] = len(router._resp_cache)
        _cf = Path("output/contatti.jsonl")
        if _cf.exists():
            _righe = [json.loads(r) for r in _cf.read_text(encoding="utf-8").splitlines() if r]
            _umani = [v for v in _righe if v.get("umano", True)]
            _persone = len({v.get("persona", v.get("nota", ""))[:40] for v in _umani})
            riepilogo["h2_voci_totali"] = len(_righe)
            riepilogo["h2_contatti_umani"] = len(_umani)
            riepilogo["h2_persone_reali_raggiunte"] = _persone
        else:
            riepilogo["h2_voci_totali"] = 0
            riepilogo["h2_contatti_umani"] = 0
            riepilogo["h2_persone_reali_raggiunte"] = 0
        print(json.dumps(riepilogo, indent=2, ensure_ascii=False))
        return 0

    if args.backup:
        from .backup import crea_backup
        etichetta = "_".join(args.testo) if args.testo else ""
        dest = crea_backup(
            memoria=memoria, vss=vss, router=router,
            config=carica_config(), etichetta=etichetta,
        )
        print(json.dumps({"backup": str(dest), "ok": True}, indent=2))
        return 0

    if args.genera:
        if not args.tema:
            print("Usa --tema per descrivere cosa generare. Es: --genera canzone --tema 'la forza di ricominciare'")
            return 1
        tipo = args.genera.lower()

        def _llm_testo(sistema: str, utente: str) -> str:
            return router.chiama(sistema, utente, profilo="default").risposta.testo

        if tipo == "canzone":
            from studio.generators import GeneratoreCanzoni
            gen = GeneratoreCanzoni(llm_fn=_llm_testo)
            risultato = gen.genera(
                tema=args.tema,
                genere=args.genere,
                lingua=args.lingua,
                struttura=args.genere if args.genere in ("pop", "ballata", "inno", "rap", "folk") else "pop",
            )
            print("=" * 60)
            print(risultato["testo"])
            print("\n--- STILE SUNO ---")
            print(risultato["stile_suno"])
            print("\n--- ISTRUZIONI ---")
            print(risultato["istruzioni_suno"])

        elif tipo == "immagine":
            from studio.generators import GeneratoreImmagini
            gen = GeneratoreImmagini()
            risultato = gen.genera(descrizione=args.tema, stile=args.stile)
            print(json.dumps(risultato, indent=2, ensure_ascii=False))

        elif tipo == "video":
            from studio.generators import GeneratoreVideoScript
            gen = GeneratoreVideoScript(llm_fn=_llm_testo)
            risultato = gen.genera_script(concept=args.tema, formato=args.formato)
            print(risultato["script"])
            print("\n--- PRODUZIONE AI ---")
            print(risultato["istruzioni_produzione_ai"])

        elif tipo == "traduzione":
            from studio.generators import GeneratoreTraduzioni
            gen = GeneratoreTraduzioni(llm_fn=_llm_testo)
            risultato = gen.traduci(testo=args.tema, da=args.da, a=args.a)
            print(risultato["traduzione"])

        elif tipo == "prompt":
            from studio.generators import GeneratorePromptEngineering
            gen = GeneratorePromptEngineering(llm_fn=_llm_testo)
            risultato = gen.prompt_ottimizzato(
                task=args.tema,
                modello_target=args.modello_target,
                tono=args.stile or "professionale",
            )
            print(risultato["testo_completo"])

        elif tipo == "agente":
            from studio.generators import GeneratorePromptEngineering
            gen = GeneratorePromptEngineering(llm_fn=_llm_testo)
            nome = args.genere or "Agente-001"
            risultato = gen.specifica_agente(
                nome=nome,
                missione=args.tema,
                strumenti=args.strumenti,
                autonomia=args.autonomia,
            )
            print(risultato["specifica_completa"])

        else:
            print(f"Tipo non riconosciuto: {tipo}. Usa: canzone | immagine | video | traduzione | prompt | agente")
            return 1
        return 0

    if args.simula:
        from .futures import SimulatoreScenari, SCENARI_DEFAULT
        filtro = set(args.scenari) if args.scenari else None
        scenari_sel = [s for s in SCENARI_DEFAULT if filtro is None or s.id in filtro]
        if not scenari_sel:
            print(f"Nessuno scenario trovato. Disponibili: {[s.id for s in SCENARI_DEFAULT]}")
            return 1

        def _llm_fn(sistema: str, utente: str):
            esito = router.chiama(sistema, utente, profilo="default")
            return esito.risposta.testo, esito.risposta.provider, int(esito.risposta.latenza_ms or 0)

        print(f"Avvio simulazioni parallele: {[s.id for s in scenari_sel]} …")
        sim = SimulatoreScenari(llm_fn=_llm_fn)
        risultati = sim.simula_parallelo(scenari_sel)
        print(SimulatoreScenari.stampa_report(risultati))
        dest = sim.salva_report(risultati)
        print(f"\nReport salvato: {dest}")
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
