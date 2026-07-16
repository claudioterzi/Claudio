# -*- coding: utf-8 -*-
"""
PARFUMS 400 — Il Codice Olfattivo
=================================

Terzo sistema simbolico del progetto, fratello dei Tarocchi Quantici R³∞
(Sistema A, 78 carte) e del Canone Alpha (Sistema B, 74 carte).

Qui il linguaggio non passa per gli occhi ma per il naso:
400 profumi in 8 famiglie olfattive da 50, ciascuno con una piramide
a tre livelli (testa, cuore, fondo), un'anima, una stagione, un momento.

Formula di presenza (eco della formula di collasso del Canone Alpha):

    Famiglia + Piramide + Momento = Presenza

Il catalogo è GENERATIVO ma DETERMINISTICO: stesso seed, stesso canone.
Zero dipendenze esterne, come tutto il resto del progetto.

Uso:
    python3 studio/parfums/codice_olfattivo.py
    → scrive studio/parfums/parfums_400.json e public/parfums.html
"""

import json
import random
from pathlib import Path

VERSIONE = "0.1.0"
SEED = 400
DATA_CANONE = "2026-07-16"

# ---------------------------------------------------------------------------
# Note comuni, condivise tra le famiglie (per livello della piramide)
# ---------------------------------------------------------------------------

TESTA_COMUNI = [
    "bergamotto", "limone di Sicilia", "mandarino", "pompelmo rosa",
    "petitgrain", "pepe rosa", "cardamomo", "zenzero", "lavanda",
    "menta", "foglia di violetta", "aldeidi", "bacche di ginepro",
    "neroli", "artemisia", "basilico",
]

CUORE_COMUNI = [
    "rosa damascena", "gelsomino sambac", "iris", "ylang-ylang",
    "fiore d'arancio", "geranio", "magnolia", "tuberosa", "peonia",
    "mughetto", "osmanto", "pesca", "fico", "albicocca",
    "garofano", "eliotropio", "mimosa", "tè verde",
]

FONDO_COMUNI = [
    "muschio bianco", "sandalo", "legno di cedro", "vetiver",
    "patchouli", "ambra grigia", "vaniglia bourbon", "fava tonka",
    "cuoio", "incenso", "benzoino", "labdano", "muschio di quercia",
    "cashmeran", "mirra",
]

# ---------------------------------------------------------------------------
# Le 8 famiglie olfattive — 50 profumi ciascuna, numerate a blocchi
# come i cicli del Canone Alpha
# ---------------------------------------------------------------------------

