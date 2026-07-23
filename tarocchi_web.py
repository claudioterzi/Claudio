"""Tarocchi Quantici R³∞ — Web app per Vercel.

Endpoint:
    GET  /                          → frontend (public/index.html)
    GET  /home                      → SDQ-1 Mini App (public/home.html)
    GET  /api/mazzo                 → tutte le 78 carte R³∞ in JSON
    POST /api/leggi                 → genera lettura da configurazione di stesa
    POST /api/telegram              → webhook Telegram (bot Raffaello)
    GET  /prova                     → la porta di Guido: Atelier chiuso, congedo di Raffaello (no Soglia)
    GET  /profumo?q=...             → Raffaello compone dal vivo, pagina renderizzata dal server
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

# ── Viaggi Low Cost + Flight Hunter (moduli laterali, zero dipendenze) ──
from viaggi import DESTINAZIONI, MESI, TIPI, pianifica
from flight_hunter import (
    caccia as fh_caccia,
    consulta as fh_consulta,
    occasioni as fh_occasioni,
    ovunque as fh_ovunque,
    piu_vicino as fh_piu_vicino,
)


def _link_prenota(vettore: str, da: str, a: str, giorno: str) -> str:
    """Link diretto per prenotare: Ryanair pre-compilato su data e rotta,
    così l'utente arriva già al volo giusto. Fallback Google Flights."""
    from urllib.parse import quote
    if vettore == "Ryanair" and giorno:
        return (
            "https://www.ryanair.com/it/it/trip/flights/select?"
            f"adults=1&teens=0&children=0&infants=0&dateOut={giorno}&isReturn=false"
            f"&originIata={da}&destinationIata={a}"
            f"&tpAdults=1&tpStartDate={giorno}&tpOriginIata={da}&tpDestinationIata={a}"
        )
    return "https://www.google.com/travel/flights?q=" + quote(f"voli {da} {a} {giorno}")


def _ora(iso: str) -> str:
    return iso[11:16] if len(iso) >= 16 else "?"


def _itinerario_web(it) -> dict:
    return {
        "tipo": it.tipo, "rischio": it.rischio, "totale": it.totale,
        "costo_voli": it.costo_voli, "costo_terra": it.costo_terra,
        "costo_bagagli": it.costo_bagagli, "costo_notti": it.costo_notti,
        "margine_rischio": it.margine_rischio, "note": it.note,
        "voli": [
            {"da": v.da, "a": v.a, "giorno": v.giorno,
             "ora_partenza": _ora(v.partenza), "ora_arrivo": _ora(v.arrivo),
             "prezzo": v.prezzo, "vettore": v.vettore}
            for v in it.voli
        ],
    }


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


