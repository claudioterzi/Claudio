"""CLI di Flight Hunter.

Caccia su rotta:
    python3 -m flight_hunter MXP TIA --mese 2026-09 [--bagaglio] [--profondo]

Ricerca per obiettivo ("dove posso andare?"):
    python3 -m flight_hunter MXP --mese 2026-09 --ovunque --budget 90
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from .memoria import Memoria
from .motore import caccia, ovunque


def _giorni_alla_partenza(giorno_volo: str) -> int | None:
    try:
        a, m, g = (int(x) for x in giorno_volo.split("-"))
        return (date(a, m, g) - date.today()).days
    except (ValueError, AttributeError):
        return None


def _stampa_ovunque(args) -> int:
    print(f"\n☠  Flight Hunter — da {args.origine}, {args.mese}, "
          f"ovunque{f' sotto {args.budget:.0f}€' if args.budget else ''}\n")
    mete = ovunque(
        args.origine, args.mese, budget=args.budget,
        raggio_origine=args.raggio, bagaglio=args.bagaglio,
        top=args.top, log=print,
    )
    if not mete:
        print("\nNessuna meta nel budget indicato (prova ad alzarlo o allargare il raggio).")
        return 1
    print(f"\n{'─' * 66}")
    for i, m in enumerate(mete, 1):
        extra = ""
        if m.costo_terra or m.costo_bagagli:
            voci = [f"volo {m.prezzo_volo:.2f}€"]
            if m.costo_terra:
                voci.append(f"terra {m.costo_terra:.2f}€")
            if m.costo_bagagli:
                voci.append(f"bagaglio {m.costo_bagagli:.2f}€")
            extra = "  (" + " + ".join(voci) + ")"
        print(f"#{i:>2}  {m.totale:>7.2f}€   {m.nome} ({m.paese})  ·  da {m.da}{extra}")
    print(f"\n{len(mete)} destinazioni raggiungibili. Prezzi live, verifica sul vettore.\n")
    return 0


def _stampa_caccia(args) -> int:
    print(f"\n☠  Flight Hunter — {args.origine} → {args.destinazione}, {args.mese}"
          f"{' (con bagaglio)' if args.bagaglio else ''}"
          f"{' [modalità profonda]' if args.profondo else ''}\n")

    risultati = caccia(
        args.origine, args.destinazione, args.mese,
        raggio_origine=args.raggio, raggio_destinazione=args.raggio_dest,
        bagaglio=args.bagaglio, top=args.top, profondo=args.profondo, log=print,
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
        # miniera dati: ogni singola tratta osservata, con l'anticipo
        for it in risultati:
            for v in it.voli:
                memoria.osserva(f"{v.da}-{v.a}", v.giorno, v.prezzo, v.vettore,
                                _giorni_alla_partenza(v.giorno))
        if vecchio is not None and vecchio != float("inf"):
            print(f"\n★ NUOVO MINIMO: {migliore.totale:.2f}€ (precedente {vecchio:.2f}€)")
        c = memoria.consiglio(rotta, args.mese, migliore.totale)
        print(f"\nConsiglio [{c.azione.upper()}]: {c.motivo}")
        memoria.chiudi()

    print(f"\nNota: prezzi live dalla fonte, ma verifica sempre sul sito del vettore"
          f"\nprima di comprare — e sui self-transfer la coincidenza è affar tuo.\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="flight_hunter",
        description="Caccia al prezzo minimo reale (voli, mese intero).")
    ap.add_argument("origine", help="IATA o città di partenza (es. MXP, Milano)")
    ap.add_argument("destinazione", nargs="?",
                    help="IATA o città di arrivo (omesso con --ovunque)")
    ap.add_argument("--mese", required=True, help="mese di viaggio, YYYY-MM")
    ap.add_argument("--ovunque", action="store_true",
                    help="ignora la destinazione: mostra tutte le mete raggiungibili")
    ap.add_argument("--budget", type=float, default=None,
                    help="con --ovunque: tetto di spesa per persona (€)")
    ap.add_argument("--profondo", action="store_true",
                    help="esplora anche il grafo della rete (fino a 3 tratte, più lento)")
    ap.add_argument("--raggio", type=float, default=250,
                    help="raggio km per gli aeroporti di partenza alternativi (default 250)")
    ap.add_argument("--raggio-dest", type=float, default=150,
                    help="raggio km per gli aeroporti di arrivo alternativi (default 150)")
    ap.add_argument("--bagaglio", action="store_true", help="includi bagaglio da stiva")
    ap.add_argument("--top", type=int, default=10, help="quanti risultati mostrare")
    ap.add_argument("--senza-memoria", action="store_true",
                    help="non salvare i minimi nel database")
    args = ap.parse_args(argv)

    if args.ovunque:
        return _stampa_ovunque(args)
    if not args.destinazione:
        ap.error("serve una destinazione (oppure usa --ovunque)")
    return _stampa_caccia(args)


if __name__ == "__main__":
    sys.exit(main())
