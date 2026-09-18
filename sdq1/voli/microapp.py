"""Micro-app Telegram `/voli` — cerca voli direttamente dalla chat.

Pensata per girare nel webhook Vercel (nessun browser, nessuna dipendenza):
riceve il testo del comando e restituisce HTML pronto per Telegram con
link di ricerca immediata (Google Flights, Skyscanner, Kayak).

Sintassi comando:
    /voli                          → guida + rotte del cacciatore
    /voli BRU GRU                  → link di ricerca Bruxelles→San Paolo
    /voli BRU GRU 2027-02-15      → con data andata
    /voli BRU GRU 2027-02-15 2027-03-01 → andata e ritorno
    /voli rotte                    → matrice del cacciatore automatico

Accetta codici IATA (BRU, CDG…) o nomi città noti (bruxelles, parigi…).
Date: AAAA-MM-GG oppure GG/MM/AAAA.
"""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import quote

# Città note → IATA (estendibile). Claudio parte di solito da Bruxelles.
CITTA = {
    "bruxelles": "BRU", "brussels": "BRU", "bru": "BRU",
    "parigi": "CDG", "paris": "CDG", "cdg": "CDG", "ory": "ORY",
    "madrid": "MAD", "mad": "MAD",
    "lisbona": "LIS", "lisbon": "LIS", "lis": "LIS",
    "milano": "MXP", "milan": "MXP", "mxp": "MXP", "lin": "LIN", "bgy": "BGY",
    "roma": "FCO", "rome": "FCO", "fco": "FCO",
    "londra": "LON", "london": "LON", "lon": "LON", "lhr": "LHR",
    "sanpaolo": "GRU", "saopaulo": "GRU", "gru": "GRU",
    "rio": "GIG", "gig": "GIG",
    "havana": "HAV", "avana": "HAV", "lavana": "HAV", "hav": "HAV", "cuba": "HAV",
    "funchal": "FNC", "madeira": "FNC", "fnc": "FNC",
    "sal": "SID", "capoverde": "SID", "sid": "SID",
    "newyork": "NYC", "nyc": "NYC", "jfk": "JFK",
    "bangkok": "BKK", "bkk": "BKK",
    "mumbai": "BOM", "bom": "BOM",
    "hongkong": "HKG", "hkg": "HKG",
    "kualalumpur": "KUL", "kul": "KUL",
    "tokyo": "TYO", "tyo": "TYO", "nrt": "NRT", "hnd": "HND",
    "istanbul": "IST", "ist": "IST",
    "marrakech": "RAK", "rak": "RAK",
    "tenerife": "TFS", "tfs": "TFS",
}


def _codice(luogo: str) -> str | None:
    """Normalizza un luogo in codice IATA (o None se ignoto)."""
    chiave = re.sub(r"[^a-z]", "", luogo.lower())
    if chiave in CITTA:
        return CITTA[chiave]
    if re.fullmatch(r"[a-z]{3}", chiave):
        return chiave.upper()  # sembra già un codice IATA
    return None


