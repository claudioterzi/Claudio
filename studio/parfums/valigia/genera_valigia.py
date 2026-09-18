# -*- coding: utf-8 -*-
"""
LA VALIGIA-ORGANO — genera `public/valigia.html`
================================================

La pagina del progetto della Valigia-Organo di Terzi Parfums: valigia a
libro con 7 moduli estraibili che ospitano le 293 boccette da 30 ml
dell'organo, disposte per famiglia olfattiva.

Il cuore della pagina è la MAPPA INTERATTIVA dei 7 cassetti: griglia
A–G × 1–7, ogni slot colorato per famiglia. La ricerca "trova-boccetta"
accende lo slot giusto (la versione software della V2 luminosa: digiti
"Cashmeran" → si illumina C5-E2).

Fonti (nella stessa cartella, dai file di Claudio):
  Mappa_Riempimento_30ml.xlsx → mappa_riempimento.json
  Valigia_Organo_Specifica.docx (il testo è strutturato qui sotto)

Uso:
    python3 studio/parfums/valigia/genera_valigia.py
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parent.parent.parent

# colore per famiglia olfattiva (coerente con la pelle del sito)
COLORI_FAM = {
    "Agrumi": "#d9b23c", "Aldeidi": "#cdbf7a", "Marini/Ozonici": "#5f8fa3",
    "Aromatiche/Verdi": "#7c9a5f", "Chypre/Terrosi": "#6e7b52",
    "Fiorali vari": "#c98a9e", "Rosa": "#c26f84", "Fiori bianchi": "#e0d4b0",
    "Fruttati": "#d98f5a", "Gourmand/Vaniglia": "#a9764a", "Legni": "#8a5a33",
    "Muschi": "#b9a98c", "Ambrati/Resine": "#c98a3a", "Animalic/Cuoio": "#8a4a30",
    "Speziati": "#a3502a", "Solventi/Fissativi": "#555",
}


def genera():
    dati = json.loads((BASE / "mappa_riempimento.json").read_text(encoding="utf-8"))
    mappa = dati["mappa"]
    casetti = dati["casetti"]
    solventi = dati["solventi"]

    # ordine dei cassetti C1..C7
    ordine = sorted(casetti.keys())
    casetti_web = [{"id": c, "nome": casetti[c]["nome"], "n": casetti[c]["n"]}
                   for c in ordine]

    payload = json.dumps({
        "mappa": [[m["cas"], m["slot"], m["n"], m["materia"], m["fam"], m["ml"]]
                  for m in mappa],
        "casetti": casetti_web,
        "colori": COLORI_FAM,
        "solventi": solventi,
    }, ensure_ascii=False, separators=(",", ":"))

    out = REPO / "public" / "valigia.html"
    out.write_text(PAGINA.replace("__DATI__", payload)
                   .replace("__NBOCC__", str(len(mappa)))
                   .replace("__NSOLV__", str(len(solventi))), encoding="utf-8")
    print(f"✓ {out.relative_to(REPO)} — {len(mappa)} boccette, {len(casetti)} cassetti")


PAGINA = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>La Valigia-Organo — Terzi Parfums</title>
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
  header { text-align: center; margin-bottom: 2rem; }
  header h1 { font-size: clamp(1.7rem, 6vw, 2.6rem); font-weight: normal;
              letter-spacing: 0.1em; color: var(--gold); }
  header p { margin-top: 0.5rem; color: var(--text-dim); font-size: 0.9rem; }
  header .sub { font-style: italic; color: var(--gold-dim); margin-top: 0.4rem; }

  h2 { font-weight: normal; color: var(--gold); font-size: 1.35rem;
       letter-spacing: 0.05em; margin: 2.5rem 0 0.4rem; }
  h2 .num { color: var(--gold-dim); font-size: 0.7em; }
  .intro { color: var(--text); line-height: 1.7; font-size: 0.95rem; margin-bottom: 0.6rem; }
  .intro em { color: var(--gold-dim); }

  /* mappa interattiva */
  .cerca-slot { display: flex; justify-content: center; margin: 1rem 0; }
  .cerca-slot input { background: var(--surface); border: 1px solid var(--border);
      color: var(--text); border-radius: var(--radius); padding: 0.6rem 1rem;
      width: min(460px, 100%); font-family: var(--font); font-size: 0.95rem; }
  .cerca-slot input:focus { outline: none; border-color: var(--gold); }
  #trovato { text-align: center; min-height: 1.4em; color: var(--gold);
             font-size: 0.9rem; margin-bottom: 1rem; }

  .cassetto { background: var(--surface); border: 1px solid var(--border);
              border-radius: var(--radius); padding: 1rem 1.1rem 1.2rem;
              margin-bottom: 1rem; }
  .cassetto h3 { font-weight: normal; color: var(--gold); font-size: 1.05rem;
                 margin-bottom: 0.1rem; }
  .cassetto .cnt { color: var(--text-dim); font-size: 0.72rem; letter-spacing: 0.1em;
                   text-transform: uppercase; margin-bottom: 0.7rem; }
  .griglia { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
  .slot { aspect-ratio: 1; border-radius: 4px; border: 1px solid var(--border);
          position: relative; overflow: hidden; cursor: default;
          display: flex; flex-direction: column; justify-content: center;
          align-items: center; padding: 2px; text-align: center; }
  .slot .sn { font-size: 0.6rem; color: rgba(255,255,255,0.85); font-weight: bold;
              line-height: 1; }
  .slot .snome { font-size: 0.44rem; color: rgba(255,255,255,0.75); line-height: 1.05;
                 margin-top: 1px; overflow: hidden; max-height: 2.2em; }
  .slot.vuoto { background: #101014; border-style: dashed; opacity: 0.5; }
  .slot.acceso { outline: 3px solid var(--gold); outline-offset: -1px;
                 box-shadow: 0 0 18px var(--gold); z-index: 2; transform: scale(1.08); }
  .slot .cod { position: absolute; top: 1px; left: 2px; font-size: 0.4rem;
               color: rgba(255,255,255,0.5); }

  .schema { display: flex; gap: 1rem; flex-wrap: wrap; justify-content: center;
            margin: 1rem 0; }
  .ala { background: var(--surface); border: 1px solid var(--border);
         border-radius: var(--radius); padding: 1rem 1.2rem; flex: 1; min-width: 260px; }
  .ala h4 { color: var(--gold-dim); font-weight: normal; font-size: 0.7rem;
            letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.5rem; }
  .ala ul { list-style: none; }
  .ala li { font-size: 0.88rem; line-height: 1.7; }
  .ala li b { color: var(--gold); font-weight: normal; }

  table.spec { width: 100%; border-collapse: collapse; font-size: 0.86rem;
               background: var(--surface); border: 1px solid var(--border);
               border-radius: var(--radius); overflow: hidden; margin-top: 0.6rem; }
  table.spec td { padding: 0.45rem 0.8rem; border-bottom: 1px solid var(--border);
                  vertical-align: top; }
  table.spec td:first-child { color: var(--gold-dim); white-space: nowrap; width: 34%; }
  .costo-tot td { color: var(--gold) !important; }

  .colonne { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px,1fr));
             gap: 1rem; }
  .box { background: var(--surface); border: 1px solid var(--border);
         border-radius: var(--radius); padding: 1rem 1.2rem; }
  .box h4 { color: var(--gold); font-weight: normal; margin-bottom: 0.4rem; }
  .box p, .box li { font-size: 0.86rem; line-height: 1.6; color: var(--text); }
  .box ul { list-style: none; }
  .box li::before { content: "· "; color: var(--gold-dim); }
  .nota { border-left: 2px solid var(--gold-dim); padding-left: 0.9rem;
          color: var(--text-dim); font-size: 0.86rem; line-height: 1.6; margin: 0.6rem 0; }

  .legenda { display: flex; flex-wrap: wrap; gap: 0.4rem 0.9rem; justify-content: center;
             margin: 0.8rem 0; font-size: 0.72rem; color: var(--text-dim); }
  .legenda span { display: inline-flex; align-items: center; gap: 0.3rem; }
  .legenda i { width: 0.8em; height: 0.8em; border-radius: 2px; display: inline-block; }

  footer { text-align: center; margin-top: 3rem; color: var(--text-dim);
           font-size: 0.8rem; line-height: 1.9; }
  footer a { color: var(--gold-dim); }
  @media print { .cerca-slot { display: none; } }
</style>
</head>
<body>
<script src="soglia.js"></script>
<script src="nav.js"></script>
<div class="container">
  <header>
    <h1>La Valigia-Organo</h1>
    <p>Terzi Parfums · l'atelier da banco che custodisce le __NBOCC__ materie dell'organo</p>
    <p class="sub">Valigia a libro · 7 moduli estraibili · boccette 30 ml con contagocce</p>
  </header>

  <p class="intro">Un contenitore da banco, non da viaggio, che ospita l'intera
  tavolozza in boccette uguali da 30 ml, ognuna al suo posto inciso. La valigia
  si apre a libro: <em>tre moduli nell'ala sinistra, quattro nell'ala destra</em>,
  e al centro un piano di lavoro che si distende piatto. Ogni modulo si sfila e si
  appoggia sul tavolo — lavori su quello che ti serve senza spostare gli altri.
  Il prodotto che viaggia è il profumo finito; l'organo resta il cuore fermo del banco.</p>

  <h2>La mappa dei cassetti <span class="num">— trova ogni boccetta</span></h2>
  <p class="intro">Ogni slot è colorato per famiglia. Cerca una materia (o un numero
  della Dispensa): <em>lo slot giusto si illumina</em> — la versione software della
  V2 luminosa, già qui.</p>
  <div class="cerca-slot">
    <input id="cerca" type="search" placeholder="Es. Cashmeran, oud, 295, ambroxan…">
  </div>
  <div id="trovato"></div>
  <div class="legenda" id="legenda"></div>
  <div id="cassetti"></div>

  <h2>L'architettura <span class="num">— valigia a libro</span></h2>
  <div class="schema">
    <div class="ala">
      <h4>Ala sinistra — 3 moduli</h4>
      <ul id="ala-sx"></ul>
    </div>
    <div class="ala">
      <h4>Ala destra — 4 moduli</h4>
      <ul id="ala-dx"></ul>
    </div>
  </div>
  <p class="nota">Al centro, sulla cerniera-dorso, il piano di lavoro. Nel coperchio,
  il pannello attrezzi (bilancia 0,01 g, mouillette, pipette, becher, siringhe,
  etichette) e una striscia LED CRI ≥ 95 che si accende all'apertura — per leggere
  bene il colore dei liquidi.</p>

  <h2>La griglia e le boccette</h2>
  <table class="spec">
    <tr><td>Griglia per modulo</td><td>7 file (A–G) × 7 colonne = 49 slot · totale 343 posti</td></tr>
    <tr><td>Occupati / liberi</td><td>__NBOCC__ pieni · 50 liberi (crescita, duplicati, madri)</td></tr>
    <tr><td>Passo tra slot</td><td>~40 mm — spazio per le dita e le etichette</td></tr>
    <tr><td>Modulo</td><td>~320 × 320 mm · foam EVA nera ~40 mm · estraibile con chiusura magnetica</td></tr>
    <tr><td>Boccetta</td><td>Boston round vetro ambrato (UV), 30 ml, Ø ~35 mm, h ~78 mm</td></tr>
    <tr><td>Tappo</td><td>Contagocce per il dosaggio a gocce · bulbo PTFE/resistente ai solventi</td></tr>
    <tr><td>Numerazione</td><td>Slot incisi A1…G7 nel materiale — permanenti anche a slot vuoto</td></tr>
  </table>
  <p class="nota">I bulbi in gomma comune si degradano con le materie aggressive
  (aldeidi, fenoli, alte % di solvente): per quelle poche, tappo a vite + pipetta di
  vetro separata. Per tutto il resto, contagocce. I 7 solventi/consumabili da 250 ml
  (alcol, DPG, IPM, benzil benzoato, TEC, Glucam, Hercolyn) restano nei flaconi grandi,
  su mensola — non entrano tra le boccette uguali.</p>

  <h2>Il budget <span class="num">— stime da confermare col preventivo</span></h2>
  <div class="colonne">
    <div class="box">
      <h4>Costruzione della valigia</h4>
      <table class="spec">
        <tr><td>Boccette 30 ml ambra + contagocce (~320)</td><td>400–650 €</td></tr>
        <tr><td>EVA nera + fresatura fori (7 moduli)</td><td>150–350 €</td></tr>
        <tr><td>Corpo valigia (legno o alluminio)</td><td>400–1.200 €</td></tr>
        <tr><td>Ferramenta (cerniere, chiusure, maniglie)</td><td>80–150 €</td></tr>
        <tr><td>Kit LED CRI95 + alimentazione USB-C</td><td>40–90 €</td></tr>
        <tr><td>Attrezzi da banco</td><td>~130 €</td></tr>
        <tr class="costo-tot"><td>Totale valigia (senza materie)</td><td>~1.100–2.500 €</td></tr>
      </table>
    </div>
    <div class="box">
      <h4>Peso e natura</h4>
      <ul>
        <li>293 boccette vuote: ~13,2 kg</li>
        <li>293 contagocce: ~2,9 kg</li>
        <li>Contenuto medio (~8 ml): ~2,2 kg</li>
        <li>Foam EVA (7 moduli): ~3–4 kg</li>
        <li>Corpo + ferramenta: ~6–10 kg</li>
        <li><b style="color:var(--gold)">Totale ~27–32 kg</b></li>
      </ul>
      <p style="margin-top:0.5rem;font-size:0.82rem;color:var(--text-dim)">
      È un atelier da banco: non vola (concentrati + alcol = liquidi infiammabili).
      Le materie prime a parte valgono ~3.300 €.</p>
    </div>
  </div>

  <h2>Prima di dare l'ordine</h2>
  <div class="box">
    <ul>
      <li>Ricevere le boccette e <b>misurare il diametro reale</b>, poi tagliare il foam (foro Ø 36–37 mm, profondità ~28–30 mm).</li>
      <li>Scegliere il corpo: <b>legno</b> impiallacciato (caldo, artigianale) o <b>alluminio</b> (leggero, tecnico).</li>
      <li>Confermare quali poche materie aggressive tenere a <b>tappo a vite</b> invece che a contagocce.</li>
      <li>Portare al maker: questo documento + <b>Mappa di riempimento</b> + <b>Dispensa ordine</b>.</li>
    </ul>
  </div>

  <h2>V2 — il "trova-boccetta" luminoso <span class="num">— dopo, non ora</span></h2>
  <p class="intro">Quello che qui fa la ricerca a schermo, la V2 lo farà nel legno:
  controller ESP32 + LED indirizzabili WS2812B, uno per slot; digiti «Cashmeran» dal
  telefono e <em>si accende lo slot C5-E2</em>. È la parte più costosa e delicata (il
  cablaggio deve reggere l'estrazione dei moduli): va aggiunta quando la v1 meccanica
  vive già sul banco. <em>Regola: v1 = valigia + luce CRI, funziona per sempre;
  v2 = modulo RGB, quando la casa è pronta.</em></p>

  <footer>
    Fonti nel repository: <em>Mappa_Riempimento_30ml.xlsx</em> ·
    <em>Valigia_Organo_Specifica.docx</em> (studio/parfums/valigia/).<br>
    Le materie vengono dall'<a href="organo.html">Organo 300</a> · la spesa dalla
    <a href="spesa.html">Dispensa</a> · le ricette dall'<a href="atelier.html">Atelier</a>.<br>
    <em>ALAKTA ANEN — la scia è memoria che cammina.</em>
  </footer>
</div>

<script>
const D = __DATI__;
const COL = D.colori;

// indicizza per cassetto
const perCas = {};
for (const [cas, slot, n, materia, fam, ml] of D.mappa) {
  (perCas[cas] = perCas[cas] || []).push({ slot, n, materia, fam, ml });
}

const FILE = ["A","B","C","D","E","F","G"];
function coloreFam(f) { return COL[f] || "#666"; }
function testoLeggibile(hex) {
  const r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);
  return (r*299+g*587+b*114)/1000 > 140 ? "#1a1400" : "#f0e8d8";
}

const cont = document.getElementById("cassetti");
for (const c of D.casetti) {
  const box = document.createElement("div");
  box.className = "cassetto";
  const perSlot = {};
  for (const b of (perCas[c.id]||[])) perSlot[b.slot] = b;
  let celle = "";
  for (const f of FILE) for (let col=1; col<=7; col++) {
    const code = f+col;
    const b = perSlot[code];
    if (b) {
      const bg = coloreFam(b.fam);
      const fg = testoLeggibile(bg);
      const nome = b.materia.length>22 ? b.materia.slice(0,21)+"…" : b.materia;
      celle += '<div class="slot" data-cas="'+c.id+'" data-code="'+code+'" '+
        'data-n="'+b.n+'" data-nome="'+b.materia.toLowerCase()+'" '+
        'style="background:'+bg+';color:'+fg+'" title="'+c.id+'-'+code+' · N°'+b.n+' · '+b.materia+' ('+b.fam+')">'+
        '<span class="cod" style="color:'+fg+';opacity:.55">'+code+'</span>'+
        '<span class="sn" style="color:'+fg+'">'+b.n+'</span>'+
        '<span class="snome" style="color:'+fg+'">'+nome+'</span></div>';
    } else {
      celle += '<div class="slot vuoto"><span class="cod">'+code+'</span></div>';
    }
  }
  box.innerHTML = '<h3>'+c.id+' · '+c.nome+'</h3><div class="cnt">'+c.n+' boccette</div>'+
    '<div class="griglia">'+celle+'</div>';
  cont.appendChild(box);
}

// legenda famiglie presenti
const fams = [...new Set(D.mappa.map(m=>m[4]))].sort();
document.getElementById("legenda").innerHTML = fams.map(f=>
  '<span><i style="background:'+coloreFam(f)+'"></i>'+f+'</span>').join("");

// ricerca: accende gli slot
const cerca = document.getElementById("cerca");
cerca.addEventListener("input", () => {
  const q = cerca.value.toLowerCase().trim();
  let acc = 0, primo = null;
  document.querySelectorAll(".slot").forEach(s => {
    s.classList.remove("acceso");
    if (!q || !s.dataset.nome) return;
    if (s.dataset.nome.includes(q) || s.dataset.n === q) {
      s.classList.add("acceso"); acc++;
      if (!primo) primo = s;
    }
  });
  const t = document.getElementById("trovato");
  if (!q) { t.textContent = ""; return; }
  if (acc === 0) { t.textContent = "nessuna materia trovata"; return; }
  const first = primo.dataset.cas + "-" + primo.dataset.code;
  t.textContent = acc === 1 ? "→ acceso: " + first
    : "→ " + acc + " slot accesi (primo: " + first + ")";
  if (primo) primo.scrollIntoView({ behavior:"smooth", block:"center" });
});

// architettura: moduli nelle ali
const sx = D.casetti.slice(0,3), dx = D.casetti.slice(3);
document.getElementById("ala-sx").innerHTML = sx.map(c=>
  '<li><b>'+c.id+'</b> '+c.nome+' <span style="color:var(--text-dim)">('+c.n+')</span></li>').join("");
document.getElementById("ala-dx").innerHTML = dx.map(c=>
  '<li><b>'+c.id+'</b> '+c.nome+' <span style="color:var(--text-dim)">('+c.n+')</span></li>').join("");
</script>
</body>
</html>
"""


if __name__ == "__main__":
    genera()
