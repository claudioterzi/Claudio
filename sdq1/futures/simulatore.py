"""Runner parallelo di scenari futuri — SDQ-1 Futures Engine."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Callable

from .scenari import Scenario

_TZ_BRUSSELS = timezone(timedelta(hours=2))


@dataclass
class RisultatoScenario:
    scenario_id: str
    titolo: str
    testo: str
    provider: str
    latenza_ms: int
    errore: str | None = None
    successo: bool = True
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "titolo": self.titolo,
            "testo": self.testo,
            "provider": self.provider,
            "latenza_ms": self.latenza_ms,
            "errore": self.errore,
            "successo": self.successo,
            "metadata": self.metadata,
        }


class SimulatoreScenari:
    """Esegue scenari futuri in parallelo tramite il router LLM."""

    def __init__(
        self,
        llm_fn: Callable[[str, str], tuple[str, str, int]],
        max_workers: int = 4,
        output_dir: Path = Path("output/scenari"),
    ):
        # llm_fn(sistema, utente) -> (testo, provider, latenza_ms)
        self._llm = llm_fn
        self._max_workers = max_workers
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _esegui_singolo(self, scenario: Scenario) -> RisultatoScenario:
        t0 = time.monotonic()
        try:
            testo, provider, latenza_ms = self._llm(
                scenario.prompt_sistema(),
                scenario.prompt_utente(),
            )
            return RisultatoScenario(
                scenario_id=scenario.id,
                titolo=scenario.titolo,
                testo=testo,
                provider=provider,
                latenza_ms=latenza_ms,
                successo=True,
            )
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            return RisultatoScenario(
                scenario_id=scenario.id,
                titolo=scenario.titolo,
                testo="",
                provider="n/a",
                latenza_ms=elapsed_ms,
                errore=str(exc),
                successo=False,
            )

    def simula_parallelo(self, scenari: list[Scenario]) -> list[RisultatoScenario]:
        risultati: list[RisultatoScenario] = []
        with ThreadPoolExecutor(max_workers=min(self._max_workers, len(scenari))) as pool:
            futures = {pool.submit(self._esegui_singolo, s): s for s in scenari}
            for fut in as_completed(futures):
                risultati.append(fut.result())
        risultati.sort(key=lambda r: r.scenario_id)
        return risultati

    def salva_report(self, risultati: list[RisultatoScenario]) -> Path:
        now = datetime.now(_TZ_BRUSSELS)
        timestamp = now.strftime("%Y-%m-%d_%H%M")
        dest = self._output_dir / f"{timestamp}_scenari.json"
        payload = {
            "generato": now.isoformat(),
            "tz": "Europe/Brussels",
            "n_scenari": len(risultati),
            "n_successi": sum(1 for r in risultati if r.successo),
            "scenari": [r.to_dict() for r in risultati],
        }
        dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return dest

    @staticmethod
    def stampa_report(risultati: list[RisultatoScenario]) -> str:
        linee = []
        linee.append("=" * 70)
        linee.append("SDQ-1 FUTURES — SIMULAZIONI PARALLELE")
        linee.append("=" * 70)
        for r in risultati:
            linee.append(f"\n{'─' * 70}")
            stato = "OK" if r.successo else f"ERRORE: {r.errore}"
            linee.append(f"[{r.scenario_id}] {r.titolo}  |  {r.provider}  |  {r.latenza_ms}ms  |  {stato}")
            linee.append("─" * 70)
            if r.successo:
                linee.append(r.testo)
            else:
                linee.append(f"Simulazione fallita: {r.errore}")
        linee.append(f"\n{'=' * 70}")
        n_ok = sum(1 for r in risultati if r.successo)
        linee.append(f"Completati: {n_ok}/{len(risultati)} scenari")
        return "\n".join(linee)
