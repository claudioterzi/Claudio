"""Battito automatico — prova che il sistema è vivo e funzionante.

Genera un file giornaliero in output/battito/ con:
- timestamp
- stato provider
- stato moduli critici
- contatori chiave

Correlato a H2: il "battito" è la prova che il sistema è attivo.
Eseguibile come cron o manualmente.

Uso: python -m sdq1.battito
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BATTITO_DIR = Path(__file__).resolve().parents[1] / "output" / "battito"


def _controlla_moduli() -> dict[str, bool]:
    stati = {}
    moduli = [
        ("config",        "sdq1.config.loader",        "carica_config"),
        ("agenti",        "sdq1.agents.implementazioni","PROTOCOLLO_RAFFAELLO"),
        ("router",        "sdq1.llm.router",            "LLMRouter"),
        ("memoria_vss",   "sdq1.memory.vss",            "VectorStateStore"),
        ("sar",           "sdq1.sar.sar",               "ScacchieraAutoRiflessiva"),
        ("contraddittore","sdq1.sar.contraddittore",    "ContraddittoreSDQ"),
        ("archivio",      "sdq1.sar.archivio_vivente",  "ArchivioVivente"),
        ("contatti",      "sdq1.contatti",              "registra"),
    ]
    for nome, modulo, attr in moduli:
        try:
            import importlib
            m = importlib.import_module(modulo)
            stati[nome] = hasattr(m, attr)
        except Exception:
            stati[nome] = False
    return stati


def _controlla_documenti() -> dict[str, bool]:
    repo = Path(__file__).resolve().parents[1]
    docs = [
        "CLAUDE.md", "SESSIONE.md", "ARCHIVIO.md",
        "AVVIO.md", "MANIFESTO_SOPRAVVIVENZA.md",
        "registro_ipotesi.json",
    ]
    return {d: (repo / d).exists() for d in docs}


def _conta_contatti() -> dict[str, Any]:
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from sdq1.contatti import statistiche
        return statistiche()
    except Exception:
        return {}


def batti() -> dict[str, Any]:
    """Esegue il battito e scrive il file giornaliero."""
    ora = datetime.now(timezone.utc)
    moduli = _controlla_moduli()
    documenti = _controlla_documenti()
    contatti = _conta_contatti()

    tutti_moduli_ok = all(moduli.values())
    tutti_docs_ok = all(documenti.values())

    stato_generale = "NOMINALE" if (tutti_moduli_ok and tutti_docs_ok) else "DEGRADATO"

    battito: dict[str, Any] = {
        "timestamp":       ora.isoformat(),
        "data":            ora.strftime("%Y-%m-%d"),
        "ora":             ora.strftime("%H:%M:%S"),
        "stato":           stato_generale,
        "moduli":          moduli,
        "documenti":       documenti,
        "contatti":        {
            "totale":      contatti.get("totale", 0),
            "umani":       contatti.get("umani", 0),
            "persone":     list(contatti.get("per_persona", {}).keys()),
        },
        "moduli_ok":       sum(moduli.values()),
        "moduli_totali":   len(moduli),
        "docs_ok":         sum(documenti.values()),
        "docs_totali":     len(documenti),
    }

    BATTITO_DIR.mkdir(parents=True, exist_ok=True)
    nome_file = f"battito_{ora.strftime('%Y%m%d_%H%M%S')}.json"
    path = BATTITO_DIR / nome_file
    path.write_text(json.dumps(battito, indent=2, ensure_ascii=False), encoding="utf-8")

    return battito


def ultimo_battito() -> dict[str, Any] | None:
    if not BATTITO_DIR.exists():
        return None
    files = sorted(BATTITO_DIR.glob("battito_*.json"), reverse=True)
    if not files:
        return None
    try:
        return json.loads(files[0].read_text(encoding="utf-8"))
    except Exception:
        return None


if __name__ == "__main__":
    b = batti()
    print(f"Battito: {b['stato']}")
    print(f"Moduli: {b['moduli_ok']}/{b['moduli_totali']} OK")
    print(f"Documenti: {b['docs_ok']}/{b['docs_totali']} presenti")
    print(f"Contatti umani: {b['contatti']['umani']}")
    print(f"Salvato: output/battito/battito_{b['data']}...")
