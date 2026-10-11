"""Categorie di viaggio per destinazione — «cosa ci trovo»: mare, arte, ecc.

Mappa curata IATA → categorie, così la pagina Parti può etichettare e filtrare
i voli per tipo. Gli aeroporti non mappati semplicemente non hanno etichette.
"""
from __future__ import annotations

# (codice, emoji, etichetta) — l'ordine è quello dei filtri in pagina.
CATEGORIE: tuple[tuple[str, str, str], ...] = (
    ("mare",     "🏖️", "Mare"),
    ("arte",     "🎨", "Arte"),
    ("città",    "🏙️", "Città"),
    ("natura",   "🌿", "Natura"),
    ("montagna", "⛰️", "Montagna"),
    ("movida",   "🎉", "Movida"),
    ("cibo",     "🍝", "Cibo"),
)

_TAG: dict[str, str] = {
    # ── Italia ───────────────────────────────────────────────────────────
    "FCO": "arte città cibo", "CIA": "arte città cibo",
    "NAP": "arte cibo mare città", "BRI": "mare cibo arte", "BDS": "mare",
    "SUF": "mare", "REG": "mare", "CTA": "mare arte cibo",
    "PMO": "mare arte cibo", "TPS": "mare", "CAG": "mare natura",
    "OLB": "mare", "AHO": "mare", "GOA": "mare cibo città",
    "VCE": "arte città", "TSF": "arte città", "TRS": "città arte",
    "FLR": "arte città cibo", "PSA": "arte città", "BLQ": "arte cibo città",
    "VRN": "arte città", "BGY": "città arte cibo", "MXP": "città arte cibo",
    "LIN": "città arte cibo", "TRN": "arte città cibo", "RMI": "mare movida",
    "AOI": "mare", "PSR": "mare", "PMF": "cibo città", "PEG": "arte natura",
    "CUF": "montagna natura",
    # ── Balcani / Est ────────────────────────────────────────────────────
    "TIA": "mare cibo città", "SKP": "città natura cibo", "BEG": "città movida cibo",
    "SJJ": "arte città cibo", "ZAG": "città arte", "ZAD": "mare arte",
    "SPU": "mare arte", "DBV": "mare arte", "SOF": "città montagna natura",
    "OTP": "città arte", "CLJ": "città arte", "BUD": "città arte movida",
    "BTS": "città arte", "VIE": "arte città", "PRG": "arte città movida",
    "KRK": "arte città cibo", "KTW": "città", "WAW": "città arte",
    "WMI": "città arte", "GDN": "mare arte città", "WRO": "arte città",
    "POZ": "città", "RIX": "arte città", "VNO": "arte città", "KUN": "città",
    "TLL": "arte città",
    # ── Grecia / Cipro / Malta ───────────────────────────────────────────
    "ATH": "arte città mare", "SKG": "cibo città mare movida", "CFU": "mare",
    "ZTH": "mare movida", "HER": "mare arte", "CHQ": "mare arte",
    "RHO": "mare arte", "KGS": "mare", "JTR": "mare arte", "JMK": "mare movida",
    "MLA": "mare arte", "PFO": "mare", "LCA": "mare", "EFL": "mare", "PVK": "mare",
    "KLX": "mare", "GPA": "mare arte", "MJT": "mare",
    # ── Spagna / Portogallo ──────────────────────────────────────────────
    "BCN": "città arte mare movida", "GRO": "mare città", "REU": "mare",
    "VLC": "mare città cibo", "ALC": "mare", "AGP": "mare movida",
    "SVQ": "arte città cibo", "MAD": "arte città movida", "PMI": "mare movida",
    "IBZ": "mare movida", "TFS": "mare natura", "LPA": "mare natura",
    "ACE": "mare natura", "FUE": "mare natura", "OPO": "arte cibo città",
    "LIS": "arte città cibo movida", "FAO": "mare",
    # ── Francia / Benelux / Germania / UK / Irlanda ──────────────────────
    "BVA": "arte città", "ORY": "arte città", "CDG": "arte città",
    "NCE": "mare città", "MRS": "mare cibo", "CRL": "città arte cibo",
    "BRU": "città arte cibo", "EIN": "città", "AMS": "arte città movida",
    "HHN": "città", "FRA": "città", "NRN": "città", "CGN": "città arte",
    "BER": "arte città movida", "FMM": "città montagna", "MUC": "città arte",
    "NUE": "arte città", "STN": "arte città movida", "LTN": "arte città movida",
    "LGW": "arte città movida", "MAN": "città movida", "EDI": "arte città",
    "DUB": "città movida cibo", "EMA": "città", "LPL": "città movida",
    "NCL": "città", "BRS": "città", "BHX": "città", "LDZ": "città",
    # ── Nord Africa ──────────────────────────────────────────────────────
    "RAK": "arte cibo", "FEZ": "arte cibo", "TNG": "mare arte", "AGA": "mare",
    "CMN": "città", "TUN": "arte mare", "DJE": "mare",
}


def tipi_di(iata: str) -> tuple[str, ...]:
    """Le categorie di una destinazione (vuoto se non mappata)."""
    return tuple(_TAG.get(iata, "").split())
