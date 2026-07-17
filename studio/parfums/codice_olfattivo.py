# -*- coding: utf-8 -*-
"""
PARFUMS 400 — Il Codice Olfattivo
=================================

Terzo sistema simbolico del progetto, fratello dei Tarocchi Quantici R³∞
(Sistema A, 78 carte) e del Canone Alpha (Sistema B, 74 carte).

Dalla v0.2.0 il sistema è fondato sull'ORGANO TERZI 300: le 300 materie
prime reali dell'organo di Claudio (`organo_terzi_300.json`, convertito
da `Organo_Terzi_300.xlsx` con `converti_organo.py`). Ogni profumo:

  - pesca le 9 note della piramide (testa/cuore/fondo) dalle materie
    reali, rispettando i livelli T/C/F dell'organo;
  - monta un MOTORE DELLA SCIA dal Grimorio Terzi: una molecola di
    diffusione + un fissativo radiante + un fissativo profondo;
  - dichiara un'OVERDOSE consigliata ("i leggendari nascono da
    un'overdose bilanciata" — regola d'oro del Grimorio);
  - dichiara la FATTIBILITÀ: con quale ondata d'acquisto (CORE → ESP
    → MASTER) è componibile al banco.

Formula di presenza (eco della formula di collasso del Canone Alpha):

    Famiglia + Piramide + Momento = Presenza

Il catalogo è GENERATIVO ma DETERMINISTICO: stesso seed, stesso canone.
Il generatore non ha dipendenze esterne (openpyxl serve solo alla
conversione dell'Excel, già fatta).

Uso:
    python3 studio/parfums/codice_olfattivo.py
    → scrive studio/parfums/parfums_400.json e public/parfums.html
"""

import json
import random
from pathlib import Path

VERSIONE = "0.3.0"
SEED = 400
DATA_CANONE = "2026-07-16"

BASE = Path(__file__).resolve().parent
ORGANO_JSON = BASE / "organo_terzi_300.json"

RANGO_LIVELLO = {"CORE": 0, "ESP": 1, "MASTER": 2}
LIVELLI = ["CORE", "ESP", "MASTER"]

# ---------------------------------------------------------------------------
# Le 8 famiglie del Sistema C e la loro mappa sulle famiglie dell'Organo
# ---------------------------------------------------------------------------

