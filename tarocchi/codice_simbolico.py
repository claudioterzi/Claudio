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

# Keywords carta per carta — Layer 1 completo (non più placeholder di seme)
# Formato: (Seme, rango) → (parole_chiave, dominio_specifico)
_KW_CARTA: dict[tuple[Seme, int], tuple[tuple[str, ...], str]] = {
    # ── BASTONI (fuoco) ───────────────────────────────────────────────────────
    (Seme.BASTONI, 1):  (("scintilla originaria", "impulso creativo", "seme di volontà", "potenziale non ancora formato"),
                         "il fuoco prima che diventi fiamma"),
    (Seme.BASTONI, 2):  (("pianificazione", "scelta coraggiosa", "visione dell'orizzonte", "espansione iniziale"),
                         "la volontà che guarda oltre il muro"),
    (Seme.BASTONI, 3):  (("impresa avviata", "attesa dei frutti", "visione a lungo termine", "spedizione"),
                         "ciò che è stato lanciato e non si può più riprendere"),
    (Seme.BASTONI, 4):  (("celebrazione", "radici conquistate", "comunità", "stabilità gioiosa"),
                         "il campo dopo la vittoria — riposo meritato"),
    (Seme.BASTONI, 5):  (("conflitto aperto", "competizione creativa", "caos fertile", "lotta di idee"),
                         "il disordine che precede una nuova forma"),
    (Seme.BASTONI, 6):  (("vittoria riconosciuta", "ritorno trionfante", "leadership meritata", "stima pubblica"),
                         "il momento in cui il mondo vede quello che hai fatto"),
    (Seme.BASTONI, 7):  (("difesa della posizione", "pressione esterna", "resistenza solitaria", "perseveranza"),
                         "tenere il terreno quando tutto spinge a cedere"),
    (Seme.BASTONI, 8):  (("velocità", "impulso improvviso", "notizie in arrivo", "movimento rapido"),
                         "l'azione che non aspetta il permesso"),
    (Seme.BASTONI, 9):  (("resilienza", "stanchezza con guardia alta", "cicatrici come saggezza", "vigilia"),
                         "il guerriero che non si fida ancora della pace"),
    (Seme.BASTONI, 10): (("peso del successo", "responsabilità eccessive", "oppressione autoimposta", "completamento faticoso"),
                         "portare ciò che si è costruito fino in fondo"),
    (Seme.BASTONI, 11): (("messaggero entusiasta", "nuovo progetto", "curiosità creativa", "apprendimento ardente"),
                         "la scintilla in un corpo giovane"),
    (Seme.BASTONI, 12): (("azione impetuosa", "avventura", "passione in corsa", "cambiamento rapido"),
                         "il fuoco che non aspetta"),
    (Seme.BASTONI, 13): (("visione matura", "leadership creativa", "ispirazione condivisa", "autorità del fuoco"),
                         "chi trasforma la propria passione in direzione per altri"),

    # ── COPPE (acqua) ─────────────────────────────────────────────────────────
    (Seme.COPPE, 1):  (("amore nascente", "cuore aperto", "dono emotivo", "sorgente del sentimento"),
                       "il cuore prima che sappia di amare"),
    (Seme.COPPE, 2):  (("unione reciproca", "connessione profonda", "scambio d'anima", "attrazione"),
                       "due acque che si riconoscono"),
    (Seme.COPPE, 3):  (("gioia condivisa", "amicizia fertile", "celebrazione emotiva", "abbondanza del cuore"),
                       "la felicità che si moltiplica nell'essere vista"),
    (Seme.COPPE, 4):  (("noia emotiva", "opportunità inosservata", "ritiro interiore", "contemplazione"),
                       "l'emozione che si stanca di sé stessa"),
    (Seme.COPPE, 5):  (("perdita e rimpianto", "lutto elaborato", "ciò che rimane", "il bicchiere pieno accanto al vuoto"),
                       "saper contare ciò che è ancora in piedi"),
    (Seme.COPPE, 6):  (("nostalgia", "innocenza del passato", "ricordi come dono", "radici emotive"),
                       "tornare a qualcosa che non esiste più ma che nutre ancora"),
    (Seme.COPPE, 7):  (("illusioni multiple", "sogni da discernere", "scelta nel vago", "tentazione della fantasia"),
                       "il pericolo di innamorarsi dell'idea invece che della realtà"),
    (Seme.COPPE, 8):  (("abbandono del noto", "ricerca di significato", "allontanamento consapevole", "partenza interiore"),
                       "lasciare ciò che non è più abbastanza"),
    (Seme.COPPE, 9):  (("desiderio realizzato", "soddisfazione profonda", "benessere guadagnato", "abbondanza emotiva"),
                       "il momento in cui si ha quello che si voleva"),
    (Seme.COPPE, 10): (("armonia familiare", "felicità condivisa", "completamento emotivo", "radici e cielo insieme"),
                       "il cerchio emotivo che si chiude"),
    (Seme.COPPE, 11): (("sensibilità aperta", "messaggio del cuore", "intuizione nascente", "creatività romantica"),
                       "la giovinezza del sentimento"),
    (Seme.COPPE, 12): (("romanticismo in movimento", "proposta d'amore", "charme", "offerta emotiva"),
                       "portare sentimento in dono"),
    (Seme.COPPE, 13): (("maturità emotiva", "saggezza del cuore", "contenimento senza repressione", "equilibrio affettivo"),
                       "chi tiene il mare senza esserne travolto"),

    # ── SPADE (aria) ──────────────────────────────────────────────────────────
    (Seme.SPADE, 1):  (("verità tagliente", "chiarezza assoluta", "decisione netta", "forza della mente"),
                       "il pensiero prima che diventi parola"),
    (Seme.SPADE, 2):  (("stallo decisionale", "tregua momentanea", "equilibrio precario", "scelta evitata"),
                       "il momento in cui sappiamo ma non diciamo"),
    (Seme.SPADE, 3):  (("dolore onesto", "ferita del cuore", "separazione", "tradimento riconosciuto"),
                       "la verità che fa male perché è vera"),
    (Seme.SPADE, 4):  (("riposo necessario", "guarigione silenziosa", "ritiro strategico", "pausa prima dell'azione"),
                       "il guerriero che dorme per tornare più forte"),
    (Seme.SPADE, 5):  (("vittoria a caro prezzo", "conflitto inutile", "umiliazione o resa", "ciò che si perde vincendo"),
                       "quando la vittoria non vale quello che è costata"),
    (Seme.SPADE, 6):  (("transizione verso la calma", "viaggio mentale", "allontanamento dal conflitto", "passaggio"),
                       "lasciare le acque agitate per acque più calme"),
    (Seme.SPADE, 7):  (("astuzia", "strategia solitaria", "azione non dichiarata", "furbizia o inganno"),
                       "muoversi dove gli altri non guardano"),
    (Seme.SPADE, 8):  (("prigionia mentale", "limitazione percepita", "confusione che blocca", "paralisi per paura"),
                       "la gabbia che si può aprire ma non si apre"),
    (Seme.SPADE, 9):  (("ansia notturna", "pensieri che non tacciono", "crisi interiore", "timore del peggio"),
                       "la mente che si tormenta da sola nel buio"),
    (Seme.SPADE, 10): (("fine definitiva", "crollo totale", "trasformazione radicale", "il fondo come punto di svolta"),
                       "quando non si può andare più in basso — e quindi si risale"),
    (Seme.SPADE, 11): (("mente acuta", "osservazione vigile", "apprendimento critico", "curiosità intellettuale"),
                       "chi vede quello che gli altri non notano"),
    (Seme.SPADE, 12): (("azione rapida", "comunicazione diretta", "assertività", "taglio netto"),
                       "il pensiero che diventa atto senza esitazione"),
    (Seme.SPADE, 13): (("intelletto sovrano", "giudizio equilibrato", "autorità della mente", "chiarezza di comando"),
                       "chi governa con la ragione senza perdere l'umanità"),

    # ── DENARI (terra) ────────────────────────────────────────────────────────
    (Seme.DENARI, 1):  (("seme materiale", "opportunità concreta", "primo investimento", "dono della terra"),
                        "il potenziale che si può toccare con mano"),
    (Seme.DENARI, 2):  (("equilibrio in movimento", "adattamento al flusso", "gestione di più cose", "danza delle priorità"),
                        "tenere in aria due pesi senza farne cadere nessuno"),
    (Seme.DENARI, 3):  (("competenza riconosciuta", "lavoro collaborativo", "artigianato", "costruzione condivisa"),
                        "quando il talento incontra il progetto e la squadra"),
    (Seme.DENARI, 4):  (("possesso difensivo", "stabilità controllata", "attaccamento al guadagno", "avarizia o prudenza"),
                        "la paura di perdere ciò che si ha"),
    (Seme.DENARI, 5):  (("perdita materiale", "povertà", "esclusione", "crisi che insegna il valore"),
                        "stare fuori dal calore sapendo che esiste"),
    (Seme.DENARI, 6):  (("generosità o controllo", "dono con potere", "squilibrio redistribuito", "carità e dipendenza"),
                        "chi dà decide anche chi riceve"),
    (Seme.DENARI, 7):  (("attesa del raccolto", "pazienza con incertezza", "investimento a lungo termine", "semi che crescono"),
                        "il contadino che guarda la terra senza poter accelerarla"),
    (Seme.DENARI, 8):  (("dedizione al mestiere", "apprendistato serio", "eccellenza artigianale", "pratica ripetuta"),
                        "fare bene una cosa mille volte finché diventa arte"),
    (Seme.DENARI, 9):  (("abbondanza autonoma", "lusso guadagnato", "indipendenza materiale", "frutto del proprio lavoro"),
                        "godere di ciò che si è costruito da soli"),
    (Seme.DENARI, 10): (("eredità e continuità", "prosperità familiare", "ricchezza che dura", "radici materiali solide"),
                        "il patrimonio che sopravvive a chi lo ha creato"),
    (Seme.DENARI, 11): (("studio pratico", "opportunità in arrivo", "apprendimento concreto", "giovane dedicato"),
                        "il seme di una competenza futura"),
    (Seme.DENARI, 12): (("affidabilità metodica", "costruzione lenta e solida", "determinazione tranquilla", "fedeltà al compito"),
                        "chi non corre mai ma arriva sempre"),
    (Seme.DENARI, 13): (("successo materiale maturo", "abbondanza costruita", "imprenditore realizzato", "autorità della terra"),
                        "chi ha trasformato il lavoro in eredità"),
}

