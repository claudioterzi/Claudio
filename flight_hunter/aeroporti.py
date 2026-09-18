"""Database aeroporti (curato) + geometria.

Copre gli aeroporti italiani e le principali destinazioni low cost europee
e nordafricane. Coordinate in gradi decimali (WGS84).
"""
from __future__ import annotations

import math
from typing import NamedTuple


class Aeroporto(NamedTuple):
    iata: str
    nome: str
    citta: str
    paese: str
    lat: float
    lon: float


_DATI: tuple[tuple[str, str, str, str, float, float], ...] = (
    # ── Italia ────────────────────────────────────────────────────────────
    ("BGY", "Milano Bergamo",       "Milano",     "Italia",  45.674,  9.704),
    ("MXP", "Milano Malpensa",      "Milano",     "Italia",  45.630,  8.723),
    ("LIN", "Milano Linate",        "Milano",     "Italia",  45.445,  9.277),
    ("TRN", "Torino Caselle",       "Torino",     "Italia",  45.200,  7.650),
    ("GOA", "Genova",               "Genova",     "Italia",  44.413,  8.837),
    ("BLQ", "Bologna",              "Bologna",    "Italia",  44.535, 11.288),
    ("VRN", "Verona",               "Verona",     "Italia",  45.396, 10.888),
    ("VCE", "Venezia Marco Polo",   "Venezia",    "Italia",  45.505, 12.352),
    ("TSF", "Treviso",              "Venezia",    "Italia",  45.648, 12.194),
    ("TRS", "Trieste",              "Trieste",    "Italia",  45.827, 13.472),
    ("PMF", "Parma",                "Parma",      "Italia",  44.824, 10.296),
    ("CUF", "Cuneo",                "Cuneo",      "Italia",  44.547,  7.623),
    ("RMI", "Rimini",               "Rimini",     "Italia",  44.020, 12.612),
    ("AOI", "Ancona",               "Ancona",     "Italia",  43.616, 13.360),
    ("PSA", "Pisa",                 "Pisa",       "Italia",  43.684, 10.393),
    ("FLR", "Firenze",              "Firenze",    "Italia",  43.810, 11.205),
    ("PEG", "Perugia",              "Perugia",    "Italia",  43.096, 12.513),
    ("PSR", "Pescara",              "Pescara",    "Italia",  42.432, 14.181),
    ("FCO", "Roma Fiumicino",       "Roma",       "Italia",  41.800, 12.240),
    ("CIA", "Roma Ciampino",        "Roma",       "Italia",  41.799, 12.595),
    ("NAP", "Napoli",               "Napoli",     "Italia",  40.884, 14.290),
    ("BRI", "Bari",                 "Bari",       "Italia",  41.138, 16.766),
    ("BDS", "Brindisi",             "Brindisi",   "Italia",  40.658, 17.947),
    ("SUF", "Lamezia Terme",        "Lamezia",    "Italia",  38.906, 16.242),
    ("REG", "Reggio Calabria",      "Reggio C.",  "Italia",  38.071, 15.652),
    ("CTA", "Catania",              "Catania",    "Italia",  37.467, 15.066),
    ("PMO", "Palermo",              "Palermo",    "Italia",  38.176, 13.091),
    ("TPS", "Trapani",              "Trapani",    "Italia",  37.911, 12.488),
    ("CAG", "Cagliari",             "Cagliari",   "Italia",  39.251,  9.054),
    ("OLB", "Olbia",                "Olbia",      "Italia",  40.899,  9.518),
    ("AHO", "Alghero",              "Alghero",    "Italia",  40.632,  8.291),
    # ── Balcani / Est ─────────────────────────────────────────────────────
    ("TIA", "Tirana",               "Tirana",     "Albania", 41.415, 19.721),
    ("SKP", "Skopje",               "Skopje",     "Macedonia del Nord", 41.962, 21.621),
    ("BEG", "Belgrado",             "Belgrado",   "Serbia",  44.818, 20.309),
    ("SJJ", "Sarajevo",             "Sarajevo",   "Bosnia",  43.825, 18.331),
    ("ZAG", "Zagabria",             "Zagabria",   "Croazia", 45.743, 16.069),
    ("ZAD", "Zara",                 "Zara",       "Croazia", 44.108, 15.347),
    ("SPU", "Spalato",              "Spalato",    "Croazia", 43.539, 16.298),
    ("DBV", "Dubrovnik",            "Dubrovnik",  "Croazia", 42.561, 18.268),
    ("SOF", "Sofia",                "Sofia",      "Bulgaria", 42.697, 23.412),
    ("OTP", "Bucarest Otopeni",     "Bucarest",   "Romania", 44.572, 26.102),
    ("CLJ", "Cluj-Napoca",          "Cluj",       "Romania", 46.785, 23.686),
    ("BUD", "Budapest",             "Budapest",   "Ungheria", 47.437, 19.256),
    ("BTS", "Bratislava",           "Bratislava", "Slovacchia", 48.170, 17.213),
    ("VIE", "Vienna",               "Vienna",     "Austria", 48.110, 16.570),
    ("PRG", "Praga",                "Praga",      "Cechia",  50.101, 14.260),
    ("KRK", "Cracovia",             "Cracovia",   "Polonia", 50.078, 19.785),
    ("KTW", "Katowice",             "Katowice",   "Polonia", 50.474, 19.080),
    ("WAW", "Varsavia Chopin",      "Varsavia",   "Polonia", 52.166, 20.967),
    ("WMI", "Varsavia Modlin",      "Varsavia",   "Polonia", 52.451, 20.652),
    ("GDN", "Danzica",              "Danzica",    "Polonia", 54.378, 18.466),
    ("WRO", "Breslavia",            "Breslavia",  "Polonia", 51.103, 16.886),
    ("POZ", "Poznań",               "Poznań",     "Polonia", 52.421, 16.826),
    ("RIX", "Riga",                 "Riga",       "Lettonia", 56.924, 23.971),
    ("VNO", "Vilnius",              "Vilnius",    "Lituania", 54.634, 25.286),
    ("KUN", "Kaunas",               "Kaunas",     "Lituania", 54.964, 24.085),
    ("TLL", "Tallinn",              "Tallinn",    "Estonia", 59.413, 24.833),
    # ── Grecia / Cipro / Malta ────────────────────────────────────────────
    ("ATH", "Atene",                "Atene",      "Grecia",  37.936, 23.947),
    ("SKG", "Salonicco",            "Salonicco",  "Grecia",  40.520, 22.971),
    ("CFU", "Corfù",                "Corfù",      "Grecia",  39.602, 19.912),
    ("ZTH", "Zante",                "Zante",      "Grecia",  37.751, 20.884),
    ("HER", "Heraklion",            "Creta",      "Grecia",  35.340, 25.180),
    ("CHQ", "Chania",               "Creta",      "Grecia",  35.532, 24.150),
    ("RHO", "Rodi",                 "Rodi",       "Grecia",  36.405, 28.086),
    ("KGS", "Kos",                  "Kos",        "Grecia",  36.793, 27.092),
    ("JTR", "Santorini",            "Santorini",  "Grecia",  36.399, 25.479),
    ("JMK", "Mykonos",              "Mykonos",    "Grecia",  37.435, 25.348),
    ("MLA", "Malta",                "Malta",      "Malta",   35.857, 14.478),
    ("PFO", "Paphos",               "Paphos",     "Cipro",   34.718, 32.486),
    ("LCA", "Larnaca",              "Larnaca",    "Cipro",   34.875, 33.625),
    # ── Spagna / Portogallo ───────────────────────────────────────────────
    ("BCN", "Barcellona El Prat",   "Barcellona", "Spagna",  41.297,  2.078),
    ("GRO", "Girona",               "Barcellona", "Spagna",  41.901,  2.760),
    ("REU", "Reus",                 "Barcellona", "Spagna",  41.147,  1.167),
    ("VLC", "Valencia",             "Valencia",   "Spagna",  39.489, -0.481),
    ("ALC", "Alicante",             "Alicante",   "Spagna",  38.282, -0.558),
    ("AGP", "Malaga",               "Malaga",     "Spagna",  36.675, -4.499),
    ("SVQ", "Siviglia",             "Siviglia",   "Spagna",  37.418, -5.893),
    ("MAD", "Madrid",               "Madrid",     "Spagna",  40.472, -3.561),
    ("PMI", "Palma di Maiorca",     "Maiorca",    "Spagna",  39.552,  2.739),
    ("IBZ", "Ibiza",                "Ibiza",      "Spagna",  38.873,  1.373),
    ("TFS", "Tenerife Sud",         "Tenerife",   "Spagna — Canarie", 28.044, -16.572),
    ("LPA", "Gran Canaria",         "Las Palmas", "Spagna — Canarie", 27.932, -15.387),
    ("ACE", "Lanzarote",            "Lanzarote",  "Spagna — Canarie", 28.946, -13.605),
    ("FUE", "Fuerteventura",        "Fuerteventura", "Spagna — Canarie", 28.453, -13.864),
    ("OPO", "Porto",                "Porto",      "Portogallo", 41.248, -8.681),
    ("LIS", "Lisbona",              "Lisbona",    "Portogallo", 38.774, -9.134),
    ("FAO", "Faro",                 "Faro",       "Portogallo", 37.014, -7.966),
    # ── Francia / Benelux / Germania / UK / Irlanda ───────────────────────
    ("BVA", "Parigi Beauvais",      "Parigi",     "Francia", 49.454,  2.113),
    ("ORY", "Parigi Orly",          "Parigi",     "Francia", 48.723,  2.379),
    ("CDG", "Parigi Charles de Gaulle", "Parigi", "Francia", 49.010,  2.550),
    ("NCE", "Nizza",                "Nizza",      "Francia", 43.665,  7.215),
    ("MRS", "Marsiglia",            "Marsiglia",  "Francia", 43.436,  5.215),
    ("CRL", "Bruxelles Charleroi",  "Bruxelles",  "Belgio",  50.460,  4.454),
    ("BRU", "Bruxelles Zaventem",   "Bruxelles",  "Belgio",  50.901,  4.484),
    ("EIN", "Eindhoven",            "Eindhoven",  "Paesi Bassi", 51.450, 5.375),
    ("AMS", "Amsterdam",            "Amsterdam",  "Paesi Bassi", 52.310, 4.762),
    ("HHN", "Francoforte Hahn",     "Francoforte", "Germania", 49.947, 7.264),
    ("FRA", "Francoforte",          "Francoforte", "Germania", 50.033, 8.570),
    ("NRN", "Düsseldorf Weeze",     "Düsseldorf", "Germania", 51.602,  6.142),
    ("CGN", "Colonia",              "Colonia",    "Germania", 50.866,  7.143),
    ("BER", "Berlino",              "Berlino",    "Germania", 52.362, 13.500),
    ("FMM", "Memmingen",            "Monaco",     "Germania", 47.989, 10.240),
    ("MUC", "Monaco di Baviera",    "Monaco",     "Germania", 48.354, 11.786),
    ("NUE", "Norimberga",           "Norimberga", "Germania", 49.499, 11.078),
    ("STN", "Londra Stansted",      "Londra",     "Regno Unito", 51.885, 0.235),
    ("LTN", "Londra Luton",         "Londra",     "Regno Unito", 51.875, -0.368),
    ("LGW", "Londra Gatwick",       "Londra",     "Regno Unito", 51.148, -0.190),
    ("MAN", "Manchester",           "Manchester", "Regno Unito", 53.354, -2.275),
    ("EDI", "Edimburgo",            "Edimburgo",  "Regno Unito", 55.950, -3.373),
    ("DUB", "Dublino",              "Dublino",    "Irlanda", 53.421, -6.270),
    # ── Nord Africa / extra ───────────────────────────────────────────────
    ("RAK", "Marrakech",            "Marrakech",  "Marocco", 31.607, -8.036),
    ("FEZ", "Fès",                  "Fès",        "Marocco", 33.927, -4.978),
    ("TNG", "Tangeri",              "Tangeri",    "Marocco", 35.727, -5.917),
    ("AGA", "Agadir",               "Agadir",     "Marocco", 30.325, -9.413),
    ("CMN", "Casablanca",           "Casablanca", "Marocco", 33.367, -7.590),
    ("TUN", "Tunisi",               "Tunisi",     "Tunisia", 36.851, 10.227),
    ("DJE", "Djerba",               "Djerba",     "Tunisia", 33.875, 10.775),
)

