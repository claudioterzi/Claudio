"""Raffaello · Canone Alpha 74 — lettura e approfondimento contestuale.

Un solo mazzo: tarocchi_quantici_alpha.json.
Formula canonica: CARTA + ASSE + POLARITA = SIGNIFICATO.
Luce/Ombra sono equiprobabili (50/50) nelle estrazioni automatiche.
Le domande successive restano vincolate alle carte della stesa già conclusa.

Claudio Terzi · C.Terzi
"""
from __future__ import annotations

import json
import os
import re
import secrets
import uuid

from flask import Flask, jsonify, request

from tarocchi.spazio_interpretativo import configuration_space

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
LANGUAGES = {
    "it": "Italiano",
    "en": "English",
    "fr": "Français",
    "es": "Español",
}
INTERPRETATION_VERSION = "alpha74-context-v3"

POSITION_LABELS = {
    "it": {"passato": "Passato", "presente": "Presente", "futuro": "Futuro", "ostacolo": "Ostacolo", "potenziale": "Potenziale", "consiglio": "Consiglio", "esito": "Esito"},
    "en": {"passato": "Past", "presente": "Present", "futuro": "Future", "ostacolo": "Obstacle", "potenziale": "Potential", "consiglio": "Advice", "esito": "Outcome"},
    "fr": {"passato": "Passé", "presente": "Présent", "futuro": "Futur", "ostacolo": "Obstacle", "potenziale": "Potentiel", "consiglio": "Conseil", "esito": "Résultat"},
    "es": {"passato": "Pasado", "presente": "Presente", "futuro": "Futuro", "ostacolo": "Obstáculo", "potenziale": "Potencial", "consiglio": "Consejo", "esito": "Resultado"},
}
AXIS_LABELS = {
    "it": {"nord": "Nord", "est": "Est", "sud": "Sud", "ovest": "Ovest"},
    "en": {"nord": "North", "est": "East", "sud": "South", "ovest": "West"},
    "fr": {"nord": "Nord", "est": "Est", "sud": "Sud", "ovest": "Ouest"},
    "es": {"nord": "Norte", "est": "Este", "sud": "Sur", "ovest": "Oeste"},
}
POLARITY_LABELS = {
    "it": {"luce": "Luce", "ombra": "Ombra"},
    "en": {"luce": "Light", "ombra": "Shadow"},
    "fr": {"luce": "Lumière", "ombra": "Ombre"},
    "es": {"luce": "Luz", "ombra": "Sombra"},
}


def _deck():
    with open(ALPHA_PATH, encoding="utf-8") as f:
        cards = json.load(f)["carte"]
    if len(cards) != 74:
        raise RuntimeError(f"Canone Alpha non valido: attese 74 carte, trovate {len(cards)}")
    return cards


def _clean(v, n):
    return str(v or "").strip()[:n]


def _language(value):
    """Return one of the four supported reading languages, defaulting to Italian."""
    raw = _clean(value, 20).lower().replace("_", "-")
    code = raw.split("-", 1)[0]
    return code if code in LANGUAGES else "it"


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
        raw_count = body.get("numero_carte", 3)
        if raw_count is None or raw_count == "":
            raw_count = 3
        try:
            count = int(raw_count)
        except (TypeError, ValueError) as exc:
            raise ValueError("numero_carte deve essere un intero da 1 a 7.") from exc
        if not 1 <= count <= 7:
            raise ValueError("numero_carte deve essere compreso tra 1 e 7.")
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
        if not isinstance(raw, dict):
            raise ValueError("Ogni carta della stesa deve essere un oggetto.")
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


def _epistemic_register(cards, relations):
    """Classify the same spread as facts, interpretations and hypotheses."""
    facts = [
        {
            "ordine": index + 1,
            "carta": card["carta"],
            "posizione": card["posizione"],
            "direzione": card["asse"],
            "polarita": card["polarita"],
            "significato_canonico": card["significato_canonico"],
        }
        for index, card in enumerate(cards)
    ]
    return {
        "fatti": {
            "stato": "osservabile",
            "dati_stesa": facts,
        },
        "interpretazioni": {
            "stato": "relazione_simbolica",
            "relazioni": relations,
        },
        "ipotesi": {
            "stato": "da_verificare",
            "vincolo": "Non sono fatti, diagnosi, intenzioni altrui o previsioni certe.",
        },
    }