def _data(testo: str) -> str | None:
    """Normalizza una data in AAAA-MM-GG (o None)."""
    testo = testo.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(testo, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _link_ricerca(da: str, a: str, andata: str | None, ritorno: str | None) -> list[tuple[str, str]]:
    """Costruisce i link di ricerca per le principali piattaforme."""
    # Google Flights — query testuale, robusta anche senza date
    q = f"Flights from {da} to {a}"
    if andata:
        q += f" on {andata}"
        if ritorno:
            q += f" through {ritorno}"
    gf = "https://www.google.com/travel/flights?curr=EUR&q=" + quote(q)

    # Skyscanner — /trasporti/voli/da/a/[aammgg[/aammgg]]
    sky = f"https://www.skyscanner.net/transport/flights/{da.lower()}/{a.lower()}/"
    if andata:
        sky += datetime.strptime(andata, "%Y-%m-%d").strftime("%y%m%d") + "/"
        if ritorno:
            sky += datetime.strptime(ritorno, "%Y-%m-%d").strftime("%y%m%d") + "/"

    # Kayak — /flights/DA-A/data[/data]
    kay = f"https://www.kayak.com/flights/{da}-{a}"
    if andata:
        kay += f"/{andata}"
        if ritorno:
            kay += f"/{ritorno}"

    return [("Google Flights", gf), ("Skyscanner", sky), ("Kayak", kay)]


def _testo_rotte() -> str:
    """Matrice del cacciatore automatico (import pigro per restare leggeri)."""
    try:
        from .rotte import ROTTE
    except Exception:
        return "⚠️ Matrice rotte non disponibile."
    righe = ["🎯 <b>Rotte del cacciatore automatico</b> (3 scansioni/giorno)\n"]
    for r in ROTTE:
        tratte = " → ".join([r.legs[0]["from"]] + [l["to"] for l in r.legs])
        righe.append(f"  • <b>{r.id}</b> — {tratte} (allarme sotto €{r.soglia_eur})")
    righe.append("\nQuando un prezzo scende sotto soglia ti arriva la nota qui. 🔴")
    return "\n".join(righe)


def _testo_lowcost(args: str) -> str:
    """Pepite Ryanair dal vivo (import pigro; API pubblica, niente browser)."""
    parti = args.split()
    try:
        prezzo_max = float(parti[1]) if len(parti) > 1 else 20.0
    except ValueError:
        prezzo_max = 20.0
    try:
        from .lowcost import cerca_pepite, formatta_nota
        pepite = cerca_pepite(prezzo_max=prezzo_max)
    except Exception as e:
        return f"⚠️ Radar lowcost non disponibile ora: {e}"
    if not pepite:
        return f"🔍 Nessun volo sotto €{prezzo_max:.0f} da Bruxelles/Parigi nei prossimi 3 mesi."
    return formatta_nota(pepite, prezzo_max)


def _guida() -> str:
    return (
        "✈️ <b>Micro-app Voli — cerca dalla chat</b>\n\n"
        "<b>Uso:</b>\n"
        "  /voli BRU GRU — link di ricerca subito\n"
        "  /voli bruxelles sanpaolo 2027-02-15 2027-03-01\n"
        "  /voli parigi madeira 15/11/2026\n"
        "  /voli lowcost — pepite Ryanair sotto €20 da BRU/CDG, dal vivo\n"
        "  /voli lowcost 30 — soglia personalizzata (€30)\n"
        "  /voli rotte — matrice del cacciatore automatico\n\n"
        "<b>Città che capisco al volo:</b> bruxelles, parigi, madrid, lisbona, "
        "milano, roma, sanpaolo, havana/cuba, madeira, capoverde, newyork, "
        "bangkok, mumbai, hongkong… oppure qualsiasi codice IATA (3 lettere).\n\n"
        "Date: AAAA-MM-GG o GG/MM/AAAA. Senza date ti do la ricerca aperta."
    )


def gestisci_comando_voli(args: str) -> str:
    """Punto d'ingresso della micro-app: testo del comando → risposta HTML."""
    args = (args or "").strip()

    if not args or args.lower() in ("help", "?"):
        return _guida()
    if args.lower() in ("rotte", "matrice", "caccia"):
        return _testo_rotte()
    if args.lower().startswith("lowcost"):
        return _testo_lowcost(args)

    parole = args.split()
    if len(parole) < 2:
        return "❓ Servono partenza e destinazione. Es: <code>/voli BRU GRU</code>\n\n" + _guida()

    da = _codice(parole[0])
    a = _codice(parole[1])
    if not da or not a:
        ignoto = parole[0] if not da else parole[1]
        return (
            f"❓ Non riconosco «{ignoto}». Usa un codice IATA (3 lettere) "
            f"o una città nota (/voli per la lista)."
        )

    andata = _data(parole[2]) if len(parole) > 2 else None
    if len(parole) > 2 and not andata:
        return f"❓ Data «{parole[2]}» non valida. Formato: AAAA-MM-GG o GG/MM/AAAA."
    ritorno = _data(parole[3]) if len(parole) > 3 else None
    if len(parole) > 3 and not ritorno:
        return f"❓ Data ritorno «{parole[3]}» non valida. Formato: AAAA-MM-GG o GG/MM/AAAA."

    righe = [f"✈️ <b>Ricerca {da} → {a}</b>"]
    if andata:
        periodo = andata + (f" → {ritorno}" if ritorno else " (sola andata)")
        righe.append(f"📅 {periodo}")
    righe.append("")
    for nome, url in _link_ricerca(da, a, andata, ritorno):
        righe.append(f'🔎 <a href="{url}">{nome}</a>')
    righe.append("")
    righe.append(
        "💡 <i>Consiglio pirata: apri Google Flights e attiva "
        "«Track prices» — ti avvisa lui sui cali. Il cacciatore SDQ-1 "
        "intanto sorveglia le rotte fisse (/voli rotte).</i>"
    )
    return "\n".join(righe)
