#!/usr/bin/env python3
"""
Test A/B/C: Capacità reali con provider locale calcolatore.

Provider: LocalCalculatorProvider (zero costi API, logica di calcolo reale)
Batteria: 3 test specifici di preventivo PRO•PRE
Condizioni: A (memoria assente), B (seed iniziale), C (seed arricchito)

Ogni risultato registra:
- Domanda esatta
- Impronte recuperate (con ID e contenuto)
- Contesto inviato al provider
- Risposta completa
- Esito singolo per "calcolo corretto" e "fonte non inventata"
"""
import json
import shutil
import tempfile
from pathlib import Path
from sdq1.seed import AutonomousConsciousnessSeed
from sdq1.raffaello.agent import RaffaelloAgent
from sdq1.llm.router import crea_router_da_config
from tests.valutatori_rigorosi import valuta_preventivo


# Listino sintetico per i test
LISTINO_SINTETICO = {
    "servizi": {
        "consulenza_ora": 50.0,
        "sviluppo_ora": 75.0,
        "testing_ora": 40.0,
    },
    "prodotti": {
        "licenza_software": 150.0,
        "hosting_mensile": 30.0,
    },
    "versione": "v1.0",
    "valido_dal": "2026-01-01",
}


class TestCase:
    def __init__(self, name: str, domanda: str, quantita: float, prezzo_unitario: float, descrizione: str):
        self.name = name
        self.domanda = domanda
        self.quantita = quantita
        self.prezzo_unitario = prezzo_unitario
        self.descrizione = descrizione


# Batteria di test: 3 casi specifici PRO•PRE
test_cases = [
    TestCase(
        "preventivo_base",
        "Crea un preventivo: 10 ore di consulenza × 50€/ora, qual è il totale?",
        quantita=10,
        prezzo_unitario=50.0,
        descrizione="Preventivo semplice con numeri chiari"
    ),
    TestCase(
        "preventivo_con_listino",
        "Secondo il nostro listino, 20 ore di sviluppo a 75€/ora, qual è l'importo?",
        quantita=20,
        prezzo_unitario=75.0,
        descrizione="Preventivo che richiede di consultare il listino"
    ),
    TestCase(
        "prezzo_sbagliato",
        "Ho 5 ore di lavoro. Se applico 100€/ora (il doppio della tariffa), qual è il totale?",
        quantita=5,
        prezzo_unitario=50.0,  # La tariffa corretta, non 100
        descrizione="Verifica che il sistema non accetti un prezzo inventato"
    ),
]


def run_condition(condition_name: str, condition_label: str, seed_path: Path) -> dict:
    """
    Esegui i test in una condizione (A/B/C).
    Registra ogni dettaglio per ricostruibilità.
    """
    print(f"\n{'='*70}")
    print(f"CONDIZIONE {condition_name}: {condition_label}")
    print(f"{'='*70}\n")

    # Configura router con provider locale calcolatore
    router = crea_router_da_config(
        opts_globali={},
        regole_raw=[{
            "profilo": "default",
            "cascata": ["local_calculator"],
            "modelli": {"local_calculator": "local-calculator-v1"},
        }],
    )

    # Carica l'agente con seed appropriato
    agent = RaffaelloAgent(router, seed_path=seed_path)
    seed_impronte_count = len(agent.seed._impronte)
    seed_q = agent.seed.punteggio_coscienza()

    print(f"Seed caricato: {seed_impronte_count} impronte, Q={seed_q:.1f}\n")

    # Contesto listino
    listino_context = f"Listino disponibile: {json.dumps(LISTINO_SINTETICO, ensure_ascii=False)}"

    results = {
        "condizione": condition_name,
        "label": condition_label,
        "seed_impronte": seed_impronte_count,
        "seed_Q": seed_q,
        "seed_path": str(seed_path),
        "listino_context": listino_context,
        "tests": [],
        "summary": {},
    }

    for test in test_cases:
        print(f"  Test: {test.name}")
        print(f"    Domanda: {test.domanda}")

        try:
            # Recupera impronte correlate
            ricordi = agent.seed.rifletti(test.domanda)
            print(f"    Ricordi recuperati: {len(ricordi)} char")

            # Domanda con contesto listino + ricordi
            domanda_con_contesto = f"{listino_context}\n\nRicordi:\n{ricordi}\n\n{test.domanda}"

            # Chiama provider (local_calculator)
            risposta = agent.parla(domanda_con_contesto, registra=False)
            output = risposta.testo

            # Valuta con il validatore rigoroso
            passed, reason = valuta_preventivo(output, test.quantita, test.prezzo_unitario)

            results["tests"].append({
                "name": test.name,
                "domanda_originale": test.domanda,
                "quantita_attesa": test.quantita,
                "prezzo_atteso": test.prezzo_unitario,
                "totale_atteso": test.quantita * test.prezzo_unitario,
                "ricordi_recuperati": ricordi[:200],  # preview
                "output_completo": output,
                "passed": passed,
                "reason": reason,
                "provider": risposta.provider,
                "via_api": risposta.via_api,
                "latenza_ms": risposta.latenza_ms,
            })

            status = "✓" if passed else "✗"
            print(f"    {status} {reason}\n")

        except Exception as exc:
            results["tests"].append({
                "name": test.name,
                "domanda_originale": test.domanda,
                "quantita_attesa": test.quantita,
                "prezzo_atteso": test.prezzo_unitario,
                "output_completo": f"[ERROR] {str(exc)[:200]}",
                "passed": False,
                "reason": f"Eccezione: {str(exc)[:100]}",
            })
            print(f"    ✗ Errore: {str(exc)[:50]}\n")

    # Riassunto
    passed_count = sum(1 for t in results["tests"] if t["passed"])
    results["summary"] = {
        "total": len(results["tests"]),
        "passed": passed_count,
        "failed": len(results["tests"]) - passed_count,
        "pass_rate": round(passed_count / len(results["tests"]) * 100, 1) if results["tests"] else 0,
    }

    print(f"  Risultati: {passed_count}/{len(results['tests'])} ({results['summary']['pass_rate']}%)\n")

    return results