AEROPORTI: dict[str, Aeroporto] = {
    iata: Aeroporto(iata, nome, citta, paese, lat, lon)
    for iata, nome, citta, paese, lat, lon in _DATI
}


def distanza_km(a: Aeroporto, b: Aeroporto) -> float:
    """Distanza ortodromica (haversine) in km."""
    r = 6371.0
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp = math.radians(b.lat - a.lat)
    dl = math.radians(b.lon - a.lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def cerca_aeroporto(chiave: str) -> Aeroporto | None:
    """Risolve un codice IATA o un nome di città/aeroporto."""
    k = chiave.strip()
    if k.upper() in AEROPORTI:
        return AEROPORTI[k.upper()]
    kl = k.lower()
    for a in AEROPORTI.values():
        if kl in a.citta.lower() or kl in a.nome.lower():
            return a
    return None


def piu_vicino(lat: float, lon: float) -> Aeroporto:
    """L'aeroporto del database più vicino a una coordinata (per geolocalizzazione)."""
    finto = Aeroporto("", "", "", "", lat, lon)
    return min(AEROPORTI.values(), key=lambda a: distanza_km(finto, a))


def vicini(centro: Aeroporto, raggio_km: float, max_n: int = 8) -> list[tuple[Aeroporto, float]]:
    """Aeroporti entro il raggio, ordinati per distanza (incluso il centro)."""
    trovati = [
        (a, distanza_km(centro, a))
        for a in AEROPORTI.values()
        if distanza_km(centro, a) <= raggio_km
    ]
    trovati.sort(key=lambda t: t[1])
    return trovati[:max_n]
