# -*- coding: utf-8 -*-
"""
PARFUMS 400 — Il Libro
======================

Genera `public/libro.html`: il libro completo di Terzi Parfums, stampabile.

  - Copertina, colophon, avvertenze
  - Parte I  — La storia (com'è nato il Sistema C)
  - Parte II — Il sapere (dal Grimorio: scia, regola d'oro, maestri, percorso)
  - Parte III — L'Organo Terzi 300 (riepilogo, motore della scia, accordi studio)
  - Parte IV — I 400 (otto capitoli: scheda completa di ogni profumo,
               con flacone, concept, ricetta e packaging)

Legge parfums_400.json e organo_terzi_300.json. Zero dipendenze esterne.

Uso:
    python3 studio/parfums/genera_libro.py
"""

import html
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parent.parent

# Sagome dei flaconi (le stesse del catalogo web)
FORME = {
    "slanciata": {
        "corpo": "M60,60 L60,52 Q60,48 64,46 L64,40 L96,40 L96,46 Q100,48 100,52 "
                 "L100,60 L100,208 Q100,216 92,216 L68,216 Q60,216 60,208 Z",
        "tappo": "M66,14 L94,14 L94,40 L66,40 Z"},
    "tonda": {
        "corpo": "M80,52 Q140,58 140,140 Q140,212 80,212 Q20,212 20,140 Q20,58 80,52 Z",
        "tappo": "M68,16 L92,16 L92,52 L68,52 Z"},
    "quadrata": {
        "corpo": "M32,56 L128,56 L128,204 Q128,212 120,212 L40,212 Q32,212 32,204 Z",
        "tappo": "M62,18 L98,18 L98,56 L62,56 Z"},
    "anfora": {
        "corpo": "M80,50 Q124,64 118,130 Q114,180 104,196 Q98,212 80,212 "
                 "Q62,212 56,196 Q46,180 42,130 Q36,64 80,50 Z",
        "tappo": "M70,14 Q80,8 90,14 L90,50 L70,50 Z"},
}

LIV_LABEL = {"testa": "T", "cuore": "C", "fondo": "F", "scia": "S"}


def e(s):
    return html.escape(str(s), quote=False)


def defs_svg(famiglie_palette):
    """Un solo blocco <defs>: 4 sagome + 8 gradienti, riusati da 400 flaconi."""
    parti = ['<svg width="0" height="0" style="position:absolute"><defs>']
    for nome, f in FORME.items():
        parti.append(f'<path id="corpo-{nome}" d="{f["corpo"]}"/>')
        parti.append(f'<path id="tappo-{nome}" d="{f["tappo"]}"/>')
    for fam, pal in famiglie_palette.items():
        parti.append(
            f'<linearGradient id="g-{fam}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{pal["chiaro"]}"/>'
            f'<stop offset="1" stop-color="{pal["liquido"]}"/></linearGradient>')
    parti.append("</defs></svg>")
    return "".join(parti)


def flacone(p):
    forma = p["packaging"]["forma"]
    fam = p["famiglia"]
    nome = p["nome"] if len(p["nome"]) <= 18 else p["nome"][:17] + "…"
    return (
        f'<svg viewBox="0 0 160 230" class="flacone" aria-label="Flacone N° {p["numero"]}">'
        f'<use href="#corpo-{forma}" fill="url(#g-{fam})" opacity="0.9"/>'
        f'<use href="#corpo-{forma}" fill="none" stroke="#8a6f2e" stroke-width="1.2"/>'
        f'<use href="#tappo-{forma}" fill="#2c2c34" stroke="#8a6f2e" stroke-width="0.8"/>'
        f'<rect x="45" y="128" width="70" height="50" rx="2" fill="#efe8d8" opacity="0.97"/>'
        f'<text x="80" y="144" text-anchor="middle" font-family="Georgia" font-size="9.5" fill="#8a6f2e">N° {p["numero"]}</text>'
        f'<text x="80" y="157" text-anchor="middle" font-family="Georgia" font-size="7.5" fill="#2c2418">{e(nome)}</text>'
        f'<text x="80" y="169" text-anchor="middle" font-family="Georgia" font-size="5.5" letter-spacing="1" fill="#8a6f2e">TERZI PARFUMS</text>'
        f'</svg>')