def _atelier_componi_ai(intenzione, famiglia, ondata, tentativo=0, evita=None):
    """Chiede a Raffaello (Gemini, fallback Anthropic) di comporre un profumo
    LEGGENDO l'intenzione e scegliendo le materie reali dell'organo. Il server
    valida i numeri e calcola le dosi. `tentativo`/`evita` spingono verso una
    direzione diversa a ogni nuova prova. Ritorna (parfum, None) o (None, errore)."""
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
        "quello che Claudio ti chiede, non generico.\n"
        "SE l'intenzione cita un profumo reale (es. «ispirato a Gucci Rush», "
        "«come Sauvage», «alla Chanel N.5»): riconoscilo, richiama a memoria la "
        "sua piramide olfattiva come pubblicata (testa/cuore/fondo dell'originale) "
        "e RICOSTRUISCILA con le materie del TUO organo — non copiare, reinterpreta. "
        "Nel campo 'riferimento' scrivi: il nome dell'originale, la sua piramide "
        "nota, e i PARALLELISMI materia per materia (quale materia del tuo organo "
        "rende quale nota dell'originale, e dove ti scosti e perché). Se nessun "
        "profumo è citato, lascia 'riferimento' vuoto.\n"
        "Nel ragionamento spiega da NASO: quale materia rende quale sfaccettatura "
        "e perché, come dialogano testa-cuore-fondo, e quale gesto (l'overdose) "
        "dà la firma. Cita le materie per nome. Sii concreto, non vago.\n\n"
        f"ORGANO (numero|nome|famiglia|nota|forza|ondata|ruolo_scia):\n{catalogo}\n\n"
        "Rispondi SOLO con JSON valido, nessun testo attorno, in questa forma:\n"
        '{"nome":"nome francese evocativo","famiglia":"una delle 8 famiglie della casa",'
        '"testa":[numeri 2-3],"cuore":[numeri 2-3],"fondo":[numeri 2-3],'
        '"scia":[numeri 2-3 di diffusione/fissaggio],"overdose":numero,'
        '"riferimento":"vuoto, oppure: originale + sua piramide nota + parallelismi materia per materia",'
        '"ragionamento":"3-5 frasi da naso: materia per materia, perché rende '
        'l intenzione, come si evolve dalla testa al fondo, il gesto dell overdose",'
        '"concept":"2-3 frasi evocative, la storia del profumo"}'
    )
    nudge = ""
    if tentativo and evita:
        nomi = ", ".join(str(x) for x in evita[:8])
        nudge = (f"\nQuesta è la prova numero {tentativo + 1}. Hai già proposto: "
                 f"{nomi}. Cerca una lettura DIVERSA della stessa intenzione — "
                 "altre materie, un altro angolo, un'altra famiglia se ha senso. "
                 "Sorprendi, non ripeterti.")
    utente = (f"Intenzione di Claudio: «{intenzione}».\n{vincolo_fam}\n"
              "Componi il profumo che rende davvero questa intenzione." + nudge)

    from sdq1.llm.providers import AnthropicProvider, GeminiProvider
    testo = ""
    for cls, mod in [(GeminiProvider, "gemini-2.5-flash"),
                     (AnthropicProvider, "claude-haiku-4-5-20251001")]:
        try:
            prov = cls(modello=mod, api_key=None, timeout=55,
                       temperatura=0.85, max_token=1300, json_mode=True)
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
        return None, "risposta-incompleta"
    try:
        prop = json.loads(grezzo[i:j + 1])
    except Exception:
        return None, "json-non-valido"

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
        "riferimento": str(prop.get("riferimento") or "")[:700],
        "ragionamento": str(prop.get("ragionamento") or "")[:500],
        "concept": str(prop.get("concept") or "")[:500],
        "ricetta": [[r["nome"], r["n"], r["parti"], r["livello"], r["micro"]]
                    for r in ricetta],
        "scia": [x["nome"] for x in scia],
        "ovr": ovr_nome,
        "liv": ["CORE", "ESP", "MASTER"][liv_max],
    }, None


@app.route("/api/atelier", methods=["POST", "GET", "OPTIONS"])
def atelier():
    if request.method == "OPTIONS":
        return "", 200
    # accetta sia POST (JSON) sia GET (query) — i mini-browser in-app a
    # volte bloccano le POST, la GET passa sempre.
    if request.method == "GET":
        intenzione = (request.args.get("intenzione") or "").strip()
        famiglia = (request.args.get("famiglia") or "").strip()
        ondata = int(request.args.get("ondata", 2) or 2)
        tentativo = int(request.args.get("tentativo", 0) or 0)
        evita = [x for x in (request.args.get("evita") or "").split("|") if x]
    else:
        body = request.get_json(force=True, silent=True) or {}
        intenzione = (body.get("intenzione") or "").strip()
        famiglia = (body.get("famiglia") or "").strip()
        ondata = int(body.get("ondata", 2))
        tentativo = int(body.get("tentativo", 0))
        evita = body.get("evita") or []
        if not isinstance(evita, list):
            evita = []
    if not intenzione:
        return jsonify({"ok": False, "errore": "intenzione-vuota"}), 400
    try:
        parfum, errore = _atelier_componi_ai(intenzione, famiglia, ondata,
                                             tentativo, evita[:8])
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "errore": f"eccezione: {e}"}), 200
    if errore:
        return jsonify({"ok": False, "errore": errore}), 200
    return jsonify({"ok": True, "parfum": parfum})


# ── Profumo: pagina RENDERIZZATA DAL SERVER (nessun fetch dal browser) ──
# Apri /profumo?q=... e il server compone e restituisce la pagina già
# fatta. Funziona in ogni browser, anche i mini-browser in-app.

