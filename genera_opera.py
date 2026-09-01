# -*- coding: utf-8 -*-
"""
LA GRANDE OPERA — genera `public/opera.html`
============================================

Il lettore HTML dell'Archivio Cosmico R³∞ (`r3/archivio/`, ~100 documenti):
indice laterale per gruppi, ricerca sui titoli, conversione markdown→HTML
minimale fatta in casa (zero dipendenze, come tutto il resto).

Uso:
    python3 genera_opera.py
"""

import html
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent
ARCHIVIO = REPO / "r3" / "archivio"
OUT = REPO / "public" / "opera.html"

GRUPPI_PREFISSO = {
    "ARCHIVIO": "Gli Archivi", "SISTEMA": "I Sistemi", "MAPPA": "Le Mappe",
    "MATRICE": "Le Matrici", "BIBBIA": "Le Bibbie", "CIVILTA": "La Civiltà",
}


def md_to_html(testo: str) -> str:
    righe = testo.split("\n")
    out, para, lista, citaz, tabella, codice = [], [], [], [], [], False

    def chiudi_para():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    def chiudi_lista():
        if lista:
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in lista) + "</ul>")
            lista.clear()

    def chiudi_citaz():
        if citaz:
            out.append("<blockquote>" + "<br>".join(inline(x) for x in citaz) + "</blockquote>")
            citaz.clear()

    def chiudi_tabella():
        if tabella:
            corpo = "".join(
                "<tr>" + "".join(f"<td>{inline(c.strip())}</td>"
                                 for c in r.strip("|").split("|")) + "</tr>"
                for r in tabella)
            out.append(f"<table>{corpo}</table>")
            tabella.clear()

    def chiudi_tutto():
        chiudi_para(); chiudi_lista(); chiudi_citaz(); chiudi_tabella()

    def inline(s):
        s = html.escape(s, quote=False)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        return s

    for r in righe:
        if r.strip().startswith("```"):
            chiudi_tutto()
            codice = not codice
            out.append("<pre>" if codice else "</pre>")
            continue
        if codice:
            out.append(html.escape(r))
            continue
        s = r.rstrip()
        if not s.strip():
            chiudi_tutto()
        elif s.startswith("### "):
            chiudi_tutto(); out.append(f"<h4>{inline(s[4:])}</h4>")
        elif s.startswith("## "):
            chiudi_tutto(); out.append(f"<h3>{inline(s[3:])}</h3>")
        elif s.startswith("# "):
            chiudi_tutto(); out.append(f"<h2>{inline(s[2:])}</h2>")
        elif re.fullmatch(r"-{3,}|\*{3,}", s.strip()):
            chiudi_tutto(); out.append("<hr>")
        elif s.count("|") >= 2 and not re.fullmatch(r"[|\s:-]+", s):
            chiudi_para(); chiudi_lista(); chiudi_citaz()
            tabella.append(s)
        elif re.fullmatch(r"[|\s:-]+", s) and s.count("|") >= 2:
            continue  # riga separatrice di tabella
        elif s.lstrip().startswith(("- ", "* ")):
            chiudi_para(); chiudi_citaz(); chiudi_tabella()
            lista.append(s.lstrip()[2:])
        elif s.lstrip().startswith("> "):
            chiudi_para(); chiudi_lista(); chiudi_tabella()
            citaz.append(s.lstrip()[2:])
        else:
            chiudi_lista(); chiudi_citaz(); chiudi_tabella()
            para.append(s.strip())
    chiudi_tutto()
    return "\n".join(out)


def gruppo_di(percorso: Path) -> str:
    rel = percorso.relative_to(ARCHIVIO)
    if len(rel.parts) > 1:
        return rel.parts[0].capitalize()
    prefisso = rel.name.split("_")[0].upper()
    return GRUPPI_PREFISSO.get(prefisso, "Fondamenta")


