"""Pianificatore: da (budget, giorni, mese, tipo) alle proposte di viaggio.

Formula del costo stimato per persona:
    totale = volo_ar + giorni × budget_giorno, maggiorato del 10% di margine imprevisti.

Il punteggio ordina le proposte: prima chi rientra nel budget con il miglior
rapporto qualità/aderenza (mese ideale, tipo richiesto, risparmio residuo).
"""
from __future__ import annotations

from dataclasses import dataclass

from .destinazioni import DESTINAZIONI, MESI, Destinazione

MARGINE_IMPREVISTI = 0.10


@dataclass(frozen=True)
class Proposta:
    destinazione: Destinazione
    giorni: int
    costo_volo: int
    costo_soggiorno: int
    margine: int
    totale: int
    residuo: int            # budget - totale (negativo se sfora)
    nel_budget: bool
    mese_ideale: bool
    tipi_combacianti: tuple[str, ...]
    punteggio: float

    def dizionario(self) -> dict:
        """Serializzazione JSON-friendly per l'API."""
        d = self.destinazione
        return {
            "nome": d.nome,
            "paese": d.paese,
            "tipi": list(d.tipi),
            "perche": d.perche,
            "consigli": list(d.consigli),
            "partenze": list(d.partenze),
            "mesi_ideali": [MESI[m - 1] for m in d.mesi_ideali],
            "giorni": self.giorni,
            "budget_giorno": d.budget_giorno,
            "costo_volo": self.costo_volo,
            "costo_soggiorno": self.costo_soggiorno,
            "margine": self.margine,
            "totale": self.totale,
            "residuo": self.residuo,
            "nel_budget": self.nel_budget,
            "mese_ideale": self.mese_ideale,
            "tipi_combacianti": list(self.tipi_combacianti),
        }


def _valuta(d: Destinazione, budget: int, giorni: int,
            mese: int | None, tipi: tuple[str, ...]) -> Proposta:
    costo_volo = d.volo_ar
    costo_soggiorno = giorni * d.budget_giorno
    base = costo_volo + costo_soggiorno
    margine = round(base * MARGINE_IMPREVISTI)
    totale = base + margine
    residuo = budget - totale

    mese_ideale = mese is None or mese in d.mesi_ideali
    combacianti = tuple(t for t in tipi if t in d.tipi)

    # Punteggio: budget rispettato pesa più di tutto, poi aderenza a mese/tipi,
    # poi il risparmio (premia le mete che lasciano più margine).
    punteggio = 0.0
    if residuo >= 0:
        punteggio += 100.0 + min(residuo / max(budget, 1), 1.0) * 20.0
    else:
        punteggio += max(0.0, 60.0 + (residuo / max(budget, 1)) * 100.0)
    if mese_ideale and mese is not None:
        punteggio += 25.0
    if tipi:
        punteggio += 30.0 * len(combacianti) / len(tipi)

    return Proposta(
        destinazione=d, giorni=giorni,
        costo_volo=costo_volo, costo_soggiorno=costo_soggiorno,
        margine=margine, totale=totale, residuo=residuo,
        nel_budget=residuo >= 0, mese_ideale=mese is not None and mese in d.mesi_ideali,
        tipi_combacianti=combacianti, punteggio=punteggio,
    )


def pianifica(budget: int, giorni: int, mese: int | None = None,
              tipo: str | tuple[str, ...] | None = None,
              max_risultati: int = 6,
              solo_nel_budget: bool = False) -> list[Proposta]:
    """Restituisce le migliori proposte ordinate per punteggio.

    budget           → totale disponibile per persona, in €
    giorni           → notti/giorni di viaggio (min 1)
    mese             → 1-12, opzionale (filtra sul periodo ideale)
    tipo             → uno o più tra TIPI, opzionale
    solo_nel_budget  → se True scarta le mete che sforano
    """
    giorni = max(1, int(giorni))
    budget = max(0, int(budget))
    if isinstance(tipo, str):
        tipi: tuple[str, ...] = (tipo,) if tipo else ()
    else:
        tipi = tuple(tipo or ())

    proposte = [_valuta(d, budget, giorni, mese, tipi) for d in DESTINAZIONI]

    if tipi:
        proposte = [p for p in proposte if p.tipi_combacianti]
    if mese is not None:
        proposte = [p for p in proposte if p.mese_ideale] or proposte
    if solo_nel_budget:
        proposte = [p for p in proposte if p.nel_budget]

    proposte.sort(key=lambda p: (-p.punteggio, p.totale))
    return proposte[:max_risultati]
