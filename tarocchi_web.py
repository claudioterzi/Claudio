"""Tarocchi Quantici R³∞ — Web app per Vercel.

Endpoint (Sistema A):
    GET  /           → frontend (public/index.html)
    GET  /api/mazzo  → tutte le 78 carte in JSON
    POST /api/leggi  → genera lettura da configurazione di stesa

Endpoint (Sistema B — Canone Alpha):
    GET  /alpha                 → frontend (public/alpha.html)
    GET  /api/alpha/carte       → tutte le 74 carte del Canone Alpha
    POST /api/alpha/collasso    → motore di collasso: domanda → asse+polarità+carta+significato
"""
from __future__ import annotations

import json
import os
import random
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

# ── Canone Alpha ──────────────────────────────────────────────────────────────

_ALPHA_PATH = os.path.join(os.path.dirname(__file__), "tarocchi_quantici_alpha.json")
with open(_ALPHA_PATH, encoding="utf-8") as _f:
    _ALPHA_DOC = json.load(_f)
_ALPHA_CARTE = _ALPHA_DOC["carte"]

_ASSE_KEYWORDS: dict[str, list[str]] = {
    "nord":  ["chi sono", "perché", "senso", "significato", "profondo", "dentro",
              "origine", "radice", "istinto", "anima", "inconscio", "nascosto",
              "segreto", "base", "fondamento", "paura", "arcano", "mistero"],
    "est":   ["fare", "futuro", "prossimo", "domani", "avanti", "azione",
              "iniziare", "decidere", "muoversi", "cambiare", "costruire",
              "creare", "dove vado", "cosa faccio", "passo", "dopo", "andrò",
              "devo", "dovrei", "come posso"],
    "sud":   ["sento", "emozione", "ora", "adesso", "oggi", "presente",
              "provo", "cuore", "relazione", "amore", "questo momento",
              "come sto", "mi sento", "sentire", "vivere"],
    "ovest": ["passato", "ieri", "prima", "storia", "imparato", "lezione",
              "memoria", "ricordo", "guarire", "lasciar andare", "chiudere",
              "quando", "ho fatto", "era", "stato", "finire"],
}

_OMBRA_KEYWORDS = {
    "paura", "dolore", "confusione", "perso", "difficile", "male", "crisi",
    "blocco", "problema", "conflitto", "sbaglio", "sbagliato", "fallito",
    "fallimento", "rotto", "stanco", "esausto", "buio", "abisso", "ansia",
    "angoscia", "incubo", "perduto", "disperato", "impossibile", "bloccato",
}

_ASSE_LABEL = {
    "nord":  "Nord · radice / inconscio",
    "est":   "Est · azione / futuro",
    "sud":   "Sud · emozione / presente",
    "ovest": "Ovest · riflessione / passato",
}

_CICLO_DESC = {
    "Origine":        "stadio primario — prima forma",
    "Legame":         "connessione — incontro",
    "Frattura":       "rottura — crisi necessaria",
    "Trasformazione": "cambiamento — metamorfosi",
    "Potere":         "forza interiore — volontà",
    "Visione":        "sguardo oltre — intuizione",
    "Totalità":       "integrazione — pienezza",
    "Trascendenti":   "oltre il ciclo — apertura",
}


def _determina_asse(testo: str) -> str:
    testo_l = testo.lower()
    punteggi: dict[str, int] = {a: 0 for a in _ASSE_KEYWORDS}
    for asse, kws in _ASSE_KEYWORDS.items():
        for kw in kws:
            if kw in testo_l:
                punteggi[asse] += 1
    massimo = max(punteggi.values())
    if massimo == 0:
        return "sud"
    candidati = [a for a, p in punteggi.items() if p == massimo]
    return candidati[0]


def _determina_polarita(testo: str) -> str:
    testo_l = testo.lower()
    for kw in _OMBRA_KEYWORDS:
        if kw in testo_l:
            return "ombra"
    return "luce"


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


# ── Route Sistema B — Canone Alpha ───────────────────────────────────────────

@app.route("/alpha")
def alpha_index():
    return send_from_directory("public", "alpha.html")


@app.route("/api/alpha/carte")
def alpha_carte():
    """Tutte le 74 carte del Canone Alpha."""
    return jsonify(_ALPHA_CARTE)


@app.route("/api/alpha/collasso", methods=["POST", "OPTIONS"])
def alpha_collasso():
    """Motore di collasso: domanda + contesto → carta + asse + polarità + significato.

    Body:
        {
          "domanda":  "Cosa sto evitando?",
          "contesto": "Mi sento a disagio ma non so perché.",
          "asse":     "nord",   // opzionale — se omesso viene determinato dal testo
          "polarita": "ombra"   // opzionale — se omesso viene determinato dal testo
        }
    """
    if request.method == "OPTIONS":
        return "", 200

    body = request.get_json(force=True, silent=True) or {}
    domanda  = (body.get("domanda")  or "").strip()
    contesto = (body.get("contesto") or "").strip()
    testo    = f"{domanda} {contesto}".strip()

    asse     = body.get("asse")     or _determina_asse(testo)
    polarita = body.get("polarita") or _determina_polarita(testo)

    if asse not in _ASSE_KEYWORDS:
        asse = "sud"
    if polarita not in ("luce", "ombra"):
        polarita = "luce"

    carta = random.choice(_ALPHA_CARTE)
    significato = carta[polarita][asse]

    ciclo_desc = _CICLO_DESC.get(carta["ciclo"], carta["ciclo"])

    pol_desc = "costruttiva" if polarita == "luce" else "dell'ombra"
    asse_nome = _ASSE_LABEL[asse].split("·")[1].strip()
    interp_umano = (
        f"{carta['nome']} emerge {asse_nome}, "
        f"nella polarità {pol_desc}. "
        f"Il campo che si apre: {significato}."
    )
    if domanda:
        interp_umano += (
            f" Di fronte a '{domanda}', questa carta non risponde — "
            f"indica il terreno su cui la risposta può crescere."
        )

    interp_ai = (
        f"{carta['nome']} appartiene al ciclo {carta['ciclo']} ({ciclo_desc}). "
        f"Collasso attivo: {asse.upper()} × {'LUCE' if polarita == 'luce' else 'OMBRA'} "
        f"→ '{significato}'. "
        f"Posizione nel canone: carta {carta['id']}/74."
    )

    return jsonify({
        "carta": {
            "id":     carta["id"],
            "nome":   carta["nome"],
            "simbolo": carta["simbolo"],
            "ciclo":  carta["ciclo"],
        },
        "asse":       asse,
        "polarita":   polarita,
        "significato": significato,
        "formula":    f"{carta['nome']} · {asse.capitalize()} · {polarita.capitalize()} → {significato}",
        "interpretazione": {
            "umano": interp_umano,
            "ai":    interp_ai,
        },
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(debug=True, port=port)
