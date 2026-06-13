"""Monitor SDQ-1 — quadro unico dello stato del sistema.

Aggrega battito, radar emozionale, ultima proiezione predittiva,
registro ipotesi e contatti in un report leggibile.

Uso:
    python -m sdq1.monitor          # report testuale
    python -m sdq1.monitor --json   # output JSON
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]


def _leggi_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _ultimo_file(pattern_dir: Path, glob: str) -> dict[str, Any]:
    if not pattern_dir.exists():
        return {}
    files = sorted(pattern_dir.glob(glob), reverse=True)
    if not files:
        return {}
    return _leggi_json(files[0])


def stato_completo() -> dict[str, Any]:
    """Restituisce lo stato completo del sistema come dizionario."""

    # Battito
    battito = _ultimo_file(REPO / "output" / "battito", "battito_*.json")

    # Radar
    radar = _ultimo_file(REPO / "output" / "radar", "radar_*.json")

    # Proiezione
    proiezione = _ultimo_file(REPO / "output" / "predittivo", "proiezione_*.json")

    # Ipotesi
    ipotesi = _leggi_json(REPO / "registro_ipotesi.json")
    h_confermate = [k for k, v in ipotesi.items() if v.get("stato") == "CONFERMATA"]
    h_aperte = [k for k, v in ipotesi.items() if v.get("stato") == "APERTA"]

    # Contatti
    contatti_path = REPO / "output" / "contatti.jsonl"
    contatti = []
    if contatti_path.exists():
        try:
            for riga in contatti_path.read_text(encoding="utf-8").strip().splitlines():
                contatti.append(json.loads(riga))
        except Exception:
            pass
    n_umani = sum(1 for c in contatti if c.get("umano") is True)
    persone = list({c.get("persona") for c in contatti if c.get("persona")})

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "battito": {
            "stato":     battito.get("stato", "SCONOSCIUTO"),
            "moduli":    f"{battito.get('moduli_ok', '?')}/{battito.get('moduli_totali', '?')}",
            "docs":      f"{battito.get('docs_ok', '?')}/{battito.get('docs_totali', '?')}",
            "data":      battito.get("data", "?"),
        },
        "radar": {
            "indice_morale":    radar.get("indici", {}).get("indice_morale"),
            "stato_narrativo":  radar.get("stato_narrativo"),
            "energia":          radar.get("indici", {}).get("energia_sistema"),
            "vitalita":         radar.get("indici", {}).get("vitalita_esterna"),
            "tensione":         radar.get("indici", {}).get("tensione_interna"),
            "data":             radar.get("data"),
        },
        "proiezione": {
            "scenario_probabile": next(
                (s.get("descrizione", "")[:120]
                 for s in proiezione.get("scenari", [])
                 if s.get("tipo") == "probabile"),
                None,
            ),
            "raccomandazione": (proiezione.get("raccomandazione") or "")[:120],
            "data":            proiezione.get("data"),
        },
        "ipotesi": {
            "confermate": h_confermate,
            "aperte":     h_aperte,
        },
        "contatti": {
            "umani":   n_umani,
            "persone": persone,
        },
    }


def _barra(valore: float | None, larghezza: int = 20) -> str:
    if valore is None:
        return "?" * larghezza
    filled = int(round(valore * larghezza))
    return "█" * filled + "░" * (larghezza - filled)


def report_testo(stato: dict[str, Any]) -> str:
    b = stato["battito"]
    r = stato["radar"]
    p = stato["proiezione"]
    ip = stato["ipotesi"]
    ct = stato["contatti"]

    indice = r.get("indice_morale")
    barra = _barra(indice)
    indice_str = f"{indice:.3f}" if indice is not None else "?"

    linee = [
        "╔══════════════════════════════════════╗",
        "║         SDQ-1  MONITOR               ║",
        "╚══════════════════════════════════════╝",
        "",
        f"  Battito:  {b['stato']} — moduli {b['moduli']}  docs {b['docs']}  ({b['data']})",
        "",
        f"  Indice morale:  {indice_str}  [{barra}]",
        f"  Stato:          {r.get('stato_narrativo', '?')}",
        f"  Energia:        {r.get('energia', '?'):.3f}   Vitalità: {r.get('vitalita', '?'):.3f}   Tensione: {r.get('tensione', '?'):.3f}",
        "",
        f"  Ipotesi confermate: {', '.join(ip['confermate']) or 'nessuna'}",
        f"  Ipotesi aperte:     {', '.join(ip['aperte']) or 'nessuna'}",
        "",
        f"  Contatti umani: {ct['umani']}  —  persone: {', '.join(ct['persone']) or 'nessuna'}",
        "",
    ]

    if p.get("scenario_probabile"):
        linee += [
            "  Proiezione 30gg:",
            f"    {p['scenario_probabile']}",
        ]
    if p.get("raccomandazione"):
        linee += [
            "",
            f"  Azione: {p['raccomandazione']}",
        ]

    linee += [""]
    return "\n".join(linee)


if __name__ == "__main__":
    stato = stato_completo()
    if "--json" in sys.argv:
        print(json.dumps(stato, indent=2, ensure_ascii=False))
    else:
        print(report_testo(stato))
