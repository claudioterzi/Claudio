#!/usr/bin/env python3
"""
agente_profumiere.py — SDQ-1 · Terzi Parfums
Studio quotidiano automatico di profumeria:
- Clona fragranze celebri con il database di 158 essenze
- Genera 1 nuova formula originale al giorno per apprendimento
- Salva tutto in progetti/aura50/ricette/ e progetti/aura50/celebri/
"""

import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RICETTE_DIR = ROOT / "progetti" / "aura50" / "ricette"
CELEBRI_DIR = ROOT / "progetti" / "aura50" / "celebri"

# ─── DATABASE ESSENZE (158) ─────────────────────────────────────────────────
# (id, nome, layer, emo_list, tipo)
ESSENZE = [
    # A. Agrumi / Esperidati — testa (001–016)
    (1,  "Bergamotto Calabria", "testa", ["SLA","ARI"], "N"),
    (2,  "Limone Sicilia",      "testa", ["SLA","VIT"], "N"),
    (3,  "Mandarino rosso",     "testa", ["GIO","SLA"], "N"),
    (4,  "Mandarino verde",     "testa", ["VIT","SLA"], "N"),
    (5,  "Arancia dolce",       "testa", ["GIO"],       "N"),
    (6,  "Arancia amara",       "testa", ["ARI","SLA"], "N"),
    (7,  "Pompelmo",            "testa", ["SLA","VIT"], "S"),
    (8,  "Lime",                "testa", ["VIT","GIO"], "N"),
    (9,  "Cedro (citron)",      "testa", ["ARI"],       "N"),
    (10, "Petitgrain",          "testa", ["VIT","ARI"], "N"),
    (11, "Neroli",              "testa", ["SEN","ARI"], "N"),
    (12, "Yuzu",                "testa", ["SLA","GIO"], "S"),
    (13, "Clementina",          "testa", ["GIO","CON"], "N"),
    (14, "Kumquat",             "testa", ["GIO","VIT"], "S"),
    (15, "Aldeide C-10",        "testa", ["SLA","ARI"], "S"),
    (16, "Accordo Cologne",     "testa", ["ARI","SLA"], "S"),
    # B. Aromatiche / Erbe — testa-cuore (017–030)
    (17, "Lavanda",             "cuore", ["ARI","MEM"], "N"),
    (18, "Lavandina",           "testa", ["ARI","VIT"], "N"),
    (19, "Rosmarino",           "testa", ["VIT","SLA"], "N"),
    (20, "Salvia sclarea",      "cuore", ["SEN","TER"], "N"),
    (21, "Menta piperita",      "testa", ["VIT","SLA"], "N"),
    (22, "Basilico",            "testa", ["VIT","GIO"], "N"),
    (23, "Timo",                "testa", ["FOR","VIT"], "N"),
    (24, "Artemisia",           "testa", ["MIS","VIT"], "N"),
    (25, "Eucalipto",           "testa", ["VIT","ARI"], "N"),
    (26, "Anice/Anetolo",       "testa", ["GIO","CON"], "N"),
    (27, "Estragone",           "testa", ["VIT","GIO"], "N"),
    (28, "Geranio",             "cuore", ["VIT","SEN"], "N"),
    (29, "Menta verde",         "testa", ["GIO","VIT"], "N"),
    (30, "Fava tonka",          "fondo", ["CON","MEM"], "N"),
    # C. Spezie — cuore (031–046)
    (31, "Pepe nero",           "cuore", ["FOR","MIS"], "N"),
    (32, "Pepe rosa",           "cuore", ["GIO","SLA"], "N"),
    (33, "Cardamomo",           "cuore", ["ARI","MIS"], "N"),
    (34, "Zenzero",             "cuore", ["SLA","FOR"], "N"),
    (35, "Noce moscata",        "cuore", ["CON","FOR"], "N"),
    (36, "Chiodi di garofano",  "cuore", ["FOR","CON"], "N"),
    (37, "Cannella corteccia",  "cuore", ["CON","FOR"], "N"),
    (38, "Coriandolo",          "cuore", ["ARI","GIO"], "N"),
    (39, "Cumino",              "cuore", ["SEN","FOR"], "N"),
    (40, "Curcuma",             "cuore", ["TER","MIS"], "S"),
    (41, "Zafferano (safraleine)", "cuore", ["MIS","FOR"], "S"),
    (42, "Peperoncino accordo", "cuore", ["FOR"],       "S"),
    (43, "Bacche di ginepro",   "testa", ["VIT","ARI"], "N"),
    (44, "Pimento (allspice)",  "cuore", ["CON","FOR"], "N"),
    (45, "Cuoio-zafferano accordo", "cuore", ["MIS","FOR"], "S"),
    (46, "Cumino tostato accordo",  "cuore", ["SEN","FOR"], "S"),
    # D. Fiori bianchi — cuore (047–060)
    (47, "Gelsomino grandiflorum", "cuore", ["SEN"],       "N"),
    (48, "Gelsomino sambac",    "cuore", ["SEN","ARI"], "N"),
    (49, "Tuberosa",            "cuore", ["SEN","FOR"], "N"),
    (50, "Fiori d'arancio",     "cuore", ["SEN","CON"], "N"),
    (51, "Gardenia (accordo)",  "cuore", ["SEN","ARI"], "S"),
    (52, "Ylang-ylang",         "cuore", ["SEN","GIO"], "N"),
    (53, "Frangipane",          "cuore", ["GIO","SEN"], "S"),
    (54, "Magnolia",            "cuore", ["ARI","GIO"], "S"),
    (55, "Mughetto",            "cuore", ["ARI","VIT"], "S"),
    (56, "Caprifoglio",         "cuore", ["GIO","CON"], "S"),
    (57, "Fior di loto",        "cuore", ["ARI"],       "S"),
    (58, "Champaca",            "cuore", ["MIS","SEN"], "N"),
    (59, "Osmanthus",           "cuore", ["MEM","SEN"], "N"),
    (60, "Narciso",             "cuore", ["MEM","MIS"], "N"),
    # E. Fiori — cuore (061–082)
    (61, "Rosa damascena",      "cuore", ["SEN","MEM"], "N"),
    (62, "Rosa centifolia",     "cuore", ["ARI","MEM"], "N"),
    (63, "Rosa ossido (damascenone)", "cuore", ["SLA","SEN"], "S"),
    (64, "Geranio rosa",        "cuore", ["VIT","SEN"], "N"),
    (65, "Violetta foglia",     "cuore", ["VIT","MEM"], "N"),
    (66, "Violetta fiore (ionone)", "cuore", ["MEM","CON"], "S"),
    (67, "Iris/Orris",          "cuore", ["MEM","ARI"], "N"),
    (68, "Iris (irone)",        "cuore", ["MEM","ARI"], "S"),
    (69, "Peonia (accordo)",    "cuore", ["GIO","ARI"], "S"),
    (70, "Lillà",               "cuore", ["VIT","MEM"], "S"),
    (71, "Fiori di ciliegio",   "cuore", ["GIO","MEM"], "S"),
    (72, "Eliotropio",          "cuore", ["CON","MEM"], "S"),
    (73, "Mimosa",              "cuore", ["MEM","GIO"], "N"),
    (74, "Garofano fiore",      "cuore", ["FOR","MEM"], "N"),
    (75, "Lavanda assoluta",    "cuore", ["MEM","CON"], "N"),
    (76, "Camomilla blu",       "cuore", ["CON","VIT"], "N"),
    (77, "Loto rosa",           "cuore", ["ARI","GIO"], "S"),
    (78, "Fresia",              "cuore", ["ARI","GIO"], "S"),
    (79, "Ibisco accordo",      "cuore", ["GIO"],       "S"),
    (80, "Cera d'api (assoluta)", "cuore", ["SEN","MEM"], "N"),
    (81, "Immortelle",          "cuore", ["MEM","CON"], "N"),
    (82, "Verbena odorosa",     "testa", ["SLA","VIT"], "N"),
    # F. Frutta — testa-cuore (083–096)
    (83, "Pera",                "testa", ["GIO","ARI"], "S"),
    (84, "Mela verde",          "testa", ["VIT","GIO"], "S"),
    (85, "Pesca (lattone)",     "cuore", ["SEN","CON"], "S"),
    (86, "Albicocca (lattone)", "cuore", ["CON","SEN"], "S"),
    (87, "Litchi",              "testa", ["GIO","ARI"], "S"),
    (88, "Ribes nero (cassis)", "testa", ["VIT","SLA"], "S"),
    (89, "Fragola",             "cuore", ["GIO","CON"], "S"),
    (90, "Lampone",             "cuore", ["GIO"],       "S"),
    (91, "Fico (foglia+frutto)", "cuore", ["TER","CON"], "S"),
    (92, "Frutto della passione", "testa", ["GIO","SLA"], "S"),
    (93, "Prugna/susina",       "cuore", ["SEN","MIS"], "S"),
    (94, "Mela cotta",          "cuore", ["CON"],       "S"),
    (95, "Cocco (lattone)",     "cuore", ["CON","GIO"], "S"),
    (96, "Melone/anguria",      "testa", ["GIO","ARI"], "S"),
    # G. Verde — testa (097–104)
    (97,  "Galbano",            "testa", ["VIT","TER"], "N"),
    (98,  "Foglia di violetta", "testa", ["VIT","MEM"], "N"),
    (99,  "Erba tagliata",      "testa", ["VIT","SLA"], "S"),
    (100, "Tè verde",           "testa", ["ARI","VIT"], "S"),
    (101, "Edera/foglia accordo", "testa", ["VIT"],     "S"),
    (102, "Bambù",              "testa", ["ARI","VIT"], "S"),
    (103, "Pomodoro foglia",    "testa", ["TER","VIT"], "S"),
    (104, "Menta-eucalipto accordo", "testa", ["VIT","ARI"], "S"),
    # H. Marino / acquatico / ozonico (105–110)
    (105, "Calone (marino)",    "testa", ["ARI"],       "S"),
    (106, "Note ozoniche",      "testa", ["ARI","SLA"], "S"),
    (107, "Sale/accordo salino", "cuore", ["SEN","ARI"], "S"),
    (108, "Alga",               "cuore", ["TER","ARI"], "S"),
    (109, "Accordo acquoso",    "testa", ["ARI"],       "S"),
    (110, "Petrichor (pioggia)", "cuore", ["TER","MEM"], "S"),
    # I. Tè / aromatici particolari (111–116)
    (111, "Tè nero",            "cuore", ["MIS","FOR"], "S"),
    (112, "Mate",               "cuore", ["TER","VIT"], "N"),
    (113, "Caffè",              "cuore", ["FOR","CON"], "N"),
    (114, "Cacao/cioccolato",   "fondo", ["CON","SEN"], "N"),
    (115, "Rabarbaro",          "testa", ["VIT","GIO"], "S"),
    (116, "Accordo minerale/inchiostro", "cuore", ["MIS","ARI"], "S"),
    # J. Legni — fondo (117–130)
    (117, "Sandalo Mysore",     "fondo", ["CON","SEN"], "N"),
    (118, "Sandalo australiano", "fondo", ["CON","TER"], "N"),
    (119, "Sandalo sintetico (Javanol)", "fondo", ["CON","SEN"], "S"),
    (120, "Cedro Atlas",        "fondo", ["FOR","TER"], "N"),
    (121, "Cedro Virginia",     "fondo", ["CON","TER"], "N"),
    (122, "Vetiver Haiti",      "fondo", ["TER","MIS"], "N"),
    (123, "Vetiver Java",       "fondo", ["MIS","TER"], "N"),
    (124, "Patchouli",          "fondo", ["TER","SEN"], "N"),
    (125, "Iso E Super",        "fondo", ["ARI","SEN"], "S"),
    (126, "Cashmeran",          "fondo", ["CON","SEN"], "S"),
    (127, "Guaiaco",            "fondo", ["MIS","CON"], "N"),
    (128, "Oud/Agarwood",       "fondo", ["MIS","FOR"], "N"),
    (129, "Betulla (cuoio)",    "fondo", ["FOR","MIS"], "N"),
    (130, "Cipresso/pino",      "fondo", ["VIT","TER"], "N"),
    # K. Resine / balsami — fondo (131–140)
    (131, "Incenso (olibano)",  "fondo", ["MIS","ARI"], "N"),
    (132, "Mirra",              "fondo", ["MIS","MEM"], "N"),
    (133, "Benzoino",           "fondo", ["CON"],       "N"),
    (134, "Labdano/cisto",      "fondo", ["MIS","FOR"], "N"),
    (135, "Elemi",              "fondo", ["ARI","MIS"], "N"),
    (136, "Opoponax",           "fondo", ["CON","MEM"], "N"),
    (137, "Storace",            "fondo", ["FOR","MIS"], "N"),
    (138, "Copale/dammar",      "fondo", ["TER","MIS"], "N"),
    (139, "Galbano resinoide",  "fondo", ["TER","VIT"], "N"),
    (140, "Pino mugo/abete",    "fondo", ["TER","VIT"], "N"),
    # L. Ambra / ambrati — fondo (141–145)
    (141, "Ambroxan",           "fondo", ["SEN","MIS"], "S"),
    (142, "Accordo ambrato classico", "fondo", ["CON","SEN"], "S"),
    (143, "Ambrette (semi)",    "fondo", ["SEN","MEM"], "N"),
    (144, "Cetalox",            "fondo", ["MIS","ARI"], "S"),
    (145, "Ambra grigia (accordo)", "fondo", ["SEN","MIS"], "S"),
    # M. Muschi — fondo (146–150)
    (146, "Muschio bianco (Galaxolide)", "fondo", ["ARI","SEN"], "S"),
    (147, "Muschio (Habanolide)", "fondo", ["ARI","SEN"], "S"),
    (148, "Muschio (Muscenone)", "fondo", ["SEN","CON"], "S"),
    (149, "Ambrette assoluta",  "fondo", ["SEN","MEM"], "N"),
    (150, "Muschio pelle (Helvetolide)", "fondo", ["SEN","GIO"], "S"),
    # N. Animalici (puliti) — fondo (151–154)
    (151, "Castoreum accordo",  "fondo", ["FOR","SEN"], "S"),
    (152, "Civetta accordo",    "fondo", ["SEN","MIS"], "S"),
    (153, "Hyraceum accordo",   "fondo", ["SEN","MIS"], "S"),
    (154, "Cuoio accordo",      "fondo", ["FOR","MIS"], "S"),
    # O. Gourmand / dolci — fondo (155–158)
    (155, "Vaniglia bourbon",   "fondo", ["CON","SEN"], "N"),
    (156, "Vaniglia (vanillina)", "fondo", ["CON","GIO"], "S"),
    (157, "Caramello/etil maltolo", "fondo", ["GIO","CON"], "S"),
    (158, "Tabacco (assoluta)", "fondo", ["CON","FOR"], "N"),
]

