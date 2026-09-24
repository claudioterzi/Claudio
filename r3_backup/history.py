"""R3-HISTORY/1 append-only history collector.

Copies user-supplied historical sources into a snapshot without altering originals.
It intentionally does not scrape private chat platforms or fabricate missing history.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from r3_backup import ORIGIN

HISTORY_PROTOCOL = "R3-HISTORY/1"

DEFAULT_SOURCE_PATHS = [
    "CLAUDE.md",
    "MEMORIA_PROGETTO.md",
    "SESSIONE.md",
    "AVVIO.md",
    "registro_ipotesi.py",
    "docs",
    "output/evoluzione",
    "output/backups",
    "docs/evidenze",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
    elif path.is_dir():
        for item in sorted(path.rglob("*")):
            if item.is_file():
                yield item


def collect_history(
    project_root: Path,
    snapshot_dir: Path,
    *,
    history_inbox: Path | None = None,
    source_paths: list[str] | None = None,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    history_root = snapshot_dir / "history"
    history_root.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    missing: list[str] = []

    candidates = source_paths or DEFAULT_SOURCE_PATHS
    for rel in candidates:
        src = project_root / rel
        if not src.exists():
            missing.append(rel)
            continue
        for item in _iter_files(src):
            relative = item.relative_to(project_root)
            dest = history_root / "project_sources" / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
            records.append({
                "class": "PROJECT_SOURCE",
                "source": str(item),
                "archive_path": dest.relative_to(snapshot_dir).as_posix(),
                "bytes": dest.stat().st_size,
                "sha256": sha256_file(dest),
            })

    inbox = history_inbox
    if inbox is None:
        raw = os.getenv("R3_HISTORY_INBOX", "").strip()
        if raw:
            inbox = Path(raw)
    if inbox is not None:
        inbox = inbox.expanduser().resolve()
        if inbox.exists():
            for item in _iter_files(inbox):
                relative = item.relative_to(inbox)
                dest = history_root / "external_sources" / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
                records.append({
                    "class": "EXTERNAL_HISTORY_SOURCE",
                    "source": str(item),
                    "archive_path": dest.relative_to(snapshot_dir).as_posix(),
                    "bytes": dest.stat().st_size,
                    "sha256": sha256_file(dest),
                })

    manifest = {
        "protocol": HISTORY_PROTOCOL,
        "origin": ORIGIN,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "records": records,
        "missing_declared_sources": missing,
        "record_count": len(records),
        "rule": "Sources are preserved; summaries never replace originals.",
    }
    manifest_path = history_root / "HISTORY_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