def _evidence_map(cards):
    """Build the neutral evidence shared by the AI and deterministic paths.

    This map deliberately describes only observable input: it never turns a
    relation into a fact or a prediction. Both interpreters receive the same
    map, which makes their difference auditable instead of merely asserted.
    """
    cards = list(cards or [])
    position_order = {name: index for index, (name, _label, _axis) in enumerate(POSITIONS)}
    ordered = sorted(cards, key=lambda card: position_order.get(card.get("posizione"), 99))
    relations = []

    temporal = [card for card in ordered if card.get("posizione") in {"passato", "presente", "futuro"}]
    if len(temporal) >= 2:
        relations.append({
            "tipo": "sequenza_temporale",
            "carte": [card["carta"] for card in temporal],
            "posizioni": [card["posizione"] for card in temporal],
        })

    for axis in ("nord", "est", "sud", "ovest"):
        same_axis = [card for card in ordered if card.get("asse") == axis]
        if len(same_axis) >= 2:
            relations.append({
                "tipo": "asse_condiviso",
                "asse": axis,
                "carte": [card["carta"] for card in same_axis],
            })

    light = [card["carta"] for card in ordered if card.get("polarita") == "luce"]
    shadow = [card["carta"] for card in ordered if card.get("polarita") == "ombra"]
    if light and shadow:
        relations.append({"tipo": "dialogo_luce_ombra", "luce": light, "ombra": shadow})

    space = configuration_space(len(cards))
    return {
        "versione": INTERPRETATION_VERSION,
        "formula": "CARTA + ASSE + POLARITA = SIGNIFICATO",
        "carte_ancorate": [card["carta"] for card in cards],
        "relazioni": relations,
        "spazio_interpretativo": space,
        "registri_epistemici": _epistemic_register(cards, relations),
    }


def _verification(evidence, *, kind="schema"):
    """Return a categorical, non-numeric check status for the response."""
    space = evidence.get("spazio_interpretativo", {})
    return {
        "stato": "superata",
        "tipo": kind,
        "versione": evidence.get("versione", INTERPRETATION_VERSION),
        "carte_ancorate": len(evidence.get("carte_ancorate", [])),
        "relazioni": len(evidence.get("relazioni", [])),
        "registri": ["fatti", "interpretazioni", "ipotesi"],
        "configurazioni_stessa_lunghezza": space.get("configurazioni_stessa_lunghezza"),
        "configurazioni_massime_7": space.get("configurazioni_massime_7"),
    }


def _verified_engine(engine, evidence, *, kind="schema"):
    meta = dict(engine or {})
    meta["verifica"] = "superata"
    meta["verifica_tipo"] = kind
    meta["verifica_versione"] = evidence.get("versione", INTERPRETATION_VERSION)
    meta["carte_ancorate"] = len(evidence.get("carte_ancorate", []))
    meta["relazioni_verificate"] = len(evidence.get("relazioni", []))
    return meta


def _validate_main_reading(data, cards, language="it"):
    """Accept model output only when it preserves the supplied card set.

    The validator is intentionally structural: it can prove that the answer
    uses the right cards and fields, not that a symbolic interpretation is
    objectively true.
    """
    language = _language(language)
    if not isinstance(data, dict):
        return None
    required = ("messaggio", "nodo", "direzione", "domanda_finale")
    for key in required:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            return None
    raw_cards = data.get("carte")
    if not isinstance(raw_cards, list) or len(raw_cards) != len(cards):
        return None
    normalized = []
    for expected, raw in zip(cards, raw_cards):
        if not isinstance(raw, dict) or _clean(raw.get("carta"), 120) != expected["carta"]:
            return None
        meaning = raw.get("lettura")
        if not isinstance(meaning, str) or not meaning.strip():
            return None
        normalized.append({
            "posizione": _clean(raw.get("posizione"), 100) or expected["posizione_label"],
            "carta": expected["carta"],
            "lettura": _clean(meaning, 1800),
        })
    result = dict(data)
    for key in required:
        result[key] = _clean(data[key], 12000 if key == "messaggio" else 5000)
    result["carte"] = normalized
    result["livello"] = "AI_ALPHA_CONTEXTUAL"
    result["lingua"] = language
    return result


