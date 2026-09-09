# -*- coding: utf-8 -*-
"""
L'ATELIER DI RAFFAELLO — genera `public/atelier.html`
=====================================================

Rigenera la pagina corrente dal template condiviso, con invio nativo
all'Atelier AI e compositore didattico locale opzionale.

  - Organo Terzi 300 incorporato (materie reali, T/C/F, forza, ondate)
  - Grimorio: motore di scia in 3 pezzi, regola d'oro dell'overdose,
    MAI un muschio solo (blend automatico), forza 5 in microdose
  - Maestri: Carles (12 materie, fondo strutturato), Ellena (formula
    corta, 8 materie), Roudnitska (silhouette: cuore dominante)
  - Guida: avvisi IFRA sulle materie critiche
  - Determinismo di casa: l'INTENZIONE è il seme — la stessa domanda
    genera sempre la stessa proposta (collasso, come nel Canone Alpha)

La selezione predefinita comprende l'intero organo. Il template mantiene
campi cliente/riferimento, stile, scelta delle essenze e invio POST.

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


PAGINA = (BASE / "atelier_template.html").read_text(encoding="utf-8")

if __name__ == "__main__":
    genera()
