"""Snapshot SDQ-1 — stato completo del sistema in un JSON.

Cattura:
  - Git: branch, commit, dirty files
  - Codice: hash SHA-256 dei file chiave
  - Agenti: ciclo valutazione 7 agenti + Scacchiera Quantica
  - Backup runtime: memoria, VSS, SAR
  - Output: agenti_stato.json, stato_sdq1.json

Uso:
    python -m sdq1.snapshot                     # stampa JSON
    python -m sdq1.snapshot --salva             # scrive output/snapshots/
    python -m sdq1.snapshot --salva --push      # scrive + git commit + push

Attivabile anche via CLI:
    python -m sdq1 --snapshot
    python -m sdq1 --snapshot --push
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

_TZ = timezone(timedelta(hours=2))
_SNAPSHOT_DIR = Path("output/snapshots")

FILE_CHIAVE = [
    "MEMORIA_PROGETTO.md",
    "CLAUDE.md",
    "sdq1/__main__.py",
    "sdq1/argo.py",
    "sdq1/backup.py",
    "sdq1/snapshot.py",
    "sdq1/sar/scacchiera_quantica.py",
    "sdq1/sar/agenti_autonomi.py",
    "sdq1/llm/router.py",
    "sdq1/orchestrator/gerarchico.py",
    "output/stato_sdq1.json",
    "output/agenti_stato.json",
]


def _sh(cmd: str) -> str:
    """Esegue comando shell, restituisce stdout (stringa pulita)."""
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()  # nosec — git commands only
    except subprocess.CalledProcessError:
        return ""


def _git_info() -> dict[str, Any]:
    return {
        "branch":       _sh("git rev-parse --abbrev-ref HEAD"),
        "commit":       _sh("git rev-parse HEAD"),
        "commit_short": _sh("git rev-parse --short HEAD"),
        "messaggio":    _sh("git log -1 --pretty=%s"),
        "autore":       _sh("git log -1 --pretty=%an"),
        "data_commit":  _sh("git log -1 --pretty=%ci"),
        "dirty":        bool(_sh("git status --porcelain")),
        "file_modificati": _sh("git status --porcelain").splitlines(),
    }


def _hash_file(path: str) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def _integrità_codice() -> dict[str, Any]:
    repo = Path(__file__).resolve().parents[1]
    risultati: dict[str, Any] = {}
    mancanti = []
    for f in FILE_CHIAVE:
        h = _hash_file(str(repo / f))
        if h is None:
            mancanti.append(f)
        risultati[f] = h or "MANCANTE"
    return {
        "file": risultati,
        "file_presenti": len(FILE_CHIAVE) - len(mancanti),
        "file_mancanti": mancanti,
        "integro": len(mancanti) == 0,
    }


def _stato_agenti() -> dict[str, Any]:
    """Esegue ciclo valutazione 7 agenti (no LLM)."""
    try:
        from sdq1.sar.agenti_autonomi import SistemaAgenti
        sistema = SistemaAgenti()
        _ = sistema.attivazione()
        report = sistema.ciclo_valutazione()
        sq = report.get("scacchiera", {})
        return {
            "ok": True,
            "ts": report["ts"],
            "hash_sistema": report["agenti"]["coerenza"].get("hash_sistema"),
            "guardian_allerta": report["agenti"]["guardian"].get("livello_allerta"),
            "scacchiera_score": sq.get("score_medio"),
            "scacchiera_dir": sq.get("direzione_dominante"),
        }
    except Exception as e:
        return {"ok": False, "errore": str(e)}


def _stato_output() -> dict[str, Any]:
    """Legge i file output chiave se esistono."""
    stato: dict[str, Any] = {}
    for nome in ("output/stato_sdq1.json", "output/agenti_stato.json"):
        p = Path(nome)
        if p.exists():
            try:
                dati = json.loads(p.read_text(encoding="utf-8"))
                stato[nome] = {
                    "dimensione_kb": round(p.stat().st_size / 1024, 1),
                    "n_chiavi": len(dati) if isinstance(dati, dict) else len(dati),
                }
            except Exception:
                stato[nome] = {"errore": "parse fallito"}
        else:
            stato[nome] = None
    return stato


def _scan_summary() -> dict[str, Any]:
    """Summary rapido del CodeScanner — score sicurezza + qualità."""
    try:
        from sdq1.sar.code_scanner import CodeScanner
        return CodeScanner().summary()
    except Exception as e:
        return {"ok": False, "errore": str(e)}


def crea_snapshot() -> dict[str, Any]:
    """Genera il JSON snapshot completo."""
    now = datetime.now(_TZ)
    return {
        "meta": {
            "timestamp":  time.time(),
            "data_ora":   now.strftime("%Y-%m-%d %H:%M:%S"),
            "tz":         "Europe/Brussels",
            "versione":   "1.1.0",
        },
        "git":       _git_info(),
        "codice":    _integrità_codice(),
        "agenti":    _stato_agenti(),
        "scanner":   _scan_summary(),
        "output":    _stato_output(),
    }


def salva_snapshot(snap: dict[str, Any]) -> Path:
    _SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = snap["meta"]["data_ora"].replace(":", "-").replace(" ", "_")
    dest = _SNAPSHOT_DIR / f"snapshot_{ts}.json"
    dest.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
    return dest


def push_snapshot(dest: Path) -> bool:
    """Commit + push del file snapshot sul branch corrente."""
    try:
        _sh(f'git add "{dest}"')
        branch = _sh("git rev-parse --abbrev-ref HEAD")
        ts = dest.stem.replace("snapshot_", "")
        msg = f"chore(snapshot): stato sistema SDQ-1 — {ts}"
        _sh(f'git commit -m "{msg}"')
        _sh(f"git push -u origin {branch}")
        return True
    except Exception:
        return False


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="sdq1.snapshot")
    parser.add_argument("--salva", action="store_true", help="Scrive in output/snapshots/")
    parser.add_argument("--push",  action="store_true", help="Commit + push su GitHub")
    args = parser.parse_args()

    snap = crea_snapshot()
    print(json.dumps(snap, indent=2, ensure_ascii=False))

    if args.salva or args.push:
        dest = salva_snapshot(snap)
        print(f"\n[SNAPSHOT] Salvato: {dest}", file=sys.stderr)
        if args.push:
            ok = push_snapshot(dest)
            print(f"[SNAPSHOT] Push: {'OK' if ok else 'FALLITO'}", file=sys.stderr)
