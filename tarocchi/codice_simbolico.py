"""Layer 1 — Il Codice Simbolico: vocabolario delle 74 carte del Mazzo Quantico.

74 carte = 22 Arcani Maggiori + 52 Arcani Minori (4 semi × 13 ranghi, senza il Fante).
Ogni carta è un nodo semantico stabile: nome, elemento, dominio, parole chiave.
Il vocabolario è condiviso sia dall'osservatore-macchina che dall'osservatore-umano.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TipoArcano(Enum):
    MAGGIORE = "maggiore"
    MINORE = "minore"


class Seme(Enum):
    BASTONI = "bastoni"   # Fuoco — volontà, creatività, azione
    COPPE   = "coppe"     # Acqua — emozioni, relazioni, inconscio
    SPADE   = "spade"     # Aria  — mente, conflitto, verità
    DENARI  = "denari"    # Terra — corpo, lavoro, manifestazione


@dataclass(frozen=True)
class Carta:
    nome: str
    indice: int                         # 0-73 nel mazzo ridotto a 74 carte
    arcano: TipoArcano
    seme: Seme | None                   # None per gli arcani maggiori
    rango: int | None                   # 1-13 per gli arcani minori (Asso=1, Re=13)
    parole_chiave: tuple[str, ...] = field(default_factory=tuple)
    elemento: str | None = None         # fuoco / acqua / aria / terra / etere
    dominio: str = ""


# ── Arcani Maggiori (22 carte, indici 0-21) ───────────────────────────────────

ARCANI_MAGGIORI: list[Carta] = [
    Carta("Il Matto",               0,  TipoArcano.MAGGIORE, None, None,
          ("inizio", "libertà", "salto nel vuoto", "ingenuità"),
          "etere", "potenziale puro non ancora formato"),
    Carta("Il Mago",                1,  TipoArcano.MAGGIORE, None, None,
          ("volontà", "azione", "manifesto", "talento"),
          "fuoco", "trasformazione dell'intenzione in realtà"),
    Carta("La Papessa",             2,  TipoArcano.MAGGIORE, None, None,
          ("intuizione", "mistero", "silenzio", "conoscenza interiore"),
          "acqua", "sapere non detto — la soglia tra mondi"),
    Carta("L'Imperatrice",          3,  TipoArcano.MAGGIORE, None, None,
          ("fertilità", "abbondanza", "creazione", "sensualità"),
          "terra", "generatività — il mondo che si fa carne"),
    Carta("L'Imperatore",           4,  TipoArcano.MAGGIORE, None, None,
          ("struttura", "autorità", "ordine", "stabilità"),
          "fuoco", "forma e legge — la volontà che diventa istituzione"),
    Carta("Il Papa",                5,  TipoArcano.MAGGIORE, None, None,
          ("tradizione", "guida spirituale", "conformità", "dottrina"),
          "terra", "mediazione del sacro attraverso il sistema"),
    Carta("Gli Amanti",             6,  TipoArcano.MAGGIORE, None, None,
          ("scelta", "unione", "valori", "desiderio"),
          "aria", "dualità che cerca integrazione — il bivio dei valori"),
    Carta("Il Carro",               7,  TipoArcano.MAGGIORE, None, None,
          ("controllo", "vittoria", "movimento", "disciplina"),
          "acqua", "forza direzionata — la volontà che guida gli opposti"),
    Carta("La Forza",               8,  TipoArcano.MAGGIORE, None, None,
          ("coraggio", "pazienza", "dominio interiore", "fiducia"),
          "fuoco", "potenza gentile — la bestia addomesticata dall'amore"),
    Carta("L'Eremita",              9,  TipoArcano.MAGGIORE, None, None,
          ("solitudine", "saggezza", "ricerca interiore", "discernimento"),
          "terra", "luce nella notte — la lanterna che illumina solo il prossimo passo"),
    Carta("La Ruota della Fortuna", 10, TipoArcano.MAGGIORE, None, None,
          ("cicli", "destino", "svolta", "opportunità"),
          "fuoco", "il giro eterno del tempo — nessuna posizione è permanente"),
    Carta("La Giustizia",           11, TipoArcano.MAGGIORE, None, None,
          ("equilibrio", "verità", "causa-effetto", "rettitudine"),
          "aria", "misura e responsabilità — ogni azione trova il suo peso"),
    Carta("L'Appeso",               12, TipoArcano.MAGGIORE, None, None,
          ("sospensione", "sacrificio", "nuova prospettiva", "resa"),
          "acqua", "il dono dell'attesa — vedere il mondo capovolto"),
    Carta("La Morte",               13, TipoArcano.MAGGIORE, None, None,
          ("trasformazione", "fine", "rinascita", "lasciar andare"),
          "acqua", "passaggio irreversibile — ciò che finisce crea spazio"),
    Carta("La Temperanza",          14, TipoArcano.MAGGIORE, None, None,
          ("moderazione", "alchimia", "flusso", "integrazione"),
          "fuoco", "sintesi degli opposti — la terza via tra gli estremi"),
    Carta("Il Diavolo",             15, TipoArcano.MAGGIORE, None, None,
          ("attaccamento", "illusione", "ombra", "potere materiale"),
          "terra", "catene interiori — l'ombra che crediamo non nostra"),
    Carta("La Torre",               16, TipoArcano.MAGGIORE, None, None,
          ("rivelazione", "crollo", "liberazione forzata", "caos"),
          "fuoco", "la struttura che cade — verità che non può essere contenuta"),
    Carta("Le Stelle",              17, TipoArcano.MAGGIORE, None, None,
          ("speranza", "ispirazione", "guarigione", "apertura"),
          "aria", "guida nel buio — la ferita che diventa dono"),
    Carta("La Luna",                18, TipoArcano.MAGGIORE, None, None,
          ("illusione", "paura", "inconscio", "cicli notturni"),
          "acqua", "il confine del sogno — ciò che è reale e ciò che sembra"),
    Carta("Il Sole",                19, TipoArcano.MAGGIORE, None, None,
          ("gioia", "chiarezza", "vitalità", "successo"),
          "fuoco", "luce piena — quando non serve più nascondersi"),
    Carta("Il Giudizio",            20, TipoArcano.MAGGIORE, None, None,
          ("risveglio", "vocazione", "rinascita", "resa dei conti"),
          "fuoco", "la chiamata — la vita che chiede di essere vissuta davvero"),
    Carta("Il Mondo",               21, TipoArcano.MAGGIORE, None, None,
          ("completamento", "integrazione", "totalità", "traguardo"),
          "terra", "il cerchio chiuso — la danza alla fine del viaggio"),
]


# ── Arcani Minori (52 carte, indici 22-73) ────────────────────────────────────
# 4 semi × 13 ranghi: Asso (1) → Dieci (10) + Fante (11) + Cavallo (12) + Re (13)
# Il Fante classico è rinominato "Fante" come figura di transizione giovane.

_NOMI_RANGO: dict[int, str] = {
    1: "Asso", 2: "Due", 3: "Tre", 4: "Quattro", 5: "Cinque",
    6: "Sei", 7: "Sette", 8: "Otto", 9: "Nove", 10: "Dieci",
    11: "Fante", 12: "Cavaliere", 13: "Re",
}

_SEME_ELEMENTO: dict[Seme, str] = {
    Seme.BASTONI: "fuoco",
    Seme.COPPE:   "acqua",
    Seme.SPADE:   "aria",
    Seme.DENARI:  "terra",
}

_SEME_DOMINIO: dict[Seme, str] = {
    Seme.BASTONI: "azione, passione e creatività",
    Seme.COPPE:   "emozioni, relazioni e intuizione",
    Seme.SPADE:   "mente, verità e conflitto",
    Seme.DENARI:  "corpo, risorse e manifestazione",
}

_SEME_KW: dict[Seme, tuple[str, ...]] = {
    Seme.BASTONI: ("energia", "iniziativa", "entusiasmo", "creatività"),
    Seme.COPPE:   ("sentimento", "connessione", "intuizione", "compassione"),
    Seme.SPADE:   ("chiarezza", "decisione", "conflitto", "analisi"),
    Seme.DENARI:  ("concretezza", "risorse", "pazienza", "manifestazione"),
}

_ARCANI_MINORI: list[Carta] = []
for _i_seme, _seme in enumerate(Seme):
    for _rango in range(1, 14):
        _nome = f"{_NOMI_RANGO[_rango]} di {_seme.value.capitalize()}"
        _indice = 22 + _i_seme * 13 + (_rango - 1)
        _ARCANI_MINORI.append(Carta(
            nome=_nome,
            indice=_indice,
            arcano=TipoArcano.MINORE,
            seme=_seme,
            rango=_rango,
            parole_chiave=_SEME_KW[_seme],
            elemento=_SEME_ELEMENTO[_seme],
            dominio=_SEME_DOMINIO[_seme],
        ))


# ── Mazzo completo: 22 + 52 = 74 carte ───────────────────────────────────────

MAZZO: list[Carta] = ARCANI_MAGGIORI + _ARCANI_MINORI

assert len(MAZZO) == 74, f"Mazzo atteso 74 carte, trovate {len(MAZZO)}"

_INDICE_NOME: dict[str, Carta] = {c.nome.lower(): c for c in MAZZO}
_INDICE_NUM: dict[int, Carta] = {c.indice: c for c in MAZZO}


def cerca_carta(nome: str) -> Carta | None:
    """Cerca una carta per nome (case-insensitive)."""
    return _INDICE_NOME.get(nome.lower().strip())


def carta_per_indice(indice: int) -> Carta | None:
    return _INDICE_NUM.get(indice)
