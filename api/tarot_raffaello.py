"""Raffaello · Lettura Tarocchi

Modalità automatica: Raffaello sceglie profondità, estrae e interpreta.
Modalità manuale: l'utente sceglie solo i dorsi; Raffaello riceve ESATTAMENTE
quelle carte, ne conserva ordine/orientamento e produce la lettura contestuale.

Principio epistemico: il simbolo può generare ipotesi e riflessioni, non fatti
privati non osservati né previsioni certe.

Claudio Terzi · C.Terzi
"""
from __future__ import annotations

import json
import re
import secrets
import uuid

from flask import Flask, jsonify, request

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

app = Flask(__name__)

_FOCUS = {"amore", "lavoro", "crescita", "creativita", "creatività", "relazioni", "salute", "denaro", "altro", ""}
LANGUAGES = {
    "it": "Italiano",
    "en": "English",
    "fr": "Français",
    "es": "Español",
}
_LAYOUTS = {
    3: [(TipoPosizione.RADICE, "Radice"),(TipoPosizione.PRESENTE, "Presente"),(TipoPosizione.CONSIGLIO, "Direzione")],
    5: [(TipoPosizione.RADICE, "Radice"),(TipoPosizione.PRESENTE, "Presente"),(TipoPosizione.OSTACOLO, "Nodo / ostacolo"),(TipoPosizione.POTENZIALE, "Potenziale"),(TipoPosizione.CONSIGLIO, "Direzione")],
    7: [(TipoPosizione.PASSATO, "Ciò che precede"),(TipoPosizione.PRESENTE, "Presente"),(TipoPosizione.OMBRA, "Ciò che resta fuori campo"),(TipoPosizione.OSTACOLO, "Nodo / ostacolo"),(TipoPosizione.POTENZIALE, "Potenziale"),(TipoPosizione.CONSIGLIO, "Direzione"),(TipoPosizione.ESITO, "Esito aperto")],
}
_MANUAL_LABELS = {
    TipoPosizione.RADICE: "Radice", TipoPosizione.PASSATO: "Passato", TipoPosizione.PRESENTE: "Presente",
    TipoPosizione.FUTURO: "Futuro", TipoPosizione.OSTACOLO: "Ostacolo", TipoPosizione.POTENZIALE: "Potenziale",
    TipoPosizione.CONSIGLIO: "Consiglio", TipoPosizione.ESITO: "Esito", TipoPosizione.OMBRA: "Ombra",
}
_POSITIONS = {p.value: p for p in TipoPosizione}
_STATES = {s.value: s for s in StatoQuantico}
_ORIENTATIONS = {o.value: o for o in OrientamentoCarta}


def _clean_text(value, limit):
    return str(value or "").strip()[:limit]


def _language(value):
    """Normalize the requested reading language without trusting client input."""
    raw = _clean_text(value, 20).lower().replace("_", "-")
    code = raw.split("-", 1)[0]
    return code if code in LANGUAGES else "it"


def _depth(question: str, context: str, focus: str, requested: str) -> tuple[int, str]:
    if requested in {"3", "5", "7"}:
        n = int(requested); return n, f"Profondità scelta dall'utente: {n} carte."
    text = f"{question} {context}".lower()
    complex_markers = ("scegli","scelta","decision","rapporto","relazione","ritorno","perché","come evol","cosa succede","conflitto","blocco","cambiamento","due persone","lavoro","famiglia","futuro","separ","ricominc")
    deep_markers = ("tutto","profondo","completo","intera situazione","molto complesso","più aspetti")
    if any(x in text for x in deep_markers) or len(text) > 900: return 7, "Il contesto contiene più livelli: Raffaello apre una stesa profonda a 7 carte."
    if any(x in text for x in complex_markers) or focus in {"amore","relazioni","lavoro","denaro","salute"} or len(text) > 260: return 5, "La domanda richiede relazioni tra più fattori: Raffaello usa 5 carte."
    return 3, "La domanda è abbastanza focalizzata: 3 carte bastano per non diluire il segnale simbolico."


def _state_for(position: TipoPosizione) -> StatoQuantico:
    if position in {TipoPosizione.RADICE, TipoPosizione.PASSATO}: return StatoQuantico.COLLASSATO
    if position in {TipoPosizione.PRESENTE, TipoPosizione.OMBRA, TipoPosizione.OSTACOLO}: return StatoQuantico.ENTANGLED
    return StatoQuantico.SOVRAPPOSTO


def _draw(n: int):
    return secrets.SystemRandom().sample(list(MAZZO), n)


def _orientation() -> OrientamentoCarta:
    return OrientamentoCarta.ROVESCIA if secrets.randbelow(100) < 28 else OrientamentoCarta.DIRITTA


