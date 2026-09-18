"""L'Oracolo del Viaggio — la parte creativa.

Non chiede «dove vuoi andare». Chiede solo *da dove parti*, guarda i prossimi
giorni sulla rete viva, e pronuncia un responso: la fuga migliore, con il suo
giorno, il suo prezzo — e un verso che la nomina. È Flight Hunter che parla
con la voce oracolare del progetto (Tarocchi Quantici): i numeri sono veri,
il responso li veste.

    from flight_hunter.oracolo import consulta
    r = consulta("Milano", giorni_avanti=10)
    print(r.responso)
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .costi import ParametriCosto
from .motore import MetaPossibile, _mete_nel_range

_MESI = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
         "agosto", "settembre", "ottobre", "novembre", "dicembre")
_GIORNI = ("lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica")

# ── Il vocabolario del responso ────────────────────────────────────────────
# Apertura oracolare (rotazione deterministica sul giorno + origine).
_APERTURE = (
    "La rotta si apre.",
    "Il responso è netto.",
    "La soglia dei prossimi giorni indica una direzione sola.",
    "Le tariffe hanno parlato prima di te.",
    "C'è una fuga che costa meno del tuo restare.",
    "Il cielo, in questi giorni, si piega da una parte.",
)

# Versi per archetipo di destinazione (per paese / carattere del luogo).
_VERSI_PAESE = {
    "Albania":   "Riviera greca al prezzo di una cena: il mare non chiede permesso.",
    "Grecia":    "Pietra bianca e sale — l'origine di tutto, scontata.",
    "Spagna":    "Tapas, luce lunga e nessuna fretta: il sud che guarisce.",
    "Spagna — Canarie": "Estate rubata all'inverno, in mezzo all'Atlantico.",
    "Portogallo": "Oceano e azulejos: malinconia dolce, a poco prezzo.",
    "Marocco":   "Un altro continente a tre ore: medina, menta, vertigine.",
    "Polonia":   "Est che sorprende: birra a due euro e centri intatti.",
    "Ungheria":  "Terme imperiali e notti lunghe sul Danubio.",
    "Cechia":    "La città che sembra dipinta, e costa come una cartolina.",
    "Romania":   "Treni lenti verso i castelli: due viaggi in uno.",
    "Bulgaria":  "La capitale più economica d'Europa, con la montagna in tasca.",
    "Serbia":    "La notte più viva dei Balcani, a metà prezzo.",
    "Bosnia":    "Storia che si tocca, ćevapi che scaldano.",
    "Croazia":   "Adriatico dall'altra sponda, senza i prezzi della costa.",
    "Macedonia del Nord": "Il viaggio più a buon mercato che ci sia: bazar e canyon.",
    "Malta":     "Isola di pietra e inglese: mare mite anche fuori stagione.",
    "Cipro":     "Ultimo sole del Mediterraneo, quando altrove è già autunno.",
    "Slovacchia": "Dormi qui, e Vienna è a un'ora di treno.",
    "Regno Unito": "La metropoli, se la prendi al volo giusto.",
    "Irlanda":   "Verde, vento e pub: l'ovest che non ti aspetti.",
    "Francia":   "Sempre lei, se il prezzo per una volta ti perdona.",
    "Belgio":    "Birre, frites e musei: il nord discreto.",
    "Paesi Bassi": "Canali e biciclette: ordinata felicità.",
    "Germania":  "Efficienza e mercatini: la Mitteleuropa in giornata.",
    "Tunisia":   "Deserto e mare in un colpo solo, appena sotto casa.",
    "Italia":    "Non partire lontano per stare bene: la penisola basta.",
}
_VERSO_DEFAULT = "Una direzione che i comparatori non ti avrebbero mostrato."

# Chiusure (il gesto).
_CHIUSURE = (
    "Vai, prima che il prezzo si accorga di te.",
    "Il resto è solo prenotare.",
    "La finestra è stretta: chi esita paga.",
    "Non è un consiglio. È un varco.",
    "Parti leggero, torna diverso.",
)


@dataclass
class Responso:
    origine: str
    da_data: str
    a_data: str
    meta: MetaPossibile | None
    responso: str
    quando_testo: str = ""
    alternative: list[MetaPossibile] = field(default_factory=list)

    def dizionario(self) -> dict:
        m = self.meta
        return {
            "origine": self.origine,
            "finestra": {"da": self.da_data, "a": self.a_data},
            "trovato": m is not None,
            "responso": self.responso,
            "quando": self.quando_testo,
            "meta": None if not m else {
                "nome": m.nome, "paese": m.paese, "iata": m.iata, "da": m.da,
                "giorno": m.giorno, "totale": m.totale, "prezzo_volo": m.prezzo_volo,
                "costo_terra": m.costo_terra,
            },
            "alternative": [
                {"nome": a.nome, "paese": a.paese, "da": a.da,
                 "giorno": a.giorno, "totale": a.totale}
                for a in self.alternative
            ],
        }


def _data_testo(iso: str) -> str:
    try:
        d = datetime.fromisoformat(iso[:10]).date()
        return f"{_GIORNI[d.weekday()]} {d.day} {_MESI[d.month - 1]}"
    except (ValueError, IndexError):
        return iso


def _scelta(opzioni: tuple, seme: str) -> str:
    """Scelta deterministica ma varia: stessa origine+giorno → stesso responso."""
    h = int(hashlib.sha256(seme.encode()).hexdigest(), 16)
    return opzioni[h % len(opzioni)]


def _componi_responso(origine: str, m: MetaPossibile) -> str:
    seme = f"{origine}|{date.today().isoformat()}|{m.iata}"
    apertura = _scelta(_APERTURE, seme + "a")
    verso = _VERSI_PAESE.get(m.paese, _VERSO_DEFAULT)
    chiusura = _scelta(_CHIUSURE, seme + "c")
    quando = _data_testo(m.giorno)
    via = "" if m.da == _sigla_origine(origine, m) else f" (via {m.da})"
    return (f"{apertura} {m.nome} — {m.paese}. {verso} "
            f"Si parte {quando}{via}, per {m.totale:.0f}€. {chiusura}")


def _sigla_origine(origine: str, m: MetaPossibile) -> str:
    # se l'aeroporto di partenza coincide con l'ancora, non scriviamo "via X"
    from .aeroporti import cerca_aeroporto
    a = cerca_aeroporto(origine)
    return a.iata if a else m.da


def consulta(origine: str, *, giorni_avanti: int = 10, da_giorni: int = 1,
             budget: float | None = None, raggio_origine: float = 250.0,
             bagaglio: bool = False, parametri: ParametriCosto | None = None,
             fonti=None, log=None) -> Responso:
    """Consulta l'Oracolo: da `origine`, nella finestra dei prossimi giorni
    (da domani a +giorni_avanti), la fuga migliore col suo responso.

    da_giorni  → primo giorno utile (1 = domani)
    giorni_avanti → ampiezza della finestra
    """
    oggi = date.today()
    dal = (oggi + timedelta(days=max(0, da_giorni))).isoformat()
    al = (oggi + timedelta(days=max(da_giorni, giorni_avanti))).isoformat()

    mete = _mete_nel_range(origine, dal, al, raggio_origine, bagaglio,
                           None, fonti, parametri, log)
    if budget is not None:
        mete = [m for m in mete if m.totale <= budget]

    if not mete:
        return Responso(
            origine=origine, da_data=dal, a_data=al, meta=None,
            responso=("L'Oracolo tace: nei prossimi giorni, da qui, nessuna "
                      "fuga entro i limiti dati. Allarga la finestra o il budget."),
        )

    scelta = mete[0]
    return Responso(
        origine=origine, da_data=dal, a_data=al, meta=scelta,
        responso=_componi_responso(origine, scelta),
        quando_testo=_data_testo(scelta.giorno),
        alternative=mete[1:6],
    )