FAMIGLIE = {
    "Agrumata": {
        "descrizione": "La luce. Scorze, sole, inizio: il profumo del mattino che non è ancora stato deluso.",
        "testa": ["bergamotto di Calabria", "limone di Sicilia", "cedro di Diamante",
                  "mandarino verde", "pompelmo rosa", "yuzu", "lime", "arancia amara"],
        "cuore": ["neroli", "petitgrain", "fiore d'arancio", "tè verde", "verbena"],
        "fondo": ["muschio bianco", "legno di cedro", "vetiver", "ambretta"],
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
        "testa": ["foglia di violetta", "pera", "litchi", "mandorla verde", "aldeidi"],
        "cuore": ["rosa damascena", "gelsomino sambac", "tuberosa", "peonia",
                  "mughetto", "magnolia", "iris", "frangipani", "gardenia"],
        "fondo": ["muschio bianco", "sandalo", "eliotropio", "nota cipriata"],
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
        "testa": ["foglia di fico", "erba tagliata", "galbano", "basilico",
                  "foglia di pomodoro", "menta"],
        "cuore": ["tè verde", "salvia", "foglia di violetta", "geranio", "edera"],
        "fondo": ["vetiver", "muschio di quercia", "legni chiari", "papiro"],
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
        "testa": ["nota marina", "accordo di sale", "ozono", "bergamotto", "calone"],
        "cuore": ["fiore di loto", "ninfea", "alga", "rosmarino", "ciclamino"],
        "fondo": ["ambra grigia", "legno flottato", "muschio bianco", "accordo minerale"],
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
        "testa": ["pepe nero", "elemi", "cipresso", "cardamomo"],
        "cuore": ["cedro dell'Atlante", "iris", "palissandro", "ginepro"],
        "fondo": ["sandalo", "vetiver di Haiti", "patchouli", "legno di guaiaco",
                  "oud", "muschio di quercia"],
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
        "testa": ["zafferano", "pepe rosa", "bergamotto", "davana"],
        "cuore": ["rosa turca", "incenso", "labdano", "prugna", "ylang-ylang"],
        "fondo": ["ambra", "vaniglia bourbon", "oud", "mirra", "benzoino", "opoponax"],
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
        "testa": ["zenzero", "pepe nero", "cardamomo", "coriandolo", "foglia di cannella"],
        "cuore": ["garofano", "noce moscata", "cumino", "curcuma", "immortelle"],
        "fondo": ["cuoio", "tabacco", "fava tonka", "sandalo", "resine scure"],
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
        "testa": ["mandorla amara", "caffè", "bergamotto", "rum", "fico fresco"],
        "cuore": ["pralina", "cannella", "fior di latte", "castagna", "miele d'acacia"],
        "fondo": ["vaniglia", "caramello salato", "cacao", "fava tonka", "zucchero filato"],
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


def _piramide(rng, famiglia):
    """Costruisce la piramide testa/cuore/fondo: una nota-firma della
    famiglia per livello, più note comuni. Nessuna nota ripetuta."""
    usate = set()
    piramide = {}
    for livello, comuni in (("testa", TESTA_COMUNI),
                            ("cuore", CUORE_COMUNI),
                            ("fondo", FONDO_COMUNI)):
        firma = famiglia[livello]
        note = [rng.choice([n for n in firma if n not in usate])]
        usate.add(note[0])
        pool = list(dict.fromkeys(n for n in firma + comuni if n not in usate))
        for n in rng.sample(pool, 2):
            note.append(n)
            usate.add(n)
        piramide[livello] = note
    return piramide


def genera_parfums(seed=SEED):
    """Genera il canone completo: 400 profumi, deterministici sul seed."""
    rng = random.Random(seed)
    parfums = []
    nomi_usati = set()
    numero = 0

    for nome_famiglia, fam in FAMIGLIE.items():
        for _ in range(50):
            numero += 1

            while True:
                nome = rng.choice(TEMPLATE_NOMI).format(rng.choice(fam["nomi"]))
                if nome not in nomi_usati:
                    nomi_usati.add(nome)
                    break

            piramide = _piramide(rng, fam)
            racconto = rng.choice(RACCONTI).format(
                testa=piramide["testa"][0],
                cuore=piramide["cuore"][0],
                fondo=piramide["fondo"][0],
            )

            parfums.append({
                "numero": numero,
                "nome": nome,
                "famiglia": nome_famiglia,
                "piramide": piramide,
                "anima": rng.choice(fam["anime"]),
                "racconto": racconto,
                "stagione": rng.choice(fam["stagioni"]),
                "momento": rng.choice(fam["momenti"]),
                "concentrazione": rng.choice(CONCENTRAZIONI),
                "sillage": rng.choice(SILLAGE),
            })

    assert len(parfums) == 400
    assert len({p["nome"] for p in parfums}) == 400
    return parfums


def documento(parfums):
    """Il documento totale, nello stile dei JSON canonici del progetto."""
    return {
        "sistema": "Parfums 400 — Il Codice Olfattivo",
        "versione": VERSIONE,
        "data": DATA_CANONE,
        "seed": SEED,
        "manifesto": {
            "principio": "Un profumo non descrive chi lo porta. Permette a chi lo porta di emergere.",
            "formula": "Famiglia + Piramide + Momento = Presenza",
            "fratelli": [
                "Sistema A — Tarocchi Quantici R³∞ (78 carte)",
                "Sistema B — Canone Alpha (74 carte, 8 cicli)",
                "Sistema C — Parfums 400 (400 profumi, 8 famiglie)",
            ],
            "nota": "Come il Canone Alpha collassa in Carta + Asse + Polarità, "
                    "un profumo collassa nel momento in cui incontra una pelle. "
                    "Il catalogo è deterministico; la presenza non lo è mai.",
        },
        "famiglie": {
            nome: {
                "descrizione": fam["descrizione"],
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
    dati = json.dumps(
        [
            {
                "n": p["numero"], "nome": p["nome"], "fam": p["famiglia"],
                "t": p["piramide"]["testa"], "c": p["piramide"]["cuore"],
                "f": p["piramide"]["fondo"], "anima": p["anima"],
                "racconto": p["racconto"], "stagione": p["stagione"],
                "momento": p["momento"], "conc": p["concentrazione"],
                "sillage": p["sillage"],
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
                margin-bottom: 1rem; }
    .chip { background: var(--surface); border: 1px solid var(--border);
            color: var(--text-dim); border-radius: 999px; padding: 0.35rem 0.9rem;
            font-family: var(--font); font-size: 0.8rem; cursor: pointer;
            letter-spacing: 0.05em; }
    .chip.active { border-color: var(--gold); color: var(--gold); }
    .searchbar { display: flex; justify-content: center; margin-bottom: 0.75rem; }
    .searchbar input { background: var(--surface); border: 1px solid var(--border);
            color: var(--text); border-radius: var(--radius); padding: 0.5rem 1rem;
            width: min(420px, 100%); font-family: var(--font); font-size: 0.9rem; }
    .searchbar input:focus { outline: none; border-color: var(--gold-dim); }
    #famdesc { text-align: center; color: var(--text-dim); font-style: italic;
               font-size: 0.85rem; min-height: 1.2em; margin-bottom: 0.5rem; }
    #count { text-align: center; color: var(--gold-dim); font-size: 0.72rem;
             letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 1.5rem; }

    #grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 0.9rem; }
    .card { background: var(--surface); border: 1px solid var(--border);
            border-radius: var(--radius); padding: 1.1rem 1.25rem; }
    .card-top { display: flex; justify-content: space-between; align-items: baseline;
                margin-bottom: 0.35rem; }
    .card-num { font-size: 0.68rem; letter-spacing: 0.14em; color: var(--gold-dim); }
    .card-fam { font-size: 0.68rem; letter-spacing: 0.1em; text-transform: uppercase;
                color: var(--text-dim); }
    .card-nome { color: var(--gold); font-size: 1.1rem; margin-bottom: 0.6rem; }
    .liv { display: flex; gap: 0.5rem; font-size: 0.8rem; margin-bottom: 0.25rem; }
    .liv b { color: var(--gold-dim); font-weight: normal; font-size: 0.66rem;
             letter-spacing: 0.14em; text-transform: uppercase; min-width: 3.4em;
             padding-top: 0.15em; }
    .liv span { color: var(--text); }
    .card-anima { margin-top: 0.6rem; font-style: italic; color: var(--text-dim);
                  font-size: 0.85rem; }
    .card-meta { margin-top: 0.6rem; font-size: 0.7rem; letter-spacing: 0.08em;
                 color: var(--text-dim); text-transform: uppercase; }
    footer { text-align: center; margin-top: 3rem; color: var(--text-dim);
             font-size: 0.8rem; }
    footer a { color: var(--gold-dim); }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Parfums 400</h1>
      <p>Il Codice Olfattivo · 8 famiglie · 400 profumi · canone __VERSIONE__</p>
      <p class="formula">Famiglia + Piramide + Momento = Presenza</p>
    </header>

    <div class="controls" id="chips"></div>
    <div class="searchbar"><input id="search" type="search"
         placeholder="Cerca per nome, nota, anima…"></div>
    <div id="famdesc"></div>
    <div id="count"></div>
    <div id="grid"></div>

    <footer>
      Sistema C del progetto Claudio · fratello dei
      <a href="/">Tarocchi Quantici R³∞</a> e del Canone Alpha
    </footer>
  </div>

  <script>
    const PARFUMS = __DATI__;
    const FAMIGLIE = __FAMIGLIE__;
    let fam = null, query = "";

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

    document.getElementById("search").addEventListener("input", e => {
      query = e.target.value.toLowerCase().trim(); render();
    });

    function render() {
      for (const b of chips.children)
        b.classList.toggle("active", b.textContent === (fam || "Tutte"));
      document.getElementById("famdesc").textContent = fam ? FAMIGLIE[fam] : "";

      const vis = PARFUMS.filter(p => {
        if (fam && p.fam !== fam) return false;
        if (!query) return true;
        const testo = (p.nome + " " + p.anima + " " + p.racconto + " " +
                       p.t.join(" ") + " " + p.c.join(" ") + " " + p.f.join(" "))
                      .toLowerCase();
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
          '</span><span class="card-fam">' + p.fam + '</span></div>' +
          '<div class="card-nome">' + p.nome + '</div>' +
          '<div class="liv"><b>Testa</b><span>' + p.t.join(", ") + '</span></div>' +
          '<div class="liv"><b>Cuore</b><span>' + p.c.join(", ") + '</span></div>' +
          '<div class="liv"><b>Fondo</b><span>' + p.f.join(", ") + '</span></div>' +
          '<div class="card-anima">' + p.anima + '</div>' +
          '<div class="card-meta">' + p.stagione + ' · ' + p.momento + ' · ' +
          p.conc + ' · sillage ' + p.sillage + '</div>';
        grid.appendChild(d);
      }
    }
    render();
  </script>
</body>
</html>
""".replace("__DATI__", dati).replace("__FAMIGLIE__", famiglie).replace("__VERSIONE__", VERSIONE)


def main():
    base = Path(__file__).resolve().parent
    repo = base.parent.parent

    doc = documento(genera_parfums())

    json_path = base / "parfums_400.json"
    json_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")

    html_path = repo / "public" / "parfums.html"
    html_path.write_text(genera_html(doc), encoding="utf-8")

    print(f"✓ {json_path.relative_to(repo)} — {doc['stato_costruzione']['totale']} profumi")
    print(f"✓ {html_path.relative_to(repo)}")
    for nome, f in doc["famiglie"].items():
        a, b = f["intervallo"]
        print(f"  {nome}: N° {a}–{b}")


if __name__ == "__main__":
    main()
