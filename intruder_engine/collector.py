"""Modulo 1 — COLLECTOR.

Ingestion da fonti multiple → Event stream normalizzato.

Fonti V1: testo/markdown, email (.mbox), calendario (Google Calendar API)
Fonti V2: trascrizioni vocali (Whisper), chat WhatsApp/Telegram
Fonti V3: foto (EXIF), cronologia browser
"""

from __future__ import annotations

import mailbox
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from .db import Event


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect_text_file(path: Path | str) -> Generator[Event, None, None]:
    """Raccoglie paragrafi da un file .txt o .md come eventi separati."""
    path = Path(path)
    source = f"file:{path.name}"
    content = path.read_text(encoding="utf-8", errors="replace")
    timestamp = _now_iso()
    for paragraph in re.split(r"\n{2,}", content.strip()):
        paragraph = paragraph.strip()
        if len(paragraph) > 20:
            yield Event(timestamp=timestamp, source=source, content=paragraph)


def collect_mbox(path: Path | str) -> Generator[Event, None, None]:
    """Raccoglie email da file .mbox."""
    mbox = mailbox.mbox(str(path))
    for message in mbox:
        date_str = message.get("Date", _now_iso())
        subject  = message.get("Subject", "")
        sender   = message.get("From", "")
        body     = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
        else:
            payload = message.get_payload(decode=True)
            if payload:
                body = payload.decode("utf-8", errors="replace")
        content = f"Da: {sender}\nOggetto: {subject}\n\n{body[:2000]}"
        yield Event(timestamp=date_str, source="email", content=content)


def collect_directory(directory: Path | str, extensions: tuple[str, ...] = (".md", ".txt")) -> Generator[Event, None, None]:
    """Raccoglie tutti i file di testo da una cartella."""
    for path in Path(directory).rglob("*"):
        if path.suffix in extensions and path.is_file():
            yield from collect_text_file(path)
