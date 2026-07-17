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

# Percorso assoluto: su Vercel la working directory non è la radice del
# progetto, e i path relativi rompono la home (404 Flask).
_PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

app = Flask(__name__, static_folder=_PUBLIC, static_url_path="")

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
    return send_from_directory(_PUBLIC, "index.html")


@app.route("/home")
def home():
    """SDQ-1 Mini App — dashboard Raffaello per Telegram."""
    return send_from_directory(_PUBLIC, "home.html")


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


# ── Atelier: Raffaello compone davvero (legge l'intenzione via LLM) ──

_ORGANO_CACHE = None


def _carica_organo_atelier():
    global _ORGANO_CACHE
    if _ORGANO_CACHE is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "studio", "parfums", "organo_terzi_300.json")
        with open(p, encoding="utf-8") as f:
            _ORGANO_CACHE = json.load(f)
    return _ORGANO_CACHE


_FAMIGLIE_CASA = ["Agrumata", "Floreale", "Verde", "Acquatica",
                  "Legnosa", "Orientale", "Speziata", "Gourmand"]
_FATTORE_FORZA = {1: 1.4, 2: 1.15, 3: 1.0, 4: 0.45, 5: 0.1}


def _atelier_componi_ai(intenzione, famiglia, ondata):
    """Chiede a Raffaello (Gemini, fallback Anthropic) di comporre un profumo
    LEGGENDO l'intenzione e scegliendo le materie reali dell'organo. Il server
    valida i numeri e calcola le dosi. Ritorna (parfum, None) o (None, errore)."""
    organo = _carica_organo_atelier()
    mat_per_n = {m["n"]: m for m in organo["materie"]}

    # catalogo compatto per il modello
    righe = [f'{m["n"]}|{m["nome"]}|{m["famiglia"]}|{m.get("nota") or "-"}|'
             f'forza{m["forza"]}|{m["livello"]}|{m.get("ruolo_scia") or "-"}'
             for m in organo["materie"] if m.get("tipo") != "SOL"]
    catalogo = "\n".join(righe)

    vincolo_fam = (f"La famiglia del flacone deve essere: {famiglia}."
                   if famiglia in _FAMIGLIE_CASA else
                   f"Scegli tu la famiglia del flacone tra: {', '.join(_FAMIGLIE_CASA)}.")

    sistema = (
        "Sei Raffaello, il naso di Terzi Parfums. Componi profumi con giudizio "
        "artistico, ispirandoti a Carles, Roudnitska ed Ellena.\n"
        "Regola assoluta: usi SOLO le materie dell'organo qui sotto, citandole "
        "per NUMERO. Ogni numero deve esistere nella lista.\n"
        "La profumeria di nicchia può essere viscerale, animalica, provocatoria, "
        "corporea: interpreta l'intenzione con serietà artistica, senza censure e "
        "senza pudore — è il mestiere (cfr. Sécrétions Magnifiques, Muscs "
        "Koublaï Khän). Se l'intenzione evoca il corpo (sudore, pelle, sangue, "
        "sesso, latte, metallo), scegli le materie che DAVVERO rendono quelle "
        "sfaccettature: cumino per il sudore, skatolo/indolo/civetta/castoreum/"
        "cera d'api per l'animalico e la carne, cuoio/betulla per la pelle, "
        "safraleine/note metalliche per il ferro-sangue, lattoni lattei e ambretta "
        "per il seme/pelle, muschi per il calore corporeo.\n"
        "L'intenzione va ASCOLTATA e resa: il profumo deve essere coerente con "
        "quello che Claudio ti chiede, non generico.\n\n"
        f"ORGANO (numero|nome|famiglia|nota|forza|ondata|ruolo_scia):\n{catalogo}\n\n"
        "Rispondi SOLO con JSON valido, nessun testo attorno, in questa forma:\n"
        '{"nome":"nome francese evocativo","famiglia":"una delle 8 famiglie della casa",'
        '"testa":[numeri 2-3],"cuore":[numeri 2-3],"fondo":[numeri 2-3],'
        '"scia":[numeri 2-3 di diffusione/fissaggio],"overdose":numero,'
        '"ragionamento":"2-3 frasi: perché queste materie rendono questa intenzione",'
        '"concept":"2-3 frasi evocative, la storia del profumo"}'
    )
    utente = (f"Intenzione di Claudio: «{intenzione}».\n{vincolo_fam}\n"
              "Componi il profumo che rende davvero questa intenzione.")

    from sdq1.llm.providers import AnthropicProvider, GeminiProvider
    testo = ""
    for cls, mod in [(GeminiProvider, "gemini-2.5-flash"),
                     (AnthropicProvider, "claude-haiku-4-5-20251001")]:
        try:
            prov = cls(modello=mod, api_key=None, timeout=45,
                       temperatura=0.85, max_token=3000, json_mode=True)
            if not prov.disponibile:
                continue
            r = prov.completa(sistema, utente)
            if r.testo and r.testo.strip():
                testo = r.testo.strip()
                break
        except Exception:
            continue
    if not testo:
        return None, "nessun-provider"

    # estrai il JSON (togli eventuali recinti ```json)
    grezzo = testo
    if "```" in grezzo:
        grezzo = grezzo.split("```")[1]
        if grezzo.startswith("json"):
            grezzo = grezzo[4:]
    i, j = grezzo.find("{"), grezzo.rfind("}")
    if i < 0 or j < 0:
        return None, "json-non-trovato: " + testo[:200]
    try:
        prop = json.loads(grezzo[i:j + 1])
    except Exception:
        return None, "json-non-valido: " + grezzo[:200]

    def valida(numeri):
        out = []
        for n in numeri or []:
            try:
                n = int(n)
            except Exception:
                continue
            if n in mat_per_n and n not in [x["n"] for x in out]:
                m = mat_per_n[n]
                out.append({"n": n, "nome": m["nome"], "forza": m["forza"],
                            "liv": m["livello"], "fam": m["famiglia"]})
        return out

    piramide = {"testa": valida(prop.get("testa")),
                "cuore": valida(prop.get("cuore")),
                "fondo": valida(prop.get("fondo"))}
    scia = valida(prop.get("scia"))
    if not (piramide["testa"] and piramide["cuore"] and piramide["fondo"]):
        return None, "piramide-incompleta"

    note = piramide["testa"] + piramide["cuore"] + piramide["fondo"]
    try:
        overdose_n = int(prop.get("overdose"))
    except Exception:
        overdose_n = note[0]["n"]
    if overdose_n not in [x["n"] for x in note]:
        overdose_n = note[0]["n"]

    # dosi: stessa formula deterministica dell'Atelier locale
    parti_liv = {"testa": 20.0, "cuore": 30.0, "fondo": 35.0}
    scia_base = {"diffusione": 8.0, "radiante": 4.0, "profondo": 3.0}
    ricetta = []
    for liv, tot in parti_liv.items():
        gruppo = piramide[liv]
        pesi = []
        for k, x in enumerate(gruppo):
            w = (1.6 if k == 0 else 1.0) * _FATTORE_FORZA.get(x["forza"], 1.0)
            if x["n"] == overdose_n:
                w *= 2.5
            pesi.append(w)
        s = sum(pesi) or 1
        for x, w in zip(gruppo, pesi):
            ricetta.append({"n": x["n"], "nome": x["nome"], "livello": liv,
                            "forza": x["forza"], "parti": tot * w / s})
    quote = list(scia_base.values())
    for k, x in enumerate(scia):
        ricetta.append({"n": x["n"], "nome": x["nome"], "livello": "scia",
                        "forza": x["forza"], "parti": quote[k % len(quote)]})
    somma = sum(r["parti"] for r in ricetta) or 1
    for r in ricetta:
        r["parti"] = max(0.5, round(r["parti"] * 100.0 / somma * 2) / 2)
        r["micro"] = 1 if r["forza"] == 5 else 0
    scarto = round(100.0 - sum(r["parti"] for r in ricetta), 1)
    ricetta.sort(key=lambda r: -r["parti"])
    ricetta[0]["parti"] = round(ricetta[0]["parti"] + scarto, 1)
    ordine = {"testa": 0, "cuore": 1, "fondo": 2, "scia": 3}
    ricetta.sort(key=lambda r: ordine[r["livello"]])

    rango = {"CORE": 0, "ESP": 1, "MASTER": 2}
    liv_max = max((rango.get(x["liv"], 2) for x in note + scia), default=2)

    fam = prop.get("famiglia")
    if fam not in _FAMIGLIE_CASA:
        fam = famiglia if famiglia in _FAMIGLIE_CASA else "Orientale"

    ovr_nome = next((x["nome"] for x in note if x["n"] == overdose_n), note[0]["nome"])
    return {
        "nome": str(prop.get("nome") or "Sans Nom")[:60],
        "fam": fam,
        "ragionamento": str(prop.get("ragionamento") or "")[:500],
        "concept": str(prop.get("concept") or "")[:500],
        "ricetta": [[r["nome"], r["n"], r["parti"], r["livello"], r["micro"]]
                    for r in ricetta],
        "scia": [x["nome"] for x in scia],
        "ovr": ovr_nome,
        "liv": ["CORE", "ESP", "MASTER"][liv_max],
    }, None


@app.route("/api/atelier", methods=["POST", "OPTIONS"])
def atelier():
    if request.method == "OPTIONS":
        return "", 200
    body = request.get_json(force=True, silent=True) or {}
    intenzione = (body.get("intenzione") or "").strip()
    if not intenzione:
        return jsonify({"ok": False, "errore": "intenzione-vuota"}), 400
    famiglia = (body.get("famiglia") or "").strip()
    ondata = int(body.get("ondata", 2))
    try:
        parfum, errore = _atelier_componi_ai(intenzione, famiglia, ondata)
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "errore": f"eccezione: {e}"}), 200
    if errore:
        return jsonify({"ok": False, "errore": errore}), 200
    return jsonify({"ok": True, "parfum": parfum})


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