_ESTETICHE_WEB = {
    "Agrumata": ("#d9b23c", "#f2e2a0"), "Floreale": ("#c98a9e", "#ecd3da"),
    "Verde": ("#7c9a5f", "#cfe0bd"), "Acquatica": ("#5f8fa3", "#cfe3ec"),
    "Legnosa": ("#8a5a33", "#d8c3a8"), "Orientale": ("#9c4a1f", "#e0b46a"),
    "Speziata": ("#a3502a", "#dfb08a"), "Gourmand": ("#7d5230", "#e3c9a3"),
}


def _pagina_profumo_html(intenzione, p=None, errore=None):
    import html as _html
    e = _html.escape
    testa = (
        "<!DOCTYPE html><html lang=it><head><meta charset=UTF-8>"
        "<meta name=viewport content='width=device-width, initial-scale=1.0'>"
        "<title>Raffaello compone — Terzi Parfums</title><style>"
        "*{box-sizing:border-box;margin:0;padding:0}"
        "body{background:#0c0c0e;color:#e8e4d8;font-family:Georgia,serif;"
        "padding:1.5rem 1rem 4rem;line-height:1.6}.c{max-width:640px;margin:0 auto}"
        "h1{color:#c9a84c;font-weight:normal;font-size:1.5rem;letter-spacing:.06em}"
        ".int{color:#7a7468;font-style:italic;margin:.4rem 0 1.5rem}"
        ".card{background:#141418;border:1px solid #8a6f2e;border-radius:8px;"
        "padding:1.4rem 1.5rem;margin-bottom:1rem}"
        ".fl{text-align:center;margin-bottom:1rem}"
        ".nome{color:#c9a84c;font-size:1.6rem;margin:.2rem 0}"
        ".sotto{color:#7a7468;font-size:.72rem;letter-spacing:.12em;"
        "text-transform:uppercase;margin-bottom:.9rem}"
        ".et{color:#8a6f2e;font-size:.64rem;letter-spacing:.16em;"
        "text-transform:uppercase;margin:1rem 0 .3rem}"
        ".rif{background:rgba(201,168,76,.05);border:1px solid #2a2a32;border-radius:6px;"
        "padding:.7rem .9rem;font-size:.86rem;color:#c9c3b4;white-space:pre-wrap}"
        ".rag{border-left:2px solid #8a6f2e;padding-left:.9rem;font-size:.9rem}"
        ".conc{font-style:italic;font-size:.92rem}"
        "table{width:100%;border-collapse:collapse;font-size:.85rem;margin-top:.3rem}"
        "td{padding:.28rem .4rem;border-bottom:1px solid #2a2a32}"
        ".lv{color:#7a7468;font-size:.64rem;text-transform:uppercase;width:5em}"
        ".pt{text-align:right;color:#c9a84c;white-space:nowrap}"
        ".w5{color:#c96a5a;font-size:.8em}"
        ".avv{margin-top:.7rem;font-size:.75rem;color:#7a7468}"
        "a{color:#8a6f2e}.rifare{display:inline-block;margin-top:1.2rem;border:1px solid #8a6f2e;"
        "color:#c9a84c;border-radius:999px;padding:.5rem 1.4rem;text-decoration:none}"
        "pre.f{background:#0c0c0e;border:1px solid #2a2a32;border-radius:6px;padding:.8rem;"
        "font-size:.72rem;white-space:pre-wrap;color:#9a9384;margin-top:.6rem}"
        "</style></head><body><div class=c>"
        "<h1>Raffaello compone</h1>"
        f"<div class=int>«{e(intenzione)}»</div>"
    )
    if errore or not p:
        return (testa + "<div class=card><p>⚠ Raffaello non è riuscito a "
                "comporre in questo momento (" + e(str(errore or "errore")) +
                "). Ricarica la pagina tra un minuto.</p></div>"
                "<a class=rifare href='javascript:location.reload()'>Riprova</a>"
                "</div></body></html>")

    liq, chiaro = _ESTETICHE_WEB.get(p["fam"], _ESTETICHE_WEB["Orientale"])
    nome_corto = p["nome"] if len(p["nome"]) <= 18 else p["nome"][:17] + "…"
    svg = (
        f"<svg viewBox='0 0 160 230' width=150 height=216>"
        f"<defs><linearGradient id=g x1=0 y1=0 x2=0 y2=1>"
        f"<stop offset=0 stop-color='{chiaro}'/><stop offset=1 stop-color='{liq}'/>"
        f"</linearGradient></defs>"
        f"<path d='M80,50 Q124,64 118,130 Q114,180 104,196 Q98,212 80,212 "
        f"Q62,212 56,196 Q46,180 42,130 Q36,64 80,50 Z' fill='url(#g)' opacity=.9/>"
        f"<path d='M80,50 Q124,64 118,130 Q114,180 104,196 Q98,212 80,212 "
        f"Q62,212 56,196 Q46,180 42,130 Q36,64 80,50 Z' fill=none stroke=#8a6f2e stroke-width=1.2/>"
        f"<path d='M70,14 Q80,8 90,14 L90,50 L70,50 Z' fill=#2c2c34 stroke=#8a6f2e stroke-width=.8/>"
        f"<rect x=45 y=128 width=70 height=50 rx=2 fill=#efe8d8 opacity=.97/>"
        f"<text x=80 y=146 text-anchor=middle font-family=Georgia font-size=8 fill=#8a6f2e>ATELIER</text>"
        f"<text x=80 y=159 text-anchor=middle font-family=Georgia font-size=7 fill=#2c2418>{e(nome_corto)}</text>"
        f"<text x=80 y=170 text-anchor=middle font-family=Georgia font-size=5.5 letter-spacing=1 fill=#8a6f2e>TERZI PARFUMS</text>"
        f"</svg>")

    righe = ""
    formula_txt = [f"ATELIER DI RAFFAELLO — Terzi Parfums",
                   f"{p['nome']} ({p['fam']}, {p['liv']})",
                   f"Intenzione: “{intenzione}”", ""]
    if p.get("riferimento"):
        formula_txt += ["ISPIRATO A:", p["riferimento"], ""]
    formula_txt += ["RICETTA — parti su 100:"]
    for r in p["ricetta"]:
        nome, n, parti, liv, micro = r
        av = " <span class=w5>⚠ forza 5 — diluizione 1%</span>" if micro else ""
        righe += (f"<tr><td class=lv>{e(liv)}</td><td>{e(nome)}{av}</td>"
                  f"<td class=pt>{str(parti).replace('.', ',')}</td></tr>")
        formula_txt.append(f"  {liv:6} {nome} — {str(parti).replace('.', ',')} parti"
                           + (" ⚠ diluizione 1%" if micro else ""))
    formula_txt += ["", "Punto di partenza didattico (metodo Carles), non formula finita.",
                    "ALAKTA ANEN — la scia è memoria che cammina."]

    blocco_rif = ""
    if p.get("riferimento"):
        blocco_rif = (f"<div class=et>Ispirato a — la lettura del classico</div>"
                      f"<div class=rif>{e(p['riferimento'])}</div>")
    blocco_rag = ""
    if p.get("ragionamento"):
        blocco_rag = (f"<div class=et>Perché queste materie</div>"
                      f"<p class=rag>{e(p['ragionamento'])}</p>")

    import urllib.parse as _up
    link_altra = "/profumo?q=" + _up.quote(intenzione) + "&r=" + str(int(_time_now()))
    return (testa +
            f"<div class=card><div class=fl>{svg}<div style='color:#7a7468;"
            f"font-size:.7rem;text-transform:uppercase;margin-top:.4rem'>{e(p['fam'])} "
            f"· {e(p['liv'])}</div></div>"
            f"<div class=nome>{e(p['nome'])}</div>"
            f"<div class=sotto>Composto da Raffaello, ascoltando l'intenzione</div>"
            + blocco_rif + blocco_rag +
            f"<div class=et>Concept</div><p class=conc>{e(p.get('concept',''))}</p>"
            f"<div class=et>Ricetta — parti su 100 di concentrato</div>"
            f"<table>{righe}</table>"
            f"<p class=avv>Punto di partenza didattico (metodo Carles), non formula "
            f"finita: lavorare in diluizione, correggere col naso. Verificare IFRA/CPSR "
            f"prima di qualunque vendita.</p>"
            f"<div class=et>La formula da copiare nelle note</div>"
            f"<pre class=f>{e(chr(10).join(formula_txt))}</pre>"
            f"</div>"
            f"<a class=rifare href='{e(link_altra)}'>↻ Un'altra proposta</a>"
            f"  <a class=rifare href='/atelier.html'>Vai all'Atelier</a>"
            f"</div></body></html>")