def _card_payload(node, label):
    c = node.carta
    return {"posizione":node.posizione.tipo.value,"posizione_label":label,"carta":c.nome,"indice":c.indice,"arcano":c.arcano.value,"seme":c.seme.value if c.seme else None,"elemento":c.elemento,"dominio":c.dominio,"parole_chiave":list(c.parole_chiave),"voce":voce(c),"eco":eco(c),"orientamento":node.orientamento.value,"stato":node.stato_effettivo.value}


def _safe_json(text: str):
    text=(text or "").strip()
    if not text:return None
    try:return json.loads(text)
    except json.JSONDecodeError:
        m=re.search(r"\{.*\}",text,re.S)
        if not m:return None
        try:return json.loads(m.group(0))
        except json.JSONDecodeError:return None


def _fallback(personale,cards,question,focus,language="it"):
    language = _language(language)
    per=[]
    position_labels = {
        "it": {"radice": "Radice", "passato": "Passato", "presente": "Presente", "futuro": "Futuro", "ostacolo": "Ostacolo", "potenziale": "Potenziale", "consiglio": "Consiglio", "esito": "Esito", "ombra": "Ombra"},
        "en": {"radice": "Root", "passato": "Past", "presente": "Present", "futuro": "Future", "ostacolo": "Obstacle", "potenziale": "Potential", "consiglio": "Advice", "esito": "Outcome", "ombra": "Shadow"},
        "fr": {"radice": "Racine", "passato": "Passé", "presente": "Présent", "futuro": "Futur", "ostacolo": "Obstacle", "potenziale": "Potentiel", "consiglio": "Conseil", "esito": "Résultat", "ombra": "Ombre"},
        "es": {"radice": "Raíz", "passato": "Pasado", "presente": "Presente", "futuro": "Futuro", "ostacolo": "Obstáculo", "potenziale": "Potencial", "consiglio": "Consejo", "esito": "Resultado", "ombra": "Sombra"},
    }[language]
    nuance = {
        "it": ("Qui il simbolo tende a mostrarsi come energia trattenuta, interiorizzata o non ancora espressa.",
               "Qui il simbolo è disponibile in forma più diretta e visibile."),
        "en": ("Here the symbol tends to appear as energy held back, internalized, or not yet expressed.",
               "Here the symbol is available in a more direct and visible form."),
        "fr": ("Ici, le symbole tend à apparaître comme une énergie retenue, intériorisée ou pas encore exprimée.",
               "Ici, le symbole est disponible sous une forme plus directe et visible."),
        "es": ("Aquí el símbolo tiende a mostrarse como energía contenida, interiorizada o aún no expresada.",
               "Aquí el símbolo está disponible de una forma más directa y visible."),
    }[language]
    for card in cards:
        rovescia=card["orientamento"]=="rovescia"
        per.append({"posizione":position_labels.get(card["posizione"], card["posizione_label"]),"carta":card["carta"],"significato":f"{card['voce']} — {card['eco']}","nel_contesto":nuance[0] if rovescia else nuance[1]})
    copy = {
        "it": {"opening":"Ti restituisco prima il senso complessivo della stesa e poi, se vuoi, puoi vedere perché ogni carta mi porta lì.", "context": "Hai aperto la stesa senza una domanda specifica: la leggo come fotografia simbolica del momento.", "direction":"Prendi come utile ciò che trova riscontro nella realtà; ciò che non risuona può restare aperto.", "final":"Quale parte della stesa descrive meglio ciò che stai davvero vivendo?"},
        "en": {"opening":"I will give you the overall meaning of the spread first, then you can see why each card leads me there.", "context": "You opened the spread without a specific question: I read it as a symbolic snapshot of this moment.", "direction":"Keep what finds an echo in reality; whatever does not resonate can remain open.", "final":"Which part of the spread best describes what you are truly living through?"},
        "fr": {"opening":"Je vous donne d'abord le sens d'ensemble du tirage, puis, si vous le souhaitez, pourquoi chaque carte m'y conduit.", "context":"Vous avez ouvert le tirage sans question précise : je le lis comme une photographie symbolique du moment.", "direction":"Gardez ce qui trouve un écho dans la réalité ; ce qui ne résonne pas peut rester ouvert.", "final":"Quelle partie du tirage décrit le mieux ce que vous vivez vraiment ?"},
        "es": {"opening":"Primero te devuelvo el sentido global de la tirada y después, si quieres, por qué cada carta me lleva hasta allí.", "context":"Has abierto la tirada sin una pregunta concreta: la leo como una fotografía simbólica del momento.", "direction":"Quédate con lo que encuentre un eco en la realidad; lo que no resuene puede quedar abierto.", "final":"¿Qué parte de la tirada describe mejor lo que estás viviendo de verdad?"},
    }[language]
    if question:
        understood = question
    elif focus:
        focus_labels = {"it": "Focus", "en": "Focus", "fr": "Domaine", "es": "Enfoque"}
        understood = f"{focus_labels[language]}: {focus}."
    else:
        understood = copy["context"]
    return {"apertura":copy["opening"],"contesto_compreso":understood,"carte":per,"trama":personale.ponte,"tensione_centrale":personale.punto_di_collasso,"sintesi":personale.integrazione,"direzione":copy["direction"],"domanda_finale":personale.domande_di_riflessione[0] if personale.domande_di_riflessione else copy["final"],"livello":"STRUCTURAL_FALLBACK","lingua":language}


