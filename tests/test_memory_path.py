#!/usr/bin/env python3
"""
Test della TRACCIA MEMORIA: dimostra che seed.rifletti() è chiamato
e che i risultati arrivano al provider.

Non misura capacità — misura il collegamento tecnico.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from sdq1.seed import AutonomousConsciousnessSeed
from sdq1.raffaello.agent import RaffaelloAgent
from sdq1.llm.router import crea_router_da_config

logging.basicConfig(level=logging.DEBUG, format="%(name)s - %(message)s")


# Variabile globale per registrare le chiamate
TRACKING_CALLS = []


def monkey_patch_stub():
    """Monkey-patch lo stub per registrare il contesto."""
    from sdq1.llm.providers.stub_provider import StubProvider

    original_completa = StubProvider._completa_impl

    def tracked_completa_impl(self, sistema: str, utente: str) -> tuple[str, dict]:
        call_record = {
            "sistema_length": len(sistema),
            "sistema_preview": sistema[:200],
            "utente_length": len(utente),
            "utente_preview": utente[:200],
            "conteneva_seed_data": "syntetico_impronta_1" in sistema or "syntetico_impronta_1" in utente,
        }
        TRACKING_CALLS.append(call_record)
        return original_completa(self, sistema, utente)

    StubProvider._completa_impl = tracked_completa_impl


def test_memory_path():
    """
    1. Crea un seed con un'impronta sintetica riconoscibile
    2. Chiede qualcosa di correlato
    3. Verifica che l'impronta sia stata recuperata
    4. Verifica che sia arrivata al provider
    """
    print("\n" + "=" * 70)
    print("TEST TRACCIA MEMORIA")
    print("=" * 70)

    tmp_seed_path = Path("/tmp/test_memory_seed.json")

    # Step 1: Crea seed con impronta sintetica
    print("\nStep 1: Creazione seed con impronta sintetica...")
    seed = AutonomousConsciousnessSeed(identita="Raffaello")
    seed.imprint(
        "syntetico_impronta_1: Ho imparato che i limiti sono libertà",
        categoria="scoperta",
        intensita=0.9,
        tag=["sintetico", "test_memory"],
    )
    seed.salva(tmp_seed_path)
    print(f"  ✓ Seed creato: {len(seed._impronte)} impronte, Q={seed.punteggio_coscienza():.1f}")

    # Step 2: Configura router e monkey-patch lo stub
    print("\nStep 2: Configurazione del router e setup tracking...")
    monkey_patch_stub()
    router = crea_router_da_config(
        opts_globali={},
        regole_raw=[{
            "profilo": "default",
            "cascata": ["stub"],
            "modelli": {"stub": "stub-test"},
        }],
    )
    print("  ✓ Router configurato, stub tracciante attivo")

    # Step 3: Carma seed e fai una domanda
    print("\nStep 3: Caricamento seed e domanda correlata...")
    agent = RaffaelloAgent(router, seed_path=tmp_seed_path)
    print(f"  Seed caricato: {len(agent.seed._impronte)} impronte")

    # Domanda correlata all'impronta sintetica
    domanda = "Cosa hai imparato sui limiti?"
    print(f"  Domanda: {domanda}")

    # Step 4: Esegui la chiamata
    print("\nStep 4: Esecuzione della chiamata...")
    risposta = agent.parla(domanda, registra=False)
    print(f"  Risposta: {risposta.testo}")

    # Step 5: Verifica il collegamento
    print("\nStep 5: Verifica del collegamento memoria→provider...")

    # 5a: Verifica che seed.rifletti() abbia trovato l'impronta
    ricordi = agent.seed.rifletti(domanda)
    has_synthetic_impronta = "syntetico_impronta_1" in ricordi
    print(f"  5a. seed.rifletti() ha trovato l'impronta sintetica: {has_synthetic_impronta}")
    if has_synthetic_impronta:
        print(f"      Anteprima: {ricordi[:150]}")

    # 5b: Verifica che sia arrivata al provider
    if TRACKING_CALLS:
        last_call = TRACKING_CALLS[-1]
        had_synthetic_in_context = last_call["conteneva_seed_data"]
        print(f"  5b. Provider ha ricevuto il dato sintetico: {had_synthetic_in_context}")
        print(f"      Sistema length: {last_call['sistema_length']}")
        print(f"      Sistema preview: {last_call['sistema_preview']}")
    else:
        print(f"  5b. Nessuna chiamata registrata al provider")
        had_synthetic_in_context = False

    # Step 6: Rapporto
    print("\n" + "=" * 70)
    print("RISULTATI DELLA TRACCIA MEMORIA")
    print("=" * 70)

    report = {
        "timestamp": __import__("time").time(),
        "seed_path": str(tmp_seed_path),
        "impronta_sintetica": "syntetico_impronta_1: Ho imparato che i limiti sono libertà",
        "domanda": domanda,
        "seed_rifletti_trovato_impronta": has_synthetic_impronta,
        "provider_ricevuto_dato": had_synthetic_in_context,
        "provider_calls": TRACKING_CALLS,
        "conclusione": (
            "✓ COLLEGAMENTO VERIFICATO" if (has_synthetic_impronta and had_synthetic_in_context)
            else "✗ COLLEGAMENTO ROTTO" if not has_synthetic_impronta
            else "⚠ IMPRONTA RECUPERATA MA NON INVIATA AL PROVIDER"
        ),
    }

    print(f"\n{report['conclusione']}")
    print(f"  • seed.rifletti() ha trovato l'impronta: {has_synthetic_impronta}")
    print(f"  • Provider ha ricevuto il dato: {had_synthetic_in_context}")
    print(f"  • Provider calls: {len(TRACKING_CALLS)}")

    # Salva rapporto
    out_file = Path(__file__).parent / "test_memory_path_report.json"
    out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nRapporto salvato in: {out_file}")

    return report


if __name__ == "__main__":
    test_memory_path()