FAMIGLIE = {
    "Agrumata": {
        "descrizione": "La luce. Scorze, sole, inizio: il profumo del mattino che non è ancora stato deluso.",
        "organo": ["Agrumi", "Aldeidi", "Aromatiche/Verdi"],
        "nomi": ["Riviera", "Capri", "Séville", "Menton", "Sorrente", "Palerme",
                 "Lisbonne", "Sicile", "Midi", "Soleil", "Verger", "l'Été"],
        "anime": [
            "luce che taglia il mattino",
            "una risata in un giardino d'estate",
            "la prima finestra aperta dell'anno",
            "acqua fredda sui polsi a mezzogiorno",
            "una promessa fatta in piena luce",
            "il coraggio semplice di cominciare",
        ],
        "stagioni": ["primavera", "estate", "estate", "primavera"],
        "momenti": ["alba", "giorno", "giorno", "giorno"],
    },
    "Floreale": {
        "descrizione": "Il cuore. Petali, incontro, apertura: ciò che si mostra quando decide di fidarsi.",
        "organo": ["Fiorali vari", "Rosa", "Fiori bianchi"],
        "nomi": ["Grasse", "Mai", "Roseraie", "Ophélie", "Flore", "Printemps",
                 "Pétale", "Damas", "Florence", "Aurore", "Camille", "Jardin"],
        "anime": [
            "una lettera scritta a mano e mai spedita",
            "il momento esatto in cui un fiore si apre",
            "tenerezza che non chiede permesso",
            "un abbraccio che dura un secondo più del previsto",
            "la memoria di un mese di maggio",
            "bellezza che non ha bisogno di spiegarsi",
        ],
        "stagioni": ["primavera", "primavera", "estate", "autunno"],
        "momenti": ["giorno", "giorno", "sera", "alba"],
    },
    "Verde": {
        "descrizione": "La linfa. Foglie, gambi, clorofilla: la vita colta nell'attimo in cui cresce.",
        "organo": ["Aromatiche/Verdi", "Chypre/Terrosi"],
        "nomi": ["Figuier", "Forêt", "Prairie", "Bambou", "Lierre", "Mousse",
                 "Toscane", "Avril", "Rosée", "Feuillage", "Ombrelle", "Sentier"],
        "anime": [
            "erba appena tagliata dietro una casa d'infanzia",
            "il silenzio verde di un sottobosco",
            "una passeggiata senza destinazione",
            "linfa che sale senza chiedere il permesso",
            "l'odore delle mani dopo il giardino",
            "un pensiero pulito, appena nato",
        ],
        "stagioni": ["primavera", "primavera", "estate", "autunno"],
        "momenti": ["alba", "giorno", "giorno", "giorno"],
    },
    "Acquatica": {
        "descrizione": "Il largo. Sale, ozono, orizzonte: la distanza che respira dentro il petto.",
        "organo": ["Marini/Ozonici", "Aldeidi", "Muschi"],
        "nomi": ["Océan", "Marée", "Bretagne", "Écume", "Lagune", "Azur",
                 "Cyclades", "Atlantique", "Brume", "Récif", "Sirène", "Horizon"],
        "anime": [
            "vento che arriva da dove non si vede terra",
            "il primo respiro davanti al mare",
            "sale rimasto sulla pelle a sera",
            "una partenza che non fa paura",
            "l'orizzonte come domanda aperta",
            "acqua che non ricorda ma accoglie",
        ],
        "stagioni": ["estate", "estate", "primavera", "estate"],
        "momenti": ["giorno", "giorno", "alba", "sera"],
    },
    "Legnosa": {
        "descrizione": "Il tronco. Radici, corteccia, durata: ciò che resta in piedi quando tutto il resto passa.",
        "organo": ["Legni", "Muschi", "Chypre/Terrosi"],
        "nomi": ["Cèdre", "Atlas", "Santal", "Kyoto", "Ébène", "Racine",
                 "Hiver", "Cabane", "Nord", "Séquoia", "Bois", "Refuge"],
        "anime": [
            "una casa di legno che ha visto tre generazioni",
            "la calma di chi non deve dimostrare niente",
            "radici che lavorano al buio",
            "il fuoco basso di fine serata",
            "una parola data e mantenuta",
            "silenzio che sa di corteccia",
        ],
        "stagioni": ["autunno", "inverno", "autunno", "inverno"],
        "momenti": ["sera", "sera", "notte", "giorno"],
    },
    "Orientale": {
        "descrizione": "La brace. Ambra, resine, notte: il calore che rimane acceso sotto la cenere.",
        "organo": ["Ambrati/Resine", "Animalic/Cuoio", "Speziati"],
        "nomi": ["Byzance", "Tanger", "Samarcande", "Ambre", "Ispahan", "Shéhérazade",
                 "Désert", "Caravane", "Orient", "Bazar", "Mille Nuits", "Sahara"],
        "anime": [
            "una storia raccontata a voce bassa",
            "oro vecchio che non ha bisogno di brillare",
            "il calore che resta dopo che il fuoco è spento",
            "una carovana che viaggia di notte",
            "segreti custoditi con eleganza",
            "la notte come stanza, non come assenza",
        ],
        "stagioni": ["inverno", "autunno", "inverno", "inverno"],
        "momenti": ["notte", "sera", "notte", "sera"],
    },
    "Speziata": {
        "descrizione": "Il fuoco. Pepe, cannella, rotte: l'energia che muove le navi e le decisioni.",
        "organo": ["Speziati", "Animalic/Cuoio", "Aromatiche/Verdi"],
        "nomi": ["Épices", "Zanzibar", "Ceylan", "Safran", "Comptoir", "Madras",
                 "Marrakech", "Cannelle", "Goa", "Route", "Feu", "Escale"],
        "anime": [
            "un mercato al tramonto, tutto insieme",
            "la decisione presa senza voltarsi",
            "calore che pizzica e poi consola",
            "una rotta tracciata a mano su una mappa",
            "il coraggio che sa di pepe",
            "una cucina dove succede qualcosa di importante",
        ],
        "stagioni": ["autunno", "autunno", "inverno", "estate"],
        "momenti": ["sera", "giorno", "sera", "notte"],
    },
    "Gourmand": {
        "descrizione": "La cucina. Vaniglia, cacao, miele: la memoria che si mangia, il conforto che si indossa.",
        "organo": ["Gourmand/Vaniglia", "Fruttati"],
        "nomi": ["Vanille", "Praline", "Havane", "Cacao", "Miel", "Automne",
                 "Dimanche", "Caramel", "Noisette", "Minuit", "Gourmandise", "Douceur"],
        "anime": [
            "una cucina d'inverno con il forno acceso",
            "la domenica pomeriggio di quando eri piccolo",
            "dolcezza che non chiede scusa",
            "un dolce condiviso in due, senza parlare",
            "il conforto come forma d'arte",
            "zucchero e malinconia in parti uguali",
        ],
        "stagioni": ["inverno", "autunno", "inverno", "autunno"],
        "momenti": ["sera", "notte", "sera", "giorno"],
    },
}

TEMPLATE_NOMI = [
    "Eau de {}", "Nuit de {}", "L'Ombre de {}", "Jardin de {}",
    "Souvenir de {}", "Clair de {}", "{} Absolu", "{} Sauvage",
    "{} Noir", "Lettre de {}", "Retour à {}", "Minuit à {}",
    "Un Matin à {}", "{} Éternel", "Le Silence de {}", "Aube de {}",
]

RACCONTI = [
    "Apre come {testa}, si scioglie in {cuore} e riposa su {fondo}.",
    "Parte da {testa}, attraversa {cuore}, finisce dove comincia {fondo}.",
    "{testa} in superficie, {cuore} al centro, {fondo} come verità ultima.",
    "Prima {testa}, poi {cuore}; alla fine resta solo {fondo}.",
    "Un lampo di {testa}, un cuore di {cuore}, una radice di {fondo}.",
]

CONCENTRAZIONI = ["Eau Fraîche", "Eau de Toilette", "Eau de Toilette",
                  "Eau de Parfum", "Eau de Parfum", "Extrait de Parfum"]
SILLAGE = ["intimo", "moderato", "moderato", "avvolgente", "imponente"]

RUOLI_SCIA = ["DIFFUSIONE", "FISSATIVO RADIANTE", "FISSATIVO PROFONDO"]

