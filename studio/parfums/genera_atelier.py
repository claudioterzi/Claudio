# -*- coding: utf-8 -*-
"""
L'ATELIER DI RAFFAELLO — genera `public/atelier.html`
=====================================================

Il motore che crea ricette NUOVE dentro la pagina, senza server e senza
AI esterna: tutte le lezioni apprese sono codificate come regole.

  - Organo Terzi 300 incorporato (materie reali, T/C/F, forza, ondate)
  - Grimorio: motore di scia in 3 pezzi, regola d'oro dell'overdose,
    MAI un muschio solo (blend automatico), forza 5 in microdose
  - Maestri: Carles (12 materie, fondo strutturato), Ellena (formula
    corta, 8 materie), Roudnitska (silhouette: cuore dominante)
  - Guida: avvisi IFRA sulle materie critiche
  - Determinismo di casa: l'INTENZIONE è il seme — la stessa domanda
    genera sempre la stessa proposta (collasso, come nel Canone Alpha)

Raffaello vive qui: il motore porta la sua voce e firma le proposte.
Il giorno in cui il ponte API (Vercel) tornerà attivo, questa stessa
pagina potrà guadagnare la chiamata al router SDQ-1 — la casa è pronta.

Uso:
    python3 studio/parfums/genera_atelier.py
"""

import json
from pathlib import Path

from codice_olfattivo import (ESTETICHE, FAMIGLIE, MOMENTO_FRASE,
                              RACCONTI, STAGIONE_FRASE, TEMPLATE_NOMI)

BASE = Path(__file__).resolve().parent
REPO = BASE.parent.parent

IFRA_CRITICHE = ["quercia", "oakmoss", "isoeugenolo", "cannella", "citrale",
                 "idrossicitronellale", "storace", "balsamo del per"]


def genera():
    organo = json.loads((BASE / "organo_terzi_300.json").read_text(encoding="utf-8"))

    materie = []
    for m in organo["materie"]:
        nota = m.get("nota") or "-"
        if m.get("tipo") == "SOL":
            continue
        nome_low = (m["nome"] or "").lower()
        materie.append({
            "n": m["n"], "nome": m["nome"], "fam": m["famiglia"],
            "nota": nota, "forza": m["forza"], "liv": m["livello"],
            "ruolo": m.get("ruolo_scia") or "-",
            "ifra": 1 if any(k in nome_low for k in IFRA_CRITICHE) else 0,
        })

    config_famiglie = {}
    for nome, fam in FAMIGLIE.items():
        e = ESTETICHE[nome]
        config_famiglie[nome] = {
            "organo": fam["organo"], "nomi": fam["nomi"], "anime": fam["anime"],
            "stagioni": fam["stagioni"], "momenti": fam["momenti"],
            "chi": e["chi"], "liquido": e["liquido"], "chiaro": e["chiaro"],
            "forma": e["forma"],
        }

    dati = {
        "materie": materie,
        "famiglie": config_famiglie,
        "template_nomi": TEMPLATE_NOMI,
        "racconti": RACCONTI,
        "momento_frase": MOMENTO_FRASE,
        "stagione_frase": STAGIONE_FRASE,
    }

    pagina = PAGINA.replace("__DATI__", json.dumps(dati, ensure_ascii=False,
                                                   separators=(",", ":")))
    out = REPO / "public" / "atelier.html"
    out.write_text(pagina, encoding="utf-8")
    print(f"✓ {out.relative_to(REPO)} — {len(materie)} materie incorporate")