ESSENZE_BY_ID = {e[0]: e for e in ESSENZE}

# ─── FRAGRANZE CELEBRI DA STUDIARE E CLONARE ────────────────────────────────
FAMOSI = [
    {
        "id": "ambre-dargent-montale",
        "nome": "Ambre d'Argent",
        "brand": "Montale",
        "anno": 2006,
        "famiglia": "Oriental Amber",
        "carattere": "Ambra calda e cremosa, rosa, cardamomo, muschio — ricco e persistente",
        "registri": ["CON", "SEN", "MIS"],
        "formula": {
            "testa": [(1,"Bergamotto Calabria",5), (33,"Cardamomo",4), (11,"Neroli",2)],
            "cuore": [(61,"Rosa damascena",15), (47,"Gelsomino grandiflorum",8), (146,"Muschio bianco",10)],
            "fondo":  [(142,"Accordo ambrato classico",22), (155,"Vaniglia bourbon",14),
                       (117,"Sandalo Mysore",12), (120,"Cedro Atlas",8)],
        },
        "lezione": (
            "L'ambra è l'architettura, non un ingrediente. Il 'segreto' è il rapporto "
            "3:1 fondo/cuore. Rosa e gelsomino sono veicoli di calore carnale, non fiori "
            "da giardino. Cardamomo apre senza speziare — è un 'riscaldatore' di testa. "
            "Vaniglia al fondo deve essere abbondante (14%+) per durare 4 ore. "
            "Muschio nel cuore (non solo al fondo) crea la scia morbida caratteristica."
        ),
        "variazione": (
            "Versione 'Bruxelles nordica': ridurre vaniglia a 8%, aggiungere Iris (irone) "
            "#68 al 3% nel cuore. Più freddo, più austero — stesso cuore caldo."
        ),
    },
    {
        "id": "rush-gucci",
        "nome": "Rush",
        "brand": "Gucci",
        "anno": 1999,
        "famiglia": "Oriental Floral",
        "carattere": "Patchouli + gardenia + vaniglia — sensuale, moderno anni '90",
        "registri": ["SEN", "GIO", "CON"],
        "formula": {
            "testa": [(78,"Fresia",8), (85,"Pesca (lattone)",5), (83,"Pera",3)],
            "cuore": [(51,"Gardenia (accordo)",18), (61,"Rosa damascena",8), (124,"Patchouli",10)],
            "fondo":  [(155,"Vaniglia bourbon",22), (146,"Muschio bianco",12),
                       (126,"Cashmeran",8), (119,"Sandalo sintetico (Javanol)",6)],
        },
        "lezione": (
            "Rush è patchouli + vaniglia come coppia dominante — tutto il resto è contorno. "
            "La fresia dura 15 minuti: il suo lavoro è aprire in modo fresco prima che il "
            "cuore prenda. La pesca (lattone) non è un frutto: è 'pelle calda carnale'. "
            "Gardenia abbondante nel cuore: 15-20%. Patchouli deve stare al cuore, non al "
            "fondo — altrimenti torna terra/hippy invece di sensuale-moderno."
        ),
        "variazione": (
            "Rush Homme: sostituisci gardenia con tabacco #158 (10%), riduci vaniglia a 14%, "
            "aggiungi cuoio accordo #154 al 4% al fondo."
        ),
    },
    {
        "id": "black-orchid-tomford",
        "nome": "Black Orchid",
        "brand": "Tom Ford",
        "anno": 2006,
        "famiglia": "Floral Oriental Dark",
        "carattere": "Tartufo, fiori scuri, patchouli, vetiver, vaniglia — opulento e misterioso",
        "registri": ["MIS", "SEN", "FOR"],
        "formula": {
            "testa": [(1,"Bergamotto Calabria",4), (93,"Prugna/susina",5), (88,"Ribes nero (cassis)",3)],
            "cuore": [(47,"Gelsomino grandiflorum",10), (52,"Ylang-ylang",5),
                      (124,"Patchouli",12), (131,"Incenso (olibano)",6)],
            "fondo":  [(122,"Vetiver Haiti",15), (155,"Vaniglia bourbon",15),
                       (117,"Sandalo Mysore",12), (141,"Ambroxan",8), (152,"Civetta accordo",5)],
        },
        "lezione": (
            "'Orchidea nera' non esiste in profumeria. È costruita con prugna scura + ylang "
            "+ gelsomino indolico + patchouli scuro. Il 'tartufo' = cuoio scuro + patchouli "
            "terroso. Civetta (accordo pulito) nel fondo dà il carattere organico-scuro. "
            "Regola: TUTTI i materiali devono essere 'pesanti'. Niente fresco. "
            "Anche il bergamotto in testa è solo una porta d'ingresso — evapora in 20 min."
        ),
        "variazione": (
            "Versione più accessibile: elimina civetta, riduci ylang a 2% "
            "(sopra questo livello tende a banana). Aggiungi Labdano #134 al 5%."
        ),
    },
    {
        "id": "santal33-lelabo",
        "nome": "Santal 33",
        "brand": "Le Labo",
        "anno": 2011,
        "famiglia": "Woody Musky",
        "carattere": "Sandalo secco + cuoio + cardamomo + muschio — texture di pelle",
        "registri": ["TER", "SEN", "ARI"],
        "formula": {
            "testa": [(33,"Cardamomo",5), (68,"Iris (irone)",4), (65,"Violetta foglia",3)],
            "cuore": [(141,"Ambroxan",15), (154,"Cuoio accordo",8), (125,"Iso E Super",12)],
            "fondo":  [(117,"Sandalo Mysore",20), (120,"Cedro Atlas",15),
                       (146,"Muschio bianco",10), (147,"Muschio (Habanolide)",8)],
        },
        "lezione": (
            "Santal 33 è il profumo dell'era 'minimal'. Il segreto: Ambroxan al 15% nel "
            "cuore — straborda la norma (5-8%) creando l'aura di 'pelle pulita'. "
            "Iso E Super + sandalo = legno vellutato quasi tattile. Il cuoio è solo un "
            "accento (8%), non il protagonista. Iris freddo in testa impedisce che "
            "l'Ambroxan pesante diventi dolce. Tecnica: oversaturare una singola molecola."
        ),
        "variazione": (
            "Per chi non percepisce Ambroxan: aumenta Sandalo a 28%, aggiungi Cashmeran "
            "#126 al 10%, riduci Ambroxan a 6%. Stessa texture, più cremosa e lenta."
        ),
    },
    {
        "id": "sauvage-dior",
        "nome": "Sauvage",
        "brand": "Dior",
        "anno": 2015,
        "famiglia": "Aromatic Fresh",
        "carattere": "Ambroxan + bergamotto + pepe — freschezza maschile con scia lunga",
        "registri": ["SLA", "ARI", "FOR"],
        "formula": {
            "testa": [(1,"Bergamotto Calabria",12), (31,"Pepe nero",5), (7,"Pompelmo",4)],
            "cuore": [(17,"Lavanda",10), (141,"Ambroxan",12), (125,"Iso E Super",8)],
            "fondo":  [(122,"Vetiver Haiti",18), (124,"Patchouli",8),
                       (120,"Cedro Atlas",15), (146,"Muschio bianco",8)],
        },
        "lezione": (
            "Sauvage funziona grazie a 2 molecole di sintesi (Ambroxan + Iso E Super) "
            "in quantità sopranormali. Il bergamotto abbondante (12%) è il 'manifesto': "
            "sparisce in 20 min ma crea aspettativa. La lavanda non è 'lavanda': è la "
            "componente 'aromatica fresca' che connette testa e cuore. Vetiver + patchouli "
            "+ cedro creano il treppiede legnoso. Tecnica: apertura bold → cuore molecolare "
            "→ fondo legnoso persistente."
        ),
        "variazione": (
            "Versione serale: dimezza bergamotto (6%), aggiungi tabacco #158 (5%) nel cuore, "
            "sostituisci pompelmo con cardamomo #33 (4%). Più caldo, meno 'sport'."
        ),
    },
    {
        "id": "tobacco-vanille-tomford",
        "nome": "Tobacco Vanille",
        "brand": "Tom Ford Private Blend",
        "anno": 2007,
        "famiglia": "Oriental Spicy",
        "carattere": "Tabacco caldo + vaniglia + spezie orientali — opulento, inverno",
        "registri": ["CON", "MIS", "FOR"],
        "formula": {
            "testa": [(37,"Cannella corteccia",4), (36,"Chiodi di garofano",3), (35,"Noce moscata",3)],
            "cuore": [(158,"Tabacco (assoluta)",20), (114,"Cacao/cioccolato",8),
                      (30,"Fava tonka",10), (113,"Caffè",5)],
            "fondo":  [(155,"Vaniglia bourbon",25), (133,"Benzoino",10),
                       (117,"Sandalo Mysore",8), (124,"Patchouli",4)],
        },
        "lezione": (
            "Tobacco Vanille è gourmand senza essere dolce-stucchevole. Il trucco: "
            "tabacco assoluta (non accordo) porta miele-fieno-legno secco che 'asciuga' "
            "la vaniglia. Fava tonka è il ponte tra tabacco e vaniglia — la cumarina "
            "ricorda entrambi. Cacao secco aggiunge profondità senza zucchero. "
            "Cannella e garofani spariscono presto ma lasciano un 'calore speziato' che "
            "dura nel cuore. Benzoino nel fondo: balsamo che allunga la vaniglia."
        ),
        "variazione": (
            "Versione 'sobria': dimezza vaniglia (12%), aggiungi vetiver #122 al 6%, "
            "incenso #131 al 5%. Tabacco rimane ma diventa 'fumo freddo'."
        ),
    },
    {
        "id": "baccarat-rouge-540-mfk",
        "nome": "Baccarat Rouge 540",
        "brand": "Maison Francis Kurkdjian",
        "anno": 2015,
        "famiglia": "Woody Floral Amber",
        "carattere": "Safraleine + gelsomino + cedro + fava tonka — il profumo del millennio",
        "registri": ["MIS", "SEN", "ARI"],
        "formula": {
            "testa": [(41,"Zafferano (safraleine)",8), (47,"Gelsomino grandiflorum",5), (11,"Neroli",3)],
            "cuore": [(47,"Gelsomino grandiflorum",18), (141,"Ambroxan",10), (125,"Iso E Super",10)],
            "fondo":  [(120,"Cedro Atlas",18), (30,"Fava tonka",15),
                       (146,"Muschio bianco",8), (144,"Cetalox",5)],
        },
        "lezione": (
            "BR540 è uno dei profumi più copiati degli anni 2010-20. Il segreto: "
            "zafferano SINTETICO (safraleine, non il naturale!) + gelsomino abbondante "
            "in architettura semplice. La complessità è PERCEPITA, non reale. "
            "Ambroxan e Iso E Super fanno la scia 'metallica-pulita'. Fava tonka "
            "nel fondo è il 'dolcificatore' che la rende addictive. Cedro Atlas = "
            "struttura secca che evita che diventi gourmand. Insegnamento: 6-7 "
            "ingredienti perfetti battono 20 ingredienti mediocri."
        ),
        "variazione": (
            "Extrait: aumenta zafferano a 12%, gelsomino a 25%, elimina Iso E Super, "
            "aggiungi oud sintetico #128 al 4%. Più scuro, più estremo."
        ),
    },
    {
        "id": "portrait-of-a-lady-malle",
        "nome": "Portrait of a Lady",
        "brand": "Frédéric Malle",
        "anno": 2010,
        "famiglia": "Floral Oriental",
        "carattere": "Rosa intensa + patchouli + incenso — femminile potente e austero",
        "registri": ["FOR", "SEN", "MEM"],
        "formula": {
            "testa": [(38,"Coriandolo",4), (88,"Ribes nero (cassis)",3), (1,"Bergamotto Calabria",3)],
            "cuore": [(61,"Rosa damascena",30), (47,"Gelsomino grandiflorum",8),
                      (124,"Patchouli",12), (131,"Incenso (olibano)",6)],
            "fondo":  [(122,"Vetiver Haiti",10), (155,"Vaniglia bourbon",8),
                       (146,"Muschio bianco",8), (134,"Labdano/cisto",6)],
        },
        "lezione": (
            "Portrait of a Lady è un manifesto: 'la rosa può essere potente come un uomo'. "
            "Rosa damascena al 30% — quasi triplo del normale. È la rosa come struttura "
            "portante, non come decorazione. Patchouli nel cuore non è terroso: bilancia "
            "e 'matura' la rosa. L'incenso aggiunge la dimensione sacra. "
            "Tecnica: quando un ingrediente è la tesi, mettilo in abbondanza coraggiosa."
        ),
        "variazione": (
            "Versione secca: riduci rosa a 20%, aggiungi Iris/Orris #67 al 8%, "
            "aumenta incenso a 10%. Più asceta, più nordica."
        ),
    },
    {
        "id": "oud-wood-tomford",
        "nome": "Oud Wood",
        "brand": "Tom Ford Private Blend",
        "anno": 2007,
        "famiglia": "Woody Oriental",
        "carattere": "Oud + sandalo + cardamomo + vaniglia — caldo, medievale, unisex",
        "registri": ["MIS", "FOR", "CON"],
        "formula": {
            "testa": [(33,"Cardamomo",6), (32,"Pepe rosa",4), (43,"Bacche di ginepro",2)],
            "cuore": [(128,"Oud/Agarwood",15), (124,"Patchouli",8),
                      (41,"Zafferano (safraleine)",5), (127,"Guaiaco",5)],
            "fondo":  [(117,"Sandalo Mysore",22), (155,"Vaniglia bourbon",10),
                       (120,"Cedro Atlas",12), (146,"Muschio bianco",8)],
        },
        "lezione": (
            "Oud Wood è il 'democratizzatore' dell'oud: non animalico-estremo ma "
            "legno esotico caldo. La chiave: oud (15%) billanciato da sandalo abbondante "
            "(22%) che 'ammorba' l'oud. Patchouli e guaiaco aggiungono fumo morbido. "
            "Cardamomo in testa è il 'traduttore culturale' — connette orient e occidente. "
            "Vaniglia nel fondo solo al 10% — fa da colla, non da protagonista."
        ),
        "variazione": (
            "Versione più accessibile (oud sintetico): usa accordo oud sintetico #128 "
            "al 8% invece di 15%. Aggiungi Cashmeran #126 al 8% per compensare la "
            "mancanza di complessità del naturale."
        ),
    },
    {
        "id": "no5-chanel",
        "nome": "N°5",
        "brand": "Chanel",
        "anno": 1921,
        "famiglia": "Floral Aldehyde",
        "carattere": "Aldeidi + rosa + gelsomino + iris + muschio — il profumo del '900",
        "registri": ["ARI", "SEN", "MEM"],
        "formula": {
            "testa": [(15,"Aldeide C-10",8), (16,"Accordo Cologne",5), (1,"Bergamotto Calabria",4)],
            "cuore": [(61,"Rosa damascena",18), (47,"Gelsomino grandiflorum",14),
                      (67,"Iris/Orris",6), (52,"Ylang-ylang",3)],
            "fondo":  [(146,"Muschio bianco",15), (119,"Sandalo sintetico (Javanol)",12),
                       (155,"Vaniglia bourbon",6), (30,"Fava tonka",4)],
        },
        "lezione": (
            "N°5 ha 100 anni e ancora insegna. Le aldeidi (C-10) in testa non hanno "
            "odore 'piacevole' da soli — ma la loro effervescenza brillante proietta gli "
            "altri materiali verso l'alto, dando quella 'luminosità' inimitabile. "
            "Rosa + gelsomino è il cuore classico: insieme sono più della somma. "
            "Iris aggiunge la terza dimensione cipriata. Muschio abbondante nel fondo "
            "(15%) — è la 'pelle' del profumo, non l'ingrediente. "
            "Insegnamento: non aver paura delle aldeidi. Prova 1-2% in qualsiasi formula."
        ),
        "variazione": (
            "Versione contemporanea: elimina aldeidi, sostituisci con Neroli #11 (6%). "
            "Risultato: Chanel Chance. Più fresca, meno 'nonna', stesso cuore."
        ),
    },
    {
        "id": "angel-mugler",
        "nome": "Angel",
        "brand": "Mugler",
        "anno": 1992,
        "famiglia": "Oriental Gourmand",
        "carattere": "Patchouli + caramello + vaniglia — il primo gourmand moderno, polarizzante",
        "registri": ["CON", "GIO", "TER"],
        "formula": {
            "testa": [(84,"Mela verde",6), (3,"Mandarino rosso",4), (8,"Lime",3)],
            "cuore": [(124,"Patchouli",18), (157,"Caramello/etil maltolo",12), (85,"Pesca (lattone)",5)],
            "fondo":  [(155,"Vaniglia bourbon",20), (30,"Fava tonka",12),
                       (146,"Muschio bianco",10), (156,"Vaniglia (vanillina)",5)],
        },
        "lezione": (
            "Angel ha inventato il gourmand nel 1992 — prima era impensabile mettere "
            "caramello in un profumo lusso. Il paradosso: patchouli terroso + caramello "
            "zuccherino sembrano incompatibili, ma si attraggono. Il patchouli sporca "
            "il caramello nel modo giusto — lo rende adulto. Etil maltolo (zucchero filato) "
            "è la molecola firma — 12% è aggressivo. La testa fruttata dura 5 min "
            "poi sparisce e inizia il cuore opulento. È o adorato o odiato: scegliere "
            "la polarizzazione è una strategia di brand valida."
        ),
        "variazione": (
            "Versione 'sopportabile' per chi non ama il gourmand: dimezza caramello (6%), "
            "aggiungi labdano #134 (5%) e tè nero #111 (4%). Il patchouli rimane re "
            "ma il tutto diventa più secco."
        ),
    },
    {
        "id": "shalimar-guerlain",
        "nome": "Shalimar",
        "brand": "Guerlain",
        "anno": 1925,
        "famiglia": "Oriental",
        "carattere": "Bergamotto + iris + vaniglia + muschio civet — il grande orientale classico",
        "registri": ["SEN", "MEM", "CON"],
        "formula": {
            "testa": [(1,"Bergamotto Calabria",8), (25,"Eucalipto",2), (9,"Cedro (citron)",2)],
            "cuore": [(67,"Iris/Orris",8), (47,"Gelsomino grandiflorum",10),
                      (61,"Rosa damascena",6), (131,"Incenso (olibano)",4)],
            "fondo":  [(155,"Vaniglia bourbon",22), (152,"Civetta accordo",5),
                       (146,"Muschio bianco",12), (133,"Benzoino",8), (30,"Fava tonka",6)],
        },
        "lezione": (
            "Shalimar ha 100 anni ed è ancora irriducibile. La lezione: bergamotto fresco "
            "in testa contro vaniglia pesante nel fondo crea una tensione drammatica. "
            "In mezzo: iris freddo + gelsomino caldo + incenso — tre opposti in "
            "dialogo. Civet (accordo pulito) nel fondo aggiunge il calore animalico "
            "che 'umanizza' la vaniglia. Benzoino non è vaniglia: è resina che "
            "profuma come un balsamo antico. Shalimar insegna la tensione come principio."
        ),
        "variazione": (
            "Shalimar Parfum Initial (versione Claudio): elimina civet, aggiungi muschio "
            "pelle #150 (8%). Stessa architettura, meno animalico — più contemporaneo."
        ),
    },
]

