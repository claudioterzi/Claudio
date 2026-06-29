"""CLI per i comandi rituali R³∞.

    python -m apps.cli.r3_cli passo
    python -m apps.cli.r3_cli loop 10
    python -m apps.cli.r3_cli trigger Rosso
    python -m apps.cli.r3_cli mappa "pytest -q"
    python -m apps.cli.r3_cli kill
"""
from __future__ import annotations

import argparse
import json
import sys

from r3_core import RaffaelloCore, carica_preset
from rituals.mapping import risolvi
from rituals.triggers import esegui_rito


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="r3", description="R³∞ — comandi rituali")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("passo", help="una iterazione del core")
    pl = sub.add_parser("loop", help="R3 continuo per N iterazioni")
    pl.add_argument("n", type=int, nargs="?", default=10)
    pt = sub.add_parser("trigger", help="esegue un rito (Rosso/Raffaello/Updater/Applica)")
    pt.add_argument("nome")
    pm = sub.add_parser("mappa", help="risolve un comando in un rito")
    pm.add_argument("comando")
    sub.add_parser("kill", help="dimostra il kill switch")
    sub.add_parser("preset", help="elenca i preset")

    args = p.parse_args(argv[1:])

    if args.cmd == "passo":
        core = RaffaelloCore()
        core.passo()
        print(json.dumps(core.riassunto(), ensure_ascii=False, indent=2))
    elif args.cmd == "loop":
        core = RaffaelloCore()
        core.loop(args.n)
        print(json.dumps(core.riassunto(), ensure_ascii=False, indent=2))
    elif args.cmd == "trigger":
        print(json.dumps(esegui_rito(args.nome), ensure_ascii=False, indent=2, default=str))
    elif args.cmd == "mappa":
        rito = risolvi(args.comando)
        print(json.dumps({"comando": args.comando, "rito": rito}, ensure_ascii=False))
    elif args.cmd == "kill":
        core = RaffaelloCore()
        core.kill("kill switch da CLI")
        core.loop(100)
        print(json.dumps(core.riassunto(), ensure_ascii=False, indent=2))
    elif args.cmd == "preset":
        print(json.dumps(carica_preset().__dict__, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
