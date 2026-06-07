#!/usr/bin/env python3
"""
Generatore Scheda Palestra HTML - App MVP
Genera una pagina web con le schede esercizi (foto macchinario, peso, ripetizioni)
e lo Strength Score gamificato. Peso e reps si salvano in locale (localStorage).

Uso:
    python cli/genera_scheda.py
    python cli/genera_scheda.py --output /percorso/scheda.html
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lgai_core.piano_palestra import PianoPalestra, TipoGiorno


GIORNI_META = {
    TipoGiorno.FORZA:      {"label": "A · Forza",      "colore": "#e53935", "emoji": "🔴"},
    TipoGiorno.IPERTROFIA: {"label": "B · Ipertrofia", "colore": "#fbc02d", "emoji": "🟡"},
    TipoGiorno.METABOLICO: {"label": "C · Metabolico", "colore": "#43a047", "emoji": "🟢"},
}


def costruisci_dati(piano: PianoPalestra) -> list:
    """Estrae i dati del piano in struttura serializzabile per il JS."""
    giorni = []
    for tipo, sessione in piano.giorni.items():
        meta = GIORNI_META[tipo]
        esercizi = []
        for es in sessione.esercizi:
            esercizi.append({
                "nome": es.nome,
                "gruppo": es.gruppo.value,
                "icona": es.icona,
                "serie": es.serie,
                "reps": es.reps_str,
                "riposo": es.riposo_str,
                "note": es.note,
                "immagine": es.immagine,  # slot foto: vuoto = segnaposto
                "peso_suggerito": es.peso_iniziale_kg,
            })
        giorni.append({
            "id": tipo.name,
            "label": meta["label"],
            "colore": meta["colore"],
            "emoji": meta["emoji"],
            "durata": sessione.durata_stimata_min,
            "descrizione": sessione.descrizione,
            "cardio": sessione.focus_cardio,
            "esercizi": esercizi,
        })
    return giorni


def genera_html(piano: PianoPalestra) -> str:
    dati = costruisci_dati(piano)
    dati_json = json.dumps(dati, ensure_ascii=False)

    return """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>💪 Scheda Palestra - Body Recomposition</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, system-ui, "Segoe UI", Roboto, sans-serif;
    background: #0f1115; color: #e8eaed; padding: 16px; max-width: 720px; margin: 0 auto;
  }
  h1 { font-size: 1.4rem; margin-bottom: 4px; }
  .sub { color: #9aa0a6; font-size: .85rem; margin-bottom: 18px; }

  /* Strength Score */
  .score-box {
    background: linear-gradient(135deg,#1d2230,#11141b);
    border:1px solid #2a2f3a; border-radius:16px; padding:16px; margin-bottom:20px;
  }
  .score-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
  .score-val { font-size:2rem; font-weight:700; }
  .score-lvl { font-size:.9rem; color:#9aa0a6; }
  .score-bar { height:10px; background:#2a2f3a; border-radius:6px; overflow:hidden; }
  .score-fill { height:100%; background:linear-gradient(90deg,#43a047,#fbc02d,#e53935); width:0%; transition:width .5s; }
  .subscores { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; font-size:.75rem; color:#c5c8cc; }
  .subscores span { background:#2a2f3a; padding:3px 8px; border-radius:8px; }

  /* Tabs giorni */
  .tabs { display:flex; gap:8px; margin-bottom:16px; }
  .tab { flex:1; padding:10px; border-radius:12px; text-align:center; cursor:pointer;
    background:#1a1d24; border:2px solid transparent; font-weight:600; font-size:.85rem; }
  .tab.active { border-color: var(--c); }

  .day-desc { font-size:.82rem; color:#9aa0a6; margin-bottom:14px; line-height:1.4; }

  /* Card esercizio */
  .card {
    background:#1a1d24; border-radius:16px; overflow:hidden; margin-bottom:14px; border:1px solid #262a33;
  }
  .photo {
    position:relative; height:170px; background:#11141b;
    display:flex; align-items:center; justify-content:center; cursor:pointer;
    border-bottom:1px solid #262a33;
  }
  .photo img { width:100%; height:100%; object-fit:cover; }
  .photo .placeholder { text-align:center; color:#5f6470; }
  .photo .placeholder .ic { font-size:3rem; }
  .photo .placeholder .txt { font-size:.72rem; margin-top:6px; }
  .badge { position:absolute; top:10px; left:10px; background:rgba(0,0,0,.65);
    padding:4px 10px; border-radius:20px; font-size:.72rem; }

  .body { padding:14px; }
  .name { font-size:1.05rem; font-weight:700; margin-bottom:4px; }
  .note { font-size:.78rem; color:#9aa0a6; margin-bottom:12px; line-height:1.35; }

  .stats { display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; }
  .stat { background:#11141b; border-radius:10px; padding:8px; text-align:center; }
  .stat label { display:block; font-size:.65rem; color:#7a808c; text-transform:uppercase; letter-spacing:.5px; margin-bottom:4px; }
  .stat .v { font-size:1.1rem; font-weight:700; }
  .stat input { width:100%; background:#0f1115; border:1px solid #2a2f3a; color:#fff;
    border-radius:8px; padding:6px; text-align:center; font-size:1.05rem; font-weight:700; }
  .stat input:focus { outline:none; border-color:#43a047; }

  .footer { text-align:center; color:#5f6470; font-size:.72rem; margin-top:24px; line-height:1.5; }
</style>
</head>
<body>
  <h1>💪 Scheda Palestra</h1>
  <div class="sub">Body Recomposition · DUP 3×/settimana · livello intermedio</div>

  <!-- STRENGTH SCORE -->
  <div class="score-box">
    <div class="score-head">
      <div>
        <div class="score-val" id="scoreVal">0<span style="font-size:1rem;color:#7a808c">/1000</span></div>
        <div class="score-lvl" id="scoreLvl">🥚 Principiante</div>
      </div>
      <div style="text-align:right">
        <div style="font-size:.72rem;color:#7a808c">PESO CORPOREO</div>
        <input id="bw" type="number" value="75" style="width:80px;background:#0f1115;border:1px solid #2a2f3a;color:#fff;border-radius:8px;padding:6px;text-align:center;font-weight:700">
        <span style="color:#7a808c">kg</span>
      </div>
    </div>
    <div class="score-bar"><div class="score-fill" id="scoreFill"></div></div>
    <div class="subscores" id="subscores"></div>
    <div style="font-size:.68rem;color:#5f6470;margin-top:8px">
      Lo Strength Score usa i carichi che inserisci su Squat, Stacco, Panca, Military Press e Rematore.
    </div>
  </div>

  <div class="tabs" id="tabs"></div>
  <div class="day-desc" id="dayDesc"></div>
  <div id="exercises"></div>

  <div class="footer">
    📸 Tocca una foto per aggiungere l'immagine del macchinario.<br>
    💾 Peso e ripetizioni si salvano automaticamente sul tuo dispositivo.<br>
    Parte del sistema LGAI · Life Game AI
  </div>

<script>
const DATA = __DATI__;

// Mappa nome esercizio -> lift dello Strength Score
const LIFT_MAP = {
  "Squat Bilanciere":"Squat",
  "Stacco da Terra":"Stacco",
  "Panca Piana Bilanciere":"Panca",
  "Military Press Bilanciere":"Military Press",
  "Rematore Bilanciere / Manubri":"Rematore"
};
const STANDARD = {"Squat":1.5,"Stacco":1.75,"Panca":1.25,"Military Press":0.8,"Rematore":1.0};

const store = {
  get(k, d){ const v = localStorage.getItem("gym_"+k); return v===null?d:v; },
  set(k, v){ localStorage.setItem("gym_"+k, v); }
};

let giornoAttivo = DATA[0].id;

function key(ex, campo){ return ex.nome.replace(/\\s+/g,"_")+"_"+campo; }

function renderTabs(){
  const t = document.getElementById("tabs");
  t.innerHTML = "";
  DATA.forEach(g=>{
    const d = document.createElement("div");
    d.className = "tab" + (g.id===giornoAttivo?" active":"");
    d.style.setProperty("--c", g.colore);
    d.innerHTML = g.emoji+"<br>"+g.label;
    d.onclick = ()=>{ giornoAttivo=g.id; render(); };
    t.appendChild(d);
  });
}

function renderExercises(){
  const g = DATA.find(x=>x.id===giornoAttivo);
  document.getElementById("dayDesc").innerHTML =
     "⏱️ ~"+g.durata+" min · "+g.descrizione + (g.cardio?"<br>🏃 "+g.cardio:"");
  const box = document.getElementById("exercises");
  box.innerHTML = "";

  g.esercizi.forEach(ex=>{
    const card = document.createElement("div");
    card.className = "card";

    const imgSaved = store.get(key(ex,"img"), ex.immagine||"");
    const peso = store.get(key(ex,"peso"), ex.peso_suggerito||"");
    const reps = store.get(key(ex,"reps"), "");

    card.innerHTML = `
      <div class="photo" data-k="${key(ex,'img')}">
        <span class="badge">${ex.gruppo}</span>
        ${imgSaved
          ? `<img src="${imgSaved}" alt="${ex.nome}">`
          : `<div class="placeholder"><div class="ic">${ex.icona}</div>
             <div class="txt">📸 Tocca per aggiungere foto macchinario</div></div>`}
      </div>
      <div class="body">
        <div class="name">${ex.nome}</div>
        <div class="note">💡 ${ex.note}</div>
        <div class="stats">
          <div class="stat"><label>Serie</label><div class="v">${ex.serie}</div></div>
          <div class="stat"><label>Peso (kg)</label>
            <input type="number" inputmode="decimal" placeholder="—" value="${peso}" data-k="${key(ex,'peso')}"></div>
          <div class="stat"><label>Ripetizioni</label>
            <input type="text" inputmode="numeric" placeholder="${ex.reps}" value="${reps}" data-k="${key(ex,'reps')}"></div>
        </div>
      </div>`;
    box.appendChild(card);
  });

  // foto: chiedi URL
  box.querySelectorAll(".photo").forEach(p=>{
    p.onclick = ()=>{
      const url = prompt("Incolla l'URL della foto del macchinario\\n(lascia vuoto per rimuovere):", "");
      if(url!==null){ store.set(p.dataset.k, url); render(); }
    };
  });

  // input: salva e aggiorna score
  box.querySelectorAll("input[data-k]").forEach(inp=>{
    inp.onclick = e=>e.stopPropagation();
    inp.oninput = ()=>{ store.set(inp.dataset.k, inp.value); calcScore(); };
  });
}

function calcScore(){
  const bw = parseFloat(document.getElementById("bw").value)||0;
  store.set("bw", bw);
  let totale = 0;
  const subs = [];
  for(const [exNome, lift] of Object.entries(LIFT_MAP)){
    const carico = parseFloat(store.get(key({nome:exNome},"peso"),"0"))||0;
    let s = 0;
    if(bw>0){ s = Math.min(200, Math.round((carico/bw)/STANDARD[lift]*200)); }
    totale += s;
    subs.push(`${lift}: ${s}`);
  }
  let lvl = "🥚 Principiante";
  if(totale>=800) lvl="🏆 Elite";
  else if(totale>=600) lvl="💪 Avanzato";
  else if(totale>=400) lvl="🔥 Intermedio";
  else if(totale>=200) lvl="🌱 Novizio";

  document.getElementById("scoreVal").innerHTML = totale+'<span style="font-size:1rem;color:#7a808c">/1000</span>';
  document.getElementById("scoreLvl").textContent = lvl;
  document.getElementById("scoreFill").style.width = (totale/10)+"%";
  document.getElementById("subscores").innerHTML = subs.map(s=>`<span>${s}</span>`).join("");
}

function render(){ renderTabs(); renderExercises(); calcScore(); }

document.getElementById("bw").value = store.get("bw","75");
document.getElementById("bw").oninput = calcScore;
render();
</script>
</body>
</html>""".replace("__DATI__", dati_json)


def main():
    parser = argparse.ArgumentParser(description="Genera la scheda palestra HTML")
    default_out = os.path.join(os.path.dirname(__file__), "..", "scheda_palestra.html")
    parser.add_argument("--output", default=default_out, help="Percorso file HTML di output")
    args = parser.parse_args()

    piano = PianoPalestra()
    html = genera_html(piano)

    out = os.path.abspath(args.output)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Scheda generata: {out}")
    print("   Aprila nel browser (anche da telefono). Peso e reps si salvano in locale.")


if __name__ == "__main__":
    main()
