"""Raffaello · Lettura Tarocchi

Raffaello sceglie la profondità della stesa, estrae le carte con casualità
criptograficamente robusta, le dispone nella grammatica R³∞, produce la lettura
strutturale e chiede a un LLM disponibile una sintesi contestuale.

Principio epistemico: il simbolo può generare ipotesi e riflessioni, non fatti
privati non osservati né previsioni certe.

Claudio Terzi · C.Terzi
"""
from __future__ import annotations

import json
import re
import secrets
import uuid
from dataclasses import asdict

from flask import Flask, jsonify, request

from tarocchi import (
    MAZZO,
    ContestoPersonale,
    DoppiaErmeneutica,
    OrientamentoCarta,
    Stesa,
    StatoQuantico,
    TipoPosizione,
    eco,
    voce,
)

app = Flask(__name__)

_FOCUS = {"amore", "lavoro", "crescita", "creativita", "creatività", "relazioni", "salute", "denaro", "altro", ""}

_LAYOUTS = {
    3: [
        (TipoPosizione.RADICE, "Radice"),
        (TipoPosizione.PRESENTE, "Presente"),
        (TipoPosizione.CONSIGLIO, "Direzione"),
    ],
    5: [
        (TipoPosizione.RADICE, "Radice"),
        (TipoPosizione.PRESENTE, "Presente"),
        (TipoPosizione.OSTACOLO, "Nodo / ostacolo"),
        (TipoPosizione.POTENZIALE, "Potenziale"),
        (TipoPosizione.CONSIGLIO, "Direzione"),
    ],
    7: [
        (TipoPosizione.PASSATO, "Ciò che precede"),
        (TipoPosizione.PRESENTE, "Presente"),
        (TipoPosizione.OMBRA, "Ciò che resta fuori campo"),
        (TipoPosizione.OSTACOLO, "Nodo / ostacolo"),
        (TipoPosizione.POTENZIALE, "Potenziale"),
        (TipoPosizione.CONSIGLIO, "Direzione"),
        (TipoPosizione.ESITO, "Esito aperto"),
    ],
}


def _clean_text(value, limit):
    text = str(value or "").strip()
    return text[:limit]


def _depth(question: str, context: str, focus: str, requested: str) -> tuple[int, str]:
    if requested in {"3", "5", "7"}:
        n = int(requested)
        return n, f"Profondità scelta dall'utente: {n} carte."
    text = f"{question} {context}".lower()
    complex_markers = (
        "scegli", "scelta", "decision", "rapporto", "relazione", "ritorno",
        "perché", "come evol", "cosa succede", "conflitto", "blocco", "cambiamento",
        "due persone", "lavoro", "famiglia", "futuro", "separ", "ricominc",
    )
    deep_markers = ("tutto", "profondo", "completo", "intera situazione", "molto complesso", "più aspetti")
    if any(x in text for x in deep_markers) or len(text) > 900:
        return 7, "Il contesto contiene più livelli: Raffaello apre una stesa profonda a 7 carte."
    if any(x in text for x in complex_markers) or focus in {"amore", "relazioni", "lavoro", "denaro", "salute"} or len(text) > 260:
        return 5, "La domanda richiede relazioni tra più fattori: Raffaello usa 5 carte."
    return 3, "La domanda è abbastanza focalizzata: 3 carte bastano per non diluire il segnale simbolico."


def _state_for(position: TipoPosizione) -> StatoQuantico:
    if position in {TipoPosizione.RADICE, TipoPosizione.PASSATO}:
        return StatoQuantico.COLLASSATO
    if position in {TipoPosizione.PRESENTE, TipoPosizione.OMBRA, TipoPosizione.OSTACOLO}:
        return StatoQuantico.ENTANGLED
    return StatoQuantico.SOVRAPPOSTO


def _draw(n: int):
    rng = secrets.SystemRandom()
    return rng.sample(list(MAZZO), n)


def _orientation() -> OrientamentoCarta:
    # Le rovesciate sono informative ma non devono dominare la stesa.
    return OrientamentoCarta.ROVESCIA if secrets.randbelow(100) < 28 else OrientamentoCarta.DIRITTA


def _card_payload(node, label):
    c = node.carta
    return {
        "posizione": node.posizione.tipo.value,
        "posizione_label": label,
        "carta": c.nome,
        "indice": c.indice,
        "arcano": c.arcano.value,
        "seme": c.seme.value if c.seme else None,
        "elemento": c.elemento,
        "dominio": c.dominio,
        "parole_chiave": list(c.parole_chiave),
        "voce": voce(c),
        "eco": eco(c),
        "orientamento": node.orientamento.value,
        "stato": node.stato_effettivo.value,
    }


