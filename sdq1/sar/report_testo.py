"""Genera report SAR in testo leggibile — nessuna dipendenza esterna."""

from __future__ import annotations

import time
from typing import Any


def _sep(c: str = "─", n: int = 60) -> str:
    return c * n


def _ts(ts: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def report_ciclo(report: dict[str, Any], soggetto: str = "utente") -> str:
    righe: list[str] = []

    righe += [
        _sep("═"),
        f"  SCACCHIERA AUTORIFLESSIVA — Report",
        f"  Soggetto : {soggetto}",
        f"  Data     : {_ts(report.get('timestamp', time.time()))}",
        f"  Tensione : {report.get('tensione', '?')}",
        _sep("═"),
        "",
    ]

    righe += [
        "CICLO DEI 7 STEP",
        _sep(),
    ]
    for r in report.get("risposte", []):
        righe += [
            f"[{r['step'].upper()}]",
            r["risposta"].strip(),
            "",
        ]

    if report.get("sintesi"):
        righe += [
            _sep(),
            "SINTESI (Livello 7 — Identità Dinamica)",
            _sep(),
            report["sintesi"].strip(),
            "",
        ]

    if report.get("meta_riflessione"):
        righe += [
            _sep(),
            "META-RIFLESSIONE (Livello 8)",
            _sep(),
            report["meta_riflessione"].strip(),
            "",
        ]

    ic = report.get("indice_coerenza", {})
    if ic:
        righe += [
            _sep(),
            f"INDICE DI COERENZA: {ic.get('indice_globale', 0):.2f}  "
            f"({ic.get('interpretazione', '')})",
        ]
        for z in ic.get("zone_critiche", []):
            righe.append(f"  ⚠ {z['dimensione']} — distanza {z['distanza']:.2f}: {z.get('nota','')}")
        righe.append("")

    pattern = report.get("pattern", [])
    if pattern:
        righe += [_sep(), "PATTERN RICORRENTI (Livello 4)", _sep()]
        for p in pattern:
            righe.append(f"  · {p['trigger']}  (freq. {p['frequenza']})")
        righe.append("")

    righe += [_sep("═"), ""]
    return "\n".join(righe)


def report_stato(stato: dict[str, Any], soggetto: str = "utente") -> str:
    righe: list[str] = [
        _sep("═"),
        f"  SDQ-1 / SAR — Stato del Sistema",
        f"  Soggetto: {soggetto}",
        _sep("═"),
        "",
    ]

    mappa = stato.get("mappa_tensioni", {})
    righe += [
        f"Osservazioni raccolte : {mappa.get('osservazioni', 0)}",
        f"Tensioni attive       : {len(mappa.get('tensioni', []))}",
        "",
        "MAPPA TENSIONI",
        _sep(),
    ]
    for t in mappa.get("tensioni", []):
        barre = int(t.get("osservazioni", 0))
        righe.append(f"  {t['label']:<35} obs={barre}")

    mem = stato.get("memoria", {})
    righe += [
        "",
        f"Entrate memoria  : {mem.get('entrate', 0)}",
        f"Report completati: {stato.get('report_completati', 0)}",
    ]

    pat = mem.get("pattern_attivi", [])
    if pat:
        righe += ["", "PATTERN ATTIVI", _sep()]
        for p in pat:
            righe.append(f"  [{p['frequenza']}x] {p['trigger']}")

    ic = stato.get("coerenza", {})
    righe += [
        "",
        f"Coerenza interna: {ic.get('indice_globale', 0):.2f} — {ic.get('interpretazione', 'n/d')}",
        "",
        _sep("═"),
    ]
    return "\n".join(righe)