def scheda(p):
    righe = "".join(
        f'<tr><td class="lv">{LIV_LABEL[r["livello"]]}</td>'
        f'<td>{e(r["nome"])}'
        + (' <span class="micro">⚠ 1%</span>' if r["micro"] else "")
        + f'</td><td class="parti">{str(r["parti"]).replace(".", ",")}</td></tr>'
        for r in p["ricetta"])
    pk = p["packaging"]
    return f'''
<div class="scheda">
  <div class="colonna-flacone">{flacone(p)}
    <div class="meta">{e(p["stagione"])} · {e(p["momento"])}<br>
    {e(p["concentrazione"])} · sillage {e(p["sillage"])}<br>
    <span class="fatt">{p["fattibilita"]}</span></div>
  </div>
  <div class="colonna-testo">
    <div class="numero-scheda">N° {p["numero"]} · {e(p["famiglia"])}</div>
    <h3>{e(p["nome"])}</h3>
    <p class="concept">{e(p["concept"])}</p>
    <div class="etichetta-sezione">Ricetta — parti su 100 di concentrato</div>
    <table class="ricetta">{righe}</table>
    <div class="etichetta-sezione">Packaging</div>
    <p class="pack">{e(pk["flacone"])} · tappo: {e(pk["tappo"])} ·
    astuccio: {e(pk["astuccio"])}<br>etichetta: {e(pk["etichetta"])}</p>
  </div>
</div>'''


