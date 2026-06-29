"""Pipeline persistente — workflow, trigger, R3 continuo.

Registra trigger→azione, esegue i workflow e mantiene uno stato persistente
(opzionalmente su file JSON), così il flusso sopravvive tra esecuzioni.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

Azione = Callable[[dict], dict]


@dataclass
class PipelinePersistente:
    """Workflow a trigger con stato persistente."""
    percorso: Optional[Path] = None
    stato: dict = field(default_factory=dict)
    _azioni: dict[str, Azione] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.percorso:
            self.percorso = Path(self.percorso)
            self._carica()

    # --- registrazione -----------------------------------------------------
    def registra(self, trigger: str, azione: Azione) -> None:
        self._azioni[trigger] = azione

    def trigger_disponibili(self) -> list[str]:
        return sorted(self._azioni)

    # --- esecuzione --------------------------------------------------------
    def esegui(self, trigger: str, **dati) -> dict:
        if trigger not in self._azioni:
            raise KeyError(f"Trigger sconosciuto: {trigger}")
        ctx = {**self.stato, **dati}
        self.stato = self._azioni[trigger](ctx)
        self.stato.setdefault("_storia", []).append(trigger)
        self._salva()
        return self.stato

    def continuo(self, sequenza: list[str], **dati) -> dict:
        """R3 continuo: esegue una sequenza di trigger uno dopo l'altro."""
        for trigger in sequenza:
            self.esegui(trigger, **dati)
        return self.stato

    # --- persistenza -------------------------------------------------------
    def _carica(self) -> None:
        if self.percorso and self.percorso.exists():
            try:
                self.stato = json.loads(self.percorso.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self.stato = {}

    def _salva(self) -> None:
        if not self.percorso:
            return
        self.percorso.parent.mkdir(parents=True, exist_ok=True)
        self.percorso.write_text(
            json.dumps(self.stato, ensure_ascii=False, indent=2), encoding="utf-8"
        )