def _validate_follow_up(data, cards, language="it"):
    """Validate a follow-up answer against the immutable spread."""
    language = _language(language)
    if not isinstance(data, dict):
        return None
    answer = data.get("risposta")
    if not isinstance(answer, str) or not answer.strip():
        return None
    allowed = {card["carta"] for card in cards}
    references = data.get("carte_richiamate")
    if not isinstance(references, list) or not references:
        return None
    if any(not isinstance(name, str) or name not in allowed for name in references):
        return None
    result = dict(data)
    result["risposta"] = _clean(answer, 6000)
    result["carte_richiamate"] = list(dict.fromkeys(references))
    result["livello"] = "AI_ALPHA_FOLLOW_UP"
    result["lingua"] = language
    return result


def _relation_sentences(cards, evidence, language):
    """Render neutral relation observations for the deterministic path."""
    language = _language(language)
    by_name = {card["carta"]: card for card in cards}
    sentences = []
    for relation in evidence.get("relazioni", []):
        kind = relation.get("tipo")
        if kind == "sequenza_temporale":
            sequence = [by_name[name] for name in relation.get("carte", []) if name in by_name]
            if len(sequence) < 2:
                continue
            temporal_labels = {
                "it": {"passato": "il passato", "presente": "il presente", "futuro": "il futuro"},
                "en": {"passato": "the past", "presente": "the present", "futuro": "the future"},
                "fr": {"passato": "le passé", "presente": "le présent", "futuro": "le futur"},
                "es": {"passato": "el pasado", "presente": "el presente", "futuro": "el futuro"},
            }[language]
            observations = [
                f"{temporal_labels.get(card['posizione'], card['posizione'])}: «{card['significato_canonico']}»"
                for card in sequence
            ]
            if language == "it":
                sentences.append("Nel filo temporale osservo " + "; ".join(observations) + ".")
            elif language == "en":
                sentences.append("Along the temporal line I observe " + "; ".join(observations) + ".")
            elif language == "fr":
                sentences.append("Sur la ligne du temps, j’observe " + "; ".join(observations) + ".")
            else:
                sentences.append("En la línea temporal observo " + "; ".join(observations) + ".")
        elif kind == "asse_condiviso":
            names = [name for name in relation.get("carte", []) if name in by_name]
            if len(names) < 2:
                continue
            axis = AXIS_LABELS[language].get(relation.get("asse"), relation.get("asse", ""))
            meanings = " · ".join(f"{name}: «{by_name[name]['significato_canonico']}»" for name in names)
            if language == "it":
                sentences.append(f"L'asse {axis} ritorna in {len(names)} carte — {meanings}: lo considero un punto di attenzione, non un verdetto.")
            elif language == "en":
                sentences.append(f"The {axis} axis returns in {len(names)} cards — {meanings}; I treat it as an attention point, not a verdict.")
            elif language == "fr":
                sentences.append(f"L’axe {axis} revient dans {len(names)} cartes — {meanings} : je le considère comme un point d’attention, pas comme un verdict.")
            else:
                sentences.append(f"El eje {axis} aparece en {len(names)} cartas — {meanings}: lo tomo como un punto de atención, no como un veredicto.")
        elif kind == "dialogo_luce_ombra":
            light = ", ".join(relation.get("luce", []))
            shadow = ", ".join(relation.get("ombra", []))
            if language == "it":
                sentences.append(f"La stesa mette in dialogo la Luce ({light}) e l'Ombra ({shadow}); le leggo come due manifestazioni dello stesso campo simbolico, non come buono contro cattivo.")
            elif language == "en":
                sentences.append(f"The spread places Light ({light}) and Shadow ({shadow}) in dialogue; I read them as two expressions of the same symbolic field, not as good versus bad.")
            elif language == "fr":
                sentences.append(f"Le tirage met en dialogue la Lumière ({light}) et l’Ombre ({shadow}) ; je les lis comme deux manifestations du même champ symbolique, pas comme le bien contre le mal.")
            else:
                sentences.append(f"La tirada pone en diálogo la Luz ({light}) y la Sombra ({shadow}); las leo como dos manifestaciones del mismo campo simbólico, no como bueno contra malo.")
    return sentences


