"""Canone Alpha 0.1 — Motore di Collasso.

Il cuore del Sistema B: CARTA + ASSE + POLARITÀ = SIGNIFICATO.

Il motore non predice: collassa. Dalla domanda deduce l'asse
(nord = radice/inconscio, est = azione/futuro, sud = emozione/presente,
ovest = riflessione/passato), dal contesto emotivo deduce la polarità
(luce/ombra), estrae una carta e lascia emergere il significato.

Doppia interpretazione:
    - osservatore-macchina → deduzione strutturale, stabile e riproducibile
      (a parità di domanda e contesto, stesso asse e stessa polarità);
    - osservatore-umano → la carta estratta e le domande di riflessione,
      unica per ogni incontro.

Zero dipendenze esterne, come il resto del pacchetto.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
from typing import Optional

# ---------------------------------------------------------------------------
# Canone
# ---------------------------------------------------------------------------

_PERCORSO_CANONE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "tarocchi_quantici_alpha.json"
)

with open(_PERCORSO_CANONE, encoding="utf-8") as _f:
    CANONE = json.load(_f)

CARTE = CANONE["carte"]
MANIFESTO = CANONE["manifesto"]
ASSI = ("nord", "est", "sud", "ovest")
POLARITA = ("luce", "ombra")

SIGNIFICATO_ASSI = {
    "nord": "radice / inconscio",
    "est": "azione / futuro",
    "sud": "emozione / presente",
    "ovest": "riflessione / passato",
}

_INDICE_NOMI = {c["nome"].lower(): c for c in CARTE}


def cerca_carta_alpha(nome: str) -> Optional[dict]:
    """Trova una carta per nome (case-insensitive, anche parziale)."""
    chiave = nome.strip().lower()
    if not chiave:
        return None
    if chiave in _INDICE_NOMI:
        return _INDICE_NOMI[chiave]
    for nome_carta, carta in _INDICE_NOMI.items():
        if chiave in nome_carta:
            return carta
    return None


# ---------------------------------------------------------------------------
# Deduzione dell'asse — la domanda orienta la bussola
# ---------------------------------------------------------------------------

_SEGNALI_ASSE = {
    "nord": (
        "chi sono", "davvero", "profond", "senso", "origine", "radice",
        "anima", "inconsci", "nascost", "sogn", "verità", "essenza",
        "identità", "dentro di me", "significa", "vocazione", "destino",
    ),
    "est": (
        "futuro", "domani", "sarà", "sarò", "divent", "prossim", "iniziar",
        "comincer", "cambiar", "cambier", "farò", "devo fare", "agire",
        "andrò", "strada", "direzione", "sceglier", "decid", "obiettivo",
        "meta", "riuscir", "progetto", "passo",
    ),
    "sud": (
        "sento", "provo", "emozion", "cuore", "amo", "amore", "oggi",
        "adesso", "in questo momento", "presente", "soffr", "gioia",
        "felic", "trist", "vivo", "relazione", "vicin", "manca",
    ),
    "ovest": (
        "passato", "ieri", "ricord", "successo", "ho fatto", "ho perso",
        "finit", "chius", "lasciat", "perché è", "rimpiant", "dietro",
        "prima", "imparat", "lezione", "allora", "andata così",
    ),
}

_SEGNALI_POLARITA = {
    "luce": (
        "speranza", "grat", "apert", "fiducia", "gioia", "curios", "amore",
        "forza", "pront", "desider", "entusiasm", "chiarezza", "pace",
        "crescita", "crescere", "sereno", "serena", "leggerezza",
    ),
    "ombra": (
        "paura", "ansia", "blocc", "dolore", "rabbia", "confus", "buio",
        "stanc", "vuot", "tradiment", "fallim", "fallit", "solitudine",
        "trist", "peso", "angoscia", "smarrit", "perso", "persa", "dubbio",
    ),
}


def _scelta_deterministica(testo: str, opzioni: tuple) -> str:
    """Scelta stabile e riproducibile: stesso testo → stessa opzione.

    È il fallback dell'osservatore-macchina quando la domanda non
    sbilancia la bussola: non casualità, ma firma del testo stesso.
    """
    impronta = hashlib.sha256(testo.encode("utf-8")).digest()
    return opzioni[impronta[0] % len(opzioni)]


def _conta_segnali(testo: str, segnali: tuple) -> tuple:
    presenti = [s for s in segnali if s in testo]
    return len(presenti), presenti


def deduci_asse(domanda: str) -> dict:
    """Domanda → asse. Restituisce asse, movente e segnali riconosciuti."""
    testo = (domanda or "").lower()
    punteggi = {}
    trovati = {}
    for asse in ASSI:
        n, presenti = _conta_segnali(testo, _SEGNALI_ASSE[asse])
        punteggi[asse] = n
        trovati[asse] = presenti

    massimo = max(punteggi.values())
    if massimo == 0:
        asse = _scelta_deterministica("asse::" + testo, ASSI)
        movente = (
            "la domanda non orienta la bussola: l'asse emerge "
            "dalla firma della domanda stessa"
        )
        segnali = []
    else:
        vincitori = tuple(a for a in ASSI if punteggi[a] == massimo)
        asse = (
            vincitori[0]
            if len(vincitori) == 1
            else _scelta_deterministica("asse::" + testo, vincitori)
        )
        segnali = trovati[asse]
        movente = f"la domanda guarda verso {SIGNIFICATO_ASSI[asse]}"

    return {"asse": asse, "movente": movente, "segnali": segnali}


def deduci_polarita(contesto: str, domanda: str = "") -> dict:
    """Contesto emotivo → polarità. Luce e ombra: stessa energia."""
    testo = ((contesto or "") + " " + (domanda or "")).lower()
    punteggi = {}
    trovati = {}
    for pol in POLARITA:
        n, presenti = _conta_segnali(testo, _SEGNALI_POLARITA[pol])
        punteggi[pol] = n
        trovati[pol] = presenti

    if punteggi["luce"] == punteggi["ombra"]:
        pol = _scelta_deterministica("polarita::" + testo, POLARITA)
        movente = (
            "il contesto non sbilancia: la polarità emerge "
            "dalla firma delle parole"
            if punteggi["luce"] == 0
            else "luce e ombra si equivalgono: decide la firma delle parole"
        )
        segnali = trovati[pol]
    else:
        pol = "luce" if punteggi["luce"] > punteggi["ombra"] else "ombra"
        segnali = trovati[pol]
        movente = f"il contesto pende verso la {pol}"

    return {"polarita": pol, "movente": movente, "segnali": segnali}


# ---------------------------------------------------------------------------
# Estrazione e collasso
# ---------------------------------------------------------------------------

def estrai_carte(n: int = 1, seme_casuale: Optional[int] = None) -> list:
    """Estrae n carte distinte dal canone (osservatore-umano: unica)."""
    n = max(1, min(n, len(CARTE)))
    rng = random.Random(seme_casuale)
    return rng.sample(CARTE, n)


def collassa(carta: dict, asse: str, polarita: str) -> dict:
    """CARTA + ASSE + POLARITÀ = SIGNIFICATO. L'eco è l'altra polarità."""
    if asse not in ASSI:
        raise ValueError(f"asse sconosciuto: {asse!r}")
    if polarita not in POLARITA:
        raise ValueError(f"polarità sconosciuta: {polarita!r}")

    opposta = "ombra" if polarita == "luce" else "luce"
    significato = carta[polarita][asse]
    return {
        "carta": carta["nome"],
        "simbolo": carta["simbolo"],
        "ciclo": carta["ciclo"],
        "asse": asse,
        "asse_significato": SIGNIFICATO_ASSI[asse],
        "polarita": polarita,
        "significato": significato,
        "eco": {"polarita": opposta, "significato": carta[opposta][asse]},
        "formula": f"{carta['nome']} · {asse.capitalize()} · {polarita.capitalize()} → {significato}",
    }


def _domande_di_riflessione(collasso: dict) -> list:
    per_asse = {
        "nord": "Che cosa, alla radice, ha preparato questo momento?",
        "est": "Qual è il primo passo che questo significato ti chiede?",
        "sud": "Dove lo senti, adesso, nel corpo e nelle emozioni?",
        "ovest": "Che cosa del passato chiede di essere riletto alla sua luce?",
    }
    return [
        f"Dove riconosci «{collasso['significato']}» nella tua vita?",
        per_asse[collasso["asse"]],
        f"E se fosse invece «{collasso['eco']['significato']}» — cosa cambierebbe?",
    ]


def leggi(
    domanda: str = "",
    contesto: str = "",
    n_carte: int = 1,
    asse: Optional[str] = None,
    polarita: Optional[str] = None,
    nomi_carte: Optional[list] = None,
    seme_casuale: Optional[int] = None,
) -> dict:
    """Lettura completa: deduzione strutturale + collasso + riflessione.

    Asse e polarità possono essere forzati (l'osservatore sceglie);
    altrimenti li deduce il motore dalla domanda e dal contesto.
    Le carte possono essere nominate; altrimenti vengono estratte.
    """
    ded_asse = (
        {"asse": asse, "movente": "asse scelto dall'osservatore", "segnali": []}
        if asse in ASSI
        else deduci_asse(domanda)
    )
    ded_pol = (
        {"polarita": polarita, "movente": "polarità scelta dall'osservatore", "segnali": []}
        if polarita in POLARITA
        else deduci_polarita(contesto, domanda)
    )

    carte = []
    if nomi_carte:
        for nome in nomi_carte:
            trovata = cerca_carta_alpha(nome)
            if trovata and trovata not in carte:
                carte.append(trovata)
    if not carte:
        carte = estrai_carte(n_carte, seme_casuale)

    collassi = [collassa(c, ded_asse["asse"], ded_pol["polarita"]) for c in carte]

    return {
        "canone": f"{MANIFESTO['nome']} — {MANIFESTO['versione']}",
        "domanda": domanda or None,
        "contesto": contesto or None,
        "strutturale": {
            "asse": ded_asse,
            "polarita": ded_pol,
            "principio": MANIFESTO["principio"],
        },
        "collassi": collassi,
        "riflessione": _domande_di_riflessione(collassi[0]),
        "conclusione": MANIFESTO["conclusione"],
    }


if __name__ == "__main__":
    # Verifica del canone: La Ferita · Sud · Luce → guarigione, · Ombra → paralisi.
    ferita = cerca_carta_alpha("La Ferita")
    assert ferita is not None
    print(collassa(ferita, "sud", "luce")["formula"])
    print(collassa(ferita, "sud", "ombra")["formula"])

    # Riproducibilità strutturale: stessa domanda → stesso asse.
    a1 = deduci_asse("Che cosa devo fare per il mio futuro?")
    a2 = deduci_asse("Che cosa devo fare per il mio futuro?")
    assert a1 == a2 and a1["asse"] == "est", a1

    p = deduci_polarita("Sento molta paura e confusione")
    assert p["polarita"] == "ombra", p

    lettura = leggi(
        domanda="Chi sono davvero, sotto tutto questo?",
        contesto="C'è gratitudine, e un po' di pace.",
        seme_casuale=42,
    )
    print(json.dumps(lettura, ensure_ascii=False, indent=2))