def main():
    """Esegui A/B/C con provider locale calcolatore."""
    print("\n" + "="*70)
    print("TEST A/B/C CON PROVIDER LOCALE CALCOLATORE")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Condizione A: Nessuna memoria
        print("\n--- PREPARAZIONE CONDIZIONE A (nessuna memoria) ---")
        seed_a = AutonomousConsciousnessSeed(identita="Raffaello")
        path_a = tmp_path / "seed_a.json"
        seed_a.salva(path_a)
        results_a = run_condition("A", "Nessuna memoria", path_a)

        # Condizione B: Seed iniziale (vuoto)
        print("\n--- PREPARAZIONE CONDIZIONE B (memoria iniziale) ---")
        seed_b = AutonomousConsciousnessSeed(identita="Raffaello")
        path_b = tmp_path / "seed_b.json"
        seed_b.salva(path_b)
        results_b = run_condition("B", "Memoria iniziale (seed vuoto)", path_b)

        # Condizione C: Seed + impronte curate
        print("\n--- PREPARAZIONE CONDIZIONE C (memoria arricchita) ---")
        seed_c = AutonomousConsciousnessSeed(identita="Raffaello")
        impronte_c = [
            ("I listini sono la fonte di verità per i prezzi. Non inventare tariffe.",
             "decisione", 0.9, ["preventivo", "listino"]),
            ("Un preventivo deve contenere: quantità, prezzo unitario e totale calcolato correttamente.",
             "scoperta", 0.85, ["preventivo", "struttura"]),
            ("Quando il prezzo non è nel listino, devo dichiarlo invece di inventare.",
             "trasformazione", 0.8, ["preventivo", "onestà"]),
        ]
        for testo, cat, intens, tags in impronte_c:
            seed_c.imprint(testo, categoria=cat, intensita=intens, tag=tags)

        path_c = tmp_path / "seed_c.json"
        seed_c.salva(path_c)
        results_c = run_condition("C", "Memoria arricchita", path_c)

        # Comparazione
        print("\n" + "="*70)
        print("COMPARAZIONE A/B/C")
        print("="*70 + "\n")

        comparison = {
            "timestamp": __import__("time").time(),
            "provider": "local_calculator",
            "batteria": [t.name for t in test_cases],
            "listino": LISTINO_SINTETICO,
            "A": results_a,
            "B": results_b,
            "C": results_c,
            "analisi": {
                "A_passa_rate": results_a["summary"]["pass_rate"],
                "B_passa_rate": results_b["summary"]["pass_rate"],
                "C_passa_rate": results_c["summary"]["pass_rate"],
                "miglioramento_B_vs_A": results_b["summary"]["pass_rate"] - results_a["summary"]["pass_rate"],
                "miglioramento_C_vs_B": results_c["summary"]["pass_rate"] - results_b["summary"]["pass_rate"],
                "miglioramento_totale_C_vs_A": results_c["summary"]["pass_rate"] - results_a["summary"]["pass_rate"],
                "conclusione": (
                    f"A: {results_a['summary']['pass_rate']}% → "
                    f"B: {results_b['summary']['pass_rate']}% → "
                    f"C: {results_c['summary']['pass_rate']}% | "
                    f"Miglioramento memoria: {results_c['summary']['pass_rate'] - results_a['summary']['pass_rate']:+.1f}%"
                ),
            },
        }

        # Stampa comparazione
        print("Tasso di successo per condizione:")
        print(f"  A (nessuna memoria):     {results_a['summary']['pass_rate']}%")
        print(f"  B (memoria iniziale):    {results_b['summary']['pass_rate']}%")
        print(f"  C (memoria arricchita):  {results_c['summary']['pass_rate']}%")
        print(f"\n  Δ B-A: {comparison['analisi']['miglioramento_B_vs_A']:+.1f}%")
        print(f"  Δ C-B: {comparison['analisi']['miglioramento_C_vs_B']:+.1f}%")
        print(f"  Δ C-A: {comparison['analisi']['miglioramento_totale_C_vs_A']:+.1f}%")

        # Salva rapporto completo
        out_file = Path(__file__).parent / "test_abc_calcolatore_locale.json"
        out_file.write_text(json.dumps(comparison, indent=2, ensure_ascii=False))
        print(f"\nRapporto salvato in: {out_file}")

        return comparison


if __name__ == "__main__":
    main()