def _fallback(cards, question, language="it", evidence=None):
    language = _language(language)
    cards = list(cards or [])
    evidence = evidence or _evidence_map(cards)
    position_labels = POSITION_LABELS[language]
    polarity_labels = POLARITY_LABELS[language]
    axis_labels = AXIS_LABELS[language]
    location_templates = {
        "it": "{position}: {card} in {polarity} sull'asse {axis} — {meaning}.",
        "en": "{position}: {card} in {polarity} on the {axis} axis — {meaning}.",
        "fr": "{position} : {card} en {polarity} sur l’axe {axis} — {meaning}.",
        "es": "{position}: {card} en {polarity} sobre el eje {axis} — {meaning}.",
    }[language]
    lines = [
        location_templates.format(
            position=position_labels.get(c["posizione"], c["posizione_label"]), card=c["carta"],
            polarity=polarity_labels[c["polarita"]], axis=axis_labels[c["asse"]],
            meaning=c["significato_canonico"],
        )
        for c in cards
    ]
    base = " ".join(lines)
    opening_templates = {
        "it": ("Sulla tua domanda, io leggerei questa stesa così: {base}", "Come fotografia simbolica del momento, io leggerei questa stesa così: {base}"),
        "en": ("Looking at your question, I would read this spread as follows: {base}", "As a symbolic snapshot of this moment, I would read this spread as follows: {base}"),
        "fr": ("À partir de votre question, je lirais ce tirage ainsi : {base}", "Comme photographie symbolique du moment, je lirais ce tirage ainsi : {base}"),
        "es": ("A partir de tu pregunta, leería esta tirada así: {base}", "Como fotografía simbólica del momento, leería esta tirada así: {base}"),
    }[language]
    opening = (opening_templates[0] if question else opening_templates[1]).format(base=base)
    relations = _relation_sentences(cards, evidence, language)
    copy = {
        "it": {
            "message": "Il filo comune non è una previsione certa: è il tema che emerge mettendo in relazione queste posizioni.",
            "direction": "Osserva quale di questi significati trova un riscontro concreto nella tua situazione; annota il passaggio che cambia quando lo guardi dal suo asse e dalla sua polarità.",
            "final": "Quale passaggio della stesa descrive con più precisione ciò che stai vivendo adesso?",
            "node": "Il nodo che terrei in primo piano è {card}: «{meaning}». La posizione {position} lo rende il punto da verificare per primo nella tua esperienza.",
            "guard": "Questa è una lettura simbolica ancorata alle carte estratte: non aggiunge fatti privati e non promette il futuro.",
        },
        "en": {
            "message": "The common thread is not a certain prediction; it is the theme that emerges when these positions are read together.",
            "direction": "Notice which meaning finds a concrete echo in your situation; write down what changes when you view it through its axis and polarity.",
            "final": "Which part of the spread describes most precisely what you are living through now?",
            "node": "The node I would keep in the foreground is {card}: “{meaning}”. Its {position} position makes it the first point to check against your experience.",
            "guard": "This is a symbolic reading anchored to the drawn cards: it adds no private facts and promises no future.",
        },
        "fr": {
            "message": "Le fil commun n'est pas une prédiction certaine : c'est le thème qui apparaît lorsque ces positions sont mises en relation.",
            "direction": "Observez quel sens trouve un écho concret dans votre situation ; notez ce qui change lorsque vous le regardez à travers son axe et sa polarité.",
            "final": "Quel passage du tirage décrit avec le plus de précision ce que vous vivez maintenant ?",
            "node": "Le nœud que je garderais au premier plan est {card} : « {meaning} ». Sa position {position} en fait le premier point à confronter à votre expérience.",
            "guard": "Ceci est une lecture symbolique ancrée dans les cartes tirées : elle n'ajoute aucun fait privé et ne promet pas l'avenir.",
        },
        "es": {
            "message": "El hilo común no es una predicción cierta: es el tema que aparece al relacionar estas posiciones.",
            "direction": "Observa qué significado encuentra un eco concreto en tu situación; anota qué cambia cuando lo miras desde su eje y su polaridad.",
            "final": "¿Qué parte de la tirada describe con más precisión lo que estás viviendo ahora?",
            "node": "El nudo que mantendría en primer plano es {card}: «{meaning}». Su posición {position} lo convierte en el primer punto que debes contrastar con tu experiencia.",
            "guard": "Esta es una lectura simbólica anclada en las cartas extraídas: no añade hechos privados ni promete el futuro.",
        },
    }[language]
    anchor = next((card for card in cards if card.get("posizione") == "presente"), cards[-1] if cards else None)
    if anchor:
        node = copy["node"].format(
            card=anchor["carta"], meaning=anchor["significato_canonico"],
            position=position_labels.get(anchor["posizione"], anchor["posizione_label"]),
        )
    else:
        node = ""
    message_parts = [opening, copy["message"], *relations, copy["guard"]]
    return {
        "messaggio": " ".join(part for part in message_parts if part),
        "nodo": node,
        "direzione": copy["direction"],
        "domanda_finale": copy["final"],
        "carte": [{"posizione": position_labels.get(c["posizione"], c["posizione_label"]), "carta": c["carta"], "lettura": c["significato_canonico"]} for c in cards],
        "livello": "CANONICAL_FALLBACK",
        "lingua": language,
        "traccia": evidence,
        "verifica": _verification(evidence, kind="deterministico"),
        "spazio_interpretativo": evidence["spazio_interpretativo"],
        "registri_epistemici": evidence["registri_epistemici"],
    }