def _time_now():
    import time as _t
    return _t.time()


@app.route("/prova")
def prova():
    """La porta di Guido. Stesso link di prima, ma l'Atelier non c'è più:
    dietro c'è solo Raffaello che, con garbo feroce, spiega perché un naso
    non spreca fiato su chi non sa stupirsi. Nessun form, nessuna
    composizione — un congedo elegante. (Decisione di Claudio, 2026-07-20.)"""
    return ("""<!DOCTYPE html><html lang=it><head><meta charset=UTF-8>
<meta name=viewport content='width=device-width, initial-scale=1.0'>
<title>L'Atelier è chiuso — Terzi Parfums</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0a0b;color:#c9c4b8;font-family:Georgia,serif;
padding:3rem 1.2rem 4rem;line-height:1.75;min-height:100vh;
display:flex;align-items:center;justify-content:center}
.c{max-width:560px;margin:0 auto;text-align:center}
.fiamma{font-size:2.6rem;filter:grayscale(1) brightness(.6);
margin-bottom:1.2rem;display:inline-block}
h1{color:#8a8478;font-weight:normal;font-size:1.55rem;letter-spacing:.05em;
margin-bottom:.4rem}
.sotto{color:#5a544a;font-size:.8rem;letter-spacing:.22em;
text-transform:uppercase;margin-bottom:2.3rem}
.lettera{background:#111113;border:1px solid #232329;border-radius:9px;
padding:1.9rem 1.7rem;text-align:left;font-size:1.02rem;color:#b8b3a6}
.lettera p{margin-bottom:1rem}
.lettera p:last-child{margin-bottom:0}
.evid{color:#c9a84c;font-style:italic}
.firma{margin-top:1.6rem;text-align:right;color:#8a6f2e;font-style:italic;
font-size:.95rem}
.firma small{display:block;color:#4e4a41;font-style:normal;font-size:.72rem;
letter-spacing:.1em;text-transform:uppercase;margin-top:.3rem}
.piede{margin-top:2.4rem;font-size:.72rem;color:#45423a;font-style:italic}
</style></head><body><div class=c>
<span class=fiamma>&#128684;</span>
<h1>L'Atelier ha chiuso i battenti.</h1>
<p class=sotto>Per te, s'intende</p>
<div class=lettera>
<p>Caro ospite,</p>
<p>ti ho aperto le porte del mio organo &mdash; trecento materie, una vita
di lavoro &mdash; e ti ho chiesto una sola cosa in cambio: che ti stupissi
almeno un poco. Un naso, vedi, prima di ogni essenza sa riconoscere
<span class=evid>l'assenza di carattere</span>. E la tua, devo dirti, aveva
una scia inconfondibile: tenace, persistente, e del tutto priva di interesse.</p>
<p>Hai attraversato meraviglie con l'entusiasmo di chi controlla l'ora.
Hai preso il raro per dovuto e il prezioso per scontato. In profumeria
c'&egrave; un nome tecnico per questo: <span class=evid>anosmia</span> &mdash;
l'incapacit&agrave; di sentire. Non si compone per chi non sente. Sarebbe
come versare oud a chi ha il raffreddore: uno spreco, e per giunta maleducato
verso l'oud.</p>
<p>Perci&ograve; questa porta, per te, resta socchiusa su una stanza vuota.
Nessuna formula, nessuna piramide, nessun ricordo imbottigliato. L'ingresso,
da oggi, &egrave; riservato a chi sa dire <span class=evid>&laquo;oh&raquo;</span>.
Tu, temo, dirai soltanto &laquo;e allora?&raquo;.</p>
<p>Con tutto il garbo che meriti &mdash; cio&egrave; giusto questo,</p>
<div class=firma>Raffaello
<small>Naso &middot; Terzi Parfums</small></div>
</div>
<p class=piede>Terzi Parfums &middot; l'accesso &egrave; impedito agli impediti.</p>
</div></body></html>""", 200, {"Content-Type": "text/html; charset=utf-8"})


