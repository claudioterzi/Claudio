"""Tarocchi Quantici R³∞ — Web app per Vercel.

Endpoint:
    GET  /           → frontend (public/index.html)
    GET  /api/mazzo  → tutte le 74 carte in JSON
    POST /api/leggi  → genera lettura da configurazione di stesa
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, request, send_from_directory

from tarocchi import (
    MAZZO,
    ContestoPersonale,
    DoppiaErmeneutica,
    OrientamentoCarta,
    Stesa,
    StatoQuantico,
    TipoPosizione,
    cerca_carta,
    eco,
    voce,
)

app = Flask(__name__, static_folder="public", static_url_path="")

_STATI      = {s.value: s for s in StatoQuantico}
_POSIZIONI  = {p.value: p for p in TipoPosizione}
_ORIENT     = {o.value: o for o in OrientamentoCarta}


@app.after_request
def _cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/")
def index():
    return send_from_directory("public", "index.html")


@app.route("/api/mazzo")
def mazzo():
    """Restituisce tutte le 74 carte. voce() è il nome per le letture."""
    return jsonify([
        {
            "nome":         c.nome,
            "voce":         voce(c),
            "eco":          eco(c),
            "arcano":       c.arcano.value,
            "seme":         c.seme.value if c.seme else None,
            "elemento":     c.elemento,
            "parole_chiave": list(c.parole_chiave),
            "indice":       c.indice,
        }
        for c in MAZZO
    ])


@app.route("/api/leggi", methods=["POST", "OPTIONS"])
def leggi():
    """Genera lettura strutturale + personale da una stesa in JSON.

    Body:
        {
          "nodi": [
            {
              "carta": "Il Matto",          // nome carta (ricerca case-insensitive)
              "stato": "sovrapposto",        // sovrapposto | collassato | entangled
              "posizione": "presente",       // presente | passato | futuro | ...
              "orientamento": "diritta"      // diritta | rovescia
            },
            ...
          ],
          "schema": "tre_carte",
          "contesto": {
            "domanda": "Cosa sto diventando?",
            "momento_vita": "...",
            "emozione_prevalente": "...",
            "aspetto_focus": "crescita",
            "disponibilita_collasso": true
          }
        }
    """
    if request.method == "OPTIONS":
        return "", 200

    body = request.get_json(force=True, silent=True) or {}

    stesa = Stesa(schema=body.get("schema", "libero"))
    for i, nodo in enumerate(body.get("nodi", []), 1):
        carta = cerca_carta(nodo.get("carta", ""))
        if not carta:
            continue
        stato   = _STATI.get(nodo.get("stato", "sovrapposto"), StatoQuantico.SOVRAPPOSTO)
        pos     = _POSIZIONI.get(nodo.get("posizione", "presente"), TipoPosizione.PRESENTE)
        orient  = _ORIENT.get(nodo.get("orientamento", "diritta"), OrientamentoCarta.DIRITTA)
        stesa.aggiungi(carta, stato, pos, i, orient)

    proto = DoppiaErmeneutica()
    strutturale = proto.leggi_struttura(stesa)

    ctx = body.get("contesto", {})
    contesto = ContestoPersonale(
        domanda=ctx.get("domanda") or None,
        momento_vita=ctx.get("momento_vita") or None,
        emozione_prevalente=ctx.get("emozione_prevalente") or None,
        aspetto_focus=ctx.get("aspetto_focus") or None,
        disponibilita_collasso=ctx.get("disponibilita_collasso", True),
    )
    personale = proto.leggi_personale(strutturale, contesto)

    return jsonify({
        "stesa_id": strutturale.stesa_id,
        "strutturale": {
            "sinossi":              strutturale.sinossi,
            "assiomi_attivati":     strutturale.assiomi_attivati,
            "tensioni":             strutturale.tensioni,
            "risorse":              strutturale.risorse,
            "relazioni":            strutturale.relazioni,
            "distribuzione_stati":  strutturale.distribuzione_stati,
        },
        "personale": {
            "ponte":                    personale.ponte,
            "punto_di_collasso":        personale.punto_di_collasso,
            "domande_di_riflessione":   personale.domande_di_riflessione,
            "integrazione":             personale.integrazione,
        },
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(debug=True, port=port)
