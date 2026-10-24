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

import copy
import hashlib
import os
import re
import uuid
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


def _snapshot_time(value: Any) -> str:
    """Validate the existing event-time contract; do not invent subsecond precision."""
    if type(value) is not str or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}", value):
        raise ValueError("meta.data_ora must be YYYY-MM-DD HH:MM:SS")
    datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return value


def salva_snapshot(snap: dict[str, Any]) -> Path:
    """Create a new record, never replace an existing pathname.

    Event time remains unchanged. Precise save time is a separate UTC field.
    UUID reduces collisions; exclusive creation is the actual overwrite guard.
    Return a Path only after exact byte readback. This is not a crash/backup
    durability certificate: an interrupted write may leave a partial new file.
    """
    payload = copy.deepcopy(snap)
    if type(payload) is not dict or type(payload.get("meta")) is not dict:
        raise ValueError("Snapshot and meta must be JSON objects")
    event_time = _snapshot_time(payload["meta"].get("data_ora"))
    saved_at = datetime.now(timezone.utc)
    snapshot_id = uuid.uuid4().hex
    payload["meta"]["snapshot_id"] = snapshot_id
    payload["meta"]["saved_at_utc"] = saved_at.isoformat(timespec="microseconds")
    payload["meta"]["snapshot_storage_version"] = 2
    encoded = json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False).encode("utf-8")
    ts = event_time.replace(":", "-").replace(" ", "_")
    save_stamp = saved_at.strftime("%Y%m%dT%H%M%S%fZ")
    dest = _SNAPSHOT_DIR / f"snapshot_{ts}__saved_{save_stamp}__{snapshot_id}.json"
    _SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    with dest.open("xb") as stream:
        written = stream.write(encoded)
        if written != len(encoded):
            raise OSError("Incomplete snapshot write")
        stream.flush()
        os.fsync(stream.fileno())
    if dest.read_bytes() != encoded:
        raise OSError("Snapshot byte readback mismatch")
    return dest


def _snapshot_git(root: Path, *args: str) -> bytes:
    """Checked, bounded Git invocation for the existing snapshot write path."""
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, timeout=30, check=True,
    )
    return result.stdout


def push_snapshot(dest: Path, *, repo_dir: Path | None = None) -> bool:
    """Publish one snapshot and verify its exact remote ref.

    False means publication was not verified, including an ambiguous timeout
    or a readback failure AFTER an accepted push. No retry or rollback occurs.
    Existing callers retain the Path -> bool API. repo_dir is for an explicit
    repository context (including isolated local-Git integration tests).
    """
    root = Path(repo_dir) if repo_dir is not None else Path(__file__).resolve().parents[1]
    try:
        root = root.resolve(strict=True)
        candidate = Path(dest)
        if not candidate.is_absolute():
            candidate = root / candidate
        if candidate.is_symlink() or not candidate.is_file():
            return False
        target = candidate.resolve(strict=True)
        relative = target.relative_to(root).as_posix()
        # Do not stage arbitrary paths or use names as executable shell text.
        if not target.name.startswith("snapshot_") or target.suffix != ".json":
            return False
        encoded = target.read_bytes()
        data = json.loads(encoded)
        event_time = _snapshot_time(data["meta"]["data_ora"])
        record_id = data["meta"].get("snapshot_id")
        if record_id is None:
            record_id = "legacy-sha256:" + hashlib.sha256(encoded).hexdigest()
        elif type(record_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", record_id):
            return False
        branch = _snapshot_git(root, "symbolic-ref", "--quiet", "--short", "HEAD").decode().strip()
        if not branch:
            return False
        _snapshot_git(root, "check-ref-format", "--branch", branch)
        # Readback must use the SAME destination as push, not a different fetch URL.
        push_urls = _snapshot_git(root, "remote", "get-url", "--push", "--all", "origin").decode().splitlines()
        if len(push_urls) != 1 or not push_urls[0]:
            return False
        push_url = push_urls[0]
        # Never commit somebody else's staged changes as a side effect.
        if _snapshot_git(root, "diff", "--cached", "--name-only", "-z"):
            return False
        _snapshot_git(root, "add", "--", relative)
        staged = _snapshot_git(root, "diff", "--cached", "--name-only", "-z")
        if staged not in (b"", os.fsencode(relative) + b"\0"):
            return False
        if staged:
            # The message contract no longer depends on filename/stem parsing.
            message = f"chore(snapshot): stato sistema SDQ-1 — {event_time} [id={record_id}]"
            _snapshot_git(root, "commit", "--only", "-m", message, "--", relative)
        head = _snapshot_git(root, "rev-parse", "--verify", "HEAD").decode().strip()
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", head):
            return False
        if _snapshot_git(root, "show", f"{head}:{relative}") != encoded:
            return False
        if target.read_bytes() != encoded:
            return False
        ref = f"refs/heads/{branch}"
        # Explicit SHA freezes what is pushed. No --force and no implicit refspec.
        _snapshot_git(root, "push", "--porcelain", "--", push_url, f"{head}:{ref}")
        observed = _snapshot_git(root, "ls-remote", "--refs", "--exit-code", "--", push_url, ref)
        return observed.decode().splitlines() == [f"{head}\t{ref}"]
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
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
            print(f"[SNAPSHOT] Push: {'VERIFICATO' if ok else 'NON VERIFICATO'}", file=sys.stderr)
            if not ok:
                sys.exit(1)