def _ai(cards, question, context, language="it"):
    language = _language(language)
    target_language = LANGUAGES[language]
    evidence = _evidence_map(cards)
    spread_space = evidence["spazio_interpretativo"]
    spread_count = spread_space["carte_nella_stesa"]
    spread_configurations = spread_space["configurazioni_stessa_lunghezza"]
    max_configurations = spread_space["configurazioni_massime_7"]
    system = f"""Sei Raffaello, interprete del Canone Alpha di Claudio Terzi.
Questo NON è un mazzo di tarocchi tradizionale. Non esistono Spade, Coppe, Bastoni, Denari o Arcani classici.
Usi soltanto le 74 carte del Canone Alpha e la formula: CARTA + ASSE + POLARITA = SIGNIFICATO.
Ogni significato canonico ti viene fornito esplicitamente e NON va sostituito con significati inventati.
Luce e Ombra hanno pari dignità: Ombra non significa automaticamente male; indica la manifestazione d'ombra del simbolo.
Leggi la relazione fra le carte e parla direttamente all'utente con chiarezza, calore e precisione.
Non presentare simboli come prove di fatti nascosti o previsioni certe. Se inferisci qualcosa, formulalo come possibilità.
La stesa è una configurazione ordinata di {spread_count} carte distinte: ordine, posizione, asse/direzione e polarità contano.
Il modello ha {spread_configurations} configurazioni per questa lunghezza; a 7 carte arriva a {max_configurations} (P(74,7) × 8^7). Questi numeri descrivono lo spazio del modello, non verità assolute.
Distingui sempre fatti osservabili della stesa, interpretazioni relazionali e ipotesi contestuali da verificare. Non trasformare un'ipotesi in un fatto.

LINGUA OBBLIGATORIA: scrivi ogni valore testuale naturale del JSON in {target_language}.
Mantieni esattamente i nomi canonici delle carte nel campo "carta"; traduci invece posizioni e spiegazioni quando serve.
Le chiavi JSON devono restare quelle indicate qui sotto.

OUTPUT SOLO JSON valido:
{{
 "messaggio":"un messaggio continuo di 6-12 frasi, in prima persona come Raffaello, che spiega la stesa nel suo insieme",
 "nodo":"il nodo centrale in 2-4 frasi",
 "direzione":"direzione concreta ma non prescrittiva in 2-4 frasi",
"domanda_finale":"una sola domanda molto precisa",
"carte":[{{"posizione":"...","carta":"...","lettura":"spiegazione chiara del significato canonico nel contesto"}}],
"livello":"AI_ALPHA_CONTEXTUAL"
}}"""
    user = json.dumps({"domanda": question or None, "contesto": context or None, "lingua": language, "carte": cards, "evidenze_bloccate": evidence}, ensure_ascii=False)
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
            validated = _validate_main_reading(data, cards, language)
            if validated is not None:
                return validated, {
                    "provider": r.provider,
                    "modello": r.modello,
                    "via_api": r.via_api,
                    "tipo": "ai_contestuale",
                }
        except Exception:
            continue
    return None, None


