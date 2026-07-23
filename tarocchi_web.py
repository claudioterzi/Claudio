"""Tarocchi Quantici R³∞ — Web app per Vercel.

Endpoint:
    GET  /                        → frontend (public/index.html)
    GET  /api/mazzo               → tutte le 74 carte in JSON
    POST /api/leggi               → genera lettura da configurazione di stesa
    GET  /viaggi                  → frontend Viaggi Low Cost (public/viaggi.html)
    GET  /api/viaggi/destinazioni → catalogo destinazioni low cost
    POST /api/viaggi/pianifica    → proposte di viaggio da budget/giorni/mese/tipo
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

from viaggi import DESTINAZIONI, MESI, TIPI, pianifica
from flight_hunter import (
    caccia as fh_caccia,
    consulta as fh_consulta,
    ovunque as fh_ovunque,
)

app = Flask(__name__, static_folder="public", static_url_path="")


def _ora(iso: str) -> str:
    return iso[11:16] if len(iso) >= 16 else "?"


def _itinerario_web(it) -> dict:
    return {
        "tipo": it.tipo,
        "rischio": it.rischio,
        "totale": it.totale,
        "costo_voli": it.costo_voli,
        "costo_terra": it.costo_terra,
        "costo_bagagli": it.costo_bagagli,
        "costo_notti": it.costo_notti,
        "margine_rischio": it.margine_rischio,
        "note": it.note,
        "voli": [
            {"da": v.da, "a": v.a, "giorno": v.giorno,
             "ora_partenza": _ora(v.partenza), "ora_arrivo": _ora(v.arrivo),
             "prezzo": v.prezzo, "vettore": v.vettore}
            for v in it.voli
        ],
    }

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


@app.route("/viaggi")
def viaggi_index():
    return send_from_directory("public", "viaggi.html")


@app.route("/api/viaggi/destinazioni")
def viaggi_destinazioni():
    """Catalogo completo delle destinazioni low cost."""
    return jsonify({
        "tipi": list(TIPI),
        "mesi": list(MESI),
        "destinazioni": [
            {
                "nome": d.nome,
                "paese": d.paese,
                "tipi": list(d.tipi),
                "budget_giorno": d.budget_giorno,
                "volo_ar": d.volo_ar,
                "mesi_ideali": list(d.mesi_ideali),
                "partenze": list(d.partenze),
                "perche": d.perche,
                "consigli": list(d.consigli),
            }
            for d in DESTINAZIONI
        ],
    })


@app.route("/api/viaggi/pianifica", methods=["POST", "OPTIONS"])
def viaggi_pianifica():
    """Proposte di viaggio ordinate per aderenza a budget/giorni/mese/tipo.

    Body:
        {
          "budget": 300,          // € totali per persona
          "giorni": 4,
          "mese": 9,              // 1-12, opzionale
          "tipo": ["mare"],       // sottoinsieme di TIPI, opzionale
          "solo_nel_budget": false
        }
    """
    if request.method == "OPTIONS":
        return "", 200

    body = request.get_json(force=True, silent=True) or {}
    try:
        budget = int(body.get("budget", 0))
        giorni = int(body.get("giorni", 3))
    except (TypeError, ValueError):
        return jsonify({"errore": "budget e giorni devono essere numeri"}), 400

    mese = body.get("mese")
    mese = int(mese) if mese not in (None, "", 0, "0") else None
    if mese is not None and not 1 <= mese <= 12:
        return jsonify({"errore": "mese deve essere tra 1 e 12"}), 400

    tipo = body.get("tipo") or ()
    if isinstance(tipo, str):
        tipo = (tipo,)
    tipo = tuple(t for t in tipo if t in TIPI)

    origine = (body.get("origine") or "").strip()
    override_volo = None
    origine_ok = False
    nota_origine = None
    if origine:
        override_volo, origine_ok, nota_origine = _prezzi_volo_da_origine(origine, mese)

    proposte = pianifica(
        budget=budget, giorni=giorni, mese=mese, tipo=tipo,
        solo_nel_budget=bool(body.get("solo_nel_budget", False)),
        override_volo=override_volo,
    )
    return jsonify({
        "budget": budget,
        "giorni": giorni,
        "mese": MESI[mese - 1] if mese else None,
        "tipi": list(tipo),
        "origine": origine or None,
        "origine_ok": origine_ok,
        "nota_origine": nota_origine,
        "proposte": [p.dizionario() for p in proposte],
    })


def _prezzi_volo_da_origine(origine: str, mese):
    """Prezzi VERI dei voli dalla città dell'utente (Flight Hunter), mappati
    sulle mete via IATA (A/R ≈ andata × 2). Ritorna (override|None, ok, nota)."""
    from datetime import date
    from viaggi import IATA
    oggi = date.today()
    if mese:
        anno = oggi.year if mese >= oggi.month else oggi.year + 1
        mese_yyyymm = f"{anno}-{mese:02d}"
    else:
        m = oggi.month % 12 + 1
        anno = oggi.year if m != 1 else oggi.year + 1
        mese_yyyymm = f"{anno}-{m:02d}"
    try:
        mete = fh_ovunque(origine, mese_yyyymm, top=400)
    except ValueError:
        return None, False, f"Non riconosco «{origine}» come città di partenza: uso stime generiche."
    except Exception:
        return None, False, "Prezzi live non raggiungibili ora: uso stime generiche."
    prezzo_per_iata = {m.iata: m.prezzo_volo for m in mete}
    override = {nome: round(prezzo_per_iata[iata] * 2)
                for nome, iata in IATA.items() if iata in prezzo_per_iata}
    if not override:
        return None, True, (f"Da {origine} nessuna di queste mete è servita diretta "
                            "nel periodo: mostro le stime generiche.")
    return override, True, None


@app.route("/oracolo")
def oracolo_index():
    return send_from_directory("public", "oracolo.html")


@app.route("/api/flight/oracolo", methods=["POST", "OPTIONS"])
def flight_oracolo():
    """L'Oracolo del Viaggio: da una città, nei prossimi giorni, la fuga migliore."""
    if request.method == "OPTIONS":
        return "", 200
    body = request.get_json(force=True, silent=True) or {}
    origine = (body.get("origine") or "").strip()
    if not origine:
        return jsonify({"errore": "serve una città di partenza ('origine')"}), 400
    try:
        giorni = max(2, min(30, int(body.get("giorni_avanti", 10))))
        raggio = float(body.get("raggio", 250))
    except (TypeError, ValueError):
        return jsonify({"errore": "giorni_avanti e raggio devono essere numeri"}), 400
    budget = body.get("budget")
    try:
        budget = float(budget) if budget else None
    except (TypeError, ValueError):
        budget = None
    try:
        r = fh_consulta(origine, giorni_avanti=giorni, budget=budget,
                        raggio_origine=raggio,
                        bagaglio=bool(body.get("bagaglio", False)))
    except ValueError as e:
        return jsonify({"errore": str(e)}), 400
    return jsonify(r.dizionario())


