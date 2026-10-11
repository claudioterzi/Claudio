"""CLI harness for the R3 reflex candidate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runtime import ReflexRuntime


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config" / "r3_reflex.json"


def load_config(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def print_outcome(fragment: str, outcome) -> None:
    d = outcome.decision
    print(
        f"{outcome.stance:7} complete={d.complete:.2f} "
        f"action={d.action} target={d.target} provider={d.provider} "
        f"detail={outcome.detail} :: {fragment}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="R3 System One reflex candidate")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--backend", choices=["auto", "demo", "typesafe"])
    parser.add_argument("--text")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-destructive", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.backend:
        config["backend"] = args.backend
    if args.execute:
        config["dry_run"] = False

    runtime = ReflexRuntime(config)

    if args.replay:
        fragments = [
            "abre el",
            "abre el bloc",
            "abre el bloc de notas",
            "apri il",
            "apri il blocco note",
            "volume al 30",
            "apri la cartella download",
        ]
        for fragment in fragments:
            print_outcome(
                fragment,
                runtime.evaluate(
                    fragment,
                    execute_actions=args.execute,
                    allow_destructive=args.allow_destructive,
                ),
            )
        return 0

    if args.text:
        print_outcome(
            args.text,
            runtime.evaluate(
                args.text,
                execute_actions=args.execute,
                allow_destructive=args.allow_destructive,
            ),
        )
        return 0

    print("Streaming text mode. One partial transcript per line; :q exits.")
    while True:
        try:
            line = input("partial> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if line in {":q", "quit", "esci"}:
            return 0
        if line:
            print_outcome(
                line,
                runtime.evaluate(
                    line,
                    execute_actions=args.execute,
                    allow_destructive=args.allow_destructive,
                ),
            )


if __name__ == "__main__":
    raise SystemExit(main())
