"""Radar promo ed error fare — legge i feed RSS delle fonti di offerte.

Fonti verificate raggiungibili senza browser (stdlib pura):
  - fly4free.com/feed        → error fare e promo Europa
  - travel-dealz.com/feed    → deal di qualità, spesso da Parigi/Bruxelles

Il radar filtra per: parole chiave forti (error fare, price drop, mistake),
prezzi bassi nel titolo, e rilevanza geografica (Bruxelles/Parigi/Europa).
Segnala solo elementi recenti (finestra configurabile) per non ripetersi.
"""

from __future__ import annotations

import logging
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

log = logging.getLogger("sdq1.voli.radar")

FEEDS = (
    "https://www.fly4free.com/feed/",
    "https://travel-dealz.com/feed/",
)

# Parole che indicano un vero colpo (non semplice pubblicità)
KEYWORD_FORTI = re.compile(
    r"error fare|mistake fare|price drop|glitch|PRICE ERROR|super deal|crazy", re.I
)
# Rilevanza geografica per Claudio
KEYWORD_GEO = re.compile(
    r"brussels|bruxelles|charleroi|paris|beauvais|orly|cdg|from europe|european cities|belgium|france",
    re.I,
)
# Prezzo nel titolo (es. €96, € 152, 19€, €1,715 — gestisce le migliaia)
PREZZO_RE = re.compile(r"€\s?(\d{1,3}(?:[.,]\d{3})+|\d{1,4})|(\d{1,3}(?:[.,]\d{3})+|\d{1,4})\s?€")


@dataclass(frozen=True)
class Segnale:
    titolo: str
    link: str
    fonte: str
    quando: str          # ISO
    prezzo_eur: int | None
    forte: bool          # ha keyword forte (error fare ecc.)


def _scarica(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def _prezzo(titolo: str) -> int | None:
    m = PREZZO_RE.search(titolo)
    if not m:
        return None
    grezzo = (m.group(1) or m.group(2)).replace(",", "").replace(".", "")
    return int(grezzo)


def scansiona(finestra_ore: int = 26, prezzo_interessante: int = 250) -> list[Segnale]:
    """Ritorna i segnali recenti e rilevanti dai feed.

    Un item entra se è nella finestra temporale E almeno una di:
      - keyword forte (error fare / price drop / glitch)
      - geograficamente rilevante (Bruxelles/Parigi/Europa) con prezzo nel titolo
      - prezzo nel titolo sotto `prezzo_interessante` (lungo raggio impazzito)
    """
    limite = datetime.now(timezone.utc) - timedelta(hours=finestra_ore)
    segnali: list[Segnale] = []
    for feed in FEEDS:
        try:
            root = ET.fromstring(_scarica(feed))
        except Exception as exc:
            log.warning("Feed %s non leggibile: %s", feed, exc)
            continue
        fonte = re.sub(r"^www\.|\.com.*$", "", re.sub(r"^https?://", "", feed)).strip("/")
        for item in root.iter("item"):
            titolo = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            try:
                quando = parsedate_to_datetime(pub)
            except Exception:
                continue
            if quando < limite:
                continue
            prezzo = _prezzo(titolo)
            forte = bool(KEYWORD_FORTI.search(titolo))
            geo = bool(KEYWORD_GEO.search(titolo))
            economico = prezzo is not None and prezzo <= prezzo_interessante
            if forte or (geo and prezzo is not None) or economico:
                segnali.append(Segnale(
                    titolo=titolo, link=link, fonte=fonte,
                    quando=quando.isoformat(), prezzo_eur=prezzo, forte=forte,
                ))
    # i colpi forti prima, poi per prezzo
    segnali.sort(key=lambda s: (not s.forte, s.prezzo_eur if s.prezzo_eur is not None else 9999))
    return segnali


def formatta_nota(segnali: list[Segnale]) -> str:
    """Nota Telegram per i segnali del radar."""
    if not segnali:
        return ""
    righe = ["📡 <b>Radar promo & error fare</b> — fonti fresche (ultime 24h)\n"]
    for s in segnali[:8]:
        icona = "🔴🔴🔴" if s.forte else "🟡"
        prezzo = f" — <b>€{s.prezzo_eur}</b>" if s.prezzo_eur is not None else ""
        righe.append(f'{icona} <a href="{s.link}">{s.titolo}</a>{prezzo} <i>({s.fonte})</i>')
    righe.append("\n#nota #voli #radar #promo")
    return "\n".join(righe)