def titolo_di(percorso: Path, testo: str) -> str:
    for r in testo.split("\n")[:5]:
        if r.startswith("# "):
            return r[2:].strip()
    return percorso.stem.replace("_", " ").title()


def genera():
    documenti = []
    for f in sorted(ARCHIVIO.rglob("*.md")):
        testo = f.read_text(encoding="utf-8", errors="replace")
        documenti.append({
            "gruppo": gruppo_di(f),
            "titolo": titolo_di(f, testo),
            "file": str(f.relative_to(REPO)),
            "html": md_to_html(testo),
        })

    ordine_gruppi = ["Fondamenta", "Gli Archivi", "I Sistemi", "Le Mappe",
                     "Le Matrici", "Le Bibbie", "La Civiltà"]
    documenti.sort(key=lambda d: (
        ordine_gruppi.index(d["gruppo"]) if d["gruppo"] in ordine_gruppi else 99,
        d["gruppo"], d["titolo"]))

    dati = json.dumps(documenti, ensure_ascii=False, separators=(",", ":"))
    pagina = PAGINA.replace("__DATI__", dati).replace("__TOT__", str(len(documenti)))
    OUT.write_text(pagina, encoding="utf-8")
    print(f"✓ {OUT.relative_to(REPO)} — {len(documenti)} documenti, "
          f"{OUT.stat().st_size // 1024} KB")


PAGINA = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>La Grande Opera — Archivio Cosmico R³∞</title>
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
  .container { max-width: 1080px; margin: 0 auto; }
  header { text-align: center; margin-bottom: 2rem; }
  header h1 { font-size: clamp(1.6rem, 5vw, 2.4rem); font-weight: normal;
              letter-spacing: 0.1em; color: var(--gold); }
  header p { margin-top: 0.5rem; color: var(--text-dim); font-size: 0.9rem; }

  .lettore { display: flex; gap: 1.2rem; align-items: flex-start; }
  .indice { flex: 0 0 300px; background: var(--surface); border: 1px solid var(--border);
            border-radius: var(--radius); padding: 1rem; position: sticky; top: 1rem;
            max-height: calc(100vh - 2rem); overflow-y: auto; }
  .indice input { width: 100%; background: var(--bg); border: 1px solid var(--border);
            color: var(--text); border-radius: var(--radius); padding: 0.45rem 0.8rem;
            font-family: var(--font); font-size: 0.85rem; margin-bottom: 0.8rem; }
  .indice input:focus { outline: none; border-color: var(--gold-dim); }
  .gruppo { font-size: 0.64rem; letter-spacing: 0.18em; text-transform: uppercase;
            color: var(--gold-dim); margin: 0.9rem 0 0.3rem; }
  .voce { display: block; width: 100%; text-align: left; background: none; border: none;
          color: var(--text-dim); font-family: var(--font); font-size: 0.82rem;
          padding: 0.22rem 0.4rem; cursor: pointer; border-radius: 4px; line-height: 1.35; }
  .voce:hover { color: var(--gold); }
  .voce.attiva { color: var(--gold); background: rgba(201,168,76,0.08); }

  .pagina { flex: 1; min-width: 0; background: var(--surface);
            border: 1px solid var(--border); border-radius: var(--radius);
            padding: 1.8rem 2rem 2.5rem; }
  .pagina .fonte { font-size: 0.68rem; letter-spacing: 0.12em; color: var(--gold-dim);
                   text-transform: uppercase; margin-bottom: 1rem; }
  .pagina h2 { color: var(--gold); font-weight: normal; font-size: 1.5rem;
               margin: 0 0 0.8rem; }
  .pagina h3 { color: var(--gold); font-weight: normal; font-size: 1.15rem;
               margin: 1.6rem 0 0.5rem; }
  .pagina h4 { color: var(--gold-dim); font-weight: normal; margin: 1.2rem 0 0.4rem; }
  .pagina p { font-size: 0.94rem; line-height: 1.7; margin-bottom: 0.8rem; }
  .pagina ul { margin: 0.4rem 0 0.9rem 1.3rem; }
  .pagina li { font-size: 0.92rem; line-height: 1.65; margin-bottom: 0.2rem; }
  .pagina blockquote { border-left: 2px solid var(--gold-dim); padding: 0.4rem 1rem;
               color: var(--text-dim); font-style: italic; margin: 0.8rem 0; }
  .pagina hr { border: none; border-top: 1px solid var(--border); margin: 1.4rem 0; }
  .pagina code { color: var(--gold); font-size: 0.9em; }
  .pagina pre { background: var(--bg); border: 1px solid var(--border);
                border-radius: 6px; padding: 0.8rem 1rem; overflow-x: auto;
                font-size: 0.82rem; margin: 0.8rem 0; }
  .pagina table { border-collapse: collapse; margin: 0.8rem 0; width: 100%;
                  display: block; overflow-x: auto; font-size: 0.84rem; }
  .pagina td { border: 1px solid var(--border); padding: 0.35rem 0.6rem; }
  .navdoc { display: flex; justify-content: space-between; margin-top: 2rem;
            font-size: 0.8rem; }
  .navdoc button { background: none; border: 1px solid var(--gold-dim);
            color: var(--gold-dim); border-radius: 999px; padding: 0.35rem 1.1rem;
            font-family: var(--font); cursor: pointer; }
  .navdoc button:hover { color: var(--gold); border-color: var(--gold); }

  @media (max-width: 760px) {
    .lettore { flex-direction: column; }
    .indice { position: static; max-height: 40vh; flex: none; width: 100%; }
  }