# ─── TEMI GIORNALIERI (rotazione settimanale) ────────────────────────────────
TEMI_GIORNALIERI = {
    0: {  # Lunedì
        "famiglia": "Oriental Amber",
        "descrizione": "Caldo, avvolgente, persistente — per una settimana che inizia con forza",
        "registri": ["CON", "SEN", "MIS"],
        "layer_ratio": {"testa": 15, "cuore": 30, "fondo": 55},
        "candidati": {
            "testa": [1, 33, 32, 11],
            "cuore": [61, 47, 141, 158, 31],
            "fondo": [142, 155, 117, 120, 122, 125],
        },
    },
    1: {  # Martedì
        "famiglia": "Woody Fresh",
        "descrizione": "Legno secco e aria pulita — lucidità operativa",
        "registri": ["TER", "ARI", "FOR"],
        "layer_ratio": {"testa": 20, "cuore": 35, "fondo": 45},
        "candidati": {
            "testa": [7, 43, 10, 82],
            "cuore": [17, 28, 125, 141, 100],
            "fondo": [120, 122, 124, 130, 118],
        },
    },
    2: {  # Mercoledì
        "famiglia": "Floral Sensual",
        "descrizione": "Fiori carnali e caldi — il profumo del mezzo della settimana",
        "registri": ["SEN", "GIO", "ARI"],
        "layer_ratio": {"testa": 18, "cuore": 42, "fondo": 40},
        "candidati": {
            "testa": [78, 83, 87, 63],
            "cuore": [51, 61, 47, 50, 85, 52],
            "fondo": [146, 155, 126, 119, 148],
        },
    },
    3: {  # Giovedì
        "famiglia": "Aromatic Spicy",
        "descrizione": "Spezie + fougère + radici — presenza, autorità sottile",
        "registri": ["FOR", "MIS", "VIT"],
        "layer_ratio": {"testa": 20, "cuore": 38, "fondo": 42},
        "candidati": {
            "testa": [34, 19, 43, 21],
            "cuore": [17, 31, 41, 111, 46],
            "fondo": [122, 120, 124, 154, 128],
        },
    },
    4: {  # Venerdì
        "famiglia": "Oriental Gourmand",
        "descrizione": "Dolce-speziato — celebrazione, fine settimana che arriva",
        "registri": ["CON", "GIO", "SEN"],
        "layer_ratio": {"testa": 12, "cuore": 33, "fondo": 55},
        "candidati": {
            "testa": [3, 5, 89, 95],
            "cuore": [157, 85, 114, 30, 113],
            "fondo": [155, 133, 156, 126, 117],
        },
    },
    5: {  # Sabato
        "famiglia": "Chypre / Mossy",
        "descrizione": "Radici, muschio, bergamotto — eleganza classica, weekend calmo",
        "registri": ["MEM", "TER", "SEN"],
        "layer_ratio": {"testa": 18, "cuore": 36, "fondo": 46},
        "candidati": {
            "testa": [1, 6, 97, 38],
            "cuore": [61, 62, 67, 59, 80, 81],
            "fondo": [124, 122, 131, 143, 146],
        },
    },
    6: {  # Domenica
        "famiglia": "Aquatic / Ozone",
        "descrizione": "Aria pulita, acqua, verde — reset prima di una nuova settimana",
        "registri": ["ARI", "VIT", "SLA"],
        "layer_ratio": {"testa": 25, "cuore": 38, "fondo": 37},
        "candidati": {
            "testa": [106, 105, 99, 2, 4, 82],
            "cuore": [55, 107, 100, 102, 28],
            "fondo": [125, 146, 147, 118, 130],
        },
    },
}


