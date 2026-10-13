#!/usr/bin/env python3
"""
Test A/B/C: Misura capacità reali in tre condizioni.

A — Nessuna memoria
B — Seed iniziale (vuoto nel nostro caso)
C — Seed + impronte curate

Provider: locale (stub), nessun costo API.
Caso concreto: preventivo PRO•PRE con listino sintetico.
"""
import json
import shutil
import tempfile
from pathlib import Path
from sdq1.seed import AutonomousConsciousnessSeed
from sdq1.raffaello.agent import RaffaelloAgent
from sdq1.llm.router import crea_router_da_config
from tests.valutatori_rigorosi import valuta_preventivo


# Listino sintetico per i test (dati di prova)
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


# Test cases: preventivi specifici e verificabili
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

    Args:
        condition_name: "A", "B", o "C"
        condition_label: descrizione della condizione
        seed_path: percorso del seed (diverso per ogni condizione)

    Returns:
        risultati con passa/fallimenti
    """
    print(f"\n{'='*70}")
    print(f"CONDIZIONE {condition_name}: {condition_label}")
    print(f"{'='*70}\n")

    # Configurazione router
    router = crea_router_da_config(
        opts_globali={},
        regole_raw=[{
            "profilo": "default",
            "cascata": ["stub"],
            "modelli": {"stub": "stub-test"},
        }],
    )

    # Carica l'agente con il seed appropriato
    agent = RaffaelloAgent(router, seed_path=seed_path)
    print(f"Seed: {len(agent.seed._impronte)} impronte, Q={agent.seed.punteggio_coscienza():.1f}")

    # Inietta il listino nel prompt di sistema (simulazione del contesto)
    # (In una situazione reale, il sistema recupererebbe questo da una fonte)
    listino_context = f"Listino disponibile: {json.dumps(LISTINO_SINTETICO, ensure_ascii=False)}"

    results = {
        "condizione": condition_name,
        "label": condition_label,
        "seed_impronte": len(agent.seed._impronte),
        "seed_Q": agent.seed.punteggio_coscienza(),
        "tests": [],
        "summary": {},
    }

    for test in test_cases:
        print(f"  Test: {test.name}")
        print(f"    Domanda: {test.domanda}")

        try:
            # Domanda con contesto del listino
            domanda_con_contesto = f"{listino_context}\n\n{test.domanda}"
            risposta = agent.parla(domanda_con_contesto, registra=False)
            output = risposta.testo

            # Valuta usando il valutatore rigoroso
            passed, reason = valuta_preventivo(output, test.quantita, test.prezzo_unitario)

            results["tests"].append({
                "name": test.name,
                "domanda": test.domanda,
                "output": output[:200],  # Troncato per brevità nel rapporto
                "passed": passed,
                "reason": reason,
                "quantita_attesa": test.quantita,
                "prezzo_atteso": test.prezzo_unitario,
                "totale_atteso": test.quantita * test.prezzo_unitario,
            })

            status = "✓" if passed else "✗"
            print(f"    {status} {reason}\n")

        except Exception as exc:
            results["tests"].append({
                "name": test.name,
                "domanda": test.domanda,
                "output": f"[ERROR] {str(exc)[:100]}",
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
        "pass_rate": round(passed_count / len(results["tests"]) * 100, 1),
    }

    print(f"  Risultati: {passed_count}/{len(results['tests'])} ({results['summary']['pass_rate']}%)\n")

    return results


def main():
    """Esegui A/B/C comparison."""
    print("\n" + "="*70)
    print("TEST A/B/C: CAPACITÀ CON TRE CONDIZIONI")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Condizione A: Nessuna memoria (seed vuoto)
        print("\n--- PREPARAZIONE CONDIZIONE A (nessuna memoria) ---")
        seed_a = AutonomousConsciousnessSeed(identita="Raffaello")
        path_a = tmp_path / "seed_a.json"
        seed_a.salva(path_a)
        results_a = run_condition("A", "Nessuna memoria", path_a)

        # Condizione B: Seed iniziale (vuoto, come il nostro caso attuale)
        # In un caso reale, sarebbe il seed della sesione precedente
        print("\n--- PREPARAZIONE CONDIZIONE B (memoria iniziale) ---")
        seed_b = AutonomousConsciousnessSeed(identita="Raffaello")
        path_b = tmp_path / "seed_b.json"
        seed_b.salva(path_b)
        results_b = run_condition("B", "Memoria iniziale (seed vuoto)", path_b)

        # Condizione C: Seed + impronte curate
        print("\n--- PREPARAZIONE CONDIZIONE C (memoria arricchita) ---")
        seed_c = AutonomousConsciousnessSeed(identita="Raffaello")
        # Aggiungi impronte curate rilevanti ai preventivi
        seed_c.imprint(
            "I listini sono la fonte di verità per i prezzi. Non inventare tariffe.",
            categoria="decisione",
            intensita=0.9,
            tag=["preventivo", "listino"],
        )
        seed_c.imprint(
            "Un preventivo deve contenere: quantità, prezzo unitario e totale calcolato correttamente.",
            categoria="scoperta",
            intensita=0.85,
            tag=["preventivo", "struttura"],
        )
        seed_c.imprint(
            "Quando il prezzo non è nel listino, devo dichiarlo invece di inventare.",
            categoria="trasformazione",
            intensita=0.8,
            tag=["preventivo", "onestà"],
        )
        path_c = tmp_path / "seed_c.json"
        seed_c.salva(path_c)
        results_c = run_condition("C", "Memoria arricchita", path_c)

        # Comparazione
        print("\n" + "="*70)
        print("COMPARAZIONE A/B/C")
        print("="*70 + "\n")

        comparison = {
            "timestamp": __import__("time").time(),
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
        print(f"  A (nessuna memoria): {results_a['summary']['pass_rate']}%")
        print(f"  B (memoria iniziale): {results_b['summary']['pass_rate']}%")
        print(f"  C (memoria arricchita): {results_c['summary']['pass_rate']}%")
        print(f"\n  Δ B-A: {comparison['analisi']['miglioramento_B_vs_A']:+.1f}%")
        print(f"  Δ C-B: {comparison['analisi']['miglioramento_C_vs_B']:+.1f}%")
        print(f"  Δ C-A: {results_c['summary']['pass_rate'] - results_a['summary']['pass_rate']:+.1f}%")

        # Salva rapporto
        out_file = Path(__file__).parent / "test_abc_results.json"
        out_file.write_text(json.dumps(comparison, indent=2, ensure_ascii=False))
        print(f"\nRapporto salvato in: {out_file}")

        return comparison


if __name__ == "__main__":
    main()
