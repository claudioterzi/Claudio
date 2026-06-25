"""Entry point CLI — The Intruder Engine.

Usage:
    python -m intruder_engine daily [--input DIR] [--no-llm]
    python -m intruder_engine scan FILE
    python -m intruder_engine shadow
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def cmd_daily(args: argparse.Namespace) -> None:
    from .db import make_session
    from .collector import collect_directory
    from .trace_detector import detect_recurrences
    from .shadow_detector import ShadowDetector
    from .scoring import IntrusionScore
    from .narrative import generate_narrative
    from .report import build_report

    input_dir = Path(args.input) if args.input else Path.home() / "notes"
    if not input_dir.exists():
        print(f"Cartella input non trovata: {input_dir}", file=sys.stderr)
        sys.exit(1)

    session = make_session()
    events = list(collect_directory(input_dir))
    if not events:
        print("Nessun file trovato nella cartella input.")
        return

    contents = [(e.source, e.content) for e in events]
    recurrences = detect_recurrences(contents)
    traces = [f"'{term}' — {count} occorrenze in {len(srcs)} fonti"
              for term, count, srcs in recurrences[:5]]

    tracked = [term for term, _, _ in recurrences[:30]]
    shadow = ShadowDetector(session)
    absences = shadow.detect(tracked)

    score_obj = IntrusionScore(
        anomaly=min(1.0, len(recurrences) / 10),
        repetition=min(1.0, max((c for _, c, _ in recurrences[:1]), default=0) / 10),
        independence=min(1.0, max((len(s) for _, _, s in recurrences[:1]), default=0) / 5),
        relevance=0.7,
        convergence=min(1.0, len(absences) / 5),
    )

    narrative = generate_narrative(traces, absences, use_llm=not args.no_llm)
    report = build_report(traces, absences, narrative, score_obj.score)
    print(report)


def cmd_shadow(args: argparse.Namespace) -> None:
    from .db import make_session
    from .shadow_detector import ShadowDetector

    session = make_session()
    tracked = args.entities.split(",") if args.entities else []
    sd = ShadowDetector(session, absence_threshold_days=args.days)
    for a in sd.detect(tracked):
        print(a)


def main() -> None:
    parser = argparse.ArgumentParser(prog="intruder_engine", description="The Intruder Engine")
    sub = parser.add_subparsers(dest="command")

    p_daily = sub.add_parser("daily", help="Report giornaliero")
    p_daily.add_argument("--input", help="Cartella note/diari")
    p_daily.add_argument("--no-llm", action="store_true", help="Disabilita Claude per la narrativa")
    p_daily.set_defaults(func=cmd_daily)

    p_shadow = sub.add_parser("shadow", help="Rileva assenze")
    p_shadow.add_argument("--entities", help="Lista entità separate da virgola")
    p_shadow.add_argument("--days", type=int, default=14)
    p_shadow.set_defaults(func=cmd_shadow)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