def _ai_reading(structural,personal,cards,question,context,focus,emotion,language="it"):
    language = _language(language)
    target_language = LANGUAGES[language]
    system=f"""Sei Raffaello, lettore canonico dei Tarocchi R³∞ di Claudio Terzi.
Scrivi come una persona che sta parlando direttamente all'utente dopo aver osservato tutta la stesa.
La prima priorità è CHIAREZZA: l'utente deve capire subito che cosa raccontano le carte nel loro insieme.

REGOLE DI VERITÀ:
- Le carte sono simboli: non sono prove di fatti nascosti né garanzie del futuro.
- Non inventare tradimenti, gravidanze, morti, malattie, reati, intenzioni di terzi, diagnosi, somme o eventi specifici.
- Oltre il testo fornito usa formulazioni verificabili: “può indicare”, “qui leggerei”, “una possibilità è”.
- Nessuna paura, dipendenza, autorità mistica o fatalismo.

QUALITÀ:
- Comprendi la domanda implicita usando solo ciò che l'utente ha scritto.
- Leggi ogni carta per significato canonico fornito, posizione, orientamento, stato, elemento e rapporti con le altre.
- La rovesciata può indicare interiorizzazione, blocco, ritardo, eccesso o energia non integrata: non è automaticamente negativa.
- Evita generalità. Collega ogni passaggio a carte/posizioni o parole esplicite del contesto.
- Se la stesa contraddice l'aspettativa dell'utente, dillo con tatto.
- Non citare tecniche psicologiche o il processo con cui formuli la lettura.

LINGUA OBBLIGATORIA: scrivi ogni valore testuale naturale del JSON in {target_language}.
Mantieni i nomi canonici delle carte nel campo "carta"; traduci posizioni e spiegazioni quando serve.
Le chiavi JSON restano esattamente quelle indicate sotto.

STILE:
{target_language} naturale, caldo, preciso. Prima persona come Raffaello. Niente gergo R³∞ nel messaggio principale. Deve sembrare un messaggio personale, non un report.

OUTPUT SOLO JSON valido:
{
 "apertura":"2-4 frasi molto chiare",
 "contesto_compreso":"cosa hai capito, senza inventare",
 "carte":[{"posizione":"...","carta":"...","significato":"spiegazione semplice","nel_contesto":"lettura specifica"}],
 "trama":"come le carte costruiscono una storia unica",
 "tensione_centrale":"il nodo principale",
 "sintesi":"4-7 frasi chiare che potresti dire direttamente all'utente",
 "direzione":"una direzione concreta ma non prescrittiva",
 "domanda_finale":"una sola domanda molto mirata",
 "livello":"AI_CONTEXTUAL"
}"""
    user=json.dumps({"domanda":question or None,"contesto_aggiuntivo":context or None,"focus":focus or None,"emozione_dichiarata":emotion or None,"lingua":language,"carte":cards,"strutturale":{"sinossi":structural.sinossi,"tensioni":structural.tensioni,"risorse":structural.risorse,"relazioni":structural.relazioni,"distribuzione_stati":structural.distribuzione_stati,"distribuzione_elementi":structural.distribuzione_elementi},"ponte_base":personal.ponte,"collasso_base":personal.punto_di_collasso,"domande_base":personal.domande_di_riflessione,"integrazione_base":personal.integrazione},ensure_ascii=False)
    try:from sdq1.llm.providers import AnthropicProvider,GeminiProvider
    except Exception:return None,None
    providers=[(GeminiProvider,"gemini-2.5-flash",{"json_mode":True,"temperatura":0.5,"max_token":3400,"timeout":32}),(AnthropicProvider,"claude-haiku-4-5-20251001",{"temperatura":0.45,"max_token":3400,"timeout_secondi":32})]
    for cls,model,opts in providers:
        try:
            p=cls(modello=model,api_key=None,**opts)
            if not p.disponibile:continue
            r=p.completa(system,user)
            if r.errore:continue
            parsed=_safe_json(r.testo)
            if isinstance(parsed,dict) and isinstance(parsed.get("carte"),list):return parsed,{"provider":r.provider,"modello":r.modello,"via_api":r.via_api,"latenza_ms":r.latenza_ms}
        except Exception:continue
    return None,None