# ─── GENERATORE FORMULA ORIGINALE ───────────────────────────────────────────

def genera_formula_originale(data: datetime) -> dict:
    """Genera una formula originale basata sul giorno e sulla famiglia tematica."""
    rng = random.Random(data.timetuple().tm_yday + data.year * 366)
    tema = TEMI_GIORNALIERI[data.weekday()]

    def pick_layer(candidati_ids: list, budget_pct: int, n: int) -> list:
        selezionati = rng.sample(candidati_ids, min(n, len(candidati_ids)))
        # Distribuisci il budget con variazione random
        parti = [rng.randint(2, 8) for _ in range(len(selezionati))]
        totale = sum(parti)
        pcts = [round(p / totale * budget_pct) for p in parti]
        # Aggiusta l'ultimo per raggiungere esatto budget
        diff = budget_pct - sum(pcts)
        if pcts:
            pcts[-1] += diff
        return [(sid, ESSENZE_BY_ID[sid][1], pct)
                for sid, pct in zip(selezionati, pcts) if pct > 0]

    lr = tema["layer_ratio"]
    testa = pick_layer(tema["candidati"]["testa"], lr["testa"], rng.randint(2, 3))
    cuore = pick_layer(tema["candidati"]["cuore"], lr["cuore"], rng.randint(3, 4))
    fondo = pick_layer(tema["candidati"]["fondo"], lr["fondo"], rng.randint(3, 4))

    # Nome formula: CLAUDIO-XXX con numero progressivo (giorno dell'anno)
    numero_formula = f"CLAUDIO-{data.timetuple().tm_yday:03d}-{data.year % 100}"

    return {
        "nome": numero_formula,
        "data": data.strftime("%Y-%m-%d"),
        "famiglia": tema["famiglia"],
        "descrizione": tema["descrizione"],
        "registri": tema["registri"],
        "formula": {"testa": testa, "cuore": cuore, "fondo": fondo},
    }