</style>
</head>
<body>
<script src="soglia.js"></script>
<script src="nav.js"></script>
<div class="container">
  <header>
    <h1>La Grande Opera</h1>
    <p>Archivio Cosmico R³∞ · __TOT__ documenti · le 100 fasi della Civiltà Narrativa</p>
  </header>
  <div class="lettore">
    <div class="indice" id="indice">
      <input id="cerca" type="search" placeholder="Cerca un documento…">
      <div id="voci"></div>
    </div>
    <div class="pagina" id="pagina"></div>
  </div>
</div>

<script>
const DOCS = __DATI__;
let corrente = 0;

function costruisciIndice(filtro) {
  const cont = document.getElementById("voci");
  cont.innerHTML = "";
  let gruppo = null;
  DOCS.forEach((d, i) => {
    if (filtro && !d.titolo.toLowerCase().includes(filtro)) return;
    if (d.gruppo !== gruppo) {
      gruppo = d.gruppo;
      const g = document.createElement("div");
      g.className = "gruppo"; g.textContent = gruppo;
      cont.appendChild(g);
    }
    const b = document.createElement("button");
    b.className = "voce" + (i === corrente ? " attiva" : "");
    b.textContent = d.titolo;
    b.onclick = () => apri(i);
    cont.appendChild(b);
  });
}

function apri(i) {
  corrente = i;
  const d = DOCS[i];
  document.getElementById("pagina").innerHTML =
    '<div class="fonte">' + d.gruppo + " \\u00b7 " + d.file + '</div>' + d.html +
    '<div class="navdoc">' +
    (i > 0 ? '<button onclick="apri(' + (i-1) + ')">\\u2190 ' +
      DOCS[i-1].titolo.slice(0, 28) + '</button>' : '<span></span>') +
    (i < DOCS.length - 1 ? '<button onclick="apri(' + (i+1) + ')">' +
      DOCS[i+1].titolo.slice(0, 28) + ' \\u2192</button>' : '<span></span>') +
    '</div>';
  costruisciIndice(document.getElementById("cerca").value.toLowerCase().trim());
  document.getElementById("pagina").scrollIntoView({ behavior: "smooth", block: "start" });
}

document.getElementById("cerca").addEventListener("input", e =>
  costruisciIndice(e.target.value.toLowerCase().trim()));

costruisciIndice("");
apri(0);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    genera()