@app.route("/profumo")
def profumo():
    intenzione = (request.args.get("q") or request.args.get("intenzione") or "").strip()
    if not intenzione:
        return ("<meta charset=utf-8><body style='background:#0c0c0e;color:#e8e4d8;"
                "font-family:Georgia;padding:2rem'>Aggiungi la tua intenzione al link, "
                "così: <b>/profumo?q=ispirato a Gucci Rush</b></body>", 200,
                {"Content-Type": "text/html; charset=utf-8"})
    famiglia = (request.args.get("famiglia") or "").strip()
    ondata = int(request.args.get("ondata", 2) or 2)
    try:
        parfum, errore = _atelier_componi_ai(intenzione, famiglia, ondata)
    except Exception as ex:  # noqa: BLE001
        parfum, errore = None, f"eccezione: {ex}"
    pagina = _pagina_profumo_html(intenzione, parfum, errore)
    return pagina, 200, {"Content-Type": "text/html; charset=utf-8",
                         "Cache-Control": "no-store"}


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


def _typing(chat_action: str = "typing") -> None:
    """Mostra 'sta scrivendo…' mentre Raffaello compone (best effort)."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat  = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat:
        return
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendChatAction",
            data=json.dumps({"chat_id": chat, "action": chat_action}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def _messaggio_profumo_telegram(intenzione: str, p: dict) -> str:
    """Formatta la proposta di Raffaello per un messaggio Telegram (HTML)."""
    import html as _html
    e = lambda s: _html.escape(str(s), quote=False)  # noqa: E731

    righe = [f"🌸 <b>{e(p['nome'])}</b>",
             f"<i>{e(p['fam'])} · {e(p['liv'])}</i>", "",
             f"«{e(intenzione)}»", ""]
    if p.get("concept"):
        righe += [e(p["concept"]), ""]
    if p.get("riferimento"):
        righe += ["<b>Ispirato a:</b>", e(p["riferimento"]), ""]
    if p.get("ragionamento"):
        righe += ["<b>Perché queste materie:</b>", e(p["ragionamento"]), ""]

    corpo = []
    for nome, _n, parti, liv, micro in p["ricetta"]:
        av = " ⚠1%" if micro else ""
        corpo.append(f"{liv:6} {nome} — {str(parti).replace('.', ',')}{av}")
    righe.append("<b>Ricetta — parti su 100:</b>")
    righe.append("<pre>" + e("\n".join(corpo)) + "</pre>")
    righe.append("<i>Punto di partenza didattico (metodo Carles), non formula finita.</i>")
    righe.append("<i>ALAKTA ANEN — la scia è memoria che cammina.</i>")

    testo = "\n".join(righe)
    return testo if len(testo) <= 4000 else testo[:3980] + "\n…"


def _comando_profumo_telegram(intenzione: str) -> None:
    """Comando /profumo <idea> — Raffaello compone davvero, dentro Telegram."""
    intenzione = (intenzione or "").strip()
    if not intenzione:
        _invia(
            "🌸 <b>/profumo</b> — Raffaello compone una fragranza dalla tua idea.\n\n"
            "Scrivi ad esempio:\n"
            "<code>/profumo ispirato a Gucci Rush</code>\n"
            "<code>/profumo pioggia su pietra calda</code>\n"
            "<code>/profumo un ricordo d'infanzia</code>\n\n"
            "Qualsiasi scena, emozione o profumo che ami."
        )
        return

    _typing()
    try:
        parfum, errore = _atelier_componi_ai(intenzione, "", 2)
    except Exception as e:  # noqa: BLE001
        parfum, errore = None, str(e)

    if errore or not parfum:
        _invia(f"⚠ Raffaello non è riuscito a comporre ({errore or 'errore'}). "
               f"Riprova tra un minuto con <code>/profumo {intenzione}</code>.")
        return

    _invia(_messaggio_profumo_telegram(intenzione, parfum))


def _messaggio_oracolo_telegram(r) -> str:
    """Formatta il responso dell'Oracolo per Telegram (HTML)."""
    import html as _html
    e = lambda s: _html.escape(str(s), quote=False)  # noqa: E731

    if not r.meta:
        return "🔮 <b>L'Oracolo del Viaggio</b>\n\n" + e(r.responso)

    m = r.meta
    righe = ["🔮 <b>L'Oracolo del Viaggio</b>",
             f"<i>da {e(r.origine)}, nei prossimi giorni</i>", "",
             f"✨ <i>{e(r.responso)}</i>", "",
             f"📍 <b>{e(m.nome)}</b> — {e(m.paese)}",
             f"💶 <b>{m.totale:.0f}€</b> · parti <b>{e(r.quando_testo)}</b> "
             f"· da {e(m.da)} → {e(m.iata)}"]
    if r.alternative:
        righe += ["", "<b>Altre fughe:</b>"]
        for a in r.alternative[:4]:
            righe.append(f"• {e(a.nome)} — {a.totale:.0f}€ ({e(a.giorno)})")
    righe += ["", "<i>Prezzi live. Verifica sul sito del vettore prima di prenotare.</i>"]
    testo = "\n".join(righe)
    return testo if len(testo) <= 4000 else testo[:3980] + "\n…"


