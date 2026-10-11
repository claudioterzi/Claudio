"""Protocollo Rosso Rosso Rosso v2.0 — testo del libro, a pagine Telegram."""

from __future__ import annotations

from pathlib import Path

_DIR = Path(__file__).resolve().parent


def _carica() -> list[tuple[str, str]]:
    raw = ""
    for name in ("libro_pagine_a.txt", "libro_pagine_b.txt"):
        p = _DIR / name
        if p.exists():
            piece = p.read_text(encoding="utf-8").strip("\n")
            raw = piece if not raw else raw + "\n=======\n" + piece
    pagine: list[tuple[str, str]] = []
    for blocco in raw.split("\n=======\n"):
        blocco = blocco.strip("\n")
        if not blocco:
            continue
        titolo, _, corpo = blocco.partition("\n")
        pagine.append((titolo.strip(), corpo.strip()))
    return pagine


PAGINE = _carica()


def indice() -> str:
    lines = ["Protocollo Rosso — indice\n"]
    for i, (titolo, _corpo) in enumerate(PAGINE):
        lines.append(f"{i}. {titolo}")
    lines.append("\nScrivi un numero, avanti, indietro o fine.")
    return "\n".join(lines)


def pagina(i: int) -> tuple[int, str]:
    n = max(len(PAGINE), 1)
    i = max(0, min(i, n - 1))
    if not PAGINE:
        return 0, "Libro non caricato."
    titolo, corpo = PAGINE[i]
    coda = f"\n\n— {i}/{n - 1} · {titolo}"
    coda += "\nScrivi avanti" if i < n - 1 else "\nFine del libro. /azione"
    return i, corpo + coda
