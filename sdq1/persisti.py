"""
Persistenza e ridondanza SDQ-1.

Aggrega lo stato chiave dei moduli (battito, radar, predittivo, ipotesi)
in output/stato_sdq1.json — file tracciato da git — e opzionalmente
fa commit + push automatico.

Uso:
    python -m sdq1.persisti              # salva stato + commit + push
    python -m sdq1.persisti --solo-stato # solo aggiorna il file JSON
"""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path(__file__).parent.parent / "output"
STATO_FILE = OUTPUT_DIR / "stato_sdq1.json"
ROOT = Path(__file__).parent.parent


def _leggi_ultimo(cartella: str, pattern: str = "*.json") -> dict[str, Any]:
    """Legge il file più recente in una cartella output."""
    d = OUTPUT_DIR / cartella
    if not d.exists():
        return {}
    files = sorted(d.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        return {}
    try:
        return json.loads(files[0].read_text(encoding="utf-8"))
    except Exception:
        return {}


def _leggi_ipotesi() -> list[dict[str, Any]]:
    p = ROOT / "registro_ipotesi.json"
    if not p.exists():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return list(raw.values())
        return raw
    except Exception:
        return []


def _leggi_contatti() -> int:
    p = ROOT / "output" / "contatti.jsonl"
    if not p.exists():
        return 0
    try:
        return sum(1 for r in p.read_text(encoding="utf-8").splitlines() if r.strip())
    except Exception:
        return 0


def aggrega_stato() -> dict[str, Any]:
    """Costruisce snapshot completo dello stato SDQ-1."""
    battito = _leggi_ultimo("battito")
    radar = _leggi_ultimo("radar")
    predittivo = _leggi_ultimo("predittivo")
    ipotesi = _leggi_ipotesi()

    aperte = [h for h in ipotesi if h.get("stato") == "APERTA"]
    confermate = [h for h in ipotesi if h.get("stato") == "CONFERMATA"]

    return {
        "timestamp": time.time(),
        "data": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "battito": {
            "stato": battito.get("stato", "?"),
            "moduli_ok": battito.get("moduli_ok", "?"),
            "contatti_umani": battito.get("contatti_umani", 0),
            "data": battito.get("data", "?"),
        },
        "radar": {
            "energia_sistema": radar.get("indici", {}).get("energia_sistema", radar.get("energia_sistema")),
            "vitalita_esterna": radar.get("indici", {}).get("vitalita_esterna", radar.get("vitalita_esterna")),
            "tensione_interna": radar.get("indici", {}).get("tensione_interna", radar.get("tensione_interna")),
            "indice_morale": radar.get("indici", {}).get("indice_morale", radar.get("indice_morale")),
            "stato": radar.get("stato_narrativo", radar.get("stato")),
        },
        "ipotesi": {
            "totale": len(ipotesi),
            "aperte": len(aperte),
            "confermate": len(confermate),
            "ids_aperte": [h.get("id") for h in aperte],
        },
        "predittivo": {
            "raccomandazione": predittivo.get("raccomandazione", ""),
            "scenario_probabile": next(
                (s["descrizione"] for s in predittivo.get("scenari", []) if s.get("tipo") == "probabile"),
                "",
            ),
            "data": predittivo.get("data", ""),
        },
        "contatti_umani": _leggi_contatti(),
    }


def salva_stato() -> Path:
    """Scrive stato_sdq1.json."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stato = aggrega_stato()
    STATO_FILE.write_text(json.dumps(stato, indent=2, ensure_ascii=False, default=str),
                          encoding="utf-8")
    return STATO_FILE


def _git(cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run(["git"] + cmd, cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def commit_e_push(messaggio: str = "") -> dict[str, Any]:
    """Commit dello stato corrente + push al branch remoto."""
    salva_stato()

    branch_code, branch = _git(["rev-parse", "--abbrev-ref", "HEAD"])
    branch = branch.strip() if branch_code == 0 else "claude/rosso-rosso-rosso-ure5A"

    if not messaggio:
        data = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        messaggio = f"stato SDQ-1: {data}"

    _git(["add", "output/stato_sdq1.json", "SESSIONE.md",
          "registro_ipotesi.json", "output/contatti.jsonl"])

    code, out = _git([
        "commit",
        "--author=Claude <noreply@anthropic.com>",
        "-m", messaggio + "\n\nhttps://claude.ai/code/session_01R5Pb86uUk91bZXzV5etqeU",
    ])

    if code != 0 and "nothing to commit" in out:
        return {"status": "nessuna_modifica", "branch": branch}

    push_code, push_out = _git(["push", "-u", "origin", branch])
    esito = {
        "status": "ok" if push_code == 0 else "push_fallito",
        "branch": branch,
        "commit": out.split("\n")[0],
        "push": push_out.split("\n")[0],
    }
    try:
        from sdq1.notifiche import notifica_completato
        icona = "✅" if esito["status"] == "ok" else "❌"
        notifica_completato(f"Persisti {icona}", [
            f"Branch: <code>{branch}</code>",
            f"Status: {esito['status']}",
        ])
    except Exception:
        pass
    return esito


def main():
    import sys
    solo_stato = "--solo-stato" in sys.argv

    print("[persisti] Aggregazione stato SDQ-1...")
    stato = aggrega_stato()

    print(f"  battito:  {stato['battito']['stato']}")
    r = stato["radar"]
    morale = r['indice_morale'] or 0.0
    tensione = r['tensione_interna'] or 0.0
    print(f"  radar:    morale {morale:.3f}  tensione {tensione:.3f}  [{r['stato']}]")
    print(f"  ipotesi:  {stato['ipotesi']['aperte']} aperte / {stato['ipotesi']['confermate']} confermate")
    print(f"  contatti: {stato['contatti_umani']} umani")

    if solo_stato:
        path = salva_stato()
        print(f"\n[persisti] Stato salvato → {path}")
    else:
        print("\n[persisti] Commit + push...")
        result = commit_e_push()
        print(f"  status: {result['status']}")
        if result.get("commit"):
            print(f"  commit: {result['commit']}")
        if result.get("push"):
            print(f"  push:   {result['push']}")


if __name__ == "__main__":
    main()
