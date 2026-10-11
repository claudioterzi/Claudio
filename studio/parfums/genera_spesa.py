# -*- coding: utf-8 -*-
"""
LA DISPENSA — genera `public/spesa.html`
========================================

La lista della spesa e i calcoli del banco di Terzi Parfums:

  - tutte le materie dell'Organo con fornitore (DH / Pell Wall / SPEC),
    quantità consigliata (in base alla forza: le potentissime bastano in
    ml piccoli) e costo STIMATO calibrato sui budget della Guida
    (CORE ~250-400 €, ESP ~500-900 €)
  - l'attrezzatura completa del banco (bilancia, boccette, alcol, DPG,
    pipette, mouillette, guanti…) dal Livello 1 del Percorso
  - spunte «preso» e campo «usato (ml)» per lo scarico — salvati nel
    browser (localStorage), così la dispensa ricorda
  - calcolatore: quanti flaconi vuoi → concentrato, alcol e costi
  - statistiche: con l'ondata scelta, quante prove e quanti flaconi
  - scarica la lista come CSV (con lo stato attuale della dispensa)

Uso:
    python3 studio/parfums/genera_spesa.py
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parent.parent

PESI_PREZZO = {"€": 1.0, "€€": 2.2, "€€€": 5.0}
BUDGET_CORE = 320.0  # centro della forchetta 250-400 € della Guida


def ml_consigliati(m):
    if m["tipo"] == "SOL":
        return 250
    if m["tipo"] == "BASE":
        return 10
    return {5: 2, 4: 5, 3: 10, 2: 15, 1: 15}.get(m["forza"] or 3, 10)


def genera():
    organo = json.loads((BASE / "organo_terzi_300.json").read_text(encoding="utf-8"))

    core = [m for m in organo["materie"] if m["livello"] == "CORE"]
    somma_pesi_core = sum(PESI_PREZZO.get(m.get("prezzo") or "€", 1.0) for m in core)
    base_prezzo = BUDGET_CORE / somma_pesi_core

    materie, totali = [], {"CORE": 0.0, "ESP": 0.0, "MASTER": 0.0}
    for m in organo["materie"]:
        costo = round(base_prezzo * PESI_PREZZO.get(m.get("prezzo") or "€", 1.0) * 2) / 2
        totali[m["livello"]] += costo
        materie.append({
            "n": m["n"], "nome": m["nome"], "fam": m["famiglia"],
            "tipo": m["tipo"], "forza": m["forza"] or 0, "liv": m["livello"],
            "forn": m.get("fornitore") or "-",
            "ml": ml_consigliati(m), "costo": costo,
        })

    print(f"  stima CORE: {totali['CORE']:.0f} € (Guida: 250-400) · "
          f"+ESP: {totali['ESP']:.0f} € (Guida: 500-900) · "
          f"+MASTER: {totali['MASTER']:.0f} €")

    attrezzatura = [
        ["Bilancia di precisione 0,01 g", 25],
        ["Boccette vetro ambrato 10 ml × 100 (diluizioni)", 30],
        ["Flaconi spray 15/30 ml × 20 (prove finite)", 25],
        ["Beaker in vetro × 3", 12],
        ["Pipette Pasteur × 100", 8],
        ["Mouillette (strisce) × 500", 10],
        ["Alcol per profumeria 96° non denaturato aromatico — 1 L", 15],
        ["DPG (dipropilen glicole) — 500 ml", 12],
        ["Guanti in nitrile (scatola)", 8],
        ["Occhiali di protezione", 6],
        ["Etichette adesive (nome, %, solvente, data)", 6],
        ["Imbuti piccoli × 2", 5],
        ["Quaderno — il diario olfattivo", 5],
    ]

    pagina = (PAGINA
              .replace("__MATERIE__", json.dumps(materie, ensure_ascii=False,
                                                 separators=(",", ":")))
              .replace("__ATTREZZI__", json.dumps(attrezzatura, ensure_ascii=False)))
    out = REPO / "public" / "spesa.html"
    out.write_text(pagina, encoding="utf-8")
    print(f"✓ {out.relative_to(REPO)} — {len(materie)} materie + "
          f"{len(attrezzatura)} attrezzi")


PAGINA = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>La Dispensa — lista della spesa e calcoli del banco</title>
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
  .container { max-width: 1080px; margin: 0 auto; }
  header { text-align: center; margin-bottom: 1.6rem; }
  header h1 { font-size: clamp(1.6rem, 5vw, 2.4rem); font-weight: normal;
              letter-spacing: 0.1em; color: var(--gold); }
  header p { margin-top: 0.5rem; color: var(--text-dim); font-size: 0.9rem; }

  .controls { display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center;
              margin-bottom: 1rem; }
  .chip { background: var(--surface); border: 1px solid var(--border);
          color: var(--text-dim); border-radius: 999px; padding: 0.35rem 1rem;
          font-family: var(--font); font-size: 0.8rem; cursor: pointer;
          letter-spacing: 0.08em; text-transform: uppercase; }
  .chip.active { border-color: var(--gold); color: var(--gold); }
  button.oro { background: none; border: 1px solid var(--gold-dim); color: var(--gold);
        border-radius: 999px; padding: 0.45rem 1.4rem; font-family: var(--font);
        font-size: 0.88rem; cursor: pointer; }
  button.oro:hover { border-color: var(--gold); }

  .totali { display: flex; flex-wrap: wrap; gap: 1rem 2.2rem; justify-content: center;
            margin-bottom: 1.4rem; }
  .tot { text-align: center; }
  .tot .v { color: var(--gold); font-size: 1.4rem; }
  .tot .l { color: var(--text-dim); font-size: 0.64rem; letter-spacing: 0.14em;
            text-transform: uppercase; margin-top: 0.15rem; }

  h2.sezione { font-weight: normal; color: var(--gold); letter-spacing: 0.06em;
               font-size: 1.25rem; margin: 2.2rem 0 0.8rem; }
  .tavola { overflow-x: auto; background: var(--surface); border: 1px solid var(--border);
            border-radius: var(--radius); }
  table { border-collapse: collapse; width: 100%; font-size: 0.84rem; min-width: 720px; }
  th { text-align: left; font-weight: normal; font-size: 0.62rem; letter-spacing: 0.13em;
       text-transform: uppercase; color: var(--gold-dim); padding: 0.65rem 0.55rem;
       border-bottom: 1px solid var(--gold-dim); white-space: nowrap; }
  td { padding: 0.4rem 0.55rem; border-bottom: 1px solid var(--border);
       vertical-align: middle; }
  td.nome { color: var(--gold); }
  td.dim { color: var(--text-dim); white-space: nowrap; }
  td.num { text-align: right; white-space: nowrap; }
  tr.preso td.nome { color: var(--text-dim); text-decoration: line-through; }
  input[type=checkbox] { accent-color: #8a6f2e; width: 1.05em; height: 1.05em; }
  input.usato { width: 4.2em; background: var(--bg); border: 1px solid var(--border);
        color: var(--text); border-radius: 5px; padding: 0.15rem 0.35rem;
        font-family: var(--font); font-size: 0.82rem; text-align: right; }
  input.usato:focus { outline: none; border-color: var(--gold-dim); }
  .rimasto { font-size: 0.72rem; color: var(--text-dim); }
  .rimasto.poco { color: var(--red); }

  .banco { background: var(--surface); border: 1px solid var(--border);
           border-radius: var(--radius); padding: 1.2rem 1.5rem; }
  .banco .riga-calc { display: flex; flex-wrap: wrap; gap: 0.8rem; align-items: center;
           font-size: 0.92rem; }
  .banco select, .banco input[type=number] { background: var(--bg);
        border: 1px solid var(--border); color: var(--text); border-radius: 6px;
        padding: 0.35rem 0.6rem; font-family: var(--font); font-size: 0.9rem; }
  .risultato { margin-top: 1rem; }
  .risultato table { min-width: 0; }
  .nota { margin-top: 0.8rem; font-size: 0.75rem; color: var(--text-dim);
          line-height: 1.55; }
  footer { text-align: center; margin-top: 2.5rem; color: var(--text-dim);
           font-size: 0.8rem; line-height: 1.8; }
  footer a { color: var(--gold-dim); }
  @media print { .controls, button.oro, input { display: none; } }
</style>
</head>
<body>
<script src="soglia.js"></script>
<script src="nav.js"></script>
<div class="container">
  <header>
    <h1>La Dispensa</h1>
    <p>Lista della spesa, scarico delle quantità e calcoli del banco — dall'Organo Terzi 300</p>
  </header>

  <div class="controls">
    <button class="chip active" data-o="0">Ondata CORE</button>
    <button class="chip" data-o="1">CORE + ESP</button>
    <button class="chip" data-o="2">Organo completo</button>
    <button class="oro" id="scarica">⬇ Scarica la lista (CSV)</button>
    <button class="oro" id="azzera">Azzera dispensa</button>
  </div>

  <div class="totali" id="totali"></div>

  <h2 class="sezione">Le materie — spunta «preso» quando arriva, segna i ml usati per lo scarico</h2>
  <div class="tavola">
    <table>
      <thead><tr>
        <th>Preso</th><th>N°</th><th>Materia</th><th>Famiglia</th><th>Forza</th>
        <th>Fornitore</th><th>Qtà consigliata</th><th>Costo stimato</th>
        <th>Usato (ml)</th><th>Rimasto</th>
      </tr></thead>
      <tbody id="corpo"></tbody>
    </table>
  </div>

  <h2 class="sezione">L'attrezzatura del banco — alcol, provette e tutto il necessario</h2>
  <div class="tavola">
    <table>
      <thead><tr><th>Preso</th><th>Attrezzo</th><th>Costo stimato</th></tr></thead>
      <tbody id="attrezzi"></tbody>
    </table>
  </div>

  <h2 class="sezione">Il calcolatore — quanti profumi vuoi fare?</h2>
  <div class="banco">
    <div class="riga-calc">
      Voglio
      <input type="number" id="c-n" value="10" min="1" max="500" style="width:4.5em">
      flaconi da
      <select id="c-ml"><option value="15">15 ml</option>
        <option value="30" selected>30 ml</option><option value="50">50 ml</option></select>
      in concentrazione
      <select id="c-conc"><option value="10">Eau de Toilette (10%)</option>
        <option value="15" selected>Eau de Parfum (15%)</option>
        <option value="25">Extrait (25%)</option></select>
    </div>
    <div class="risultato" id="risultato"></div>
    <p class="nota">Formule del Grimorio: 1 prova (étude) = 2,5 ml di concentrato ≈ 100
    gocce. Le statistiche «prove possibili» usano un'efficienza prudente del 35%:
    le materie non si consumano mai in modo uniforme. I costi sono <b>stime</b>
    calibrate sui budget della Guida (CORE ~250–400 €, ESP ~500–900 €) — prima di
    ordinare verifica i cataloghi: De Hekserij (DH, dehekserij.nl) e Pell Wall
    (PW, pellwall.com); SPEC = fornitori specializzati (Hermitage Oils, ecc.).</p>
  </div>

  <footer>
    La dispensa si salva in questo browser (spunte e scarichi). Il CSV scaricato
    fotografa lo stato attuale.<br>
    Le materie vengono dall'<a href="organo.html">Organo 300</a> · le ricette dal
    <a href="parfums.html">catalogo</a> e dall'<a href="atelier.html">Atelier</a> ·
    il metodo dal Grimorio e dal Percorso 0→10.
  </footer>
</div>

<script>
const M = __MATERIE__;
const ATTR = __ATTREZZI__;
const ONDATE = [["CORE"], ["CORE","ESP"], ["CORE","ESP","MASTER"]];
let ondata = 0;

let stato = {};
try { stato = JSON.parse(localStorage.getItem("dispensa_terzi") || "{}"); } catch (e) {}
function salva() {
  try { localStorage.setItem("dispensa_terzi", JSON.stringify(stato)); } catch (e) {}
}
function st(id) { return stato[id] || (stato[id] = { p: false, u: 0 }); }

function visibili() { return M.filter(m => ONDATE[ondata].includes(m.liv)); }

function render() {
  document.querySelectorAll(".chip").forEach(c =>
    c.classList.toggle("active", Number(c.dataset.o) === ondata));

  const vis = visibili();
  const corpo = document.getElementById("corpo");
  corpo.innerHTML = vis.map(m => {
    const s = st("m" + m.n);
    const rimasto = s.p ? Math.max(0, m.ml - s.u) : null;
    return '<tr' + (s.p ? ' class="preso"' : '') + '>' +
      '<td><input type="checkbox" data-id="m' + m.n + '"' + (s.p ? ' checked' : '') + '></td>' +
      '<td class="dim">' + m.n + '</td>' +
      '<td class="nome">' + m.nome + '</td>' +
      '<td class="dim">' + m.fam + '</td>' +
      '<td class="dim" title="forza ' + m.forza + '/5">' +
        "\\u25cf".repeat(m.forza) + '</td>' +
      '<td class="dim">' + m.forn + '</td>' +
      '<td class="num">' + m.ml + ' ml</td>' +
      '<td class="num">~' + m.costo.toFixed(1).replace(".", ",") + ' \\u20ac</td>' +
      '<td><input class="usato" type="number" min="0" step="0.5" data-u="m' + m.n +
        '" value="' + (s.u || "") + '" placeholder="0"' + (s.p ? '' : ' disabled') + '></td>' +
      '<td class="rimasto' + (rimasto !== null && rimasto <= m.ml * 0.2 ? ' poco' : '') + '">' +
        (rimasto === null ? "\\u2014" : rimasto.toFixed(1).replace(".", ",") + " ml") + '</td>' +
      '</tr>';
  }).join("");

  document.getElementById("attrezzi").innerHTML = ATTR.map((a, i) => {
    const s = st("a" + i);
    return '<tr' + (s.p ? ' class="preso"' : '') + '>' +
      '<td><input type="checkbox" data-id="a' + i + '"' + (s.p ? ' checked' : '') + '></td>' +
      '<td class="nome">' + a[0] + '</td><td class="num">~' + a[1] + ' \\u20ac</td></tr>';
  }).join("");

  corpo.querySelectorAll("input[type=checkbox]").forEach(c =>
    c.addEventListener("change", () => { st(c.dataset.id).p = c.checked; salva(); render(); }));
  document.getElementById("attrezzi").querySelectorAll("input[type=checkbox]").forEach(c =>
    c.addEventListener("change", () => { st(c.dataset.id).p = c.checked; salva(); render(); }));
  corpo.querySelectorAll("input.usato").forEach(i =>
    i.addEventListener("change", () => {
      st(i.dataset.u).u = Math.max(0, parseFloat(i.value) || 0); salva(); render(); }));

  aggiornaTotali(vis);
  calcola();
}

function aggiornaTotali(vis) {
  const daComprare = vis.filter(m => !st("m" + m.n).p);
  const presi = vis.filter(m => st("m" + m.n).p);
  const mlTot = vis.reduce((a, m) => a + m.ml, 0);
  const mlPresi = presi.reduce((a, m) => a + m.ml, 0);
  const mlUsati = presi.reduce((a, m) => a + (st("m" + m.n).u || 0), 0);
  const costoTot = vis.reduce((a, m) => a + m.costo, 0);
  const costoResta = daComprare.reduce((a, m) => a + m.costo, 0);
  const attrResta = ATTR.reduce((a, x, i) => a + (st("a" + i).p ? 0 : x[1]), 0);
  const t = [
    [vis.length, "materie in lista"],
    [presi.length, "gi\\u00e0 prese"],
    ["~" + Math.round(costoTot) + " \\u20ac", "costo ondata"],
    ["~" + Math.round(costoResta + attrResta) + " \\u20ac", "resta da spendere"],
    [mlTot + " ml", "liquido totale"],
    [(mlPresi - mlUsati).toFixed(1).replace(".", ",") + " ml", "in dispensa ora"],
    [mlUsati.toFixed(1).replace(".", ",") + " ml", "gi\\u00e0 usati"],
  ];
  document.getElementById("totali").innerHTML = t.map(x =>
    '<div class="tot"><div class="v">' + x[0] + '</div><div class="l">' + x[1] +
    '</div></div>').join("");
}

function calcola() {
  const n = Math.max(1, parseInt(document.getElementById("c-n").value, 10) || 1);
  const ml = parseInt(document.getElementById("c-ml").value, 10);
  const conc = parseInt(document.getElementById("c-conc").value, 10) / 100;
  const concentrato = n * ml * conc;
  const alcol = n * ml * (1 - conc);
  const vis = visibili();
  const presi = vis.filter(m => st("m" + m.n).p);
  const base = (presi.length ? presi : vis);
  const mlDisp = base.reduce((a, m) =>
    a + Math.max(0, m.ml - (st("m" + m.n).p ? (st("m" + m.n).u || 0) : 0)), 0);
  const proveMax = Math.floor(mlDisp * 0.35 / 2.5);
  const flaconiMax = Math.floor(mlDisp * 0.35 / (ml * conc));
  const bottiglieAlcol = Math.ceil(alcol / 1000);
  const fonte = presi.length ? "materie gi\\u00e0 prese" : "l'ondata intera (nulla ancora preso)";

  document.getElementById("risultato").innerHTML =
    '<div class="tavola"><table>' +
    '<tr><td>Concentrato necessario</td><td class="num">' + concentrato.toFixed(1).replace(".", ",") + ' ml</td></tr>' +
    '<tr><td>Alcol necessario</td><td class="num">' + alcol.toFixed(0) + ' ml (' + bottiglieAlcol + ' L da comprare)</td></tr>' +
    '<tr><td>Costo alcol stimato</td><td class="num">~' + (bottiglieAlcol * 15) + ' \\u20ac</td></tr>' +
    '<tr><td>Con ' + fonte + ' (' + mlDisp.toFixed(0) + ' ml disponibili)</td>' +
    '<td class="num">fino a ~' + proveMax + ' prove da 100 gocce \\u00b7 ~' +
    flaconiMax + ' flaconi da ' + ml + ' ml</td></tr>' +
    '</table></div>';
}

document.querySelectorAll(".chip").forEach(c =>
  c.addEventListener("click", () => { ondata = Number(c.dataset.o); render(); }));
for (const id of ["c-n", "c-ml", "c-conc"])
  document.getElementById(id).addEventListener("input", calcola);

document.getElementById("azzera").addEventListener("click", () => {
  if (confirm("Azzerare spunte e scarichi della dispensa?")) {
    stato = {}; salva(); render();
  }
});

document.getElementById("scarica").addEventListener("click", () => {
  const vis = visibili();
  const righe = ["N;Materia;Famiglia;Forza;Fornitore;Qta_ml;Costo_stimato_EUR;Preso;Usato_ml;Rimasto_ml"];
  for (const m of vis) {
    const s = st("m" + m.n);
    righe.push([m.n, '"' + m.nome + '"', '"' + m.fam + '"', m.forza, m.forn, m.ml,
      m.costo.toFixed(1), s.p ? "SI" : "NO", s.u || 0,
      s.p ? Math.max(0, m.ml - s.u).toFixed(1) : ""].join(";"));
  }
  righe.push("");
  for (const [i, a] of ATTR.entries())
    righe.push(['ATTR', '"' + a[0] + '"', "", "", "", "", a[1],
      st("a" + i).p ? "SI" : "NO", "", ""].join(";"));
  const blob = new Blob(["\\ufeff" + righe.join("\\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "dispensa_terzi_" + ["core", "core_esp", "completa"][ondata] + ".csv";
  a.click();
  URL.revokeObjectURL(a.href);
});

render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    genera()
