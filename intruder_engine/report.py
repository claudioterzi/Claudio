"""Report giornaliero aggregato — The Intruder Engine."""

from __future__ import annotations

from datetime import datetime, timezone


BANNER = """\
═══════════════════════════════════════════════
THE INTRUDER ENGINE
{date}
═══════════════════════════════════════════════"""

FOOTER = "═══════════════════════════════════════════════"


def _classify(score: int) -> str:
    if score >= 81: return "EVENTO INTRUSO"
    if score >= 61: return "FORTE CONVERGENZA"
    if score >= 41: return "TRACCIA INTERESSANTE"
    if score >= 21: return "PATTERN DEBOLE"
    return "RUMORE"


def build_report(
    traces: list,
    absences: list,
    narrative: str,
    overall_score: int,
    daily_question: str = "",
) -> str:
    date = datetime.now(timezone.utc).strftime("%d %B %Y").upper()
    lines = [BANNER.format(date=date), ""]

    if traces:
        lines.append("TRACCE RILEVATE")
        for t in traces:
            lines.append(f"  • {t}")
        lines.append("")

    if absences:
        lines.append("ASSENZE RILEVATE")
        for a in absences:
            lines.append(f"  • {a}")
        lines.append("")

    if narrative:
        lines.append("OSSERVAZIONE")
        for row in narrative.split("\n"):
            lines.append(f"  {row}")
        lines.append("")

    lines.append(f"PUNTEGGIO INTRUSO")
    lines.append(f"  {overall_score} / 100 — {_classify(overall_score)}")
    lines.append("")

    if daily_question:
        lines.append("DOMANDA DEL GIORNO")
        lines.append(f'  "{daily_question}"')
        lines.append("")

    lines.append(FOOTER)
    return "\n".join(lines)
