"""Repository: persistenza dello stato R³∞ (pattern repository)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class StatoRepository:
    """Salva/recupera lo stato. In-memory di default, su file se dato un percorso."""

    def __init__(self, percorso: Optional[Path] = None):
        self.percorso = Path(percorso) if percorso else None
        self._mem: dict = {}
        if self.percorso and self.percorso.exists():
            try:
                self._mem = json.loads(self.percorso.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self._mem = {}

    def salva(self, stato: dict) -> None:
        self._mem = dict(stato)
        if self.percorso:
            self.percorso.parent.mkdir(parents=True, exist_ok=True)
            self.percorso.write_text(
                json.dumps(self._mem, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    def carica(self) -> dict:
        return dict(self._mem)
