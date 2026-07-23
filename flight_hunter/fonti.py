"""Fonti tariffarie. Solo API pubbliche o con chiave — niente scraping.

Oggi implementata: Ryanair (API pubblica farfnd, la stessa usata dal loro sito).
L'interfaccia `Fonte` permette di aggiungere provider (Kiwi Tequila, Amadeus
Self-Service, Travelpayouts) quando ci sono le chiavi API.
"""
from __future__ import annotations

import json
import os
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

PAUSA_RICHIESTE = 0.35   # secondi tra richieste: educazione prima di tutto


@dataclass(frozen=True)
class Volo:
    """Un volo con la sua tariffa minima nota (per persona, senza extra)."""
    da: str
    a: str
    giorno: str          # YYYY-MM-DD
    partenza: str        # ISO datetime locale
    arrivo: str          # ISO datetime locale
    prezzo: float        # €
    vettore: str


def _contesto_ssl() -> ssl.SSLContext | None:
    """Contesto di default; se fallisce, prova i CA bundle indicati in env
    (necessario dietro proxy aziendali con CA propria)."""
    for var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        percorso = os.environ.get(var)
        if percorso and os.path.exists(percorso):
            return ssl.create_default_context(cafile=percorso)
    percorso = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(percorso):
        return ssl.create_default_context(cafile=percorso)
    return None


class Fonte:
    """Interfaccia di un provider tariffe."""

    nome = "base"

    def mappa_tariffe(self, da: str, dal: str, al: str) -> dict[str, float]:
        """{iata_arrivo: prezzo_minimo} per tutte le destinazioni servite da `da`."""
        raise NotImplementedError

    def calendario(self, da: str, a: str, mese: str) -> list[Volo]:
        """Minimo giornaliero sulla rotta per il mese YYYY-MM."""
        raise NotImplementedError


class FonteRyanair(Fonte):
    nome = "Ryanair"
    _BASE = "https://services-api.ryanair.com/farfnd/v4"

    def __init__(self) -> None:
        self._cache: dict[str, object] = {}
        self._ctx = None
        self._ctx_provato = False
        self._ultima_richiesta = 0.0
        self.richieste_fatte = 0

    # ── HTTP ──────────────────────────────────────────────────────────────
    def _get(self, url: str) -> dict:
        if url in self._cache:
            return self._cache[url]  # type: ignore[return-value]

        attesa = PAUSA_RICHIESTE - (time.monotonic() - self._ultima_richiesta)
        if attesa > 0:
            time.sleep(attesa)

        req = urllib.request.Request(url, headers={"User-Agent": "flight-hunter/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=20, context=self._ctx) as r:
                dati = json.load(r)
        except (urllib.error.URLError, ssl.SSLError, OSError):
            if self._ctx_provato:
                raise
            self._ctx = _contesto_ssl()
            self._ctx_provato = True
            with urllib.request.urlopen(req, timeout=20, context=self._ctx) as r:
                dati = json.load(r)

        self._ultima_richiesta = time.monotonic()
        self.richieste_fatte += 1
        self._cache[url] = dati
        return dati

    # ── API ───────────────────────────────────────────────────────────────
    def mappa_tariffe(self, da: str, dal: str, al: str) -> dict[str, float]:
        url = (f"{self._BASE}/oneWayFares?departureAirportIataCode={da}"
               f"&outboundDepartureDateFrom={dal}&outboundDepartureDateTo={al}"
               f"&market=it-it")
        dati = self._get(url)
        mappa: dict[str, float] = {}
        for f in dati.get("fares") or []:
            out = f.get("outbound") or {}
            arrivo = (out.get("arrivalAirport") or {}).get("iataCode")
            prezzo = ((out.get("price") or {}).get("value"))
            if arrivo and prezzo is not None:
                mappa[arrivo] = min(mappa.get(arrivo, float("inf")), float(prezzo))
        return mappa

    def calendario(self, da: str, a: str, mese: str) -> list[Volo]:
        url = (f"{self._BASE}/oneWayFares/{da}/{a}/cheapestPerDay"
               f"?outboundMonthOfDate={mese}-01&currency=EUR")
        try:
            dati = self._get(url)
        except urllib.error.HTTPError:
            return []
        voli: list[Volo] = []
        for f in (dati.get("outbound") or {}).get("fares") or []:
            if f.get("unavailable") or f.get("soldOut") or not f.get("price"):
                continue
            voli.append(Volo(
                da=da, a=a,
                giorno=f["day"],
                partenza=f.get("departureDate") or "",
                arrivo=f.get("arrivalDate") or "",
                prezzo=float(f["price"]["value"]),
                vettore=self.nome,
            ))
        return voli