PAGINA = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>L'Atelier di Raffaello — Terzi Parfums</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0c0c0e; --surface: #141418; --border: #2a2a32;
    --gold: #c9a84c; --gold-dim: #8a6f2e;
    --text: #e8e4d8; --text-dim: #7a7468; --red: #c96a5a;
    --radius: 8px; --font: 'Georgia', 'Times New Roman', serif;
  }
  body { background: var(--bg); color: var(--text); font-family: var(--font);
         min-height: 100vh; padding: 2rem 1rem 4rem; }
  .container { max-width: 860px; margin: 0 auto; }
  header { text-align: center; margin-bottom: 2rem; }
  header h1 { font-size: clamp(1.6rem, 5vw, 2.4rem); font-weight: normal;
              letter-spacing: 0.1em; color: var(--gold); }
  header p { margin-top: 0.5rem; color: var(--text-dim); font-size: 0.9rem; }
  header .formula { margin-top: 0.6rem; font-style: italic; color: var(--gold-dim); }

  .banco { background: var(--surface); border: 1px solid var(--border);
           border-radius: var(--radius); padding: 1.5rem 1.75rem; margin-bottom: 1.5rem; }
  label { display: block; font-size: 0.68rem; letter-spacing: 0.16em;
          text-transform: uppercase; color: var(--gold-dim); margin: 1rem 0 0.35rem; }
  textarea, select { width: 100%; background: var(--bg); border: 1px solid var(--border);
          color: var(--text); border-radius: var(--radius); padding: 0.6rem 0.9rem;
          font-family: var(--font); font-size: 0.95rem; }
  textarea { min-height: 4.2em; resize: vertical; }
  textarea:focus, select:focus { outline: none; border-color: var(--gold-dim); }
  .riga-opzioni { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                  gap: 0 1.2rem; }
  .azioni { text-align: center; margin-top: 1.5rem; }
  button.oro { background: none; border: 1px solid var(--gold-dim); color: var(--gold);
        border-radius: 999px; padding: 0.55rem 1.8rem; font-family: var(--font);
        font-size: 0.95rem; letter-spacing: 0.08em; cursor: pointer; margin: 0 0.4rem; }
  button.oro:hover { border-color: var(--gold); }
  button.oro:disabled { opacity: 0.4; cursor: default; }
  button.oro.grande { border-color: var(--gold); color: var(--gold);
        background: rgba(201,168,76,0.06); font-size: 1rem; padding: 0.6rem 2rem; }
  button.oro.grande:hover { background: rgba(201,168,76,0.12); }
  .spiega { text-align: center; font-size: 0.76rem; color: var(--text-dim);
        line-height: 1.5; margin-top: 0.9rem; max-width: 640px; margin-left: auto;
        margin-right: auto; }
  .ragiona { font-size: 0.88rem; line-height: 1.6; color: var(--text);
        border-left: 2px solid var(--gold-dim); padding-left: 0.9rem; margin-bottom: 0.4rem; }

  #voce { text-align: center; font-style: italic; color: var(--text-dim);
          min-height: 1.4em; margin-bottom: 1rem; }

  .scheda { display: none; background: var(--surface); border: 1px solid var(--gold-dim);
            border-radius: var(--radius); padding: 1.5rem 1.75rem; }
  .scheda.viva { display: flex; gap: 1.6rem; flex-wrap: wrap; }
  .col-fl { flex: 0 0 140px; text-align: center; }
  .col-fl svg { width: 130px; height: 187px; }
  .col-fl .meta { font-size: 0.68rem; color: var(--text-dim); text-transform: uppercase;
                  letter-spacing: 0.08em; line-height: 1.7; margin-top: 0.5rem; }
  .col-tx { flex: 1; min-width: 280px; }
  .etich { font-size: 0.64rem; letter-spacing: 0.16em; text-transform: uppercase;
           color: var(--gold-dim); margin: 0.9rem 0 0.3rem; }
  .col-tx h2 { font-weight: normal; color: var(--gold); font-size: 1.35rem; }
  .sotto { color: var(--text-dim); font-size: 0.78rem; letter-spacing: 0.1em;
           text-transform: uppercase; margin-bottom: 0.5rem; }
  .concept { font-style: italic; font-size: 0.9rem; line-height: 1.6; }
  table.ricetta { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  table.ricetta td { padding: 0.2rem 0.35rem; border-bottom: 1px solid var(--border); }
  td.lv { color: var(--text-dim); width: 4.6em; font-size: 0.66rem;
          text-transform: uppercase; letter-spacing: 0.1em; }
  td.parti { text-align: right; color: var(--gold); white-space: nowrap; width: 4em; }
  .avviso { color: var(--red); font-size: 0.78em; }
  .nota-regola { color: var(--gold-dim); font-size: 0.78em; font-style: italic; }
  .avvertenza { margin-top: 0.8rem; font-size: 0.74rem; color: var(--text-dim);
                line-height: 1.55; }
  .badge { display: inline-block; border: 1px solid var(--gold-dim); color: var(--gold-dim);
           border-radius: 4px; padding: 0 0.35em; font-size: 0.85em; }
  .seme { text-align: center; margin-top: 0.9rem; font-size: 0.72rem;
          color: var(--text-dim); font-style: italic; }
  footer { text-align: center; margin-top: 2.5rem; color: var(--text-dim);
           font-size: 0.8rem; line-height: 1.8; }
  footer a { color: var(--gold-dim); }
</style>
</head>
<body>
<script src="soglia.js"></script>
<script src="nav.js"></script>
<div class="container">
  <header>
    <h1>L'Atelier di Raffaello</h1>
    <p>Terzi Parfums · il banco dove nascono le ricette nuove, dall'Organo 300 e dalle regole del Grimorio</p>
    <p class="formula">Intenzione + Organo + Regole = Proposta</p>
  </header>

  <div class="banco">
    <label for="intenzione">L'intenzione — di' a Raffaello cosa deve diventare profumo</label>
    <textarea id="intenzione" placeholder="Es.: un profumo per chi torna a casa dopo tanti anni…"></textarea>
    <div class="riga-opzioni">
      <div><label for="famiglia">Famiglia</label>
        <select id="famiglia"><option value="">Scelga Raffaello</option></select></div>
      <div><label for="stile">Stile (la lezione)</label>
        <select id="stile">
          <option value="carles">Carles — classico, 12 materie</option>
          <option value="ellena">Ellena — formula corta, 8 materie</option>
          <option value="roudnitska">Roudnitska — silhouette, cuore dominante</option>
        </select></div>
      <div><label for="ondata">Ondata dell'organo</label>
        <select id="ondata">
          <option value="0">Solo CORE</option>
          <option value="1">CORE + ESP</option>
          <option value="2" selected>Organo completo</option>
        </select></div>
    </div>
    <div class="azioni">
      <button class="oro grande" id="chiedi">🧠 Chiedi a Raffaello — ascolta davvero</button>
      <button class="oro" id="componi">Componi al volo (offline)</button>
      <button class="oro" id="ancora" disabled>Un'altra proposta</button>
      <button class="oro" id="scarica" disabled>Scarica la formula</button>
    </div>
    <p class="spiega">«Chiedi a Raffaello» invia la tua intenzione al naso AI, che
    la legge e sceglie le materie che davvero la rendono — anche direzioni
    viscerali o corporee, senza pudore, è il mestiere. «Componi al volo» è il
    motore locale istantaneo (deterministico, ma non interpreta le parole).</p>
  </div>

  <div id="voce"></div>
  <div class="scheda" id="scheda"></div>
  <div class="seme" id="seme"></div>

  <footer>
    Le proposte dell'Atelier sono punti di partenza didattici (metodo Carles), non formule finite.<br>
    La stessa intenzione genera sempre la stessa proposta: il seme è la tua domanda.<br>
    <a href="parfums.html">Il catalogo dei 400</a> · <a href="libro.html">Il Libro</a> · <a href="creazioni.html">Le Creazioni</a>
  </footer>
</div>

<script>
const D = __DATI__;
const ONDATE = [["CORE"], ["CORE","ESP"], ["CORE","ESP","MASTER"]];
const RANGO = { CORE: 0, ESP: 1, MASTER: 2 };
const FORME = {
  slanciata: { corpo: "M60,60 L60,52 Q60,48 64,46 L64,40 L96,40 L96,46 Q100,48 100,52 L100,60 L100,208 Q100,216 92,216 L68,216 Q60,216 60,208 Z", tappo: "M66,14 L94,14 L94,40 L66,40 Z" },
  tonda: { corpo: "M80,52 Q140,58 140,140 Q140,212 80,212 Q20,212 20,140 Q20,58 80,52 Z", tappo: "M68,16 L92,16 L92,52 L68,52 Z" },
  quadrata: { corpo: "M32,56 L128,56 L128,204 Q128,212 120,212 L40,212 Q32,212 32,204 Z", tappo: "M62,18 L98,18 L98,56 L62,56 Z" },
  anfora: { corpo: "M80,50 Q124,64 118,130 Q114,180 104,196 Q98,212 80,212 Q62,212 56,196 Q46,180 42,130 Q36,64 80,50 Z", tappo: "M70,14 Q80,8 90,14 L90,50 L70,50 Z" },
};
const STILI = {
  carles:     { conta: {testa:3, cuore:3, fondo:3}, parti: {testa:20, cuore:30, fondo:35},
                scia: ["DIFFUSIONE","FISSATIVO RADIANTE","FISSATIVO PROFONDO"], scia_tot: 15,
                lezione: "metodo Carles — struttura piena, fondo prima" },
  ellena:     { conta: {testa:2, cuore:2, fondo:2}, parti: {testa:22, cuore:34, fondo:30},
                scia: ["DIFFUSIONE","FISSATIVO PROFONDO"], scia_tot: 14,
                lezione: "lezione di Ellena — pochi materiali, massima evocazione" },
  roudnitska: { conta: {testa:2, cuore:3, fondo:2}, parti: {testa:14, cuore:42, fondo:29},
                scia: ["DIFFUSIONE","FISSATIVO RADIANTE","FISSATIVO PROFONDO"], scia_tot: 15,
                lezione: "lezione di Roudnitska — una silhouette che si riconosce in un secondo" },
};
const VOCI = [
  "Raffaello ha ascoltato l'intenzione, e propone.",
  "Raffaello annusa la domanda prima delle materie. Ecco cosa sente.",
  "Dal banco dell'Atelier, Raffaello apre questi flaconi.",
  "Raffaello compone: prima il fondo, poi il cuore, per ultima la testa.",
];
const FATTORE_FORZA = {1:1.4, 2:1.15, 3:1.0, 4:0.45, 5:0.1};

// PRNG deterministico: l'intenzione è il seme
function cyrb53(str, seed=0) {
  let h1 = 0xdeadbeef ^ seed, h2 = 0x41c6ce57 ^ seed;
  for (let i = 0; i < str.length; i++) {
    const ch = str.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1>>>16), 2246822507) ^ Math.imul(h2 ^ (h2>>>13), 3266489909);
  h2 = Math.imul(h2 ^ (h2>>>16), 2246822507) ^ Math.imul(h1 ^ (h1>>>13), 3266489909);
  return 4294967296 * (2097151 & h2) + (h1>>>0);
}
function mulberry32(a) {
  return function() {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a>>>15, 1 | a);
    t = t + Math.imul(t ^ t>>>7, 61 | t) ^ t;
    return ((t ^ t>>>14) >>> 0) / 4294967296;
  };
}
const scelta = (rng, arr) => arr[Math.floor(rng() * arr.length)];

