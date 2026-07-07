"""Orchestratore della caccia voli (SDQ-1 — Protocollo Rosso Rosso Rosso).

Esegue un ciclo completo: per ogni rotta della matrice interroga il motore
(SCOUT), valuta il prezzo (VALUTATORE) e, se è notevole, scrive una nota su
Telegram (CRONISTA). Pensato per girare a mano o da cron/trigger giornaliero.

Uso:
    python -m sdq1.voli                 # caccia tutte le rotte, invia note
    python -m sdq1.voli --dry-run       # non invia, stampa soltanto
    python -m sdq1.voli --tag cuba      # solo rotte con quel tag
    python -m sdq1.voli --rotta BRU-GRU-CDG
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass

from .agenti import CronistaVoli, ScoutVoli, ValutatoreVoli, Valutazione
from .rotte import ROTTE, Rotta, rotte_per_tag

log = logging.getLogger("sdq1.voli.caccia")


@dataclass
class RisultatoCaccia:
    valutazioni: list[Valutazione]
    inviate: int

    @property
    def notevoli(self) -> list[Valutazione]:
        return [v for v in self.valutazioni if v.notevole]


class Cacciatore:
    """Façade che coordina i tre agenti su una lista di rotte."""

    def __init__(self, dry_run: bool | None = None, timeout_s: float = 300.0):
        self.scout = ScoutVoli(timeout_s=timeout_s)
        self.valutatore = ValutatoreVoli()
        self.cronista = CronistaVoli(dry_run=dry_run)

    def caccia(self, rotte: tuple[Rotta, ...] = ROTTE) -> RisultatoCaccia:
        valutazioni: list[Valutazione] = []
        inviate = 0
        for rotta in rotte:
            log.info("Caccia rotta %s …", rotta.id)
            esito = self.scout.cerca(rotta)
            v = self.valutatore.valuta(rotta, esito)
            valutazioni.append(v)
            stato = "‼️ NOTEVOLE" if v.notevole else "ok"
            log.info("  %s → %s [%s] %s", rotta.id, v.classe, stato, v.nota)
            if v.notevole and self.cronista.scrivi(v, esito):
                inviate += 1
        return RisultatoCaccia(valutazioni, inviate)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Caccia agli errori di prezzo voli (SDQ-1).")
    p.add_argument("--dry-run", action="store_true", help="non inviare note, stampa soltanto")
    p.add_argument("--tag", nargs="*", default=None, help="filtra le rotte per tag (es. cuba brasile)")
    p.add_argument("--rotta", default=None, help="esegui una sola rotta per id")
    p.add_argument("--timeout", type=float, default=300.0, help="timeout motore per rotta (s)")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.rotta:
        rotte = tuple(r for r in ROTTE if r.id == args.rotta)
        if not rotte:
            print(f"Rotta '{args.rotta}' non trovata. Disponibili: {', '.join(r.id for r in ROTTE)}")
            return 2
    elif args.tag:
        rotte = rotte_per_tag(*args.tag)
    else:
        rotte = ROTTE

    cacciatore = Cacciatore(dry_run=True if args.dry_run else None)
    ris = cacciatore.caccia(rotte)

    print(f"\nCaccia completata: {len(rotte)} rotte, {len(ris.notevoli)} notevoli, {ris.inviate} note inviate.")
    for v in ris.valutazioni:
        marca = "‼️" if v.notevole else "  "
        prezzo = f"€{v.min_eur}" if v.min_eur is not None else "—"
        print(f" {marca} {v.rotta.id:<14} {prezzo:>7}  [{v.classe}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