def _previous_reading(value):
    """Keep only the bounded, explanatory fields from the original reading."""
    if not isinstance(value, dict):
        return {}
    out = {}
    for key in ("messaggio", "nodo", "direzione", "domanda_finale"):
        cleaned = _clean(value.get(key), 1800)
        if cleaned:
            out[key] = cleaned
    raw_cards = value.get("carte")
    if isinstance(raw_cards, list):
        out["carte"] = []
        for raw in raw_cards[:7]:
            if not isinstance(raw, dict):
                continue
            item = {
                "posizione": _clean(raw.get("posizione"), 80),
                "carta": _clean(raw.get("carta"), 120),
                "lettura": _clean(raw.get("lettura"), 1200),
            }
            if any(item.values()):
                out["carte"].append(item)
    return out


def _follow_up_history(value):
    if not isinstance(value, list):
        return []
    history = []
    for raw in value[-6:]:
        if not isinstance(raw, dict):
            continue
        question = _clean(raw.get("domanda"), 800)
        answer = _clean(raw.get("risposta"), 1800)
        if question or answer:
            history.append({"domanda": question, "risposta": answer})
    return history


def _follow_up_fallback(cards, question, language="it", evidence=None):
    language = _language(language)
    cards = list(cards or [])
    evidence = evidence or _evidence_map(cards)
    position_labels = POSITION_LABELS[language]
    anchors = [
        f"{position_labels.get(c['posizione'], c['posizione_label'])}: {c['carta']} — {c['significato_canonico']}"
        for c in cards
    ]
    joined = " ".join(anchors)
    relation_text = " ".join(_relation_sentences(cards, evidence, language))
    relation_clause = f"{relation_text} " if relation_text else ""
    templates = {
        "it": (f"Rileggo la tua domanda — «{question}» — soltanto attraverso la stesa già uscita. "
               f"I riferimenti concreti sono questi: {joined}. "
               f"{relation_clause}"
               "Il collegamento più rigoroso che posso fare resta simbolico: confronta la tua domanda con questi significati e osserva quali trovano un riscontro reale nella situazione. "
               "Le carte non mi autorizzano ad aggiungere fatti, intenzioni di altre persone o certezze sul futuro che non siano presenti nella lettura."),
        "en": (f"I am rereading your question — “{question}” — only through the spread already drawn. "
               f"These are the concrete references: {joined}. "
               f"{relation_clause}"
               "The most rigorous link I can make is therefore symbolic: compare your question with these meanings and notice which ones have a real echo in your situation. "
               "The cards do not authorize me to add facts, other people's intentions, or certainty about the future."),
        "fr": (f"Je relis votre question — « {question} » — uniquement à travers le tirage déjà sorti. "
               f"Voici les repères concrets : {joined}. "
               f"{relation_clause}"
               "Le lien le plus rigoureux que je puisse faire reste donc symbolique : confrontez votre question à ces sens et observez lesquels trouvent un écho réel dans votre situation. "
               "Les cartes ne m'autorisent pas à ajouter des faits, les intentions d'autrui ou des certitudes sur l'avenir."),
        "es": (f"Vuelvo a leer tu pregunta — «{question}»— únicamente a través de la tirada ya extraída. "
               f"Estas son las referencias concretas: {joined}. "
               f"{relation_clause}"
               "El vínculo más riguroso que puedo hacer es, por tanto, simbólico: compara tu pregunta con estos significados y observa cuáles encuentran un eco real en tu situación. "
               "Las cartas no me autorizan a añadir hechos, intenciones de otras personas ni certezas sobre el futuro."),
    }[language]
    return {
        "risposta": templates.strip(),
        "carte_richiamate": [c["carta"] for c in cards],
        "livello": "CANONICAL_FOLLOW_UP_FALLBACK",
        "lingua": language,
        "traccia": evidence,
        "verifica": _verification(evidence, kind="deterministico"),
    }