def _manual_spread(items):
    if not isinstance(items,list) or not 1<=len(items)<=7:return None,"carte_scelte deve contenere da 1 a 7 carte"
    spread=Stesa(schema=f"manuale_guidata_{len(items)}_carte");labels=[];seen=set()
    for i,item in enumerate(items,1):
        if not isinstance(item,dict):return None,"carta manuale non valida"
        name=_clean_text(item.get("carta"),120);card=cerca_carta(name)
        if not card:return None,f"carta non riconosciuta: {name}"
        if card.nome in seen:return None,"la stessa carta non può comparire due volte nella stessa stesa"
        seen.add(card.nome)
        pos=_POSITIONS.get(_clean_text(item.get("posizione"),30),TipoPosizione.PRESENTE)
        state=_STATES.get(_clean_text(item.get("stato"),30),_state_for(pos))
        orient=_ORIENTATIONS.get(_clean_text(item.get("orientamento"),30),OrientamentoCarta.DIRITTA)
        spread.aggiungi(card,state,pos,i,orient);labels.append(_MANUAL_LABELS.get(pos,pos.value.capitalize()))
    return (spread,labels),None


def _build(body):
    question=_clean_text(body.get("domanda"),1800);context=_clean_text(body.get("contesto"),3200);focus=_clean_text(body.get("focus"),40).lower();emotion=_clean_text(body.get("emozione"),120);requested=_clean_text(body.get("profondita"),10).lower() or "auto";language=_language(body.get("lingua") or body.get("language"))
    if focus not in _FOCUS:focus="altro"
    manual=body.get("carte_scelte")
    if not question and not context and not manual:return None,("scrivi una domanda o un contesto da esplorare",400)

    if manual:
        built,error=_manual_spread(manual)
        if error:return None,(error,400)
        spread,labels=built;count=len(spread.nodi);reason=f"Hai scelto personalmente {count} {'carta' if count==1 else 'carte'}; Raffaello ne conserva esattamente ordine, posizione e orientamento."
        extraction="scelta_manuale_utente"
    else:
        count,reason=_depth(question,context,focus,requested);selected=_draw(count);layout=_LAYOUTS[count];spread=Stesa(schema=f"raffaello_{count}_carte");labels=[]
        for i,(card,(position,label)) in enumerate(zip(selected,layout),1):spread.aggiungi(card,_state_for(position),position,i,_orientation());labels.append(label)
        extraction="casuale_server_side"

    proto=DoppiaErmeneutica();structural=proto.leggi_struttura(spread)
    personal_context=ContestoPersonale(domanda=question or None,momento_vita=context or None,emozione_prevalente=emotion or None,aspetto_focus=focus or None,disponibilita_collasso=True)
    personal=proto.leggi_personale(structural,personal_context);cards=[_card_payload(n,l) for n,l in zip(spread.nodi,labels)]
    reading,provider_meta=_ai_reading(structural,personal,cards,question,context,focus,emotion,language)
    if reading is None:reading=_fallback(personal,cards,question,focus,language)
    reading.setdefault("lingua", language)
    return {"lettura_id":str(uuid.uuid4()),"metodo":{"sistema":"Tarocchi R³∞ · Raffaello","numero_carte":count,"schema":spread.schema,"perche_questa_stesa":reason,"estrazione":extraction,"fatti_privati_inventati":False},"contesto":{"domanda":question or None,"focus":focus or None,"emozione":emotion or None,"lingua":language},"carte":cards,"strutturale":{"sinossi":structural.sinossi,"tensioni":structural.tensioni,"risorse":structural.risorse,"relazioni":structural.relazioni,"assiomi_attivati":structural.assiomi_attivati},"lettura":reading,"motore":provider_meta or {"provider":"deterministic-fallback","via_api":False},"epistemica":"INTERPRETAZIONE_SIMBOLICA_NON_PREVISIONE_CERTA","lingua":language},None


def _response():
    if request.method=="OPTIONS":return "",200
    body=request.get_json(silent=True)
    if not isinstance(body,dict):return jsonify({"errore":"serve un oggetto JSON"}),400
    result,error=_build(body)
    if error:return jsonify({"errore":error[0]}),error[1]
    response=jsonify(result);response.headers["Cache-Control"]="no-store";response.headers["X-Content-Type-Options"]="nosniff";return response


@app.route("/api/tarocchi/raffaello",methods=["POST","OPTIONS"])
def tarot_raffaello():return _response()

@app.route("/",methods=["POST","OPTIONS"])
def root():return _response()
