"""Radar iper low cost — interroga direttamente l'API fare-finder di Ryanair.

Metodo pirata: nessun blog, nessun intermediario. L'endpoint pubblico
`services-api.ryanair.com/farfnd/v4/oneWayFares` restituisce le tariffe più
basse reali per aeroporto di partenza. Zero dipendenze (urllib + json).

Aeroporti di Claudio: Bruxelles (CRL, BRU) e Parigi (BVA, ORY).
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta

log = logging.getLogger("sdq1.voli.lowcost")

_API = "https://services-api.ryanair.com/farfnd/v4/oneWayFares"

# Aeroporti di partenza sorvegliati (città → codici)
AEROPORTI = {
    "Bruxelles": ("CRL", "BRU"),
    "Parigi": ("BVA",),  # Ryanair su Parigi vola quasi solo da Beauvais
}


@dataclass(frozen=True)
class Pepita:
    partenza: str          # codice IATA di partenza
    citta_partenza: str    # nome umano (Bruxelles/Parigi)
    destinazione: str      # nome aeroporto di arrivo
    codice_dest: str
    prezzo_eur: float
    data: str              # AAAA-MM-GG


def _interroga(aeroporto: str, prezzo_max: float, giorni: int, limite: int) -> list[dict]:
    da = date.today() + timedelta(days=1)
    a = da + timedelta(days=giorni)
    params = urllib.parse.urlencode({
        "departureAirportIataCode": aeroporto,
        "outboundDepartureDateFrom": da.isoformat(),
        "outboundDepartureDateTo": a.isoformat(),
        "priceValueTo": prezzo_max,
        "currency": "EUR",
        "limit": limite,
    })
    req = urllib.request.Request(
        f"{_API}?{params}",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read()).get("fares", [])


def cerca_pepite(prezzo_max: float = 20.0, giorni: int = 90, limite: int = 40) -> list[Pepita]:
    """Tariffe sotto `prezzo_max` nei prossimi `giorni` dai nostri aeroporti.

    Errori di rete su un aeroporto non fermano gli altri.
    """
    pepite: list[Pepita] = []
    for citta, codici in AEROPORTI.items():
        for ap in codici:
            try:
                fares = _interroga(ap, prezzo_max, giorni, limite)
            except Exception as exc:
                log.warning("Ryanair %s non risponde: %s", ap, exc)
                continue
            for f in fares:
                o = f.get("outbound") or {}
                dest = o.get("arrivalAirport") or {}
                prezzo = (o.get("price") or {}).get("value")
                if prezzo is None:
                    continue
                pepite.append(Pepita(
                    partenza=ap,
                    citta_partenza=citta,
                    destinazione=dest.get("name", "?"),
                    codice_dest=dest.get("iataCode", "?"),
                    prezzo_eur=float(prezzo),
                    data=(o.get("departureDate") or "")[:10],
                ))
    # dedup per (partenza, destinazione): tieni la più economica
    migliori: dict[tuple[str, str], Pepita] = {}
    for p in pepite:
        k = (p.partenza, p.codice_dest)
        if k not in migliori or p.prezzo_eur < migliori[k].prezzo_eur:
            migliori[k] = p
    return sorted(migliori.values(), key=lambda p: p.prezzo_eur)


def formatta_nota(pepite: list[Pepita], prezzo_max: float) -> str:
    """Nota Telegram per le pepite trovate."""
    if not pepite:
        return ""
    righe = [f"💎 <b>Iper low cost sotto €{prezzo_max:.0f}</b> — API Ryanair, prezzi reali\n"]
    for citta in AEROPORTI:
        blocco = [p for p in pepite if p.citta_partenza == citta][:8]
        if not blocco:
            continue
        righe.append(f"<b>Da {citta}:</b>")
        for p in blocco:
            righe.append(f"  • {p.destinazione} <b>€{p.prezzo_eur:.2f}</b> ({p.data}) da {p.partenza}")
        righe.append("")
    righe.append("Prenota su ryanair.com — a questi prezzi durano poco.")
    righe.append("#nota #voli #lowcost #ryanair")
    return "\n".join(righe)