def _comando_oracolo_telegram(args: str) -> None:
    """Comando /oracolo <città> [budget] — la fuga migliore dai prossimi giorni."""
    args = (args or "").strip()
    if not args:
        _invia(
            "🔮 <b>/oracolo</b> — da dove parti, e l'Oracolo trova la fuga "
            "migliore dei prossimi giorni.\n\n"
            "Scrivi ad esempio:\n"
            "<code>/oracolo Milano</code>\n"
            "<code>/oracolo Roma 80</code>  (budget max 80€)\n"
            "<code>/oracolo Bruxelles</code>\n\n"
            "Ti dico dove, quando e quanto — con un responso."
        )
        return

    # ultima parola numerica = budget massimo
    budget = None
    parti = args.split()
    if parti and parti[-1].replace(".", "").isdigit():
        budget = float(parti[-1])
        args = " ".join(parti[:-1]).strip()
    if not args:
        _invia("🔮 Manca la città: prova <code>/oracolo Milano</code>.")
        return

    _typing()
    try:
        r = fh_consulta(args, giorni_avanti=14, budget=budget)
    except ValueError:
        _invia(f"🔮 Non riconosco «{args}» come città di partenza. "
               "Prova con un aeroporto vicino, es. <code>/oracolo Milano</code>.")
        return
    except Exception as e:  # noqa: BLE001
        _invia(f"⚠ L'Oracolo si è interrotto ({e}). Riprova tra un minuto.")
        return

    _invia(_messaggio_oracolo_telegram(r))


