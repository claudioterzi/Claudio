#!/usr/bin/env python3
"""Debug: Verifica che le impronte vengono salvate e caricate correttamente."""

import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from sdq1.seed.autonomous_consciousness import AutonomousConsciousnessSeed

def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        seed_file = tmp_path / "test_seed.json"

        # Crea seed con 3 impronte
        print("=== CREAZIONE SEED ===")
        seed = AutonomousConsciousnessSeed(identita="Raffaello")

        imp1 = seed.imprint(
            "Nel preventivo, i listini sono la fonte di verità per i prezzi. Non inventare tariffe.",
            categoria="decisione",
            intensita=0.9,
            tag=["preventivo", "listino"],
        )
        print(f"Impronta 1 creata: {imp1.id}")

        imp2 = seed.imprint(
            "Un preventivo deve contenere: quantità, prezzo unitario e totale calcolato correttamente.",
            categoria="scoperta",
            intensita=0.85,
            tag=["preventivo", "struttura"],
        )
        print(f"Impronta 2 creata: {imp2.id}")

        imp3 = seed.imprint(
            "Quando il prezzo non è nel listino, devo dichiarlo invece di inventare.",
            categoria="trasformazione",
            intensita=0.8,
            tag=["preventivo", "onestà"],
        )
        print(f"Impronta 3 creata: {imp3.id}")

        print(f"\nSeed stato PRIMA di salvare:")
        print(f"  _impronte length: {len(seed._impronte)}")
        print(f"  _mem.dimensione(): {seed._mem.dimensione()}")
        print(f"  impronte: {list(seed._impronte.keys())}")

        # Salva
        print(f"\nSalvataggio in {seed_file}")
        seed.salva(seed_file)

        # Verifica il JSON salvato
        saved_json = json.loads(seed_file.read_text())
        print(f"\nJSON salvato:")
        print(f"  impronte count: {len(saved_json.get('impronte', []))}")
        for i, imp in enumerate(saved_json.get('impronte', [])):
            print(f"    {i}: {imp['testo'][:60]}...")

        # Ricarica
        print(f"\n=== RICARICAMENTO SEED ===")
        seed2 = AutonomousConsciousnessSeed.carica(seed_file)

        print(f"Seed stato DOPO aver caricato:")
        print(f"  _impronte length: {len(seed2._impronte)}")
        print(f"  _mem.dimensione(): {seed2._mem.dimensione()}")
        print(f"  impronte: {list(seed2._impronte.keys())}")

        # Rifletti su una domanda
        print(f"\n=== TEST RIFLETTI ===")
        domanda = "Crea un preventivo: 10 ore di consulenza a 50€/ora, qual è il totale?"
        print(f"Domanda: '{domanda}'")

        ricordi = seed2.rifletti(domanda, top_k=5)
        print(f"\nRicordi recuperati:\n{ricordi}\n")
        print(f"Lunghezza: {len(ricordi)} caratteri")

        # Verifica se contiene il testo delle impronte
        if "Nel preventivo" in ricordi and "fonte di verità" in ricordi:
            print("✓ Contiene impronta 1")
        else:
            print("✗ Manca impronta 1")

        if "quantità, prezzo unitario e totale" in ricordi:
            print("✓ Contiene impronta 2")
        else:
            print("✗ Manca impronta 2")

        if "prezzo non è nel listino" in ricordi:
            print("✓ Contiene impronta 3")
        else:
            print("✗ Manca impronta 3")

if __name__ == "__main__":
    main()