# Estetica per famiglia: palette del liquido, forma del flacone, packaging,
# e il "chi" del concept. Le forme sono 4 sagome SVG disegnate dal catalogo.
ESTETICHE = {
    "Agrumata": {"liquido": "#d9b23c", "chiaro": "#f2e2a0", "forma": "slanciata",
                 "vetro": "vetro chiaro", "tappo": "legno d'ulivo chiaro",
                 "astuccio": "cartoncino avorio, interno giallo sole",
                 "chi": "comincia le cose senza chiedere il permesso"},
    "Floreale": {"liquido": "#c98a9e", "chiaro": "#ecd3da", "forma": "tonda",
                 "vetro": "vetro chiaro satinato", "tappo": "sfera di vetro smerigliato",
                 "astuccio": "cartoncino cipria, interno petalo",
                 "chi": "si fida ancora, e lo sa"},
    "Verde": {"liquido": "#7c9a5f", "chiaro": "#cfe0bd", "forma": "slanciata",
              "vetro": "vetro chiaro", "tappo": "legno grezzo",
              "astuccio": "carta kraft, interno felce",
              "chi": "cammina senza destinazione e arriva sempre"},
    "Acquatica": {"liquido": "#5f8fa3", "chiaro": "#cfe3ec", "forma": "tonda",
                  "vetro": "vetro azzurrato", "tappo": "alluminio spazzolato",
                  "astuccio": "cartoncino grigio nebbia, interno orizzonte",
                  "chi": "guarda il largo senza paura di partire"},
    "Legnosa": {"liquido": "#8a5a33", "chiaro": "#d8c3a8", "forma": "quadrata",
                "vetro": "vetro fumé", "tappo": "legno di cedro massiccio",
                "astuccio": "cartoncino tabacco, interno corteccia",
                "chi": "mantiene la parola data"},
    "Orientale": {"liquido": "#9c4a1f", "chiaro": "#e0b46a", "forma": "anfora",
                  "vetro": "vetro ambrato", "tappo": "ottone brunito",
                  "astuccio": "cartoncino notte, interno oro vecchio",
                  "chi": "racconta a voce bassa e tutti si avvicinano"},
    "Speziata": {"liquido": "#a3502a", "chiaro": "#dfb08a", "forma": "quadrata",
                 "vetro": "vetro ambrato", "tappo": "bakelite nera",
                 "astuccio": "cartoncino terracotta, interno pepe",
                 "chi": "decide senza voltarsi indietro"},
    "Gourmand": {"liquido": "#7d5230", "chiaro": "#e3c9a3", "forma": "anfora",
                 "vetro": "vetro fumé caldo", "tappo": "ceramica crema",
                 "astuccio": "cartoncino cacao, interno crema",
                 "chi": "sa che il conforto è una forma d'arte"},
}

MOMENTO_FRASE = {"alba": "le albe", "giorno": "il pieno giorno",
                 "sera": "le sere", "notte": "la notte"}
STAGIONE_FRASE = {"primavera": "di primavera", "estate": "d'estate",
                  "autunno": "d'autunno", "inverno": "d'inverno"}

# Fattori di dosaggio: più una materia è potente, meno parti riceve.
FATTORE_FORZA = {1: 1.4, 2: 1.15, 3: 1.0, 4: 0.45, 5: 0.1}
PARTI_LIVELLO = {"testa": 20.0, "cuore": 30.0, "fondo": 35.0}
PARTI_SCIA = {"diffusione": 8.0, "fissativo radiante": 4.0,
              "fissativo profondo": 3.0}

# Strategia a 3 ondate del Grimorio: in ogni famiglia i primi 10 profumi
# pescano solo dal CORE, i successivi 15 da CORE+ESP, gli ultimi 25
# dall'organo completo. Se un pool si esaurisce, si allarga all'ondata
# successiva (la fattibilità dichiarata resta quella reale).
ONDATE = [{"CORE"}, {"CORE", "ESP"}, {"CORE", "ESP", "MASTER"}]


def _ondata_del(indice):
    return 0 if indice < 10 else (1 if indice < 25 else 2)


# ---------------------------------------------------------------------------
# Organo: caricamento e pool
# ---------------------------------------------------------------------------

def carica_organo():
    doc = json.loads(ORGANO_JSON.read_text(encoding="utf-8"))
    assert doc["totale_materie"] == 300
    return doc


def _livelli_nota(materia):
    """'T-C' → {'T','C'}; solventi e materie senza nota → set vuoto."""
    nota = materia.get("nota") or "-"
    if nota == "-" or materia.get("tipo") == "SOL":
        return set()
    return set(nota.split("-"))


def _costruisci_pool(materie):
    """Pool globali per livello di piramide, pool firma per famiglia
    del sistema, pool per ruolo di scia."""
    globali = {"T": [], "C": [], "F": []}
    for m in materie:
        for liv in _livelli_nota(m):
            globali[liv].append(m)

    firme = {}
    for nome_fam, fam in FAMIGLIE.items():
        organo_fam = set(fam["organo"])
        firme[nome_fam] = {
            liv: [m for m in pool if m["famiglia"] in organo_fam]
            for liv, pool in globali.items()
        }

    ruoli = {r: [m for m in materie if m.get("ruolo_scia") == r]
             for r in RUOLI_SCIA}
    return globali, firme, ruoli


def _nota(m):
    return {"n": m["n"], "nome": m["nome"], "forza": m["forza"],
            "livello": m["livello"]}


def _pesca(rng, pools, usate, ondata):
    """Estrae una materia provando i pool in ordine di preferenza dentro
    l'ondata richiesta; se tutti sono vuoti, allarga all'ondata dopo."""
    for i in range(ondata, len(ONDATE)):
        for pool in pools:
            candidati = [m for m in pool
                         if m["n"] not in usate and m["livello"] in ONDATE[i]]
            if candidati:
                m = rng.choice(candidati)
                usate.add(m["n"])
                return m
    raise ValueError("pool esaurito")


def _piramide(rng, firma, globali, ondata):
    """1 nota-firma di famiglia + 2 dal pool allargato, per livello.
    Le 9 materie sono tutte distinte."""
    usate = set()
    piramide = {}
    for liv_pir, liv_org in (("testa", "T"), ("cuore", "C"), ("fondo", "F")):
        fir, glob = firma[liv_org], globali[liv_org]
        scelte = [_pesca(rng, [fir, glob], usate, ondata)]
        for _ in range(2):
            scelte.append(_pesca(rng, [fir + glob], usate, ondata))
        piramide[liv_pir] = [_nota(m) for m in scelte]
    return piramide