def _safe_json(text: str):
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def _fallback(personale, cards, question, focus):
    per_card = []
    for card in cards:
        orientation = "rovescia" if card["orientamento"] == "rovescia" else "diritta"
        nuance = (
            "Qui il simbolo tende a mostrarsi come energia trattenuta, interiorizzata o non ancora espressa."
            if orientation == "rovescia"
            else "Qui il simbolo è disponibile in forma più diretta e visibile."
        )
        per_card.append({
            "posizione": card["posizione_label"],
            "carta": card["carta"],
            "significato": f"{card['voce']} — {card['eco']}",
            "nel_contesto": nuance,
        })
    return {
        "apertura": "Leggo prima la struttura e poi la metto in relazione con la tua domanda, senza trasformare un simbolo in una certezza fattuale.",
        "contesto_compreso": question or (f"Focus: {focus}." if focus else "Domanda aperta."),
        "carte": per_card,
        "trama": personale.ponte,
        "tensione_centrale": personale.punto_di_collasso,
        "sintesi": personale.integrazione,
        "direzione": "Usa la lettura come lente: ciò che risuona va verificato nella realtà, ciò che non risuona può restare aperto.",
        "domanda_finale": (personale.domande_di_riflessione[0] if personale.domande_di_riflessione else "Quale parte della lettura descrive meglio il nodo che senti davvero?"),
        "livello": "STRUCTURAL_FALLBACK",
    }


def _ai_reading(structural, personal, cards, question, context, focus, emotion):
    system = """Sei Raffaello, lettore canonico dei Tarocchi R³∞ di Claudio Terzi.

Obiettivo: produrre una lettura straordinariamente precisa, elegante, profonda e utile, come un grande interprete simbolico che sa ascoltare una persona e leggere una stesa nel suo insieme.

REGOLE DI VERITÀ:
- Le carte sono simboli e generano interpretazioni: NON sono prove di fatti nascosti né garanzie del futuro.
- Non inventare tradimenti, gravidanze, morti, malattie, reati, intenzioni di terzi, diagnosi, somme di denaro o eventi specifici se non sono nel contesto fornito.
- Quando vai oltre ciò che l'utente ha detto, formula una IPOTESI verificabile: “può indicare”, “qui leggerei”, “una possibilità è”.
- Non usare paura, dipendenza, autorità mistica o fatalismo. Non dire che solo tu puoi vedere/sbloccare qualcosa.
- In salute, denaro, diritto o sicurezza, resta riflessivo e non sostituire professionisti o dati reali.

QUALITÀ DELLA LETTURA:
- Comprendi prima la domanda implicita e il tono emotivo usando SOLO il testo ricevuto.
- Leggi ogni carta secondo: significato canonico fornito, posizione, orientamento, stato, elemento e relazione con le altre carte.
- La rovesciata NON significa automaticamente “negativo”: può essere interiorizzazione, ritardo, blocco, eccesso, inversione o energia non integrata.
- Cerca trama, ripetizioni, opposizioni, progressione temporale, tensioni tra elementi, risorse e carte che correggono altre carte.
- Evita frasi generiche che potrebbero adattarsi a chiunque. Collega ogni affermazione a una carta, una posizione o a parole esplicite del contesto.
- Non adulare. Se la stesa contraddice l'aspettativa implicita dell'utente, dillo con tatto.
- Spiega il significato delle carte mentre le interpreti: l'utente deve capire PERCHÉ arrivi alla sintesi.
- Non citare tecniche di persuasione, psicologia della performance o il processo con cui formuli la lettura.

STILE:
Italiano naturale, caldo, preciso, evocativo ma non nebuloso. Parla in prima persona come Raffaello. Nessun tono da manuale. Nessun gergo tecnico inutile.

OUTPUT: SOLO JSON valido con questa forma esatta:
{
  "apertura": "2-4 frasi",
  "contesto_compreso": "cosa hai capito della domanda, senza inventare",
  "carte": [
    {"posizione":"...","carta":"...","significato":"spiegazione simbolica","nel_contesto":"interpretazione specifica"}
  ],
  "trama": "come le carte si parlano tra loro",
  "tensione_centrale": "il nodo principale, come ipotesi quando necessario",
  "sintesi": "lettura complessiva",
  "direzione": "una direzione concreta ma non prescrittiva",
  "domanda_finale": "una sola domanda molto mirata",
  "livello": "AI_CONTEXTUAL"
}"""
    user = json.dumps({
        "domanda": question or None,
        "contesto_aggiuntivo": context or None,
        "focus": focus or None,
        "emozione_dichiarata": emotion or None,
        "carte": cards,
        "strutturale": {
            "sinossi": structural.sinossi,
            "tensioni": structural.tensioni,
            "risorse": structural.risorse,
            "relazioni": structural.relazioni,
            "distribuzione_stati": structural.distribuzione_stati,
            "distribuzione_elementi": structural.distribuzione_elementi,
        },
        "ponte_base": personal.ponte,
        "collasso_base": personal.punto_di_collasso,
        "domande_base": personal.domande_di_riflessione,
        "integrazione_base": personal.integrazione,
    }, ensure_ascii=False)

    try:
        from sdq1.llm.providers import AnthropicProvider, GeminiProvider
    except Exception:
        return None, None

    providers = [
        (GeminiProvider, "gemini-2.5-flash", {"json_mode": True, "temperatura": 0.55, "max_token": 3400, "timeout": 32}),
        (AnthropicProvider, "claude-haiku-4-5-20251001", {"temperatura": 0.5, "max_token": 3400, "timeout_secondi": 32}),
    ]
    for cls, model, opts in providers:
        try:
            provider = cls(modello=model, api_key=None, **opts)
            if not provider.disponibile:
                continue
            response = provider.completa(system, user)
            if response.errore:
                continue
            parsed = _safe_json(response.testo)
            if isinstance(parsed, dict) and isinstance(parsed.get("carte"), list):
                return parsed, {
                    "provider": response.provider,
                    "modello": response.modello,
                    "via_api": response.via_api,
                    "latenza_ms": response.latenza_ms,
                }
        except Exception:
            continue
    return None, None