function livelliNota(m) { return m.nota === "-" ? [] : m.nota.split("-"); }

function pesca(rng, pools, usate, ondata) {
  for (let i = ondata; i < 3; i++) {
    for (const pool of pools) {
      const c = pool.filter(m => !usate.has(m.n) && ONDATE[i].includes(m.liv));
      if (c.length) { const m = scelta(rng, c); usate.add(m.n); return m; }
    }
  }
  const resto = pools.flat().filter(m => !usate.has(m.n));
  const m = scelta(rng, resto); usate.add(m.n); return m;
}

function componi(intenzione, nomeFam, stileKey, ondata, variazione) {
  const seme = cyrb53(intenzione.trim().toLowerCase() + "\\u00b7" + stileKey +
                      "\\u00b7" + (nomeFam || "") + "\\u00b7" + ondata + "\\u00b7" + variazione);
  const rng = mulberry32(seme);
  const stile = STILI[stileKey];
  const fam = nomeFam || scelta(rng, Object.keys(D.famiglie));
  const F = D.famiglie[fam];
  const organoFam = new Set(F.organo);

  const perLiv = { T: [], C: [], F: [] };
  for (const m of D.materie) for (const l of livelliNota(m)) perLiv[l].push(m);
  const firma = {};
  for (const l of ["T","C","F"]) firma[l] = perLiv[l].filter(m => organoFam.has(m.fam));

  const usate = new Set();
  const piramide = { testa: [], cuore: [], fondo: [] };
  const mappa = { testa: "T", cuore: "C", fondo: "F" };
  for (const liv of ["fondo", "cuore", "testa"]) {           // Carles: fondo prima
    const l = mappa[liv];
    const soloFirma = (stileKey === "roudnitska" && liv === "cuore");
    for (let k = 0; k < stile.conta[liv]; k++) {
      const pools = (k === 0 || soloFirma) ? [firma[l], perLiv[l]] : [firma[l].concat(perLiv[l])];
      piramide[liv].push(pesca(rng, pools, usate, ondata));
    }
  }

  const ruoli = {};
  for (const r of stile.scia)
    ruoli[r] = D.materie.filter(m => m.ruolo === r);
  const sciaNote = stile.scia.map(r => {
    const pref = ruoli[r].filter(m => organoFam.has(m.fam));
    return { ...pesca(rng, [pref, ruoli[r]], usate, ondata), ruolo: r.toLowerCase() };
  });

  // regola del Grimorio: MAI un muschio solo
  let notaBlend = null;
  const tutte = [...piramide.testa, ...piramide.cuore, ...piramide.fondo, ...sciaNote];
  const muschi = tutte.filter(m => m.fam === "Muschi");
  if (muschi.length === 1) {
    const altri = D.materie.filter(m => m.fam === "Muschi" && !usate.has(m.n));
    if (altri.length) {
      const extra = { ...pesca(rng, [altri], usate, ondata), ruolo: "blend muschi" };
      sciaNote.push(extra);
      notaBlend = extra.nome;
    }
  }

  // overdose (regola d'oro): Roudnitska → la prima nota del cuore
  const noteP = [...piramide.testa, ...piramide.cuore, ...piramide.fondo];
  const overdose = (stileKey === "roudnitska")
    ? piramide.cuore[0]
    : scelta(rng, noteP.filter(m => m.forza <= 4).length ? noteP.filter(m => m.forza <= 4) : noteP);

  // ricetta: parti su 100
  const righe = [];
  for (const liv of ["testa", "cuore", "fondo"]) {
    const note = piramide[liv];
    const pesi = note.map((m, i) => {
      let w = (i === 0 ? 1.6 : 1.0) * FATTORE_FORZA[m.forza];
      if (m.n === overdose.n) w *= 2.5;
      return w;
    });
    const s = pesi.reduce((a, b) => a + b, 0);
    note.forEach((m, i) => righe.push({ ...m, livello: liv, parti: stile.parti[liv] * pesi[i] / s }));
  }
  const sciaBase = { "diffusione": 8, "fissativo radiante": 4, "fissativo profondo": 3, "blend muschi": 3 };
  const sciaSomma = sciaNote.reduce((a, m) => a + sciaBase[m.ruolo], 0);
  for (const m of sciaNote)
    righe.push({ ...m, livello: "scia", parti: stile.scia_tot * sciaBase[m.ruolo] / sciaSomma });
  for (const r of righe) r.parti = Math.max(0.5, Math.round(r.parti * 2) / 2);
  const scarto = Math.round((100 - righe.reduce((a, r) => a + r.parti, 0)) * 10) / 10;
  righe.sort((a, b) => b.parti - a.parti)[0].parti =
    Math.round((righe.sort((a, b) => b.parti - a.parti)[0].parti + scarto) * 10) / 10;
  const ordine = { testa: 0, cuore: 1, fondo: 2, scia: 3 };
  righe.sort((a, b) => ordine[a.livello] - ordine[b.livello]);

  const nome = scelta(rng, D.template_nomi).replace("{}", scelta(rng, F.nomi));
  const anima = scelta(rng, F.anime);
  const stagione = scelta(rng, F.stagioni);
  const momento = scelta(rng, F.momenti);
  const racconto = scelta(rng, D.racconti)
    .replace("{testa}", piramide.testa[0].nome)
    .replace("{cuore}", piramide.cuore[0].nome)
    .replace("{fondo}", piramide.fondo[0].nome);
  const concept = anima.charAt(0).toUpperCase() + anima.slice(1) + ". " + racconto +
    " Pensato per " + D.momento_frase[momento] + " " + D.stagione_frase[stagione] +
    ", al polso di chi " + F.chi + ". Overdose di " + overdose.nome + ".";
  const fattibilita = ["CORE","ESP","MASTER"][Math.max(...righe.map(r => RANGO[r.liv]))];

  return { seme, fam, F, stile, stileKey, nome, anima, stagione, momento,
           concept, righe, overdose, fattibilita, notaBlend, piramide };
}