def _motore(rng, organo_fam, ruoli, usate, ondata):
    """Un motore di scia dal Grimorio: diffusione + fissativo radiante
    + fissativo profondo, preferendo le famiglie del profumo."""
    motore = []
    for ruolo in RUOLI_SCIA:
        pref = [m for m in ruoli[ruolo] if m["famiglia"] in organo_fam]
        m = _pesca(rng, [pref, ruoli[ruolo]], usate, ondata)
        motore.append({**_nota(m), "ruolo": ruolo.lower()})
    return motore


def _ricetta(piramide, motore, overdose_n):
    """Ricetta mini pronta: parti su 100 di concentrato, derivate (non a caso)
    da livello di piramide, forza della materia, ruolo di scia e overdose.
    Punto di partenza didattico alla maniera degli Accordi Studio."""
    righe = []
    for liv, tot in PARTI_LIVELLO.items():
        note = piramide[liv]
        pesi = []
        for i, x in enumerate(note):
            w = (1.6 if i == 0 else 1.0) * FATTORE_FORZA[x["forza"]]
            if x["n"] == overdose_n:
                w *= 2.5
            pesi.append(w)
        somma = sum(pesi)
        for x, w in zip(note, pesi):
            righe.append({"n": x["n"], "nome": x["nome"], "livello": liv,
                          "forza": x["forza"], "parti": tot * w / somma})
    for m in motore:
        righe.append({"n": m["n"], "nome": m["nome"], "livello": "scia",
                      "forza": m["forza"], "parti": PARTI_SCIA[m["ruolo"]]})

    for r in righe:
        r["parti"] = max(0.5, round(r["parti"] * 2) / 2)
        r["micro"] = r["forza"] == 5
    scarto = round(100.0 - sum(r["parti"] for r in righe), 1)
    massimo = max(righe, key=lambda r: r["parti"])
    massimo["parti"] = round(massimo["parti"] + scarto, 1)
    return righe


def _packaging(nome_famiglia, numero, nome):
    e = ESTETICHE[nome_famiglia]
    return {
        "flacone": f"flacone {e['forma']}, {e['vetro']}, 30 ml",
        "tappo": e["tappo"],
        "etichetta": f"carta avorio, serif oro: “N° {numero} — {nome}” · Terzi Parfums",
        "astuccio": e["astuccio"],
        "palette": {"liquido": e["liquido"], "chiaro": e["chiaro"]},
        "forma": e["forma"],
    }


def _concept(p, nome_famiglia):
    e = ESTETICHE[nome_famiglia]
    anima = p["anima"][0].upper() + p["anima"][1:]
    return (f"{anima}. {p['racconto']} Pensato per {MOMENTO_FRASE[p['momento']]} "
            f"{STAGIONE_FRASE[p['stagione']]}, al polso di chi {e['chi']}. "
            f"La firma della casa: overdose di {p['overdose']['nome']}, "
            f"sillage {p['sillage']}.")


def genera_parfums(seed=SEED, organo=None):
    """Genera il canone completo: 400 profumi dall'Organo Terzi 300,
    deterministici sul seed."""
    organo = organo or carica_organo()
    globali, firme, ruoli = _costruisci_pool(organo["materie"])

    rng = random.Random(seed)
    parfums = []
    nomi_usati = set()
    numero = 0

    for nome_famiglia, fam in FAMIGLIE.items():
        organo_fam = set(fam["organo"])
        for indice in range(50):
            numero += 1
            ondata = _ondata_del(indice)

            while True:
                nome = rng.choice(TEMPLATE_NOMI).format(rng.choice(fam["nomi"]))
                if nome not in nomi_usati:
                    nomi_usati.add(nome)
                    break

            piramide = _piramide(rng, firme[nome_famiglia], globali, ondata)
            note_tutte = piramide["testa"] + piramide["cuore"] + piramide["fondo"]
            usate = {n["n"] for n in note_tutte}

            motore = _motore(rng, organo_fam, ruoli, usate, ondata)

            # regola d'oro del Grimorio: un'overdose bilanciata come firma
            candidate = [n for n in note_tutte if n["forza"] <= 4] or note_tutte
            overdose = rng.choice(candidate)

            fattibile = LIVELLI[max(RANGO_LIVELLO[n["livello"]]
                                    for n in note_tutte + motore)]

            racconto = rng.choice(RACCONTI).format(
                testa=piramide["testa"][0]["nome"],
                cuore=piramide["cuore"][0]["nome"],
                fondo=piramide["fondo"][0]["nome"],
            )

            p = {
                "numero": numero,
                "nome": nome,
                "famiglia": nome_famiglia,
                "piramide": piramide,
                "motore_scia": motore,
                "overdose": {"n": overdose["n"], "nome": overdose["nome"]},
                "fattibilita": fattibile,
                "anima": rng.choice(fam["anime"]),
                "racconto": racconto,
                "stagione": rng.choice(fam["stagioni"]),
                "momento": rng.choice(fam["momenti"]),
                "concentrazione": rng.choice(CONCENTRAZIONI),
                "sillage": rng.choice(SILLAGE),
            }
            p["ricetta"] = _ricetta(piramide, motore, overdose["n"])
            p["packaging"] = _packaging(nome_famiglia, numero, nome)
            p["concept"] = _concept(p, nome_famiglia)
            parfums.append(p)

    assert len(parfums) == 400
    assert len({p["nome"] for p in parfums}) == 400
    return parfums


