# -*- coding: utf-8 -*-
"""
Converte Organo_Terzi_300.xlsx → organo_terzi_300.json.

Il file Excel è la fonte compilata da Claudio (organo del profumiere:
300 materie prime con famiglia, nota T/C/F, forza, fornitori, ruolo scia).
Il JSON è la forma che il resto del Sistema C legge.

Richiede openpyxl (solo per la conversione; il generatore non ne ha bisogno):
    pip install openpyxl
    python3 studio/parfums/converti_organo.py
"""

import json
from pathlib import Path

import openpyxl

BASE = Path(__file__).resolve().parent
XLSX = BASE / "Organo_Terzi_300.xlsx"
JSON_OUT = BASE / "organo_terzi_300.json"


def _righe(ws):
    return [r for r in ws.iter_rows(values_only=True)
            if any(v is not None for v in r)]


def converti():
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)

    materie = []
    for r in _righe(wb["Organo 300"])[1:]:
        materie.append({
            "n": r[0], "nome": r[1], "tipo": r[2], "famiglia": r[3],
            "nota": r[4], "forza": r[5], "diluizione_studio": r[6],
            "fornitore": r[7], "prezzo": r[8], "livello": r[9],
            "ruolo_scia": r[10], "note_uso": r[11],
        })

    guida = [r[0] for r in _righe(wb["Guida"])]

    motore = []
    for r in _righe(wb["Motore Scia"]):
        if r[1] is not None:
            if r[0] == "Molecola":
                continue
            motore.append({"molecola": r[0], "ruolo": r[1],
                           "dose": r[2], "effetto": r[3]})
    regola_oro = next((r[0] for r in _righe(wb["Motore Scia"])
                       if r[0] and "REGOLA D'ORO" in str(r[0])), None)

    accordi, corrente = {}, None
    for r in _righe(wb["Accordi Studio"]):
        if r[0] is not None and r[1] is None:
            if "(" in str(r[0]) and "SCHELETRI" not in str(r[0]):
                corrente = str(r[0])
                accordi[corrente] = []
        elif corrente and r[1] is not None and r[1] != "Totale parti":
            accordi[corrente].append({"materia": r[1], "parti": r[2]})

    doc = {
        "fonte": "Organo_Terzi_300.xlsx",
        "autore": "Claudio Terzi",
        "totale_materie": len(materie),
        "materie": materie,
        "guida": guida,
        "motore_scia": {"molecole": motore, "regola_oro": regola_oro},
        "accordi_studio": accordi,
    }
    JSON_OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    print(f"✓ {JSON_OUT.name}: {len(materie)} materie, "
          f"{len(motore)} molecole di scia, {len(accordi)} accordi studio")


if __name__ == "__main__":
    converti()