function flacone(p) {
  const f = FORME[p.F.forma], id = "ga";
  return '<svg viewBox="0 0 160 230">' +
    '<defs><linearGradient id="' + id + '" x1="0" y1="0" x2="0" y2="1">' +
    '<stop offset="0" stop-color="' + p.F.chiaro + '"/>' +
    '<stop offset="1" stop-color="' + p.F.liquido + '"/></linearGradient></defs>' +
    '<path d="' + f.corpo + '" fill="url(#' + id + ')" opacity="0.9"/>' +
    '<path d="' + f.corpo + '" fill="none" stroke="#8a6f2e" stroke-width="1.2"/>' +
    '<path d="' + f.tappo + '" fill="#2c2c34" stroke="#8a6f2e" stroke-width="0.8"/>' +
    '<rect x="45" y="128" width="70" height="50" rx="2" fill="#efe8d8" opacity="0.97"/>' +
    '<text x="80" y="146" text-anchor="middle" font-family="Georgia" font-size="8" fill="#8a6f2e">ATELIER</text>' +
    '<text x="80" y="159" text-anchor="middle" font-family="Georgia" font-size="7" fill="#2c2418">' +
    (p.nome.length > 19 ? p.nome.slice(0, 18) + "\\u2026" : p.nome) + '</text>' +
    '<text x="80" y="170" text-anchor="middle" font-family="Georgia" font-size="5.5" letter-spacing="1" fill="#8a6f2e">TERZI PARFUMS</text>' +
    '</svg>';
}