# ─── FORMATTATORI MD ────────────────────────────────────────────────────────

def _formato_piramide(formula: dict) -> str:
    lines = []
    totale = 0
    for layer_name, emoji in [("testa","🌿"), ("cuore","🌸"), ("fondo","🪵")]:
        layer = formula["formula"].get(layer_name, [])
        layer_tot = sum(p for _, _, p in layer)
        totale += layer_tot
        lines.append(f"\n**{emoji} {layer_name.upper()}** ({layer_tot}%)")
        for sid, nome, pct in layer:
            tipo = ESSENZE_BY_ID.get(sid, (0,"","","",))[4] if len(ESSENZE_BY_ID.get(sid,())) >= 5 else "?"
            lines.append(f"- #{sid:03d} {nome} — **{pct}%** [{tipo}]")
    lines.append(f"\n*Totale concentrato: {totale}%*")
    return "\n".join(lines)


def formatta_ricetta_originale(formula: dict) -> str:
    data = formula["data"]
    registri_str = " · ".join(formula["registri"])
    piramide = _formato_piramide(formula)
    return f"""# {formula['nome']} — {formula['famiglia']}

*Studio del profumiere · {data}*

> **Registri:** {registri_str}
> **Tema del giorno:** {formula['descrizione']}

---

## Piramide olfattiva
{piramide}

---

## Concentrazione consigliata

| Formato       | Concentrato | Alcol  |
|---------------|-------------|--------|
| Eau de Parfum | 18–20%      | ~41 ml su 50 ml |
| Extrait        | 25–30%      | ~37 ml su 50 ml |

*Per 50 ml EDP (9 g concentrato): moltiplicare ogni % × 0,09 g*

---

## Note del profumiere

Questa formula nasce dallo studio sistematico della famiglia **{formula['famiglia']}**.
I registri dominanti ({registri_str}) guidano la selezione: ogni ingrediente porta
almeno uno di questi toni. La piramide rispetta il rapporto testa/cuore/fondo
con prevalenza {['del fondo' if formula['formula'].get('fondo') and sum(p for _,_,p in formula['formula']['fondo']) > 40 else 'del cuore'][0]}.

**Da testare sulla mouillette:**
1. Annusa subito → la testa regge l'apertura?
2. Dopo 15 min → il cuore emerge con carattere proprio?
3. Dopo 2 ore → il fondo è caldo ma non pesante?

**Prossimo passo:** se il profilo piace, provare su pelle. Se un ingrediente domina
troppo, ridurlo del 30% e compensare con il vicino di piramide.

---

*Generato da agente_profumiere.py · SDQ-1 · Terzi Parfums · {data}*
"""