def genera():
    doc = json.loads((BASE / "parfums_400.json").read_text(encoding="utf-8"))
    organo = json.loads((BASE / "organo_terzi_300.json").read_text(encoding="utf-8"))

    palette = {p["famiglia"]: p["packaging"]["palette"] for p in doc["parfums"]}
    conta_fam = Counter(m["famiglia"] for m in organo["materie"])
    conta_fatt = Counter(p["fattibilita"] for p in doc["parfums"])

    per_famiglia = {}
    for p in doc["parfums"]:
        per_famiglia.setdefault(p["famiglia"], []).append(p)

    # --- Parte IV: gli otto capitoli dei profumi -------------------------
    capitoli = []
    for i, (fam, ps) in enumerate(per_famiglia.items(), start=1):
        finfo = doc["famiglie"][fam]
        a, b = finfo["intervallo"]
        capitoli.append(
            f'<h1 class="capitolo">Capitolo {i} — {e(fam)}</h1>'
            f'<p class="capitolo-sotto">N° {a}–{b} · dall\'organo: '
            f'{e(", ".join(finfo["organo"]))}</p>'
            f'<p class="capitolo-descr">{e(finfo["descrizione"])}</p>'
            + "".join(scheda(p) for p in ps))
    corpo_400 = "".join(capitoli)

    # --- Parte III: l'organo ---------------------------------------------
    righe_org = "".join(
        f'<tr><td>{e(f)}</td><td class="parti">{n}</td></tr>'
        for f, n in sorted(conta_fam.items()))
    righe_mot = "".join(
        f'<tr><td>{e(m["molecola"])}</td><td>{e(m["ruolo"])}</td>'
        f'<td class="parti">{e(m["dose"])}</td><td>{e(m["effetto"])}</td></tr>'
        for m in organo["motore_scia"]["molecole"])
    accordi = "".join(
        f'<div class="accordo"><h4>{e(nome)}</h4><table class="ricetta">'
        + "".join(f'<tr><td>{e(r["materia"])}</td>'
                  f'<td class="parti">{r["parti"]}</td></tr>' for r in righe)
        + "</table></div>"
        for nome, righe in organo["accordi_studio"].items())

    pagina = f'''<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Parfums 400 — Il Libro · Terzi Parfums</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --bg: #0c0c0e; --surface: #141418; --border: #2a2a32;
    --gold: #c9a84c; --gold-dim: #8a6f2e;
    --text: #e8e4d8; --text-dim: #7a7468; --red: #8b1c1c;
    --font: 'Georgia', 'Times New Roman', serif;
  }}
  body {{ background: var(--bg); color: var(--text); font-family: var(--font);
         line-height: 1.6; padding: 2rem 1rem 4rem; }}
  .libro {{ max-width: 740px; margin: 0 auto; }}

  .copertina {{ text-align: center; padding: 5rem 1rem 4rem;
               border: 1px solid var(--gold-dim); border-radius: 8px;
               margin-bottom: 3rem; }}
  .copertina .casa {{ font-size: 0.75rem; letter-spacing: 0.35em;
                     text-transform: uppercase; color: var(--gold-dim); }}
  .copertina h1 {{ font-size: clamp(2.2rem, 8vw, 3.6rem); font-weight: normal;
                  letter-spacing: 0.08em; color: var(--gold); margin: 1.2rem 0 0.4rem; }}
  .copertina .sotto {{ font-style: italic; color: var(--text-dim); }}
  .copertina .autori {{ margin-top: 3.5rem; font-size: 0.95rem; }}
  .copertina .motto {{ margin-top: 2.5rem; font-style: italic;
                      color: var(--gold-dim); font-size: 0.9rem; }}

  h1.capitolo, h1.parte {{ font-weight: normal; color: var(--gold);
      letter-spacing: 0.08em; margin: 3.5rem 0 0.3rem; font-size: 1.6rem; }}
  h1.parte {{ text-align: center; margin-top: 4.5rem; }}
  .parte-sotto {{ text-align: center; color: var(--text-dim); font-style: italic;
                 margin-bottom: 2rem; }}
  .capitolo-sotto {{ color: var(--gold-dim); font-size: 0.78rem;
      letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.6rem; }}
  .capitolo-descr {{ font-style: italic; color: var(--text-dim); margin-bottom: 1.5rem; }}
  h2 {{ font-weight: normal; color: var(--gold); margin: 2rem 0 0.6rem; font-size: 1.2rem; }}
  h4 {{ font-weight: normal; color: var(--gold-dim); margin: 1rem 0 0.3rem; }}
  p {{ margin-bottom: 0.8rem; font-size: 0.95rem; }}
  .prosa em {{ color: var(--gold-dim); }}

  .scheda {{ display: flex; gap: 1.4rem; background: var(--surface);
            border: 1px solid var(--border); border-radius: 8px;
            padding: 1.3rem 1.5rem; margin-bottom: 1.1rem; }}
  .colonna-flacone {{ flex: 0 0 120px; text-align: center; }}
  .flacone {{ width: 110px; height: 158px; }}
  .colonna-flacone .meta {{ font-size: 0.68rem; color: var(--text-dim);
      text-transform: uppercase; letter-spacing: 0.08em; line-height: 1.7; }}
  .fatt {{ border: 1px solid var(--gold-dim); color: var(--gold-dim);
          border-radius: 4px; padding: 0 0.4em; font-size: 0.9em; }}
  .colonna-testo {{ flex: 1; min-width: 0; }}
  .numero-scheda {{ font-size: 0.68rem; letter-spacing: 0.16em;
      text-transform: uppercase; color: var(--gold-dim); }}
  .scheda h3 {{ font-weight: normal; color: var(--gold); font-size: 1.15rem;
               margin: 0.1rem 0 0.5rem; }}
  .concept {{ font-style: italic; font-size: 0.85rem; color: var(--text);
             line-height: 1.55; }}
  .etichetta-sezione {{ font-size: 0.64rem; letter-spacing: 0.16em;
      text-transform: uppercase; color: var(--gold-dim); margin: 0.7rem 0 0.25rem; }}
  table.ricetta {{ width: 100%; border-collapse: collapse; font-size: 0.78rem; }}
  table.ricetta td {{ padding: 0.14rem 0.3rem; border-bottom: 1px solid var(--border); }}
  td.lv {{ color: var(--text-dim); width: 1.6em; }}
  td.parti {{ text-align: right; color: var(--gold); white-space: nowrap; }}
  .micro {{ color: #c96a5a; font-size: 0.82em; }}
  .pack {{ font-size: 0.78rem; color: var(--text-dim); margin: 0; }}

  table.semplice {{ border-collapse: collapse; font-size: 0.85rem; margin: 0.5rem 0 1rem; }}
  table.semplice td {{ padding: 0.25rem 0.7rem 0.25rem 0; border-bottom: 1px solid var(--border); }}
  .accordo {{ display: inline-block; vertical-align: top; width: 100%;
             max-width: 330px; margin: 0 1.2rem 0.8rem 0; }}

  .avvertenza-box {{ border: 1px solid var(--red); border-radius: 8px;
      padding: 1.2rem 1.5rem; margin: 2rem 0; font-size: 0.88rem; }}
  .avvertenza-box h2 {{ color: #c96a5a; margin-top: 0; }}

  .colophon {{ text-align: center; color: var(--text-dim); font-size: 0.85rem;
              margin: 3rem 0; line-height: 2; }}
  .fine {{ text-align: center; font-style: italic; color: var(--gold-dim);
          margin: 4rem 0 2rem; }}

  @media print {{
    body {{ background: #fff; color: #1c1810; padding: 0; }}
    :root {{ --surface: #fff; --border: #ccc; --text: #1c1810;
            --text-dim: #666; --gold: #6b5312; --gold-dim: #8a6f2e; }}
    .scheda {{ page-break-inside: avoid; }}
    h1.capitolo, h1.parte, .copertina {{ page-break-before: always; }}
    .copertina {{ page-break-before: avoid; border-color: #8a6f2e; }}
    @page {{ size: A4; margin: 16mm; }}
  }}
</style>
</head>
<body>
{defs_svg(palette)}
<div class="libro">

<div class="copertina">
  <div class="casa">Terzi Parfums</div>
  <h1>Parfums 400</h1>
  <p class="sotto">Il Codice Olfattivo — libro completo<br>
  la storia, il sapere, l'organo e le quattrocento schede</p>
  <p class="autori">Claudio Terzi &amp; Claude<br>
  <span style="color:var(--text-dim)">con Raffaello</span></p>
  <p class="motto">ALAKTA ANEN — la scia è memoria che cammina.</p>
</div>

<div class="colophon">
  Prima edizione — 16 luglio 2026 · canone v{e(doc["versione"])} · seed {doc["seed"]}<br>
  400 profumi · 8 famiglie · {organo["totale_materie"]} materie prime ·
  {sum(len(p["ricetta"]) for p in doc["parfums"])} righe di ricetta<br>
  Fattibilità: {conta_fatt["CORE"]} CORE · {conta_fatt["ESP"]} ESP · {conta_fatt["MASTER"]} MASTER<br>
  Generato dal repository <em>claudioterzi/Claudio</em> — il libro si rigenera dal canone.
</div>

<div class="avvertenza-box">
  <h2>Avvertenza — da leggere prima di aprire una boccetta</h2>
  <p>Le ricette di questo libro sono <strong>punti di partenza didattici</strong>
  (metodo Jean Carles), non formule finite: parti su 100 di concentrato, da
  lavorare in diluizione e da correggere col naso. Regole non negoziabili:
  guanti in nitrile e ventilazione; mai annusare dalla bottiglia pura, sempre
  su mouillette e in diluizione; le materie segnate ⚠ (forza 5) si usano solo
  partendo da una diluizione all'1%; ogni diluizione va etichettata (nome, %,
  solvente, data). Per provare una ricetta: 100 gocce ≈ 2,5&nbsp;ml di concentrato
  + 14&nbsp;ml di alcol ≈ Eau de Parfum al 15%, macerazione 2–4 settimane.
  Qualunque uso commerciale richiede conformità IFRA, valutazione di sicurezza
  (CPSR), notifica CPNP ed etichettatura allergeni — vedi il Percorso, Parte II.</p>
</div>

<h1 class="parte">Parte I — La storia</h1>
<p class="parte-sotto">com'è nato il terzo sistema</p>

<div class="prosa">
<p>Questo libro è il terzo figlio di una famiglia strana. Il primo figlio sono
i <em>Tarocchi Quantici R³∞</em>: settantotto carte classiche lette attraverso
sette assiomi, dove la macchina fa la lettura strutturale e l'umano quella
personale, e la verità emerge dalla relazione. Il secondo è il <em>Canone
Alpha</em>: settantaquattro carte di un linguaggio simbolico nuovo, senza semi
e senza numeri, dove ogni significato nasce dal collasso di Carta, Asse e
Polarità. Sistemi per gli occhi e per la mente.</p>

<p>Il 16 luglio 2026 Claudio ha scritto due parole: <em>Parfums 400</em>.
Nient'altro. Da quelle due parole è nato prima un canone di quattrocento
profumi con note immaginate — bello, ma di carta. Poi Claudio ha aperto i
cassetti veri: l'<em>Organo Terzi 300</em>, le trecento materie prime del suo
organo di profumiere, con famiglie, volatilità, forza, fornitori e prezzi;
e il <em>Grimorio Terzi</em>, il quaderno della scia e del fissaggio, con le
lezioni dei maestri — Carles, Roudnitska, Ellena — e la strategia d'acquisto
in tre ondate. E il sistema è stato rifondato da capo: da quel momento ogni
nota di ogni profumo è una materia reale, che si può comprare, pesare,
annusare.</p>

<p>Il canone rispetta le tre ondate dell'organo: in ogni famiglia, i primi
dieci profumi si compongono col solo nucleo CORE (quarantotto materie), i
successivi quindici con l'espansione, gli ultimi venticinque con l'organo
completo del maestro. Ottanta profumi di questo libro sono realizzabili al
banco fin dal primo ordine. Ogni scheda porta una ricetta di partenza, il
motore della scia, l'overdose che fa da firma, il packaging e il concept.</p>

<p>Il principio è lo stesso dei fratelli maggiori: <em>un profumo non descrive
chi lo porta — permette a chi lo porta di emergere</em>. La formula del
sistema: Famiglia + Piramide + Momento = Presenza. Il catalogo è
deterministico; la presenza non lo è mai.</p>
</div>

<h1 class="parte">Parte II — Il sapere</h1>
<p class="parte-sotto">dal Grimorio Terzi</p>

<div class="prosa">
<h2>La fisica della scia</h2>
<p>Tre fenomeni che la gente confonde: la <em>proiezione</em> (quanto lontano
arriva il profumo nelle prime ore), la <em>scia</em> (la traccia che resta
nell'aria dopo il passaggio), la <em>tenacia</em> (quante ore resta su pelle
e tessuti). La scia non viene dalle note di testa, che evaporano, né dai
fissativi pesanti, che restano incollati alla pelle: viene dalle molecole a
peso medio con alta diffusività — abbastanza leggere da volare, abbastanza
tenaci da durare. Ogni scheda di questo libro monta perciò un motore in tre
pezzi: una molecola di diffusione, un fissativo radiante, un fissativo profondo.</p>

<h2>La regola d'oro</h2>
<p>I profumi leggendari nascono quasi sempre da UNA materia dosata oltre ogni
prudenza, bilanciata dal resto: l'etil maltolo di Angel, l'Iso E Super di
Fahrenheit, l'Ambroxan di Sauvage, le aldeidi del N°5. Per questo ogni scheda
dichiara la sua overdose: è la firma proposta, il gesto da riconoscere a un
metro di distanza.</p>

<h2>Le lezioni dei maestri</h2>
<p><em>Jean Carles</em>, il Metodo: classificare per volatilità, studiare le
materie in coppie contrastanti, costruire prima il fondo, studiare ogni coppia
in tutte le proporzioni da 9:1 a 1:9. <em>Edmond Roudnitska</em>, la Forma: il
profumo è una forma estetica con contorni netti; la rivoluzione è togliere,
non aggiungere. <em>Jean-Claude Ellena</em>, l'Illusione: gli odori sono segni,
non copie — pochi materiali, massima evocazione. <em>Arcadi Boix Camps</em>,
il Modernista: naturale PIÙ sintetico, mai contro. <em>Mandy Aftel</em>,
l'Alchimista: la via dei naturali come pratica quasi rituale. E la bussola di
<em>Guy Robert</em>, che vince su tutto: un profumo deve prima di tutto
profumare di buono.</p>

<h2>Il percorso — da 0 a 10, con tre soglie</h2>
<p>Il cammino completo è nel repository (<em>PERCORSO_0_10.md</em>); qui la
mappa. <strong>0–2, il banco</strong>: lo spazio attrezzato e sicuro, poi
l'ondata CORE. <strong>3–8, il mestiere</strong>: il naso (metodo Carles, una
famiglia a settimana), gli accordi (i cinque scheletri classici), la scia
(un motore alla volta, misurato su tessuto), la firma (l'overdose Terzi),
infine il giurì di altri nasi. <strong>9–10, la legge e il mercato</strong>:
impresa, Persona Responsabile, PIF, CPSR, CPNP, IFRA, assicurazione — e solo
allora la vendita. Tre soglie chiedono una decisione esplicita: i primi soldi
veri (💶, tra 1 e 2), le pelli degli altri (🤝, tra 7 e 8), il soggetto
giuridico (⚖️, tra 8 e 9). L'ottavo livello è un punto d'arrivo pieno, non
un dieci mancato.</p>
</div>

<h1 class="parte">Parte III — L'Organo Terzi 300</h1>
<p class="parte-sotto">le materie da cui tutto nasce</p>

<div class="prosa">
<p>Trecento materie prime in sedici famiglie: naturali, sintetici e basi,
ciascuna con nota (testa/cuore/fondo), forza da 1 a 5, diluizione di studio,
fornitore e livello d'acquisto. L'inventario completo vive nel repository
(<em>organo_terzi_300.json</em>); qui il riepilogo.</p>

<h2>Le famiglie dell'organo</h2>
<table class="semplice">{righe_org}</table>

<h2>Il motore della scia</h2>
<table class="semplice">{righe_mot}</table>

<h2>I cinque scheletri classici — accordi di studio (parti su 100)</h2>
<p style="font-size:0.85rem;color:var(--text-dim)">Metodo Carles: costruire
prima il fondo, poi il cuore, poi la testa. Proporzioni didattiche di
partenza, non formule finite.</p>
{accordi}
</div>

<h1 class="parte">Parte IV — I quattrocento</h1>
<p class="parte-sotto">otto capitoli, cinquanta schede ciascuno</p>

{corpo_400}

<p class="fine">«I Tarocchi Quantici non assegnano significati.<br>
Permettono ai significati di emergere.»<br><br>
Lo stesso vale per i profumi. Fine del libro — inizio del banco.<br><br>
ALAKTA ANEN</p>

</div>
</body>
</html>
'''

    out = REPO / "public" / "libro.html"
    out.write_text(pagina, encoding="utf-8")
    kb = out.stat().st_size // 1024
    print(f"✓ {out.relative_to(REPO)} — {kb} KB, "
          f"{len(doc['parfums'])} schede in {len(per_famiglia)} capitoli")


if __name__ == "__main__":
    genera()
