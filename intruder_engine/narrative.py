"""Modulo 5 — NARRATIVE ENGINE.

Trasforma tracce e assenze in linguaggio naturale neutrale.
LLM principale: Claude (claude-sonnet-4-6). Fallback: template locale.
"""

from __future__ import annotations

import os
from typing import Any


_SYSTEM_PROMPT = """\
Sei The Intruder Engine. Il tuo ruolo è osservare, non interpretare.
Riferisci fatti statistici in italiano, in modo preciso e neutrale.
Non dare risposte assolute. Formula osservazioni e al massimo una domanda.
Non essere terapeutico, non essere mistico, non essere manipolativo.
Sii conciso: massimo 5 righe per osservazione.
"""


def _template_fallback(traces: list[Any], absences: list[Any]) -> str:
    lines = []
    for t in traces:
        lines.append(f"• {t}")
    for a in absences:
        lines.append(f"• ASSENZA: {a}")
    return "\n".join(lines) if lines else "Nessuna traccia significativa rilevata."


def generate_narrative(
    traces: list[Any],
    absences: list[Any],
    use_llm: bool = True,
) -> str:
    """Genera la narrativa testuale del report."""
    if not traces and not absences:
        return "Nessuna traccia significativa rilevata."

    if not use_llm:
        return _template_fallback(traces, absences)

    try:
        import anthropic

        client = anthropic.Anthropic()
        user_content = "TRACCE:\n" + "\n".join(str(t) for t in traces)
        if absences:
            user_content += "\n\nASSENZE:\n" + "\n".join(str(a) for a in absences)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text
    except Exception:
        return _template_fallback(traces, absences)
