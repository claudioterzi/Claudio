# -*- coding: utf-8 -*-
"""
L'ORGANO TERZI 300 — genera `public/organo.html`
================================================

La pagina dei 300 ingredienti: tutte le materie prime dell'organo di
Claudio (da `Organo_Terzi_300.xlsx` via `organo_terzi_300.json`),
consultabili con ricerca e filtri per famiglia, nota T/C/F, forza,
ondata d'acquisto e tipo. Con le note d'uso originali dell'Excel.

Uso:
    python3 studio/parfums/genera_organo.py
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parent.parent


def genera():
    organo = json.loads((BASE / "organo_terzi_300.json").read_text(encoding="utf-8"))
    materie = [{
        "n": m["n"], "nome": m["nome"], "tipo": m["tipo"], "fam": m["famiglia"],
        "nota": m["nota"] or "-", "forza": m["forza"] or 0,
        "dil": m.get("diluizione_studio") or "-",
        "forn": m.get("fornitore") or "-", "prezzo": m.get("prezzo") or "-",
        "liv": m["livello"], "scia": (m.get("ruolo_scia") or "-"),
        "uso": m.get("note_uso") or "",
    } for m in organo["materie"]]

    famiglie = sorted({m["fam"] for m in materie})
    dati = json.dumps(materie, ensure_ascii=False, separators=(",", ":"))
    pagina = (PAGINA
              .replace("__DATI__", dati)
              .replace("__FAMIGLIE__", json.dumps(famiglie, ensure_ascii=False)))
    out = REPO / "public" / "organo.html"
    out.write_text(pagina, encoding="utf-8")
    print(f"✓ {out.relative_to(REPO)} — {len(materie)} materie, "
          f"{len(famiglie)} famiglie")


PAGINA = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Organo Terzi 300 — le materie prime</title>
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
  header { text-align: center; margin-bottom: 1.8rem; }
  header h1 { font-size: clamp(1.6rem, 5vw, 2.4rem); font-weight: normal;
              letter-spacing: 0.1em; color: var(--gold); }
  header p { margin-top: 0.5rem; color: var(--text-dim); font-size: 0.9rem; }

  .filtri { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.6rem; margin-bottom: 0.8rem; }
  .filtri input, .filtri select { width: 100%; background: var(--surface);
      border: 1px solid var(--border); color: var(--text); border-radius: var(--radius);
      padding: 0.5rem 0.8rem; font-family: var(--font); font-size: 0.85rem; }
  .filtri input:focus, .filtri select:focus { outline: none; border-color: var(--gold-dim); }
  #conta { text-align: center; color: var(--gold-dim); font-size: 0.72rem;
           letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 1.2rem; }

  .tavola { overflow-x: auto; background: var(--surface); border: 1px solid var(--border);
            border-radius: var(--radius); }
  table { border-collapse: collapse; width: 100%; font-size: 0.84rem; min-width: 760px; }
  th { text-align: left; font-weight: normal; font-size: 0.64rem; letter-spacing: 0.14em;
       text-transform: uppercase; color: var(--gold-dim); padding: 0.7rem 0.6rem;
       border-bottom: 1px solid var(--gold-dim); cursor: pointer; white-space: nowrap; }
  th:hover { color: var(--gold); }
  td { padding: 0.45rem 0.6rem; border-bottom: 1px solid var(--border);
       vertical-align: top; }
  td.n { color: var(--gold-dim); white-space: nowrap; }
  td.nome { color: var(--gold); min-width: 12em; }
  td.fam, td.forn { color: var(--text-dim); white-space: nowrap; }
  td.forza { color: var(--gold); letter-spacing: 0.1em; white-space: nowrap; }
  .tipo { font-size: 0.68rem; border: 1px solid var(--border); border-radius: 4px;
          padding: 0 0.3em; color: var(--text-dim); }
  .liv { font-size: 0.68rem; border: 1px solid var(--gold-dim); border-radius: 4px;
         padding: 0 0.35em; color: var(--gold-dim); white-space: nowrap; }
  .scia { color: var(--red); font-size: 0.72rem; letter-spacing: 0.06em; }
  td.uso { color: var(--text-dim); font-size: 0.8rem; font-style: italic;
           min-width: 16em; }
  footer { text-align: center; margin-top: 2rem; color: var(--text-dim);
           font-size: 0.8rem; line-height: 1.8; }
  footer a { color: var(--gold-dim); }
</style>
</head>
<body>
<script src="soglia.js"></script>
<script src="nav.js"></script>
<div class="container">
  <header>
    <h1>Organo Terzi 300</h1>
    <p>Le materie prime — famiglia, nota, forza, ondata d'acquisto e note d'uso dall'Excel di Claudio</p>
  </header>

  <div class="filtri">
    <input id="cerca" type="search" placeholder="Cerca materia o nota d'uso…">
    <select id="f-fam"><option value="">Tutte le famiglie</option></select>
    <select id="f-nota"><option value="">Ogni nota</option>
      <option value="T">Testa</option><option value="C">Cuore</option>
      <option value="F">Fondo</option></select>
    <select id="f-liv"><option value="">Ogni ondata</option>
      <option value="CORE">CORE</option><option value="ESP">ESP</option>
      <option value="MASTER">MASTER</option></select>
    <select id="f-tipo"><option value="">Ogni tipo</option>
      <option value="NAT">Naturale</option><option value="SIN">Sintetico</option>
      <option value="BASE">Base</option><option value="SOL">Solvente</option></select>
  </div>
  <div id="conta"></div>

  <div class="tavola">
    <table>
      <thead><tr>
        <th data-k="n">N°</th><th data-k="nome">Materia</th><th data-k="fam">Famiglia</th>
        <th data-k="nota">Nota</th><th data-k="forza">Forza</th><th data-k="liv">Ondata</th>
        <th>Dil.</th><th>Forn.</th><th>€</th><th>Note d'uso</th>
      </tr></thead>
      <tbody id="corpo"></tbody>
    </table>
  </div>

  <footer>
    Fonte: <em>Organo_Terzi_300.xlsx</em> di Claudio Terzi, nel repository.<br>
    Forza 5 = tracce o microdosi (diluizione 1%). I ruoli in rosso sono il motore della scia.<br>
    Da qui nascono i <a href="parfums.html">400 profumi</a> e le proposte dell'<a href="atelier.html">Atelier</a>.
  </footer>
</div>

<script>
const M = __DATI__;
const FAMIGLIE = __FAMIGLIE__;
let ordina = "n", verso = 1;

const selFam = document.getElementById("f-fam");
for (const f of FAMIGLIE) {
  const o = document.createElement("option");
  o.value = f; o.textContent = f; selFam.appendChild(o);
}

function pallini(f) { return "\\u25cf".repeat(f) + "\\u25cb".repeat(Math.max(0, 5 - f)); }

function render() {
  const q = document.getElementById("cerca").value.toLowerCase().trim();
  const fam = selFam.value, nota = document.getElementById("f-nota").value,
        liv = document.getElementById("f-liv").value,
        tipo = document.getElementById("f-tipo").value;
  let vis = M.filter(m =>
    (!fam || m.fam === fam) &&
    (!nota || m.nota.includes(nota)) &&
    (!liv || m.liv === liv) &&
    (!tipo || m.tipo === tipo) &&
    (!q || (m.nome + " " + m.uso).toLowerCase().includes(q)));
  vis.sort((a, b) => {
    const x = a[ordina], y = b[ordina];
    return (x < y ? -1 : x > y ? 1 : 0) * verso;
  });
  document.getElementById("conta").textContent =
    vis.length + " / " + M.length + " materie";
  document.getElementById("corpo").innerHTML = vis.map(m =>
    '<tr><td class="n">' + m.n + '</td>' +
    '<td class="nome">' + m.nome +
      (m.scia !== "-" ? '<br><span class="scia">' + m.scia.toLowerCase() + '</span>' : "") +
    '</td>' +
    '<td class="fam">' + m.fam + ' <span class="tipo">' + m.tipo + '</span></td>' +
    '<td>' + m.nota + '</td>' +
    '<td class="forza" title="forza ' + m.forza + '/5">' + pallini(m.forza) + '</td>' +
    '<td><span class="liv">' + m.liv + '</span></td>' +
    '<td class="fam">' + m.dil + '</td>' +
    '<td class="forn">' + m.forn + '</td>' +
    '<td class="fam">' + m.prezzo + '</td>' +
    '<td class="uso">' + m.uso + '</td></tr>').join("");
}

for (const id of ["cerca", "f-fam", "f-nota", "f-liv", "f-tipo"])
  document.getElementById(id).addEventListener("input", render);
document.querySelectorAll("th[data-k]").forEach(th =>
  th.addEventListener("click", () => {
    const k = th.dataset.k;
    verso = (ordina === k) ? -verso : 1;
    ordina = k; render();
  }));

render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    genera()