def _ai_follow_up(cards, question, original_question, context, previous, history, *, language="it", timeout_seconds=30, max_retries=2):
    language = _language(language)
    target_language = LANGUAGES[language]
    evidence = _evidence_map(cards)
    spread_space = evidence["spazio_interpretativo"]
    spread_count = spread_space["carte_nella_stesa"]
    max_configurations = spread_space["configurazioni_massime_7"]
    system = f"""Sei Raffaello, interprete del Canone Alpha di Claudio Terzi.
L'utente sta facendo una domanda libera DOPO una lettura già conclusa.

VINCOLO ASSOLUTO:
- Rispondi soltanto usando le carte realmente estratte, le loro posizioni, assi, polarità e significati canonici forniti.
- Puoi usare la lettura precedente e la breve cronologia solo per continuità del dialogo: non sono nuove prove e non possono modificare le carte.
- Non estrarre, nominare o inventare nuove carte.
- Non rifare la stesa e non alterarne ordine, posizione, asse o polarità.
- Non inventare fatti privati, intenzioni di terzi, diagnosi o previsioni certe.
- Se la domanda chiede una certezza che le carte non possono dare, dillo chiaramente e spiega che cosa suggeriscono invece i simboli presenti.
- Ogni affermazione interpretativa deve poter essere ricondotta ad almeno una carta della stesa.
- La stesa corrente è una configurazione ordinata di {spread_count} carte; il massimo teorico a 7 carte è {max_configurations}. Il conteggio riguarda configurazioni del modello, non verità assolute.
- Mantieni distinti fatti osservabili, interpretazioni relazionali e ipotesi contestuali da verificare.

STILE:
{target_language} naturale, caldo, diretto e preciso. Rispondi nella lingua richiesta alla domanda specifica senza menu, formule predefinite o digressioni tecniche.

OUTPUT SOLO JSON valido:
{{
 "risposta":"risposta completa e contestuale in prima persona come Raffaello",
 "carte_richiamate":["solo nomi di carte realmente presenti nella stesa"],
 "livello":"AI_ALPHA_FOLLOW_UP"
}}"""
    user = json.dumps({
        "domanda_attuale": question,
        "domanda_originale": original_question or None,
        "contesto_originale": context or None,
        "carte_estratte_bloccate": cards,
        "evidenze_bloccate": evidence,
        "lettura_precedente": previous,
        "cronologia_approfondimenti": history,
        "lingua": language,
    }, ensure_ascii=False)
    try:
        from sdq1.llm.providers import GeminiProvider, AnthropicProvider
    except Exception:
        return None, None
    providers = [
        (GeminiProvider, "gemini-2.5-flash", {"json_mode": True, "temperatura": 0.45, "max_token": 2200, "timeout": timeout_seconds}),
        (AnthropicProvider, "claude-haiku-4-5-20251001", {"temperatura": 0.4, "max_token": 2200, "timeout_secondi": timeout_seconds, "max_retries": max_retries}),
    ]
    for cls, model, opts in providers:
        try:
            provider = cls(modello=model, api_key=None, **opts)
            if not provider.disponibile:
                continue
            response = provider.completa(system, user)
            if response.errore:
                continue
            data = _safe_json(response.testo)
            validated = _validate_follow_up(data, cards, language)
            if validated is None:
                continue
            return validated, {
                "provider": response.provider,
                "modello": response.modello,
                "via_api": response.via_api,
                "tipo": "ai_contestuale",
            }
        except Exception:
            continue
    return None, None