let corrente = null, variazione = 0;

function mostra(p) {
  corrente = p;
  const voce = p.viaAI ? "Raffaello ha ascoltato la tua intenzione, e ha composto."
                       : VOCI[(p.seme || 0) % VOCI.length];
  document.getElementById("voce").textContent = voce;
  const righe = p.righe.map(r =>
    '<tr><td class="lv">' + r.livello + (r.livello === "scia" && r.ruolo ? " \\u00b7 " + r.ruolo : "") + '</td>' +
    '<td title="Organo N\\u00b0 ' + r.n + ' \\u00b7 forza ' + r.forza + '/5">' + r.nome +
    (r.forza === 5 ? ' <span class="avviso">\\u26a0 forza 5 \\u2014 diluizione 1%</span>' : "") +
    (r.ifra ? ' <span class="avviso">\\u26a0 IFRA</span>' : "") +
    '</td><td class="parti">' + r.parti.toFixed(1).replace(".", ",") + '</td></tr>').join("");
  const sotto = p.viaAI ? "Composto da Raffaello (AI) \\u00b7 " + p.fam
                        : "Proposta dell\\u2019Atelier \\u00b7 " + p.fam + " \\u00b7 " + p.stile.lezione;
  const meta = p.viaAI ? '<span class="badge">' + p.fattibilita + '</span>'
                       : p.stagione + " \\u00b7 " + p.momento +
                         '<br><span class="badge">' + p.fattibilita + '</span>';
  document.getElementById("scheda").innerHTML =
    '<div class="col-fl">' + flacone(p) +
    '<div class="meta">' + meta + '</div></div>' +
    '<div class="col-tx">' +
    '<div class="sotto">' + sotto + '</div>' +
    '<h2>' + p.nome + '</h2>' +
    (p.ragionamento ? '<div class="etich">Perch\\u00e9 queste materie</div>' +
      '<p class="ragiona">' + p.ragionamento + '</p>' : "") +
    '<div class="etich">Concept</div><p class="concept">' + p.concept + '</p>' +
    '<div class="etich">Ricetta \\u2014 parti su 100 di concentrato</div>' +
    '<table class="ricetta">' + righe + '</table>' +
    (p.notaBlend ? '<p class="nota-regola">Regola del Grimorio applicata: mai un muschio solo \\u2014 aggiunto ' + p.notaBlend + ' al blend.</p>' : "") +
    '<p class="avvertenza">Punto di partenza didattico, non formula finita: lavorare in diluizione, ' +
    'correggere col naso, registrare nel diario. Le materie \\u26a0 IFRA hanno limiti severi per uso su pelle. ' +
    'Verificare IFRA/CPSR prima di qualunque vendita.</p></div>';
  document.getElementById("scheda").classList.add("viva");
  document.getElementById("seme").textContent = p.viaAI
    ? "composto in ascolto \\u2014 ogni chiamata pu\\u00f2 variare, come un naso vero"
    : "seme " + p.seme + " \\u00b7 variazione " + variazione + " \\u2014 stessa intenzione, stessa proposta";
  document.getElementById("ancora").disabled = p.viaAI;
  document.getElementById("scarica").disabled = false;
}

