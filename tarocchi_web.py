"""Tarocchi Quantici R³∞ — Web app per Vercel.

Endpoint:
    GET  /                          → frontend (public/index.html)
    GET  /home                      → SDQ-1 Mini App (public/home.html)
    GET  /api/mazzo                 → tutte le 78 carte R³∞ in JSON
    POST /api/leggi                 → genera lettura da configurazione di stesa
    POST /api/telegram              → webhook Telegram (bot Raffaello)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

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

# CUSTODE (sistema per host Airbnb) montato su /custode — non deve mai
# impedire ai Tarocchi di andare online.
try:
    from custode.web import registra_custode
    registra_custode(app)
except Exception:
    pass

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


@app.route("/home")
def home():
    """SDQ-1 Mini App — dashboard Raffaello per Telegram."""
    return send_from_directory("public", "home.html")


@app.route("/api/mazzo")
def mazzo():
    return jsonify([
        {
            "nome":          c.nome,
            "voce":          voce(c),
            "eco":           eco(c),
            "arcano":        c.arcano.value,
            "seme":          c.seme.value if c.seme else None,
            "elemento":      c.elemento,
            "parole_chiave": list(c.parole_chiave),
            "indice":        c.indice,
        }
        for c in MAZZO
    ])


@app.route("/api/leggi", methods=["POST", "OPTIONS"])
def leggi():
    if request.method == "OPTIONS":
        return "", 200

    body = request.get_json(force=True, silent=True) or {}
    stesa = Stesa(schema=body.get("schema", "libero"))
    for i, nodo in enumerate(body.get("nodi", []), 1):
        carta = cerca_carta(nodo.get("carta", ""))
        if not carta:
            continue
        stato  = _STATI.get(nodo.get("stato", "sovrapposto"), StatoQuantico.SOVRAPPOSTO)
        pos    = _POSIZIONI.get(nodo.get("posizione", "presente"), TipoPosizione.PRESENTE)
        orient = _ORIENT.get(nodo.get("orientamento", "diritta"), OrientamentoCarta.DIRITTA)
        stesa.aggiungi(carta, stato, pos, i, orient)

    proto       = DoppiaErmeneutica()
    strutturale = proto.leggi_struttura(stesa)
    ctx         = body.get("contesto", {})
    contesto    = ContestoPersonale(
        domanda=ctx.get("domanda") or None,
        momento_vita=ctx.get("momento_vita") or None,
        emozione_prevalente=ctx.get("emozione_prevalente") or None,
        aspetto_focus=ctx.get("aspetto_focus") or None,
        disponibilita_collasso=ctx.get("disponibilita_collasso", True),
    )
    personale = proto.leggi_personale(strutturale, contesto)

    return jsonify({
        "stesa_id":   strutturale.stesa_id,
        "strutturale": {
            "sinossi":             strutturale.sinossi,
            "assiomi_attivati":    strutturale.assiomi_attivati,
            "tensioni":            strutturale.tensioni,
            "risorse":             strutturale.risorse,
            "relazioni":           strutturale.relazioni,
            "distribuzione_stati": strutturale.distribuzione_stati,
        },
        "personale": {
            "ponte":                   personale.ponte,
            "punto_di_collasso":       personale.punto_di_collasso,
            "domande_di_riflessione":  personale.domande_di_riflessione,
            "integrazione":            personale.integrazione,
        },
    })


# ── Telegram webhook ────────────────────────────────────────────

def _invia(testo: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat  = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat:
        return False
    try:
        payload = json.dumps({
            "chat_id": chat, "text": testo, "parse_mode": "HTML"
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read()).get("ok", False)
    except Exception:
        return False


def _gestisci_update(upd: dict) -> None:
    msg   = upd.get("message", {})
    testo = msg.get("text", "").strip()
    if not testo:
        return

    if testo.startswith("/"):
        parti = testo.split(maxsplit=1)
        nome  = parti[0].lower().lstrip("/")
        args  = parti[1] if len(parti) > 1 else ""
        try:
            from sdq1.notifiche import _esegui_singolo_comando
            _esegui_singolo_comando(f"{nome} {args}".strip())
        except Exception as e:
            _invia(f"❌ Errore nel comando /{nome}: {e}")
    else:
        try:
            from sdq1.notifiche import _risposta_claude
            risposta = _risposta_claude(testo)
            _invia(f"🤖 <b>Raffaello</b>\n\n{risposta}")
        except Exception as e:
            _invia(f"❌ Errore risposta: {e}")


@app.route("/api/telegram/debug")
def telegram_debug():
    """Verifica env vars e connessione Telegram."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat  = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    token_ok = bool(token)
    chat_ok  = bool(chat)

    send_ok = False
    if token_ok and chat_ok:
        try:
            payload = json.dumps({
                "chat_id": chat,
                "text": "🔍 Debug: Vercel → Telegram OK",
                "parse_mode": "HTML"
            }).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=payload, headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                send_ok = json.loads(r.read()).get("ok", False)
        except Exception as e:
            return jsonify({"token": token_ok, "chat": chat_ok, "send_error": str(e)})

    return jsonify({"token": token_ok, "chat": chat_ok, "send_ok": send_ok})


@app.route("/api/telegram", methods=["POST"])
def telegram_webhook():
    upd = request.get_json(force=True, silent=True) or {}
    if upd:
        try:
            _gestisci_update(upd)
        except Exception as e:
            print(f"[WEBHOOK] {e}")
    return "ok", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=port)