def formatta_clone_celebre(famoso: dict, data_str: str) -> str:
    nome_file = famoso["id"]
    registri_str = " · ".join(famoso["registri"])
    piramide = _formato_piramide(famoso)
    return f"""# Clone Studio: {famoso['nome']} ({famoso['brand']}, {famoso['anno']})

*Studio di reverse-engineering · {data_str}*

> **Famiglia:** {famoso['famiglia']}
> **Carattere originale:** {famoso['carattere']}
> **Registri target:** {registri_str}

---

## Note ufficiali (dichiarate)

{famoso.get('note_originale', '—')}

---

## Formula clone con 158 essenze Terzi Parfums
{piramide}

---

## Lezione del profumiere

{famoso['lezione']}

---

## Variazione proposta

{famoso['variazione']}

---

## Come usare questo studio

1. **Costruisci la formula clone** (pesi esatti in sezione B del MASTER)
2. **Testa fianco a fianco** con l'originale se possibile
3. **Nota le differenze** — dove diverge? Perché?
4. **Proponi una variante** ispirata ai tuoi registri (es. MIS+SEN per Claudio-001)

*La copia non è il fine. La comprensione è il fine.*

---

*Generato da agente_profumiere.py · SDQ-1 · Terzi Parfums · {data_str}*
"""


