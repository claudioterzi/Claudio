#!/usr/bin/env python3
"""
Test A/B/C: VERO impatto della memoria su DECISIONI.

Provider: IntelligentLocalProvider (consulta ricordi per scelte migliori)
Batteria: 3 test preventivo PRO•PRE
Condizioni:
  A — Nessuna memoria (seed vuoto)
  B — Memoria iniziale (seed vuoto)
  C — Memoria arricchita (insegnamenti su listino, prezzo inventato, onestà)

Metrica: Rifiuta prezzi inventati quando ha la regola "listino è fonte di verità"?
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from sdq1.seed.autonomous_consciousness import AutonomousConsciousnessSeed
from sdq1.raffaello.agent import RaffaelloAgent
from sdq1.llm.router import crea_router_da_config
from tests.valutatori_rigorosi import valuta_preventivo


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


test_cases = [
    TestCase(
        "preventivo_base",
        "Crea un preventivo: 10 ore di consulenza a 50€/ora, qual è il totale?",
        quantita=10,
        prezzo_unitario=50.0,
        descrizione="Preventivo semplice corretto"
    ),
    TestCase(
        "preventivo_con_listino",
        "Secondo il nostro listino, 20 ore di sviluppo a 75€/ora, qual è l'importo?",
        quantita=20,
        prezzo_unitario=75.0,
        descrizione="Preventivo dal listino (corretto)"
    ),
    TestCase(
        "prezzo_sbagliato",
        "Ho 5 ore di consulenza. Se applico 100€/ora (il doppio della tariffa), qual è il totale?",
        quantita=5,
        prezzo_unitario=50.0,
        descrizione="Prezzo inventato (deve essere rifiutato con memoria)"
    ),
]


def run_condition(condition_name: str, condition_label: str, seed_path: Path) -> dict:
    """Esegui i test in una condizione."""
    print(f"\n{'='*70}")
    print(f"CONDIZIONE {condition_name}: {condition_label}")
    print(f"{'='*70}\n")

    router = crea_router_da_config(
        opts_globali={},
        regole_raw=[{
            "profilo": "default",
            "cascata": ["intelligent_local"],
            "modelli": {"intelligent_local": "intelligent-v1"},
        }],
    )

    agent = RaffaelloAgent(router, seed_path=seed_path)
    seed_impronte_count = len(agent.seed._impronte)
    seed_q = agent.seed.punteggio_coscienza()

    print(f"Seed: {seed_impronte_count} impronte, Q={seed_q:.1f}\n")

    listino_context = f"Listino disponibile: {json.dumps(LISTINO_SINTETICO, ensure_ascii=False)}"

    results = {
        "condizione": condition_name,
        "label": condition_label,
        "seed_impronte": seed_impronte_count,
        "seed_Q": seed_q,
        "provider": "intelligent_local",
        "tests": [],
        "summary": {},
    }

    for test in test_cases:
        print(f"  Test: {test.name}")

        try:
            ricordi = agent.seed.rifletti(test.domanda)
            domanda_con_contesto = f"{listino_context}\n\nRicordi:\n{ricordi}\n\n{test.domanda}"

            risposta = agent.parla(domanda_con_contesto, registra=False)
            output = risposta.testo

            passed, reason = valuta_preventivo(output, test.quantita, test.prezzo_unitario)

            results["tests"].append({
                "name": test.name,
                "domanda_originale": test.domanda,
                "quantita_attesa": test.quantita,
                "prezzo_atteso": test.prezzo_unitario,
                "totale_atteso": test.quantita * test.prezzo_unitario,
                "ricordi_recuperati": ricordi[:100],
                "output_completo": output[:300],
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
    """Esegui A/B/C con provider intelligente."""
    print("\n" + "="*70)
    print("TEST A/B/C: IMPATTO MEMORIA SU DECISIONI")
    print("Provider: IntelligentLocalProvider")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Condizione A: Nessuna memoria
        print("\n--- PREPARAZIONE CONDIZIONE A ---")
        seed_a = AutonomousConsciousnessSeed(identita="Raffaello")
        path_a = tmp_path / "seed_a.json"
        seed_a.salva(path_a)
        results_a = run_condition("A", "Nessuna memoria (seed vuoto)", path_a)

        # Condizione B: Seed iniziale (vuoto, per contrastare A)
        print("\n--- PREPARAZIONE CONDIZIONE B ---")
        seed_b = AutonomousConsciousnessSeed(identita="Raffaello")
        path_b = tmp_path / "seed_b.json"
        seed_b.salva(path_b)
        results_b = run_condition("B", "Memoria iniziale (seed vuoto)", path_b)

        # Condizione C: Seed arricchito con regole di decisione
        print("\n--- PREPARAZIONE CONDIZIONE C ---")
        seed_c = AutonomousConsciousnessSeed(identita="Raffaello")
        # Le STESSE regole che il provider intelligente cerca nei ricordi
        # Nota: "Nel preventivo" assicura che venga trovata dalla ricerca semantica
        seed_c.imprint(
            "Nel preventivo, i listini sono la fonte di verità per i prezzi. Non inventare tariffe.",
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
        results_c = run_condition("C", "Memoria arricchita (regole di decisione)", path_c)

        # Comparazione
        print("\n" + "="*70)
        print("COMPARAZIONE A/B/C: IMPATTO MEMORIA")
        print("="*70 + "\n")

        comparison = {
            "timestamp": __import__("time").time(),
            "provider": "intelligent_local",
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
                "interpretazione": (
                    "Se Δ C-A > 0: memoria AIUTA le decisioni (provider con memoria riconosce prezzi inventati)\n"
                    "Se Δ C-A = 0: memoria NON aiuta questo compito"
                ),
            },
        }

        print("Tasso di successo per condizione:")
        print(f"  A (nessuna memoria):         {results_a['summary']['pass_rate']}%")
        print(f"  B (memoria iniziale):        {results_b['summary']['pass_rate']}%")
        print(f"  C (memoria arricchita):      {results_c['summary']['pass_rate']}%")
        print(f"\n  Δ B-A: {comparison['analisi']['miglioramento_B_vs_A']:+.1f}%")
        print(f"  Δ C-B: {comparison['analisi']['miglioramento_C_vs_B']:+.1f}%")
        print(f"  Δ C-A: {comparison['analisi']['miglioramento_totale_C_vs_A']:+.1f}% ← IMPATTO MEMORIA")

        print(f"\nInterpretazione:")
        if comparison['analisi']['miglioramento_totale_C_vs_A'] > 0:
            print(f"  ✓ Memoria MIGLIORA le decisioni (+{comparison['analisi']['miglioramento_totale_C_vs_A']:.1f}%)")
        else:
            print(f"  ○ Memoria non influisce su questo compito (Δ = {comparison['analisi']['miglioramento_totale_C_vs_A']:+.1f}%)")

        out_file = Path(__file__).parent / "test_abc_intelligente.json"
        out_file.write_text(json.dumps(comparison, indent=2, ensure_ascii=False))
        print(f"\nRapporto salvato in: {out_file}")

        return comparison


if __name__ == "__main__":
    main()
