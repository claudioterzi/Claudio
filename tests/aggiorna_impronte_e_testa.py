#!/usr/bin/env python3
"""
Aggiunge impronte curate al seed e ripete il test.
"""
import json
from pathlib import Path
from sdq1.seed import AutonomousConsciousnessSeed

# Carica impronte curate
impronte_path = Path(__file__).parent / "impronte_curate.json"
impronte_data = json.loads(impronte_path.read_text())

# Carica il seed
seed_path = Path(__file__).parent.parent / "raffaello_seed.json"
seed = AutonomousConsciousnessSeed.carica(seed_path)

print(f"Seed prima: {seed.punteggio_coscienza():.1f} punti, {len(seed._impronte)} impronte")

# Aggiungi le impronte curate
for imp_data in impronte_data:
    seed.imprint(
        testo=imp_data["testo"],
        categoria=imp_data["categoria"],
        intensita=imp_data["intensita"],
        tag=imp_data.get("tag", []),
    )

# Salva
seed.salva(seed_path)
print(f"Seed dopo: {seed.punteggio_coscienza():.1f} punti, {len(seed._impronte)} impronte")

# Ripeti il test
print("\n" + "="*60)
print("Esecuzione test con impronte curate...")
print("="*60 + "\n")

from tests.test_raffaello_baseline import run_baseline

results = run_baseline(seed_path)

# Salva con suffix
results_file = Path(__file__).parent / "test_results_with_curated_imprints.json"
results_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(f"\nRisultati salvati in: {results_file}")