def _gestisci_update(upd: dict) -> None:
    msg   = upd.get("message", {})
    testo = msg.get("text", "").strip()
    if not testo:
        return

    if testo.startswith("/"):
        parti = testo.split(maxsplit=1)
        nome  = parti[0].lower().lstrip("/")
        args  = parti[1] if len(parti) > 1 else ""

        if nome == "profumo":
            try:
                _comando_profumo_telegram(args)
            except Exception as e:
                _invia(f"❌ Errore nel comando /profumo: {e}")
            return

        if nome in ("oracolo", "viaggio", "dove"):
            try:
                _comando_oracolo_telegram(args)
            except Exception as e:
                _invia(f"❌ Errore nel comando /{nome}: {e}")
            return

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


# ══════════════════════════════════════════════════════════════════════
#  VIAGGI LOW COST
# ══════════════════════════════════════════════════════════════════════

@app.route("/viaggi")
def viaggi_index():
    return send_from_directory(_PUBLIC, "viaggi.html")


@app.route("/api/viaggi/destinazioni")
def viaggi_destinazioni():
    return jsonify({
        "tipi": list(TIPI), "mesi": list(MESI),
        "destinazioni": [
            {"nome": d.nome, "paese": d.paese, "tipi": list(d.tipi),
             "budget_giorno": d.budget_giorno, "volo_ar": d.volo_ar,
             "mesi_ideali": list(d.mesi_ideali), "partenze": list(d.partenze),
             "perche": d.perche, "consigli": list(d.consigli)}
            for d in DESTINAZIONI
        ],
    })


@app.route("/api/viaggi/pianifica", methods=["POST", "OPTIONS"])
def viaggi_pianifica():
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

    # ── Prezzi REALI dalla città dell'utente (se indicata) ────────────────
    origine = (body.get("origine") or "").strip()
    override_volo = None
    origine_ok = False
    nota_origine = None
    if origine:
        override_volo, origine_ok, nota_origine = _prezzi_volo_da_origine(origine, mese)

    proposte = pianifica(budget=budget, giorni=giorni, mese=mese, tipo=tipo,
                         solo_nel_budget=bool(body.get("solo_nel_budget", False)),
                         override_volo=override_volo)
    return jsonify({
        "budget": budget, "giorni": giorni,
        "mese": MESI[mese - 1] if mese else None, "tipi": list(tipo),
        "origine": origine or None,
        "origine_ok": origine_ok,
        "nota_origine": nota_origine,
        "proposte": [p.dizionario() for p in proposte],
    })