def documento(parfums, organo=None):
    """Il documento totale, nello stile dei JSON canonici del progetto."""
    organo = organo or carica_organo()
    return {
        "sistema": "Parfums 400 — Il Codice Olfattivo",
        "versione": VERSIONE,
        "data": DATA_CANONE,
        "seed": SEED,
        "organo": {
            "nome": "Organo Terzi 300",
            "fonte": organo["fonte"],
            "autore": organo["autore"],
            "totale_materie": organo["totale_materie"],
            "nota": "Ogni nota di ogni profumo è una materia reale dell'organo "
                    "(riferimento: campo `n`). Ogni profumo è componibile al banco.",
        },
        "manifesto": {
            "principio": "Un profumo non descrive chi lo porta. Permette a chi lo porta di emergere.",
            "formula": "Famiglia + Piramide + Momento = Presenza",
            "regola_oro": organo["motore_scia"]["regola_oro"],
            "grimorio": "studio/parfums/GRIMORIO_TERZI.md — la fisica della scia, "
                        "l'arsenale, le architetture classiche, le lezioni dei maestri, "
                        "il percorso in 4 fasi.",
            "motto": "ALAKTA ANEN — la scia è memoria che cammina.",
            "ondate": "In ogni famiglia: N° 1-10 componibili col CORE, "
                      "N° 11-25 con CORE+ESP, N° 26-50 con l'organo completo "
                      "(salvo allargamenti di pool, dichiarati in `fattibilita`).",
            "ricette": "Le ricette sono punti di partenza DIDATTICI (parti su "
                       "100 di concentrato), derivati da piramide, forza e "
                       "motore di scia — non formule finite. Lavorare in "
                       "diluizione col metodo Carles; materie forza 5 solo in "
                       "diluizione all'1%. Verificare IFRA prima di vendere.",
            "fratelli": [
                "Sistema A — Tarocchi Quantici R³∞ (78 carte)",
                "Sistema B — Canone Alpha (74 carte, 8 cicli)",
                "Sistema C — Parfums 400 (400 profumi, 8 famiglie, Organo Terzi 300)",
            ],
            "nota": "Come il Canone Alpha collassa in Carta + Asse + Polarità, "
                    "un profumo collassa nel momento in cui incontra una pelle. "
                    "Il catalogo è deterministico; la presenza non lo è mai.",
        },
        "famiglie": {
            nome: {
                "descrizione": fam["descrizione"],
                "organo": fam["organo"],
                "intervallo": [i * 50 + 1, (i + 1) * 50],
            }
            for i, (nome, fam) in enumerate(FAMIGLIE.items())
        },
        "parfums": parfums,
        "stato_costruzione": {"completo": True, "totale": len(parfums)},
    }


# ---------------------------------------------------------------------------
# Catalogo HTML — stessa pelle del sito dei Tarocchi (nero, oro, serif)
# ---------------------------------------------------------------------------

