"""Watchdog SDQ-1 — monitor continuo dei nodi con auto-healing.

Gira come processo daemon in background. Ogni INTERVALLO_S:
  1. Pinga tutti i provider configurati
  2. Apre/chiude circuit breaker di conseguenza
  3. Scrive log di salute in output/health_log.jsonl
  4. Se tutti i provider reali sono morti, emette allarme su stderr

Avvio: python -m sdq1 --watchdog [--intervallo 120]
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .monitoring import HealthChecker
    from .llm.router import LLMRouter

log = logging.getLogger(__name__)
_LOG_FILE = Path("output/health_log.jsonl")


class Watchdog:
    def __init__(
        self,
        health: "HealthChecker",
        router: "LLMRouter",
        intervallo_s: float = 120.0,
    ):
        self.health = health
        self.router = router
        self.intervallo = intervallo_s
        self._running = False

    def _tick(self) -> dict:
        azioni = self.health.aggiorna_circuit_breaker()
        stati = self.health.controlla_tutti()
        vivi = [s.provider for s in stati if s.raggiungibile]
        morti = [s.provider for s in stati if s.configurato and not s.raggiungibile]

        record = {
            "timestamp": time.time(),
            "data_ora": time.strftime("%Y-%m-%d %H:%M:%S"),
            "provider_vivi": vivi,
            "provider_morti": morti,
            "circuit_breaker": self.router.stato_circuit_breaker(),
            "azioni_cb": azioni,
        }

        _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        if not any(s.raggiungibile and s.provider != "stub" for s in stati):
            log.warning("WATCHDOG ALLARME: nessun provider reale raggiungibile — modalità stub")

        log.info("Watchdog tick: vivi=%s morti=%s", vivi, morti)
        return record

    def avvia(self) -> None:
        """Blocca il thread corrente: usare in un daemon thread."""
        self._running = True
        log.info("Watchdog avviato (intervallo %ds)", self.intervallo)
        while self._running:
            try:
                self._tick()
            except Exception as exc:  # noqa: BLE001
                log.error("Watchdog errore: %s", exc)
            time.sleep(self.intervallo)

    def ferma(self) -> None:
        self._running = False

    def stato(self) -> dict:
        """Legge l'ultimo record dal log."""
        if not _LOG_FILE.exists():
            return {"ok": False, "messaggio": "nessun log disponibile"}
        try:
            ultime = _LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
            return json.loads(ultime[-1]) if ultime else {}
        except Exception:
            return {}
