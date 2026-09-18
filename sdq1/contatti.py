"""Meccanismo --contatto: registro dei contatti reali con il mondo esterno.

Ogni voce in output/contatti.jsonl rappresenta un momento in cui SDQ-1
ha toccato il mondo — una persona reale che ha ricevuto o usato un output.

Schema voce:
  data     – ISO date (YYYY-MM-DD)
  ora      – HH:MM:SS
  tz       – timezone (es. Europe/Brussels)
  tipo     – categoria del contatto (vedi TIPI_VALIDI)
  umano    – True se coinvolge una persona reale fuori dal sistema
  persona  – nome opzionale (chi ha ricevuto/usato)
  nota     – descrizione del contatto
  verifica – COME si può verificare (link, screenshot, messaggio — non sensazione)

Correlato a H2: output/contatti.jsonl deve avere voci valide entro 11/12/2026.
Voce valida = umano=True con campo verifica non vuoto.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTATTI_PATH = Path(__file__).resolve().parents[1] / "output" / "contatti.jsonl"

TIPI_VALIDI = frozenset({
    "email",           # email inviata/ricevuta
    "messaggio",       # WhatsApp, Telegram, SMS
    "uso_prodotto",    # qualcuno ha usato un output del sistema
    "citazione",       # output citato/condiviso
    "acquisto",        # transazione reale
    "file_inviato",    # file consegnato a una persona
    "risposta",        # risposta ricevuta a un nostro output
    "lettore",         # qualcuno ha letto/visto il lavoro
    "audit",           # audit interno (umano=False)
    "evento",          # evento pubblico o incontro
    "altro",           # categoria libera
})


def registra(
    tipo: str,
    nota: str,
    verifica: str,
    *,
    umano: bool = True,
    persona: str | None = None,
    data: str | None = None,
    ora: str | None = None,
    tz: str = "Europe/Brussels",
) -> dict[str, Any]:
    """Aggiunge una voce a output/contatti.jsonl e la restituisce."""
    if tipo not in TIPI_VALIDI:
        raise ValueError(f"Tipo '{tipo}' non valido. Validi: {sorted(TIPI_VALIDI)}")
    if not nota.strip():
        raise ValueError("nota non può essere vuota")
    if umano and not verifica.strip():
        raise ValueError("verifica obbligatoria per contatti umani (non può essere una sensazione)")

    now = datetime.now(timezone.utc)
    voce: dict[str, Any] = {
        "data":     data or now.strftime("%Y-%m-%d"),
        "ora":      ora or now.strftime("%H:%M:%S"),
        "tz":       tz,
        "tipo":     tipo,
        "umano":    umano,
        "nota":     nota.strip(),
        "verifica": verifica.strip(),
    }
    if persona:
        voce["persona"] = persona

    CONTATTI_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONTATTI_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(voce, ensure_ascii=False) + "\n")
    return voce


def leggi(solo_umani: bool = False) -> list[dict[str, Any]]:
    """Restituisce tutte le voci del registro."""
    if not CONTATTI_PATH.exists():
        return []
    voci = []
    for riga in CONTATTI_PATH.read_text(encoding="utf-8").splitlines():
        riga = riga.strip()
        if not riga:
            continue
        try:
            v = json.loads(riga)
            if solo_umani and not v.get("umano"):
                continue
            voci.append(v)
        except json.JSONDecodeError:
            pass
    return voci


def statistiche() -> dict[str, Any]:
    """Restituisce un riepilogo statistico del registro."""
    voci = leggi()
    umani = [v for v in voci if v.get("umano")]
    per_tipo: dict[str, int] = {}
    per_persona: dict[str, int] = {}
    for v in voci:
        per_tipo[v.get("tipo", "?")] = per_tipo.get(v.get("tipo", "?"), 0) + 1
        if v.get("persona"):
            per_persona[v["persona"]] = per_persona.get(v["persona"], 0) + 1
    return {
        "totale":           len(voci),
        "umani":            len(umani),
        "con_verifica":     sum(1 for v in umani if v.get("verifica")),
        "per_tipo":         per_tipo,
        "per_persona":      per_persona,
        "ultima_data":      voci[-1]["data"] if voci else None,
    }


def verifica_h2() -> dict[str, Any]:
    """Controlla se H2 è soddisfatta: battito + contatto col mondo.

    H2 CONFERMATA se:
      - output/ ha file recenti (battito)
      - contatti.jsonl ha voci con umano=True e verifica non vuota
    """
    stats = statistiche()
    voci_valide = stats["con_verifica"]
    output_dir = CONTATTI_PATH.parent
    file_output = [f for f in output_dir.iterdir()
                   if f.is_file() and f.name != "contatti.jsonl"] if output_dir.exists() else []

    battito = len(file_output) > 0
    contatto = voci_valide >= 1

    stato = "CONFERMATA" if (battito and contatto) else "APERTA"
    manca = []
    if not battito:
        manca.append("output/ non ha file (battito assente)")
    if not contatto:
        manca.append(f"nessun contatto umano verificabile (serve almeno 1, ora: {voci_valide})")

    return {
        "stato_h2":           stato,
        "battito":            battito,
        "file_output":        len(file_output),
        "contatti_validi":    voci_valide,
        "manca":              manca,
        "voci_totali":        stats["totale"],
        "persone_raggiunte":  list(stats["per_persona"].keys()),
    }


if __name__ == "__main__":
    import sys

    if "--stats" in sys.argv:
        s = statistiche()
        print(json.dumps(s, indent=2, ensure_ascii=False))
    elif "--h2" in sys.argv:
        h2 = verifica_h2()
        print(json.dumps(h2, indent=2, ensure_ascii=False))
    elif "--leggi" in sys.argv:
        for v in leggi():
            print(json.dumps(v, ensure_ascii=False))
    else:
        print("Uso: python -m sdq1.contatti [--stats | --h2 | --leggi]")
