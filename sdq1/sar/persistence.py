"""Persistenza SAR su disco — stato sopravvive al riavvio.

Salva in JSON nella cartella ~/.sdq1/sar/ (o path configurabile).
Nessuna dipendenza esterna.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .tensioni import MappaTeensioni, Polo, Tensione, Osservazione
from .memoria_evolutiva import MemoriaEvolutiva, PatternRicorrente, EntrataMemo
from .coerenza import IndiceCoerenza, CoppiaCoerenza


DEFAULT_DIR = Path.home() / ".sdq1" / "sar"


class PersistenzaSAR:
    """Salva e carica lo stato della ScacchieraAutoRiflessiva."""

    def __init__(self, cartella: Path | str = DEFAULT_DIR, soggetto: str = "utente"):
        self.cartella = Path(cartella)
        self.soggetto = soggetto
        self.cartella.mkdir(parents=True, exist_ok=True)
        self._file_stato = self.cartella / f"{soggetto}_stato.json"
        self._file_report = self.cartella / f"{soggetto}_report.jsonl"

    # ------------------------------------------------------------------ #
    # Salvataggio                                                          #
    # ------------------------------------------------------------------ #

    def salva_stato(self, mappa: MappaTeensioni, memoria: MemoriaEvolutiva,
                    coerenza: IndiceCoerenza) -> None:
        stato = {
            "soggetto":   self.soggetto,
            "salvato_at": time.time(),
            "osservazioni": [
                {
                    "id": o.id, "testo": o.testo, "timestamp": o.timestamp,
                    "tag": o.tag, "intensita": o.intensita,
                }
                for o in mappa._osservazioni.values()
            ],
            "tensioni_custom": [
                {
                    "id": t.id,
                    "polo_a": t.polo_a.nome, "polo_b": t.polo_b.nome,
                    "forza": t.forza,
                    "osservazioni_collegate": t.osservazioni,
                }
                for t in mappa._tensioni.values()
                if (t.polo_a.nome, t.polo_b.nome) not in MappaTeensioni.POLI_STANDARD
            ],
            "entrate_memoria": [
                {
                    "id": e.id, "categoria": e.categoria, "testo": e.testo,
                    "intensita": e.intensita, "timestamp": e.timestamp,
                    "tag": e.tag,
                }
                for e in memoria._entrate.values()
            ],
            "pattern": [
                {
                    "trigger": p.trigger, "sequenza": p.sequenza,
                    "frequenza": p.frequenza, "ultima_occorrenza": p.ultima_occorrenza,
                }
                for p in memoria._pattern
            ],
            "coppie_coerenza": [
                {
                    "dimensione": c.dimensione, "interno": c.interno,
                    "esterno": c.esterno, "distanza": c.distanza, "nota": c.nota,
                }
                for c in coerenza._coppie
            ],
        }
        self._file_stato.write_text(
            json.dumps(stato, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def salva_report(self, report: dict[str, Any]) -> None:
        with self._file_report.open("a", encoding="utf-8") as f:
            f.write(json.dumps(report, ensure_ascii=False, default=str) + "\n")

    # ------------------------------------------------------------------ #
    # Caricamento                                                          #
    # ------------------------------------------------------------------ #

    def carica_stato(self) -> dict[str, Any] | None:
        if not self._file_stato.exists():
            return None
        try:
            return json.loads(self._file_stato.read_text(encoding="utf-8"))
        except Exception:
            return None

    def applica_stato(self, mappa: MappaTeensioni,
                      memoria: MemoriaEvolutiva,
                      coerenza: IndiceCoerenza) -> bool:
        """Carica lo stato salvato nelle strutture fornite. Restituisce True se ok."""
        dati = self.carica_stato()
        if not dati:
            return False

        import uuid as _uuid

        for o in dati.get("osservazioni", []):
            obs = Osservazione(
                id=o["id"], testo=o["testo"], timestamp=o["timestamp"],
                tag=o.get("tag", []), intensita=o.get("intensita", 0.5),
            )
            mappa._osservazioni[obs.id] = obs
            mappa._collega_a_tensioni(obs)

        for e in dati.get("entrate_memoria", []):
            entrata = EntrataMemo(
                id=e["id"], categoria=e["categoria"], testo=e["testo"],
                intensita=e.get("intensita", 0.5), timestamp=e["timestamp"],
                tag=e.get("tag", []),
            )
            memoria._entrate[entrata.id] = entrata

        for p in dati.get("pattern", []):
            pr = PatternRicorrente(
                trigger=p["trigger"], sequenza=p["sequenza"],
                frequenza=p.get("frequenza", 1),
                ultima_occorrenza=p.get("ultima_occorrenza", time.time()),
            )
            memoria._pattern.append(pr)

        for c in dati.get("coppie_coerenza", []):
            coerenza.aggiungi(
                dimensione=c["dimensione"], interno=c["interno"],
                esterno=c["esterno"], distanza=c.get("distanza", 0.5),
                nota=c.get("nota", ""),
            )
        return True

    def storico_report(self) -> list[dict[str, Any]]:
        if not self._file_report.exists():
            return []
        risultati = []
        for riga in self._file_report.read_text(encoding="utf-8").splitlines():
            try:
                risultati.append(json.loads(riga))
            except Exception:
                pass
        return risultati

    def info(self) -> dict[str, Any]:
        dati = self.carica_stato() or {}
        return {
            "file_stato":   str(self._file_stato),
            "file_report":  str(self._file_report),
            "esiste":       self._file_stato.exists(),
            "osservazioni": len(dati.get("osservazioni", [])),
            "report":       len(self.storico_report()),
            "salvato_at":   dati.get("salvato_at"),
        }