# ─── SALVATAGGIO ────────────────────────────────────────────────────────────

def salva_ricetta(formula: dict, contenuto: str) -> Path:
    RICETTE_DIR.mkdir(parents=True, exist_ok=True)
    path = RICETTE_DIR / f"ricetta_{formula['data']}.md"
    path.write_text(contenuto, encoding="utf-8")
    return path


def salva_clone(famoso: dict, contenuto: str) -> Path:
    CELEBRI_DIR.mkdir(parents=True, exist_ok=True)
    path = CELEBRI_DIR / f"clone_{famoso['id']}.md"
    path.write_text(contenuto, encoding="utf-8")
    return path


def seleziona_famoso_del_giorno(data: datetime) -> dict:
    """Seleziona il famoso da studiare oggi basandosi sul giorno dell'anno."""
    idx = data.timetuple().tm_yday % len(FAMOSI)
    return FAMOSI[idx]


# ─── REPORT GIORNALIERO ─────────────────────────────────────────────────────

def genera_report_giornaliero(formula: dict, famoso: dict, data: datetime) -> str:
    tema = TEMI_GIORNALIERI[data.weekday()]
    registri_formula = " · ".join(formula["registri"])
    return f"""# Studio Profumiere — {data.strftime('%Y-%m-%d')}

**Tema del giorno:** {tema['famiglia']} — {tema['descrizione']}
**Registri dominanti:** {registri_formula}

---

## 1. Formula originale generata

**Nome:** {formula['nome']}

| Layer | Ingredienti |
|-------|-------------|
| Testa | {', '.join(f"#{s:03d} {n} {p}%" for s,n,p in formula['formula']['testa'])} |
| Cuore | {', '.join(f"#{s:03d} {n} {p}%" for s,n,p in formula['formula']['cuore'])} |
| Fondo | {', '.join(f"#{s:03d} {n} {p}%" for s,n,p in formula['formula']['fondo'])} |

→ File completo: `ricette/ricetta_{formula['data']}.md`

---

## 2. Famoso studiato oggi

**{famoso['nome']}** ({famoso['brand']}, {famoso['anno']}) — {famoso['famiglia']}
*"{famoso['carattere']}"*

→ File clone: `celebri/clone_{famoso['id']}.md`

---

## 3. Apprendimento del giorno

> {famoso['lezione'][:300]}...

**Domanda aperta per il naso:**
Come si traduce questa lezione nella formula originale di oggi?

---

*agente_profumiere.py · SDQ-1 · {data.strftime('%Y-%m-%d %H:%M')} UTC*
"""


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    now = datetime.now(timezone.utc)
    data_str = now.strftime("%Y-%m-%d")
    print(f"\n🌹 Agente Profumiere — {data_str}")
    print("─" * 50)

    # 1. Formula originale del giorno
    print("\n[1/3] Generazione formula originale...")
    formula = genera_formula_originale(now)
    contenuto_ricetta = formatta_ricetta_originale(formula)
    path_ricetta = salva_ricetta(formula, contenuto_ricetta)
    tema = TEMI_GIORNALIERI[now.weekday()]
    print(f"  ✓ {formula['nome']} — {formula['famiglia']}")
    print(f"  ✓ Salvato: {path_ricetta}")

    # 2. Studio clone del famoso del giorno
    print("\n[2/3] Studio clone del giorno...")
    famoso = seleziona_famoso_del_giorno(now)
    contenuto_clone = formatta_clone_celebre(famoso, data_str)
    path_clone = salva_clone(famoso, contenuto_clone)
    print(f"  ✓ Studiando: {famoso['nome']} ({famoso['brand']})")
    print(f"  ✓ Salvato: {path_clone}")

    # 3. Report giornaliero
    print("\n[3/3] Report giornaliero...")
    report_dir = ROOT / "output" / "profumiere"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"studio_{data_str}.md"
    report_path.write_text(
        genera_report_giornaliero(formula, famoso, now), encoding="utf-8"
    )
    print(f"  ✓ Report: {report_path}")

    print("\n─" * 50)
    print(f"Studio completo.")
    print(f"  Formula: {formula['nome']} ({tema['famiglia']})")
    print(f"  Clone:   {famoso['nome']} ({famoso['brand']})")
    print(f"  Output:  {report_path}\n")


if __name__ == "__main__":
    main()
