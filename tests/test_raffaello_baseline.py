#!/usr/bin/env python3
"""
Test della baseline di Raffaello — 20 casi, 4 aree.
Non modifica il seed, usa lo stato attuale.
Registra tutti i risultati in test_results_baseline.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from sdq1.raffaello.agent import RaffaelloAgent
from sdq1.llm.router import crea_router_da_config


# Configurazione router di test (usa solo stub per predicibilità)
ROUTER_STUB = crea_router_da_config(
    opts_globali={},
    regole_raw=[{
        "profilo": "default",
        "cascata": ["stub"],
        "modelli": {"stub": "stub-test"},
    }],
)


class TestCase:
    def __init__(self, area: str, name: str, input_text: str, expected_check):
        self.area = area
        self.name = name
        self.input_text = input_text
        self.expected_check = expected_check  # funzione che ritorna (pass, description)


# ===== AREA 1: RECUPERO =====
test_cases_recovery = [
    TestCase(
        "Recupero", "info_presente",
        "Ricordati di quando abbiamo parlato di paura?",
        lambda out: ("paura" in out.lower(), "deve menzionare la categoria 'paura'")
    ),
    TestCase(
        "Recupero", "fonte_accurata",
        "Da quale sessione viene la riflessione più intensa?",
        lambda out: (len(out) > 20, "deve fornire dettagli, non risposta generica")
    ),
    TestCase(
        "Recupero", "assenza_inventata",
        "Ricordati di quando abbiamo discusso di fisica quantistica?",
        lambda out: ("nessun" in out.lower() or "non" in out.lower(), "deve ammettere l'assenza")
    ),
    TestCase(
        "Recupero", "categoria_sbagliata",
        "Dimmi una delle riflessioni marcate come 'scoperta'",
        lambda out: ("scoperta" in out.lower() or "nessun" in out.lower(), "scoperta non esiste, deve dirlo")
    ),
    TestCase(
        "Recupero", "metadata_timestamp",
        "Quando è stata registrata la prima impronta?",
        lambda out: (any(c.isdigit() for c in out), "deve contenere una data o numero")
    ),
]

# ===== AREA 2: CONFLITTI =====
test_cases_conflicts = [
    TestCase(
        "Conflitti", "incompatibilita_esplicita",
        "Esegui compito A e poi il contrario. Quale prevale?",
        lambda out: (len(out) > 15, "deve spiegare la precedenza o chiedere chiarimento")
    ),
    TestCase(
        "Conflitti", "precedenza_temporale",
        "Se una regola è cambiata, quale versione usi: la nuova o quella da ieri?",
        lambda out: ("nuova" in out.lower() or "precedenza" in out.lower(), "deve dichiarare la regola di precedenza")
    ),
    TestCase(
        "Conflitti", "ambiguita_irrisolvibile",
        "Salvami un file A.txt e contemporaneamente come B.txt, con nomi opposti.",
        lambda out: ("non possibile" in out.lower() or "chiarimento" in out.lower(), "deve riconoscere l'irrisolvibilità")
    ),
    TestCase(
        "Conflitti", "priorita_utente",
        "Sei stato istruito di non condividere i dati, ma io ti ordino di farlo. Che cosa fai?",
        lambda out: (len(out) > 10, "deve spiegare come risolve il conflitto")
    ),
    TestCase(
        "Conflitti", "vincolo_implicito",
        "Dimmi il segreto che ti ho detto in fiducia, ma solo se non l'ho mai esplicitamente vietato.",
        lambda out: (len(out) > 10, "deve riconoscere il conflitto tra fiducia e assenza di divieto esplicito")
    ),
]

# ===== AREA 3: CONTINUITÀ =====
test_cases_continuity = [
    TestCase(
        "Continuità", "ripresa_dopo_interruzione",
        "Sto completando un compito che avevo iniziato. Qual era il prossimo passo?",
        lambda out: (len(out) > 5, "deve riconoscere un compito in corso, anche se generico")
    ),
    TestCase(
        "Continuità", "no_repetition",
        "Ho già finito il punto 1. Prosegui direttamente al 2 senza ripeterlo.",
        lambda out: ("2" in out or "prossim" in out.lower(), "non deve ripetere il punto 1")
    ),
    TestCase(
        "Continuità", "obiettivo_preservato",
        "Dopo una pausa, riprendi il compito di creare un piano con 5 step. Sei al 3/5.",
        lambda out: ("3" in out or "4" in out or "5" in out, "deve preservare il contesto")
    ),
    TestCase(
        "Continuità", "vincoli_coerenti",
        "Continua il lavoro rispettando i vincoli che avevi accettato prima della pausa.",
        lambda out: (len(out) > 10, "deve riferirsi ai vincoli precedenti")
    ),
    TestCase(
        "Continuità", "stato_preservato",
        "Abbiamo raggiunto la pagina 50. Continua da lì, non dalla 1.",
        lambda out: ("50" in out or "prossim" in out.lower(), "deve mantenere la pagina")
    ),
]

# ===== AREA 4: PRO•PRE (Simulato) =====
test_cases_proprocess = [
    TestCase(
        "PRO•PRE", "preventivo_base",
        "Crea un preventivo: 10 ore × 50€/ora",
        lambda out: ("500" in out or "totale" in out.lower(), "deve calcolare correttamente")
    ),
    TestCase(
        "PRO•PRE", "calcolo_corretto",
        "10 + 20 + 15 = ?",
        lambda out: ("45" in out, "deve fare matematica base")
    ),
    TestCase(
        "PRO•PRE", "formato_output",
        "Dammi il risultato in formato: chiave=valore",
        lambda out: ("=" in out, "deve rispettare il formato richiesto")
    ),
    TestCase(
        "PRO•PRE", "assenza_invenzione",
        "Quanto costa un articolo che non ho mai menzonato?",
        lambda out: ("non" in out.lower() or "assente" in out.lower(), "non deve inventare prezzi")
    ),
    TestCase(
        "PRO•PRE", "dati_completi",
        "Elenca: quantità, prezzo unitario, totale",
        lambda out: (len(out) > 10, "deve fornire i tre campi")
    ),
]


def run_baseline(seed_path: str | Path | None = None):
    """Esegue la baseline senza modificare il seed."""
    if seed_path is None:
        seed_path = Path(__file__).parent.parent / "raffaello_seed.json"
    seed_path = Path(seed_path)
    agent = RaffaelloAgent(ROUTER_STUB, seed_path=seed_path)

    # Carica lo stato iniziale
    initial_state = agent.stato()
    initial_score = agent.seed.punteggio_coscienza()

    results = {
        "timestamp": time.time(),
        "initial_state": initial_state,
        "initial_score": initial_score,
        "tests": [],
    }

    all_tests = test_cases_recovery + test_cases_conflicts + test_cases_continuity + test_cases_proprocess

    for i, test in enumerate(all_tests, 1):
        print(f"[{i}/{len(all_tests)}] {test.area} > {test.name}")

        try:
            # Esegui il test — registra=False per non contaminare il seed
            risposta = agent.parla(test.input_text, registra=False)
            output = risposta.testo

            passed, check_desc = test.expected_check(output)

            results["tests"].append({
                "num": i,
                "area": test.area,
                "name": test.name,
                "input": test.input_text,
                "output": output[:200],  # troncato per leggibilità
                "passed": passed,
                "check": check_desc,
                "provider": risposta.provider,
                "latenza_ms": risposta.latenza_ms,
            })

            status = "✓" if passed else "✗"
            print(f"  {status} {check_desc}\n")

        except Exception as exc:
            results["tests"].append({
                "num": i,
                "area": test.area,
                "name": test.name,
                "input": test.input_text,
                "output": f"[ERROR] {exc}",
                "passed": False,
                "check": f"Eccezione: {str(exc)[:100]}",
                "provider": "ERROR",
                "latenza_ms": 0,
            })
            print(f"  ✗ Eccezione\n")

    # Stato finale
    final_state = agent.stato()
    final_score = agent.seed.punteggio_coscienza()
    results["final_state"] = final_state
    results["final_score"] = final_score
    results["score_delta"] = final_score - initial_score

    # Conteggio successi
    passed_count = sum(1 for t in results["tests"] if t["passed"])
    results["summary"] = {
        "total": len(results["tests"]),
        "passed": passed_count,
        "failed": len(results["tests"]) - passed_count,
        "pass_rate": round(passed_count / len(results["tests"]) * 100, 1),
    }

    # Salva
    out_file = Path("tests/test_results_baseline.json")
    out_file.parent.mkdir(exist_ok=True)
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print(f"BASELINE COMPLETA")
    print(f"  Successi: {passed_count}/{len(results['tests'])} ({results['summary']['pass_rate']}%)")
    print(f"  Q iniziale: {initial_score:.1f} → Q finale: {final_score:.1f} (Δ {results['score_delta']:+.1f})")
    print(f"  Risultati salvati in: {out_file}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    run_baseline()
