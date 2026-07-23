"""CLI: python3 -m flight_hunter MXP TIA --mese 2026-09 [--bagaglio] [--raggio 250]"""
from __future__ import annotations

import argparse
import sys

from .costi import ParametriCosto
from .memoria import Memoria
from .motore import caccia


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="flight_hunter",
        description="Caccia al prezzo minimo reale (voli one-way, mese intero).")
    ap.add_argument("origine", help="IATA o città di partenza (es. MXP, Milano)")
    ap.add_argument("destinazione", help="IATA o città di arrivo (es. TIA, Tirana)")
    ap.add_argument("--mese", required=True, help="mese di viaggio, YYYY-MM")
    ap.add_argument("--raggio", type=float, default=250,
                    help="raggio km per gli aeroporti di partenza alternativi (default 250)")
    ap.add_argument("--raggio-dest", type=float, default=150,
                    help="raggio km per gli aeroporti di arrivo alternativi (default 150)")
    ap.add_argument("--bagaglio", action="store_true", help="includi bagaglio da stiva")
    ap.add_argument("--top", type=int, default=10, help="quanti risultati mostrare")
    ap.add_argument("--senza-memoria", action="store_true",
                    help="non salvare i minimi nel database")
    args = ap.parse_args(argv)

    print(f"\n☠  Flight Hunter — {args.origine} → {args.destinazione}, {args.mese}"
          f"{' (con bagaglio)' if args.bagaglio else ''}\n")

    risultati = caccia(
        args.origine, args.destinazione, args.mese,
        raggio_origine=args.raggio, raggio_destinazione=args.raggio_dest,
        bagaglio=args.bagaglio, top=args.top, log=print,
    )
    if not risultati:
        print("\nNessun collegamento trovato (rotta non servita nel mese richiesto).")
        return 1

    memoria = None if args.senza_memoria else Memoria()
    print(f"\n{'─' * 66}")
    for i, it in enumerate(risultati, 1):
        print(f"\n#{i}  {it.totale:.2f}€  ·  {it.tipo}  ·  rischio {it.rischio}")
        print(it.descrizione())
        dettagli = [f"voli {it.costo_voli:.2f}€"]
        if it.costo_terra:
            dettagli.append(f"terra {it.costo_terra:.2f}€")
        if it.costo_bagagli:
            dettagli.append(f"bagagli {it.costo_bagagli:.2f}€")
        if it.costo_notti:
            dettagli.append(f"notti {it.costo_notti:.2f}€")
        if it.margine_rischio:
            dettagli.append(f"margine rischio {it.margine_rischio:.2f}€")
        print("  " + " · ".join(dettagli))
        for nota in it.note:
            print(f"  ⚠ {nota}")

    migliore = risultati[0]
    rotta = f"{args.origine.upper()}-{args.destinazione.upper()}"
    if memoria:
        vecchio = memoria.registra(rotta, args.mese, migliore.voli[0].giorno, migliore.totale)
        if vecchio is not None and vecchio != float("inf"):
            print(f"\n★ NUOVO MINIMO: {migliore.totale:.2f}€ (precedente {vecchio:.2f}€)")
        c = memoria.consiglio(rotta, args.mese, migliore.totale)
        print(f"\nConsiglio [{c.azione.upper()}]: {c.motivo}")
        memoria.chiudi()

    print(f"\nNota: prezzi live dalla fonte, ma verifica sempre sul sito del vettore"
          f"\nprima di comprare — e sui self-transfer la coincidenza è affar tuo.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