_ARCANI_MINORI: list[Carta] = []
for _i_seme, _seme in enumerate(Seme):
    for _rango in range(1, 14):
        _nome = f"{_NOMI_RANGO[_rango]} di {_seme.value.capitalize()}"
        _indice = 22 + _i_seme * 13 + (_rango - 1)
        _kw, _dom = _KW_CARTA[(_seme, _rango)]
        _ARCANI_MINORI.append(Carta(
            nome=_nome,
            indice=_indice,
            arcano=TipoArcano.MINORE,
            seme=_seme,
            rango=_rango,
            parole_chiave=_kw,
            elemento=_SEME_ELEMENTO[_seme],
            dominio=_dom,
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


def voce(carta: Carta) -> str:
    """La voce della carta nelle letture — solo parole, mai coordinate.

    Arcani Maggiori: nome proprio (Il Matto, La Torre, Le Stelle).
    Arcani Minori: la prima parola chiave — l'essenza senza etichetta.

    Questo è il confine tra il livello-motore (seme/numero) e il livello-lettura.
    Il motore conosce 'Cinque di Spade'. La lettura dice 'vittoria a caro prezzo'.
    """
    if carta.arcano == TipoArcano.MAGGIORE:
        return carta.nome
    return carta.parole_chiave[0] if carta.parole_chiave else carta.dominio


def eco(carta: Carta) -> str:
    """L'eco estesa della carta — dominio completo, per letture personali profonde."""
    if carta.arcano == TipoArcano.MAGGIORE:
        return f"{carta.nome} — {carta.dominio}"
    return carta.dominio
