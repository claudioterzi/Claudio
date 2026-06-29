"""Script operativo: sequenza di attivazione R³∞.

Esegue il ciclo rituale completo: Rosso → Raffaello → Updater → Applica.
    python -m rituals.scripts.attiva
"""
from __future__ import annotations

import json

from ..triggers import REGISTRO, esegui_rito


def attiva() -> dict:
    ctx: dict = {"osservazione": "avvio", "energia": 0.6}
    for rito in ("Rosso", "Raffaello", "Updater", "Applica"):
        ctx = esegui_rito(rito, ctx)
    return ctx


if __name__ == "__main__":
    print(f"Riti disponibili: {sorted(REGISTRO)}")
    print(json.dumps(attiva(), ensure_ascii=False, indent=2, default=str))