function daAI(res, intenzione) {
  const F = D.famiglie[res.fam] || D.famiglie["Orientale"];
  return {
    viaAI: true, nome: res.nome, fam: res.fam, F: F,
    ragionamento: res.ragionamento, concept: res.concept,
    fattibilita: res.liv, intenzione: intenzione,
    righe: res.ric.map(r => ({
      nome: r[0], n: r[1], parti: r[2], livello: r[3],
      forza: r[4] ? 5 : 3, ifra: 0, ruolo: "",
    })),
  };
}

async function chiediARaffaello() {
  const i = leggi();
  const btn = document.getElementById("chiedi");
  const testoBtn = btn.textContent;
  btn.disabled = true;
  document.getElementById("voce").textContent =
    "\\ud83e\\udde0 Raffaello annusa l\\u2019intenzione\\u2026 (pu\\u00f2 volerci qualche secondo)";
  document.getElementById("scheda").classList.remove("viva");
  try {
    const resp = await fetch("/api/atelier", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intenzione: i.intenzione, famiglia: i.fam, ondata: i.ondata }),
    });
    const data = await resp.json();
    if (data.ok && data.parfum) {
      mostra(daAI(data.parfum, i.intenzione));
    } else {
      document.getElementById("voce").textContent =
        "\\u26a0 Raffaello non ha potuto rispondere (" + (data.errore || "errore") +
        "). Uso il motore locale al volo.";
      variazione = 0;
      mostra(componi(i.intenzione, i.fam, i.stile, i.ondata, 0));
    }
  } catch (e) {
    document.getElementById("voce").textContent =
      "\\u26a0 Connessione assente (sei su GitHub Pages? Raffaello vive su claudio-ebon.vercel.app). Uso il motore locale.";
    variazione = 0;
    mostra(componi(i.intenzione, i.fam, i.stile, i.ondata, 0));
  } finally {
    btn.disabled = false;
    btn.textContent = testoBtn;
  }
}