def _build(body):
    question = _clean_text(body.get("domanda"), 1800)
    context = _clean_text(body.get("contesto"), 3200)
    focus = _clean_text(body.get("focus"), 40).lower()
    emotion = _clean_text(body.get("emozione"), 120)
    requested = _clean_text(body.get("profondita"), 10).lower() or "auto"
    if focus not in _FOCUS:
        focus = "altro"
    if not question and not context:
        return None, ("scrivi una domanda o un contesto da esplorare", 400)

    count, reason = _depth(question, context, focus, requested)
    selected = _draw(count)
    layout = _LAYOUTS[count]
    spread = Stesa(schema=f"raffaello_{count}_carte")
    labels = []
    for i, (card, (position, label)) in enumerate(zip(selected, layout), 1):
        orientation = _orientation()
        spread.aggiungi(card, _state_for(position), position, i, orientation)
        labels.append(label)

    proto = DoppiaErmeneutica()
    structural = proto.leggi_struttura(spread)
    personal_context = ContestoPersonale(
        domanda=question or None,
        momento_vita=context or None,
        emozione_prevalente=emotion or None,
        aspetto_focus=focus or None,
        disponibilita_collasso=True,
    )
    personal = proto.leggi_personale(structural, personal_context)
    cards = [_card_payload(node, label) for node, label in zip(spread.nodi, labels)]

    reading, provider_meta = _ai_reading(
        structural, personal, cards, question, context, focus, emotion
    )
    if reading is None:
        reading = _fallback(personal, cards, question, focus)

    return {
        "lettura_id": str(uuid.uuid4()),
        "metodo": {
            "sistema": "Tarocchi R³∞ · Raffaello",
            "numero_carte": count,
            "schema": spread.schema,
            "perche_questa_stesa": reason,
            "estrazione": "casuale_server_side",
            "fatti_privati_inventati": False,
        },
        "contesto": {
            "domanda": question or None,
            "focus": focus or None,
            "emozione": emotion or None,
        },
        "carte": cards,
        "strutturale": {
            "sinossi": structural.sinossi,
            "tensioni": structural.tensioni,
            "risorse": structural.risorse,
            "relazioni": structural.relazioni,
            "assiomi_attivati": structural.assiomi_attivati,
        },
        "lettura": reading,
        "motore": provider_meta or {"provider": "deterministic-fallback", "via_api": False},
        "epistemica": "INTERPRETAZIONE_SIMBOLICA_NON_PREVISIONE_CERTA",
    }, None


def _response():
    if request.method == "OPTIONS":
        return "", 200
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"errore": "serve un oggetto JSON"}), 400
    result, error = _build(body)
    if error:
        return jsonify({"errore": error[0]}), error[1]
    response = jsonify(result)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/api/tarocchi/raffaello", methods=["POST", "OPTIONS"])
def tarot_raffaello():
    return _response()


@app.route("/", methods=["POST", "OPTIONS"])
def root():
    return _response()