def genera_html(doc):
    def note_compatte(note):
        return [{"n": x["n"], "nome": x["nome"], "forza": x["forza"]} for x in note]

    dati = json.dumps(
        [
            {
                "n": p["numero"], "nome": p["nome"], "fam": p["famiglia"],
                "t": note_compatte(p["piramide"]["testa"]),
                "c": note_compatte(p["piramide"]["cuore"]),
                "f": note_compatte(p["piramide"]["fondo"]),
                "scia": [x["nome"] for x in p["motore_scia"]],
                "ovr": p["overdose"]["nome"],
                "liv": p["fattibilita"],
                "anima": p["anima"], "racconto": p["racconto"],
                "stagione": p["stagione"], "momento": p["momento"],
                "conc": p["concentrazione"], "sillage": p["sillage"],
                "ric": [[r["nome"], r["n"], r["parti"], r["livello"],
                         1 if r["micro"] else 0] for r in p["ricetta"]],
                "pack": p["packaging"],
                "concept": p["concept"],
            }
            for p in doc["parfums"]
        ],
        ensure_ascii=False, separators=(",", ":"),
    )
    famiglie = json.dumps(
        {n: f["descrizione"] for n, f in doc["famiglie"].items()},
        ensure_ascii=False,
    )

    return """<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Parfums 400 — Il Codice Olfattivo</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0c0c0e; --surface: #141418; --border: #2a2a32;
      --gold: #c9a84c; --gold-dim: #8a6f2e;
      --text: #e8e4d8; --text-dim: #7a7468;
      --radius: 8px; --font: 'Georgia', 'Times New Roman', serif;
    }
    body { background: var(--bg); color: var(--text); font-family: var(--font);
           min-height: 100vh; padding: 2rem 1rem 4rem; }
    .container { max-width: 980px; margin: 0 auto; }
    header { text-align: center; margin-bottom: 2.5rem; }
    header h1 { font-size: clamp(1.6rem, 5vw, 2.4rem); font-weight: normal;
                letter-spacing: 0.1em; color: var(--gold); }
    header p { margin-top: 0.5rem; color: var(--text-dim); font-size: 0.9rem;
               letter-spacing: 0.05em; }
    header .formula { margin-top: 0.75rem; font-style: italic; color: var(--gold-dim); }

    .controls { display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center;
                margin-bottom: 0.6rem; }
    .chip { background: var(--surface); border: 1px solid var(--border);
            color: var(--text-dim); border-radius: 999px; padding: 0.35rem 0.9rem;
            font-family: var(--font); font-size: 0.8rem; cursor: pointer;
            letter-spacing: 0.05em; }
    .chip.active { border-color: var(--gold); color: var(--gold); }
    .controls.livelli .chip { font-size: 0.7rem; text-transform: uppercase;
                              letter-spacing: 0.12em; }
    .searchbar { display: flex; justify-content: center; margin: 0.6rem 0 0.75rem; }
    .searchbar input { background: var(--surface); border: 1px solid var(--border);
            color: var(--text); border-radius: var(--radius); padding: 0.5rem 1rem;
            width: min(420px, 100%); font-family: var(--font); font-size: 0.9rem; }
    .searchbar input:focus { outline: none; border-color: var(--gold-dim); }
    #famdesc { text-align: center; color: var(--text-dim); font-style: italic;
               font-size: 0.85rem; min-height: 1.2em; margin-bottom: 0.5rem; }
    #count { text-align: center; color: var(--gold-dim); font-size: 0.72rem;
             letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 1.5rem; }

    #grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
            gap: 0.9rem; }
    .card { background: var(--surface); border: 1px solid var(--border);
            border-radius: var(--radius); padding: 1.1rem 1.25rem; cursor: pointer; }
    .card:hover { border-color: var(--gold-dim); }
    .card .apri { margin-top: 0.6rem; font-size: 0.68rem; letter-spacing: 0.14em;
                  text-transform: uppercase; color: var(--gold-dim); }

    /* Scheda profumo (overlay) */
    #velo { position: fixed; inset: 0; background: rgba(6,6,8,0.85);
            display: none; align-items: flex-start; justify-content: center;
            overflow-y: auto; padding: 3rem 1rem; z-index: 50; }
    #velo.aperto { display: flex; }
    .scheda { background: var(--surface); border: 1px solid var(--gold-dim);
              border-radius: var(--radius); max-width: 760px; width: 100%;
              padding: 1.75rem 2rem 2rem; position: relative; }
    .scheda-chiudi { position: absolute; top: 0.8rem; right: 1rem; background: none;
              border: none; color: var(--text-dim); font-size: 1.4rem;
              cursor: pointer; font-family: var(--font); }
    .scheda-chiudi:hover { color: var(--gold); }
    .scheda-corpo { display: flex; gap: 1.75rem; flex-wrap: wrap; }
    .scheda-flacone { flex: 0 0 180px; display: flex; flex-direction: column;
              align-items: center; gap: 0.75rem; }
    .scheda-info { flex: 1 1 300px; min-width: 260px; }
    .scheda h2 { color: var(--gold); font-weight: normal; font-size: 1.4rem;
                 margin-bottom: 0.1rem; padding-right: 2rem; }
    .scheda .sotto { color: var(--text-dim); font-size: 0.8rem;
                     letter-spacing: 0.1em; text-transform: uppercase;
                     margin-bottom: 1rem; }
    .scheda h3 { color: var(--gold-dim); font-weight: normal; font-size: 0.72rem;
                 letter-spacing: 0.18em; text-transform: uppercase;
                 margin: 1.1rem 0 0.4rem; }
    .scheda .concept { font-style: italic; line-height: 1.65; font-size: 0.92rem; }
    table.ricetta { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    table.ricetta td { padding: 0.28rem 0.4rem; border-bottom: 1px solid var(--border); }
    table.ricetta td.parti { text-align: right; color: var(--gold);
                             white-space: nowrap; width: 4.5em; }
    table.ricetta td.lv { color: var(--text-dim); font-size: 0.68rem;
                          text-transform: uppercase; letter-spacing: 0.1em;
                          width: 5.5em; }
    .micro { color: var(--red); font-size: 0.75em; }
    .avvertenza { margin-top: 0.6rem; font-size: 0.75rem; color: var(--text-dim);
                  line-height: 1.55; }
    .packlist { list-style: none; font-size: 0.85rem; line-height: 1.7; }
    .packlist b { color: var(--gold-dim); font-weight: normal; font-size: 0.7rem;
                  letter-spacing: 0.12em; text-transform: uppercase;
                  display: inline-block; min-width: 5.5em; }
    .card-top { display: flex; justify-content: space-between; align-items: baseline;
                margin-bottom: 0.35rem; }
    .card-num { font-size: 0.68rem; letter-spacing: 0.14em; color: var(--gold-dim); }
    .card-fam { font-size: 0.68rem; letter-spacing: 0.1em; text-transform: uppercase;
                color: var(--text-dim); }
    .card-nome { color: var(--gold); font-size: 1.1rem; margin-bottom: 0.6rem; }
    .liv { display: flex; gap: 0.5rem; font-size: 0.8rem; margin-bottom: 0.25rem; }
    .liv b { color: var(--gold-dim); font-weight: normal; font-size: 0.66rem;
             letter-spacing: 0.14em; text-transform: uppercase; min-width: 3.6em;
             padding-top: 0.15em; }
    .liv span { color: var(--text); }
    .liv.scia span { color: var(--text-dim); }
    .card-anima { margin-top: 0.6rem; font-style: italic; color: var(--text-dim);
                  font-size: 0.85rem; }
    .card-meta { margin-top: 0.6rem; font-size: 0.7rem; letter-spacing: 0.08em;
                 color: var(--text-dim); text-transform: uppercase; }
    .badge { display: inline-block; border: 1px solid var(--gold-dim);
             color: var(--gold-dim); border-radius: 4px; padding: 0 0.35em;
             margin-left: 0.4em; }
    footer { text-align: center; margin-top: 3rem; color: var(--text-dim);
             font-size: 0.8rem; line-height: 1.6; }
    footer a { color: var(--gold-dim); }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Parfums 400</h1>
      <p>Terzi Parfums · Il Codice Olfattivo · 8 famiglie · 400 profumi dall'Organo Terzi 300 · canone __VERSIONE__</p>
      <p class="formula">Famiglia + Piramide + Momento = Presenza</p>
    </header>

    <div class="controls" id="chips"></div>
    <div class="controls livelli" id="livchips" title="Componibile con quale ondata d'acquisto dell'organo"></div>
    <div class="searchbar"><input id="search" type="search"
         placeholder="Cerca per nome, materia, anima…"></div>
    <div id="famdesc"></div>
    <div id="count"></div>
    <div id="grid"></div>

    <div id="velo" role="dialog" aria-modal="true">
      <div class="scheda" id="scheda"></div>
    </div>

    <footer>
      Ogni nota è una materia reale dell'Organo Terzi 300 (passa il mouse per il N°).<br>
      <a href="libro.html">Il Libro dei Parfums</a> — storia, sapere, organo e le 400 schede, stampabile.<br>
      Sistema C del progetto Claudio · fratello dei
      <a href="index.html">Tarocchi Quantici R³∞</a> e del Canone Alpha<br>
      <em>ALAKTA ANEN — la scia è memoria che cammina.</em>
    </footer>
  </div>

  <script>
    const PARFUMS = __DATI__;
    const FAMIGLIE = __FAMIGLIE__;
    const LIVELLI = { "CORE": 0, "ESP": 1, "MASTER": 2 };
    let fam = null, query = "", livMax = 2;

    const chips = document.getElementById("chips");
    const tutte = document.createElement("button");
    tutte.className = "chip active"; tutte.textContent = "Tutte";
    tutte.onclick = () => { fam = null; render(); };
    chips.appendChild(tutte);
    for (const f of Object.keys(FAMIGLIE)) {
      const b = document.createElement("button");
      b.className = "chip"; b.textContent = f;
      b.onclick = () => { fam = f; render(); };
      chips.appendChild(b);
    }

    const livchips = document.getElementById("livchips");
    for (const [testo, v] of [["Solo CORE", 0], ["CORE + ESP", 1], ["Organo completo", 2]]) {
      const b = document.createElement("button");
      b.className = "chip" + (v === 2 ? " active" : "");
      b.textContent = testo; b.dataset.v = v;
      b.onclick = () => { livMax = v; render(); };
      livchips.appendChild(b);
    }

    document.getElementById("search").addEventListener("input", e => {
      query = e.target.value.toLowerCase().trim(); render();
    });

    function noteHtml(note) {
      return note.map(x =>
        '<span title="Organo N° ' + x.n + ' · forza ' + x.forza + '/5">' +
        x.nome + '</span>').join(", ");
    }

    // ---- Scheda profumo -------------------------------------------------
    const FORME = {
      slanciata: { corpo: "M60,60 L60,52 Q60,48 64,46 L64,40 L96,40 L96,46 Q100,48 100,52 L100,60 L100,208 Q100,216 92,216 L68,216 Q60,216 60,208 Z",
                   tappo: "M66,14 L94,14 L94,40 L66,40 Z", liquidoY: 92 },
      tonda:     { corpo: "M80,52 Q140,58 140,140 Q140,212 80,212 Q20,212 20,140 Q20,58 80,52 Z",
                   tappo: "M68,16 L92,16 L92,52 L68,52 Z", liquidoY: 100 },
      quadrata:  { corpo: "M32,56 L128,56 L128,204 Q128,212 120,212 L40,212 Q32,212 32,204 Z",
                   tappo: "M62,18 L98,18 L98,56 L62,56 Z", liquidoY: 96 },
      anfora:    { corpo: "M80,50 Q124,64 118,130 Q114,180 104,196 Q98,212 80,212 Q62,212 56,196 Q46,180 42,130 Q36,64 80,50 Z",
                   tappo: "M70,14 Q80,8 90,14 L90,50 L70,50 Z", liquidoY: 104 },
    };

    function flaconeSvg(p) {
      const f = FORME[p.pack.forma] || FORME.slanciata;
      const c = p.pack.palette;
      const id = "g" + p.n;
      return '<svg viewBox="0 0 160 230" width="170" height="244" aria-label="Flacone">' +
        '<defs><linearGradient id="' + id + '" x1="0" y1="0" x2="0" y2="1">' +
        '<stop offset="0" stop-color="' + c.chiaro + '"/>' +
        '<stop offset="1" stop-color="' + c.liquido + '"/></linearGradient>' +
        '<clipPath id="c' + id + '"><path d="' + f.corpo + '"/></clipPath></defs>' +
        '<path d="' + f.corpo + '" fill="#1a1a20" stroke="#3a3a44" stroke-width="1.5"/>' +
        '<rect clip-path="url(#c' + id + ')" x="0" y="' + f.liquidoY +
        '" width="160" height="230" fill="url(#' + id + ')" opacity="0.9"/>' +
        '<path d="' + f.corpo + '" fill="none" stroke="#c9a84c" stroke-width="0.8" opacity="0.5"/>' +
        '<path d="' + f.tappo + '" fill="#2c2c34" stroke="#c9a84c" stroke-width="0.8"/>' +
        '<rect x="45" y="132" width="70" height="46" rx="2" fill="#efe8d8" opacity="0.96"/>' +
        '<text x="80" y="147" text-anchor="middle" font-family="Georgia" font-size="9" fill="#8a6f2e">N° ' + p.n + '</text>' +
        '<text x="80" y="160" text-anchor="middle" font-family="Georgia" font-size="7.5" fill="#2c2418">' + nomeCorto(p.nome, 18) + '</text>' +
        '<text x="80" y="171" text-anchor="middle" font-family="Georgia" font-size="5.5" letter-spacing="1" fill="#8a6f2e">TERZI PARFUMS</text>' +
        '</svg>';
    }

    function nomeCorto(s, max) {
      return s.length <= max ? s : s.slice(0, max - 1) + "…";
    }

    const LIV_LABEL = { testa: "Testa", cuore: "Cuore", fondo: "Fondo", scia: "Scia" };

    function apriScheda(p) {
      const righe = p.ric.map(r =>
        '<tr><td class="lv">' + LIV_LABEL[r[3]] + '</td>' +
        '<td title="Organo N° ' + r[1] + '">' + r[0] +
        (r[4] ? ' <span class="micro">⚠ forza 5 — diluizione 1%</span>' : '') +
        '</td><td class="parti">' + r[2].toFixed(1).replace('.', ',') + '</td></tr>'
      ).join('');

      document.getElementById("scheda").innerHTML =
        '<button class="scheda-chiudi" onclick="chiudiScheda()" aria-label="Chiudi">✕</button>' +
        '<h2>' + p.nome + '</h2>' +
        '<div class="sotto">N° ' + p.n + ' · ' + p.fam + ' · ' + p.conc +
        ' · <span class="badge">' + p.liv + '</span></div>' +
        '<div class="scheda-corpo">' +
          '<div class="scheda-flacone">' + flaconeSvg(p) +
            '<div style="font-size:0.72rem;color:var(--text-dim);text-align:center">' +
            p.stagione + ' · ' + p.momento + ' · sillage ' + p.sillage + '</div>' +
          '</div>' +
          '<div class="scheda-info">' +
            '<h3>Concept</h3><p class="concept">' + p.concept + '</p>' +
            '<h3>Ricetta mini pronta — parti su 100 di concentrato</h3>' +
            '<table class="ricetta">' + righe + '</table>' +
            '<p class="avvertenza">Come provarla: pesa le parti in gocce ' +
            '(100 gocce ≈ 2,5 ml di concentrato), poi 2,5 ml + 14 ml di alcol ' +
            '≈ Eau de Parfum al 15%. Macerare 2–4 settimane. Punto di partenza ' +
            'didattico (metodo Carles), non formula finita: le materie ⚠ vanno ' +
            'usate partendo dalla diluizione all\\'1%. Verificare IFRA prima di ' +
            'qualunque vendita.</p>' +
            '<h3>Packaging</h3>' +
            '<ul class="packlist">' +
              '<li><b>Flacone</b> ' + p.pack.flacone + '</li>' +
              '<li><b>Tappo</b> ' + p.pack.tappo + '</li>' +
              '<li><b>Etichetta</b> ' + p.pack.etichetta + '</li>' +
              '<li><b>Astuccio</b> ' + p.pack.astuccio + '</li>' +
            '</ul>' +
          '</div>' +
        '</div>';
      document.getElementById("velo").classList.add("aperto");
      document.body.style.overflow = "hidden";
    }

    function chiudiScheda() {
      document.getElementById("velo").classList.remove("aperto");
      document.body.style.overflow = "";
    }
    document.getElementById("velo").addEventListener("click", e => {
      if (e.target.id === "velo") chiudiScheda();
    });
    document.addEventListener("keydown", e => {
      if (e.key === "Escape") chiudiScheda();
    });

    function render() {
      for (const b of chips.children)
        b.classList.toggle("active", b.textContent === (fam || "Tutte"));
      for (const b of livchips.children)
        b.classList.toggle("active", Number(b.dataset.v) === livMax);
      document.getElementById("famdesc").textContent = fam ? FAMIGLIE[fam] : "";

      const vis = PARFUMS.filter(p => {
        if (fam && p.fam !== fam) return false;
        if (LIVELLI[p.liv] > livMax) return false;
        if (!query) return true;
        const note = p.t.concat(p.c, p.f).map(x => x.nome).join(" ");
        const testo = (p.nome + " " + p.anima + " " + p.racconto + " " + note +
                       " " + p.scia.join(" ") + " " + p.ovr).toLowerCase();
        return testo.includes(query);
      });

      document.getElementById("count").textContent =
        vis.length + " / " + PARFUMS.length + " profumi";

      const grid = document.getElementById("grid");
      grid.innerHTML = "";
      for (const p of vis) {
        const d = document.createElement("div");
        d.className = "card";
        d.innerHTML =
          '<div class="card-top"><span class="card-num">N° ' + p.n +
          '</span><span class="card-fam">' + p.fam +
          '<span class="badge">' + p.liv + '</span></span></div>' +
          '<div class="card-nome">' + p.nome + '</div>' +
          '<div class="liv"><b>Testa</b><span>' + noteHtml(p.t) + '</span></div>' +
          '<div class="liv"><b>Cuore</b><span>' + noteHtml(p.c) + '</span></div>' +
          '<div class="liv"><b>Fondo</b><span>' + noteHtml(p.f) + '</span></div>' +
          '<div class="liv scia"><b>Scia</b><span>' + p.scia.join(" · ") + '</span></div>' +
          '<div class="liv scia"><b>Firma</b><span>overdose di ' + p.ovr + '</span></div>' +
          '<div class="card-anima">' + p.anima + '</div>' +
          '<div class="card-meta">' + p.stagione + ' · ' + p.momento + ' · ' +
          p.conc + ' · sillage ' + p.sillage + '</div>' +
          '<div class="apri">Apri la scheda — ricetta · packaging · concept →</div>';
        d.addEventListener("click", () => apriScheda(p));
        grid.appendChild(d);
      }
    }
    render();
  </script>
</body>
</html>
""".replace("__DATI__", dati).replace("__FAMIGLIE__", famiglie).replace("__VERSIONE__", VERSIONE)


def main():
    repo = BASE.parent.parent

    organo = carica_organo()
    doc = documento(genera_parfums(organo=organo), organo=organo)

    json_path = BASE / "parfums_400.json"
    json_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")

    html_path = repo / "public" / "parfums.html"
    html_path.write_text(genera_html(doc), encoding="utf-8")

    print(f"✓ {json_path.relative_to(repo)} — {doc['stato_costruzione']['totale']} profumi")
    print(f"✓ {html_path.relative_to(repo)}")
    conta = {}
    for p in doc["parfums"]:
        conta[p["fattibilita"]] = conta.get(p["fattibilita"], 0) + 1
    print("  Fattibilità:", " · ".join(f"{k}: {v}" for k, v in sorted(conta.items())))
    for nome, f in doc["famiglie"].items():
        a, b = f["intervallo"]
        print(f"  {nome}: N° {a}–{b} ← {', '.join(f['organo'])}")


if __name__ == "__main__":
    main()