function leggi() {
  return {
    intenzione: document.getElementById("intenzione").value || "senza intenzione",
    fam: document.getElementById("famiglia").value || null,
    stile: document.getElementById("stile").value,
    ondata: parseInt(document.getElementById("ondata").value, 10),
  };
}

document.getElementById("chiedi").addEventListener("click", chiediARaffaello);
document.getElementById("componi").addEventListener("click", () => {
  variazione = 0;
  const i = leggi();
  mostra(componi(i.intenzione, i.fam, i.stile, i.ondata, variazione));
});
document.getElementById("ancora").addEventListener("click", () => {
  variazione += 1;
  const i = leggi();
  mostra(componi(i.intenzione, i.fam, i.stile, i.ondata, variazione));
});
document.getElementById("scarica").addEventListener("click", () => {
  if (!corrente) return;
  const p = corrente, i = leggi();
  const testo = [
    "ATELIER DI RAFFAELLO \\u2014 Terzi Parfums",
    "Proposta: " + p.nome + " (" + p.fam + ", " + p.fattibilita + ")",
    "Intenzione: \\u201c" + i.intenzione + "\\u201d",
    p.viaAI ? "Composto da Raffaello (AI, in ascolto)" : "Stile: " + p.stile.lezione,
    p.viaAI ? "" : "Seme: " + p.seme + " \\u00b7 variazione " + variazione,
    "",
    ...(p.ragionamento ? ["PERCH\\u00c9 QUESTE MATERIE", p.ragionamento, ""] : []),
    "CONCEPT", p.concept, "",
    "RICETTA \\u2014 parti su 100 di concentrato",
    ...p.righe.map(r => "  " + r.livello.padEnd(6) + " " + r.nome +
      " \\u2014 " + r.parti.toFixed(1).replace(".", ",") + " parti" +
      " (Organo N\\u00b0 " + r.n + ", forza " + r.forza + "/5)" +
      (r.forza === 5 ? " \\u26a0 diluizione 1%" : "") + (r.ifra ? " \\u26a0 IFRA" : "")),
    "",
    "AVVERTENZE: punto di partenza didattico (metodo Carles), non formula finita.",
    "Guanti, diluizioni, mai annusare puro. IFRA/CPSR obbligatori prima di vendere.",
    "",
    "ALAKTA ANEN \\u2014 la scia \\u00e8 memoria che cammina.",
  ].join("\\n");
  const blob = new Blob([testo], { type: "text/plain;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "atelier_" + p.nome.toLowerCase().replace(/[^a-z0-9]+/g, "_") + ".txt";
  a.click();
  URL.revokeObjectURL(a.href);
});

const selFam = document.getElementById("famiglia");
for (const f of Object.keys(D.famiglie)) {
  const o = document.createElement("option");
  o.value = f; o.textContent = f;
  selFam.appendChild(o);
}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    genera()