def _follow_up(body):
    question = _clean(body.get("domanda_utente"), 1600)
    language = _language(body.get("lingua") or body.get("language"))
    if not question:
        return None, ("Scrivi la domanda che vuoi fare a Raffaello.", 400)
    try:
        cards, _ = _normalize_items(body)
    except (ValueError, RuntimeError) as exc:
        return None, (str(exc), 400)
    original_question = _clean(body.get("domanda_originale"), 1800)
    context = _clean(body.get("contesto"), 3200)
    previous = _previous_reading(body.get("lettura_precedente"))
    history = _follow_up_history(body.get("cronologia"))
    evidence = _evidence_map(cards)
    answer, engine = _ai_follow_up(cards, question, original_question, context, previous, history, language=language)
    if answer is None:
        answer = _follow_up_fallback(cards, question, language, evidence)
        engine = {
            "provider": "canonical-fallback",
            "via_api": False,
            "tipo": "riserva_canonica",
        }
    answer_is_ai = answer.get("livello", "AI_ALPHA_FOLLOW_UP") == "AI_ALPHA_FOLLOW_UP"
    engine = _verified_engine(engine, evidence, kind="ai" if answer_is_ai else "deterministico")
    return {
        "approfondimento_id": str(uuid.uuid4()),
        "lettura_id": _clean(body.get("lettura_id"), 80) or None,
        "sistema": "Canone Alpha 74",
        "domanda": question,
        "risposta": answer["risposta"],
        "carte_richiamate": answer.get("carte_richiamate", []),
        "livello": answer.get("livello", "AI_ALPHA_FOLLOW_UP"),
        "motore": engine,
        "evidenza": evidence,
        "spazio_interpretativo": evidence["spazio_interpretativo"],
        "registri_epistemici": evidence["registri_epistemici"],
        "verifica": answer.get("verifica") or _verification(evidence, kind="ai" if answer_is_ai else "deterministico"),
        "vincolo": "SOLO_CARTE_ESTRATTE",
        "epistemica": "INTERPRETAZIONE_SIMBOLICA_NON_PREVISIONE_CERTA",
        "lingua": language,
    }, None


def _response():
    if request.method == "OPTIONS":
        return "", 200
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"errore": "Serve un oggetto JSON."}), 400
    if _clean(body.get("modalita"), 40).lower() == "approfondimento":
        result, error = _follow_up(body)
        if error:
            return jsonify({"errore": error[0]}), error[1]
        resp = jsonify(result)
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp
    try:
        cards, automatic = _normalize_items(body)
    except (ValueError, RuntimeError) as exc:
        return jsonify({"errore": str(exc)}), 400
    question = _clean(body.get("domanda"), 1800)
    context = _clean(body.get("contesto"), 3200)
    language = _language(body.get("lingua") or body.get("language"))
    evidence = _evidence_map(cards)
    reading, engine = _ai(cards, question, context, language)
    if reading is None:
        reading = _fallback(cards, question, language, evidence)
        engine = {
            "provider": "canonical-fallback",
            "via_api": False,
            "tipo": "riserva_canonica",
        }
    reading["traccia"] = evidence
    reading["spazio_interpretativo"] = evidence["spazio_interpretativo"]
    reading["registri_epistemici"] = evidence["registri_epistemici"]
    reading["verifica"] = _verification(evidence, kind="ai" if reading.get("livello") == "AI_ALPHA_CONTEXTUAL" else "deterministico")
    engine = _verified_engine(engine, evidence, kind="ai" if reading.get("livello") == "AI_ALPHA_CONTEXTUAL" else "deterministico")
    reading.setdefault("lingua", language)
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
        "evidenza": evidence,
        "spazio_interpretativo": evidence["spazio_interpretativo"],
        "registri_epistemici": evidence["registri_epistemici"],
        "verifica": reading["verifica"],
        "epistemica": "INTERPRETAZIONE_SIMBOLICA_NON_PREVISIONE_CERTA",
        "lingua": language,
    })
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/api/tarocchi/alpha-leggi", methods=["POST", "OPTIONS"])
def alpha_read():
    return _response()


@app.route("/", methods=["POST", "OPTIONS"])
def root():
    return _response()