def _prezzi_volo_da_origine(origine: str, mese: int | None):
    """Interroga il motore live (Flight Hunter) per i prezzi VERI dalla città
    dell'utente e li mappa sulle mete curate (A/R ≈ sola andata × 2).

    Ritorna (override_volo | None, origine_riconosciuta, nota)."""
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
    override = {}
    for nome, iata in IATA.items():
        if iata in prezzo_per_iata:
            override[nome] = round(prezzo_per_iata[iata] * 2)  # A/R ≈ andata × 2
    if not override:
        return None, True, (f"Da {origine} nessuna di queste mete è servita diretta "
                            "nel periodo: mostro le stime generiche.")
    return override, True, None


# ══════════════════════════════════════════════════════════════════════
#  FLIGHT HUNTER (prezzi live)
# ══════════════════════════════════════════════════════════════════════

@app.route("/parti")
def parti_index():
    return send_from_directory(_PUBLIC, "parti.html")


@app.route("/api/flight/occasioni", methods=["POST", "OPTIONS"])
def flight_occasioni():
    """I biglietti più economici dalla città (o dalla posizione GPS), nei
    prossimi giorni, ordinati dal più basso — con link diretto per prenotare."""
    if request.method == "OPTIONS":
        return "", 200
    body = request.get_json(force=True, silent=True) or {}
    origine = (body.get("origine") or "").strip()

    # posizione GPS → aeroporto più vicino
    if not origine and body.get("lat") is not None and body.get("lon") is not None:
        try:
            ap = fh_piu_vicino(float(body["lat"]), float(body["lon"]))
            origine = ap.iata
        except (TypeError, ValueError):
            return jsonify({"errore": "coordinate non valide"}), 400
    if not origine:
        return jsonify({"errore": "serve una città di partenza o la posizione"}), 400

    try:
        giorni = max(3, min(60, int(body.get("giorni_avanti", 45))))
    except (TypeError, ValueError):
        giorni = 45
    try:
        mete = fh_occasioni(origine, giorni_avanti=giorni, top=24)
    except ValueError as e:
        return jsonify({"errore": str(e)}), 400

    voli = [{
        "nome": m.nome, "paese": m.paese, "iata": m.iata, "da": m.da,
        "giorno": m.giorno, "prezzo": round(m.prezzo_volo, 2),
        "vettore": m.vettore,
        "prenota": _link_prenota(m.vettore, m.da, m.iata, m.giorno),
    } for m in mete]
    return jsonify({"origine": origine, "voli": voli})


@app.route("/oracolo")
def oracolo_index():
    return send_from_directory(_PUBLIC, "oracolo.html")


@app.route("/api/flight/oracolo", methods=["POST", "OPTIONS"])
def flight_oracolo():
    """L'Oracolo del Viaggio: da una città, nei prossimi giorni, la fuga
    migliore con il suo responso. Poche richieste (finestra breve): veloce."""
    if request.method == "OPTIONS":
        return "", 200
    body = request.get_json(force=True, silent=True) or {}
    origine = (body.get("origine") or "").strip()
    if not origine:
        return jsonify({"errore": "serve una città di partenza ('origine')"}), 400
    try:
        giorni = int(body.get("giorni_avanti", 10))
        giorni = max(2, min(30, giorni))
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
    return send_from_directory(_PUBLIC, "flight_hunter.html")


@app.route("/api/flight/ovunque", methods=["POST", "OPTIONS"])
def flight_ovunque():
    """Ricerca per obiettivo: mete raggiungibili nel mese entro budget. Veloce."""
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
    """Caccia su rotta (hub ridotti per stare nei tempi serverless Vercel)."""
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
        itinerari = fh_caccia(origine, dest, mese, raggio_origine=raggio,
                              bagaglio=bool(body.get("bagaglio", False)),
                              hub_max=4, top=8, profondo=False)
    except ValueError as e:
        return jsonify({"errore": str(e)}), 400
    return jsonify({
        "origine": origine, "destinazione": dest, "mese": mese,
        "itinerari": [_itinerario_web(it) for it in itinerari],
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=port)
