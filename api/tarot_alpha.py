"""Raffaello · Canone Alpha 74 — lettura unica.

Un solo mazzo: tarocchi_quantici_alpha.json.
Formula canonica: CARTA + ASSE + POLARITA = SIGNIFICATO.
Luce/Ombra sono equiprobabili (50/50) nelle estrazioni automatiche.

Claudio Terzi · C.Terzi
"""
from __future__ import annotations

import json
import os
import re
import secrets
import uuid

from flask import Flask, jsonify, request

app = Flask(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALPHA_PATH = os.path.join(ROOT, "tarocchi_quantici_alpha.json")

POSITIONS = [
    ("passato", "Passato", "ovest"),
    ("presente", "Presente", "sud"),
    ("futuro", "Futuro", "est"),
    ("ostacolo", "Ostacolo", "nord"),
    ("potenziale", "Potenziale", "est"),
    ("consiglio", "Consiglio", "nord"),
    ("esito", "Esito", "est"),
]
VALID_AXES = {"nord", "est", "sud", "ovest"}
VALID_POLARITIES = {"luce", "ombra"}


def _deck():
    with open(ALPHA_PATH, encoding="utf-8") as f:
        cards = json.load(f)["carte"]
    if len(cards) != 74:
        raise RuntimeError(f"Canone Alpha non valido: attese 74 carte, trovate {len(cards)}")
    return cards


def _clean(v, n):
    return str(v or "").strip()[:n]


def _polarity():
    return "luce" if secrets.randbelow(2) == 0 else "ombra"


def _safe_json(text):
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None


def _normalize_items(body):
    deck = _deck()
    by_name = {c["nome"]: c for c in deck}
    items = body.get("carte_scelte")
    automatic = not isinstance(items, list) or not items
    if automatic:
        count = int(body.get("numero_carte") or 3)
        count = 3 if count not in {3, 5, 7} else count
        chosen = secrets.SystemRandom().sample(deck, count)
        items = []
        for i, card in enumerate(chosen):
            pos, label, axis = POSITIONS[i]
            items.append({"carta": card["nome"], "posizione": pos, "posizione_label": label, "asse": axis, "polarita": _polarity()})
    if not 1 <= len(items) <= 7:
        raise ValueError("La stesa deve contenere da 1 a 7 carte.")

    seen = set()
    out = []
    for i, raw in enumerate(items):
        name = _clean(raw.get("carta"), 120)
        card = by_name.get(name)
        if not card:
            raise ValueError(f"Carta non presente nel Canone Alpha: {name}")
        if name in seen:
            raise ValueError("La stessa carta non può comparire due volte.")
        seen.add(name)
        default_pos, default_label, default_axis = POSITIONS[min(i, len(POSITIONS)-1)]
        pos = _clean(raw.get("posizione"), 30) or default_pos
        label = _clean(raw.get("posizione_label"), 50) or default_label
        axis = _clean(raw.get("asse"), 20).lower() or default_axis
        if axis not in VALID_AXES:
            axis = default_axis
        polarity = _clean(raw.get("polarita"), 20).lower()
        if polarity not in VALID_POLARITIES:
            polarity = _polarity()
        meaning = card[polarity][axis]
        out.append({
            "id": card["id"], "carta": name, "simbolo": card["simbolo"], "ciclo": card["ciclo"],
            "posizione": pos, "posizione_label": label, "asse": axis, "polarita": polarity,
            "significato_canonico": meaning,
        })
    return out, automatic


def _fallback(cards, question):
    lines = []
    for c in cards:
        lines.append(f"{c['posizione_label']}: {c['carta']} in {c['polarita'].capitalize()} sull'asse {c['asse'].capitalize()} — {c['significato_canonico']}.")
    base = " ".join(lines)
    if question:
        opening = f"Sulla tua domanda, io leggerei questa stesa così: {base}"
    else:
        opening = f"Come fotografia simbolica del momento, io leggerei questa stesa così: {base}"
    return {
        "messaggio": opening + " Il filo comune non è una previsione certa: è il tema che emerge mettendo in relazione queste posizioni.",
        "nodo": cards[-1]["significato_canonico"] if cards else "",
        "direzione": "Osserva quale di questi significati trova un riscontro concreto nella tua situazione e usa quello come punto di partenza.",
        "domanda_finale": "Quale passaggio della stesa descrive con più precisione ciò che stai vivendo adesso?",
        "carte": [{"posizione": c["posizione_label"], "carta": c["carta"], "lettura": c["significato_canonico"]} for c in cards],
        "livello": "CANONICAL_FALLBACK",
    }


def _ai(cards, question, context):
    system = """Sei Raffaello, interprete del Canone Alpha di Claudio Terzi.
Questo NON è un mazzo di tarocchi tradizionale. Non esistono Spade, Coppe, Bastoni, Denari o Arcani classici.
Usi soltanto le 74 carte del Canone Alpha e la formula: CARTA + ASSE + POLARITA = SIGNIFICATO.
Ogni significato canonico ti viene fornito esplicitamente e NON va sostituito con significati inventati.
Luce e Ombra hanno pari dignità: Ombra non significa automaticamente male; indica la manifestazione d'ombra del simbolo.
Leggi la relazione fra le carte e parla direttamente all'utente con chiarezza, calore e precisione.
Non presentare simboli come prove di fatti nascosti o previsioni certe. Se inferisci qualcosa, formulalo come possibilità.

OUTPUT SOLO JSON valido:
{
 "messaggio":"un messaggio continuo di 6-12 frasi, in prima persona come Raffaello, che spiega la stesa nel suo insieme",
 "nodo":"il nodo centrale in 2-4 frasi",
 "direzione":"direzione concreta ma non prescrittiva in 2-4 frasi",
 "domanda_finale":"una sola domanda molto precisa",
 "carte":[{"posizione":"...","carta":"...","lettura":"spiegazione chiara del significato canonico nel contesto"}],
 "livello":"AI_ALPHA_CONTEXTUAL"
}"""
    user = json.dumps({"domanda": question or None, "contesto": context or None, "carte": cards}, ensure_ascii=False)
    try:
        from sdq1.llm.providers import GeminiProvider, AnthropicProvider
    except Exception:
        return None, None
    providers = [
        (GeminiProvider, "gemini-2.5-flash", {"json_mode": True, "temperatura": 0.5, "max_token": 3000, "timeout": 30}),
        (AnthropicProvider, "claude-haiku-4-5-20251001", {"temperatura": 0.45, "max_token": 3000, "timeout_secondi": 30}),
    ]
    for cls, model, opts in providers:
        try:
            p = cls(modello=model, api_key=None, **opts)
            if not p.disponibile:
                continue
            r = p.completa(system, user)
            if r.errore:
                continue
            data = _safe_json(r.testo)
            if isinstance(data, dict) and data.get("messaggio"):
                return data, {"provider": r.provider, "modello": r.modello, "via_api": r.via_api}
        except Exception:
            continue
    return None, None


def _response():
    if request.method == "OPTIONS":
        return "", 200
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"errore": "Serve un oggetto JSON."}), 400
    try:
        cards, automatic = _normalize_items(body)
    except (ValueError, RuntimeError) as exc:
        return jsonify({"errore": str(exc)}), 400
    question = _clean(body.get("domanda"), 1800)
    context = _clean(body.get("contesto"), 3200)
    reading, engine = _ai(cards, question, context)
    if reading is None:
        reading = _fallback(cards, question)
        engine = {"provider": "canonical-fallback", "via_api": False}
    resp = jsonify({
        "lettura_id": str(uuid.uuid4()),
        "sistema": "Canone Alpha 74",
        "formula": "CARTA + ASSE + POLARITA = SIGNIFICATO",
        "numero_carte": len(cards),
        "estrazione": "automatica" if automatic else "manuale",
        "polarita": "50/50 Luce/Ombra",
        "carte": cards,
        "lettura": reading,
        "motore": engine,
        "epistemica": "INTERPRETAZIONE_SIMBOLICA_NON_PREVISIONE_CERTA",
    })
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/api/tarocchi/alpha-leggi", methods=["POST", "OPTIONS"])
def alpha_read():
    return _response()


@app.route("/", methods=["POST", "OPTIONS"])
def root():
    return _response()
