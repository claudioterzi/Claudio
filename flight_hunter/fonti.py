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
import urllib.parse
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


@dataclass(frozen=True)
class Offerta:
    """La tariffa più bassa verso una destinazione, CON il giorno reale.
    È il mattone dell'Oracolo: dice non solo quanto ma anche quando partire.
    nome/paese arrivano dalla fonte: coprono anche gli aeroporti fuori dal DB."""
    da: str
    a: str
    prezzo: float
    giorno: str          # YYYY-MM-DD del volo più economico nel range
    partenza: str        # ISO datetime locale
    vettore: str
    nome: str = ""       # nome aeroporto/città di arrivo (dalla fonte)
    paese: str = ""      # paese di arrivo (dalla fonte)


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


def fonti_disponibili() -> list["Fonte"]:
    """Le fonti realmente utilizzabili adesso: Ryanair sempre, Kiwi se c'è la
    chiave. Aggiungere qui altri provider man mano che diventano attivi."""
    attive: list[Fonte] = [FonteRyanair()]
    kiwi = FonteKiwi()
    if kiwi.attiva():
        attive.append(kiwi)
    return attive


class Fonte:
    """Interfaccia di un provider tariffe."""

    nome = "base"

    def mappa_tariffe(self, da: str, dal: str, al: str) -> dict[str, float]:
        """{iata_arrivo: prezzo_minimo} per tutte le destinazioni servite da `da`."""
        return {o.a: o.prezzo for o in self.offerte(da, dal, al)}

    def offerte(self, da: str, dal: str, al: str) -> list[Offerta]:
        """Migliori offerte (dest, prezzo, giorno) nel range di date [dal, al]."""
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
    def offerte(self, da: str, dal: str, al: str) -> list[Offerta]:
        url = (f"{self._BASE}/oneWayFares?departureAirportIataCode={da}"
               f"&outboundDepartureDateFrom={dal}&outboundDepartureDateTo={al}"
               f"&market=it-it")
        dati = self._get(url)
        migliori: dict[str, Offerta] = {}
        for f in dati.get("fares") or []:
            out = f.get("outbound") or {}
            arrivo = (out.get("arrivalAirport") or {}).get("iataCode")
            prezzo = (out.get("price") or {}).get("value")
            if not arrivo or prezzo is None:
                continue
            prezzo = float(prezzo)
            attuale = migliori.get(arrivo)
            if attuale is None or prezzo < attuale.prezzo:
                dep = out.get("departureDate") or ""
                ap = out.get("arrivalAirport") or {}
                citta = (ap.get("city") or {}).get("name")
                migliori[arrivo] = Offerta(
                    da=da, a=arrivo, prezzo=prezzo,
                    giorno=dep[:10], partenza=dep, vettore=self.nome,
                    nome=citta or ap.get("name") or arrivo,
                    paese=ap.get("countryName") or "")
        return list(migliori.values())

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


class FonteKiwi(Fonte):
    """Adattatore Kiwi (Tequila Search API). PRONTO ma dormiente finché non c'è
    la chiave: esporta KIWI_API_KEY (gratuita su tequila.kiwi.com) e si attiva.

    A differenza di Ryanair copre il MONDO (voli di centinaia di compagnie,
    self-transfer già combinati da Kiwi). Non testato in questa sessione perché
    la chiave non c'è: quando la aggiungi, `attiva()` dice se risponde.
    """
    nome = "Kiwi"
    _BASE = "https://api.tequila.kiwi.com/v2"

    def __init__(self, chiave: str | None = None) -> None:
        self.chiave = chiave or os.environ.get("KIWI_API_KEY", "")
        self._ctx = _contesto_ssl()
        self._ultima = 0.0
        self.richieste_fatte = 0

    def attiva(self) -> bool:
        return bool(self.chiave)

    @staticmethod
    def _kiwi_data(iso: str) -> str:
        # Kiwi vuole dd/mm/yyyy; il resto del sistema usa YYYY-MM-DD
        a, m, g = iso[:10].split("-")
        return f"{g}/{m}/{a}"

    def _get(self, path: str, params: dict) -> dict:
        if not self.chiave:
            raise RuntimeError("KIWI_API_KEY assente: FonteKiwi è dormiente")
        attesa = PAUSA_RICHIESTE - (time.monotonic() - self._ultima)
        if attesa > 0:
            time.sleep(attesa)
        query = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
        req = urllib.request.Request(f"{self._BASE}{path}?{query}",
                                     headers={"apikey": self.chiave,
                                              "User-Agent": "flight-hunter/0.2"})
        with urllib.request.urlopen(req, timeout=20, context=self._ctx) as r:
            dati = json.load(r)
        self._ultima = time.monotonic()
        self.richieste_fatte += 1
        return dati

    def offerte(self, da: str, dal: str, al: str) -> list[Offerta]:
        dati = self._get("/search", {
            "fly_from": da, "date_from": self._kiwi_data(dal),
            "date_to": self._kiwi_data(al), "curr": "EUR",
            "limit": 500, "sort": "price", "one_for_city": 1,
        })
        migliori: dict[str, Offerta] = {}
        for v in dati.get("data") or []:
            arrivo, prezzo = v.get("flyTo"), v.get("price")
            if not arrivo or prezzo is None:
                continue
            prezzo = float(prezzo)
            attuale = migliori.get(arrivo)
            if attuale is None or prezzo < attuale.prezzo:
                dep = v.get("local_departure") or ""
                migliori[arrivo] = Offerta(
                    da=da, a=arrivo, prezzo=prezzo,
                    giorno=dep[:10], partenza=dep, vettore=self.nome,
                    nome=v.get("cityTo") or arrivo,
                    paese=(v.get("countryTo") or {}).get("name") or "")
        return list(migliori.values())

    def calendario(self, da: str, a: str, mese: str) -> list[Volo]:
        dati = self._get("/search", {
            "fly_from": da, "fly_to": a,
            "date_from": self._kiwi_data(f"{mese}-01"),
            "date_to": self._kiwi_data(f"{mese}-28"),
            "curr": "EUR", "limit": 200, "sort": "price",
        })
        voli: list[Volo] = []
        for v in dati.get("data") or []:
            if v.get("price") is None:
                continue
            dep = v.get("local_departure") or ""
            voli.append(Volo(da=da, a=a, giorno=dep[:10], partenza=dep,
                             arrivo=v.get("local_arrival") or "",
                             prezzo=float(v["price"]), vettore=self.nome))
        return voli