@app.route("/flight")
def flight_index():
    return send_from_directory("public", "flight_hunter.html")


@app.route("/api/flight/ovunque", methods=["POST", "OPTIONS"])
def flight_ovunque():
    """Ricerca per obiettivo: tutte le mete raggiungibili nel mese entro budget.
    Poche richieste (una mappa tariffe per aeroporto di partenza): veloce."""
    if request.method == "OPTIONS":
        return "", 200
    body = request.get_json(force=True, silent=True) or {}
    origine = (body.get("origine") or "").strip()
    mese = (body.get("mese") or "").strip()
    if not origine or len(mese) != 7:
        return jsonify({"errore": "servono 'origine' e 'mese' (YYYY-MM)"}), 400
    budget = body.get("budget")
    try:
        budget = float(budget) if budget else None
        raggio = float(body.get("raggio", 250))
    except (TypeError, ValueError):
        return jsonify({"errore": "budget e raggio devono essere numeri"}), 400
    try:
        mete = fh_ovunque(origine, mese, budget=budget, raggio_origine=raggio,
                          bagaglio=bool(body.get("bagaglio", False)), top=60)
    except ValueError as e:
        return jsonify({"errore": str(e)}), 400
    return jsonify({
        "origine": origine, "mese": mese, "budget": budget,
        "mete": [
            {"iata": m.iata, "nome": m.nome, "paese": m.paese, "da": m.da,
             "prezzo_volo": m.prezzo_volo, "costo_terra": m.costo_terra,
             "costo_bagagli": m.costo_bagagli, "totale": m.totale}
            for m in mete
        ],
    })


@app.route("/api/flight/caccia", methods=["POST", "OPTIONS"])
def flight_caccia():
    """Caccia su rotta (versione web: hub ridotti per stare nei tempi serverless)."""
    if request.method == "OPTIONS":
        return "", 200
    body = request.get_json(force=True, silent=True) or {}
    origine = (body.get("origine") or "").strip()
    dest = (body.get("destinazione") or "").strip()
    mese = (body.get("mese") or "").strip()
    if not origine or not dest or len(mese) != 7:
        return jsonify({"errore": "servono 'origine', 'destinazione' e 'mese' (YYYY-MM)"}), 400
    try:
        raggio = float(body.get("raggio", 250))
    except (TypeError, ValueError):
        return jsonify({"errore": "raggio deve essere un numero"}), 400
    try:
        itinerari = fh_caccia(
            origine, dest, mese,
            raggio_origine=raggio, bagaglio=bool(body.get("bagaglio", False)),
            hub_max=4, top=8, profondo=False,
        )
    except ValueError as e:
        return jsonify({"errore": str(e)}), 400
    return jsonify({
        "origine": origine, "destinazione": dest, "mese": mese,
        "itinerari": [_itinerario_web(it) for it in itinerari],
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(debug=True, port=port)
