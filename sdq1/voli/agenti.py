"""Agenti di caccia voli (SDQ-1 — Protocollo Rosso Rosso Rosso).

Tre agenti che cooperano in pipeline:

  SCOUT-VOLI     interroga il motore (Google Flights) per una rotta e riporta
                 il prezzo minimo reale e le migliori offerte.
  VALUTATORE     confronta il prezzo con la soglia della rotta e classifica
                 l'esito (error_fare / promo_forte / normale).
  CRONISTA       scrive la nota su Telegram quando c'è qualcosa di notevole.

Filosofia: non seguire il branco dei blog di offerte — andare al motore di
prenotazione e leggere il prezzo vero. Gli errori si trovano prima così.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .rotte import Rotta
from .ambiente import telegram_pronto
from .. import notifiche

log = logging.getLogger("sdq1.voli")

_ENGINE = str(Path(__file__).with_name("engine.js"))
_CA_BUNDLE = "/root/.ccr/ca-bundle.crt"


# ---------------------------------------------------------------- SCOUT-VOLI

@dataclass
class EsitoScout:
    rotta_id: str
    ok: bool
    min_eur: int | None
    offers: list[dict[str, Any]]
    errore: str | None = None


class ScoutVoli:
    """Interroga il motore Node/Playwright per una rotta."""

    def __init__(self, engine_path: str = _ENGINE, timeout_s: float = 300.0):
        self.engine = engine_path
        self.timeout = timeout_s

    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        # Il browser deve fidarsi del CA del proxy di egress.
        if os.path.exists(_CA_BUNDLE):
            env.setdefault("NODE_EXTRA_CA_CERTS", _CA_BUNDLE)
        return env

    def cerca(self, rotta: Rotta) -> EsitoScout:
        query = json.dumps({"legs": list(rotta.legs)})
        try:
            proc = subprocess.run(
                ["node", self.engine, query],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self._env(),
                cwd=str(Path(self.engine).parent),
            )
        except subprocess.TimeoutExpired:
            return EsitoScout(rotta.id, False, None, [], errore="timeout motore")
        except FileNotFoundError:
            return EsitoScout(rotta.id, False, None, [], errore="node non trovato")

        out = (proc.stdout or "").strip()
        if not out:
            return EsitoScout(rotta.id, False, None, [], errore=(proc.stderr or "nessun output")[:200])
        try:
            data = json.loads(out.splitlines()[-1])
        except json.JSONDecodeError:
            return EsitoScout(rotta.id, False, None, [], errore="output non JSON")

        if not data.get("ok"):
            return EsitoScout(rotta.id, False, None, [], errore=data.get("error", "motore ko"))
        return EsitoScout(rotta.id, True, data.get("min_eur"), data.get("offers", []))


# ---------------------------------------------------------------- VALUTATORE

@dataclass
class Valutazione:
    rotta: Rotta
    min_eur: int | None
    classe: str          # "error_fare" | "promo_forte" | "normale" | "nessun_prezzo"
    notevole: bool
    nota: str


class ValutatoreVoli:
    """Decide se un prezzo è notevole e lo classifica.

    - `error_fare`  : prezzo <= 55% della soglia → probabile errore tariffario.
    - `promo_forte` : prezzo <= soglia           → offerta forte da segnalare.
    - `normale`     : sopra soglia               → si tace.
    """

    def valuta(self, rotta: Rotta, esito: EsitoScout) -> Valutazione:
        if not esito.ok or esito.min_eur is None:
            return Valutazione(rotta, None, "nessun_prezzo", False, esito.errore or "nessun prezzo")

        p = esito.min_eur
        if p <= round(rotta.soglia_eur * 0.55):
            return Valutazione(rotta, p, "error_fare", True, f"€{p} — sotto il 55% della soglia (€{rotta.soglia_eur})")
        if p <= rotta.soglia_eur:
            return Valutazione(rotta, p, "promo_forte", True, f"€{p} — sotto soglia (€{rotta.soglia_eur})")
        return Valutazione(rotta, p, "normale", False, f"€{p} — sopra soglia (€{rotta.soglia_eur})")


# ---------------------------------------------------------------- CRONISTA

class CronistaVoli:
    """Formatta e invia la nota su Telegram (o la stampa in dry-run)."""

    def __init__(self, dry_run: bool | None = None):
        # dry_run automatico se Telegram non è configurato.
        self.dry_run = (not telegram_pronto()) if dry_run is None else dry_run

    def _formatta(self, v: Valutazione, esito: EsitoScout) -> str:
        ora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        icona = "🔴🔴🔴" if v.classe == "error_fare" else "✈️"
        titolo = "ERROR FARE" if v.classe == "error_fare" else "Offerta forte"
        righe = [
            f"{icona} <b>{titolo} — {v.rotta.descrizione}</b>  <i>{ora}</i>",
            f"Prezzo minimo trovato: <b>€{v.min_eur}</b> (soglia €{v.rotta.soglia_eur})",
        ]
        for off in esito.offers[:3]:
            s = off.get("summary", "").strip()
            righe.append(f"• €{off.get('price_eur')} — {s}" if s else f"• €{off.get('price_eur')}")
        tratte = " → ".join([v.rotta.legs[0]["from"]] + [l["to"] for l in v.rotta.legs])
        righe.append(f"Tratte: {tratte}")
        righe.append("Prenota diretto sul sito compagnia / Google Flights. Aspetta 2 settimane prima di hotel.")
        tags = " ".join(f"#{t}" for t in ("nota", "voli", v.classe, *v.rotta.tag))
        righe.append(tags)
        return "\n".join(righe)

    def scrivi(self, v: Valutazione, esito: EsitoScout) -> bool:
        if not v.notevole:
            return False
        testo = self._formatta(v, esito)
        if self.dry_run:
            log.info("[DRY-RUN] nota non inviata:\n%s", testo)
            print("----- NOTA (dry-run) -----")
            print(testo)
            return False
        return notifiche.invia(testo)
