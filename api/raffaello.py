"""Private Telegram continuity and shared Raffaello engine. Claudio Terzi · C.Terzi."""
from __future__ import annotations

import json
import os
import re
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
COOKIE = "__Host-raffaello"
PREFIX = "/api/raffaello"


class BridgeError(Exception):
    def __init__(self, message, status=503):
        super().__init__(message)
        self.status = status


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _secret():
    return os.getenv("RAFFAELLO_BRIDGE_SECRET", "")


def _configured():
    return len(_secret()) >= 32 and bool(os.getenv("RAFFAELLO_BOT_URL"))


def _bridge(method, path, body=None, token=None):
    base = os.getenv("RAFFAELLO_BOT_URL", "").rstrip("/")
    parsed = urlparse(base)
    if not _configured() or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
        raise BridgeError("Il collegamento Telegram sarà disponibile appena attivato.")
    headers = {"X-Raffaello-Secret": _secret(), "Content-Type": "application/json"}
    if token:
        headers["X-Raffaello-Session"] = token
    req = Request(base + "/raffaello/v1" + path, headers=headers, method=method,
                  data=json.dumps(body).encode() if body is not None else None)
    try:
        with build_opener(NoRedirect).open(req, timeout=75 if path.endswith("/analyze") else 15) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError("oversize")
            data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("not an object")
        return data
    except HTTPError as exc:
        status = exc.code if exc.code in (400, 401, 403, 404, 409, 429, 502, 503) else 503
        messages = {401: "Collega il sito con un nuovo codice /collega del bot.", 403: "Account non abilitato.",
                    404: "Questa lettura o domanda non è disponibile nel tuo account.",
                    409: "L'operazione è già in corso oppure il contesto è cambiato. Riapri la lettura.",
                    429: "Limite di analisi raggiunto. Riprova più tardi.", 400: "Controlla il testo e i dati della lettura."}
        raise BridgeError(messages.get(status, "Raffaello non è raggiungibile. La domanda salvata può essere riprovata."), status) from exc
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise BridgeError("Il bot non è raggiungibile in questo momento. Riprova tra poco.") from exc


def _engine(body):
    from api import tarot_alpha as alpha
    question = body.get("domanda")
    if not isinstance(question, str) or not question.strip() or len(question) > 4000:
        raise BridgeError("Domanda non valida.", 400)
    history = alpha._follow_up_history(body.get("cronologia"))
    snapshot = body.get("lettura")
    if snapshot is not None:
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("carte"), list) or not snapshot["carte"]:
            raise BridgeError("Manca la lettura già estratta.", 400)
        for item in snapshot["carte"]:
            if not isinstance(item, dict) or item.get("asse") not in alpha.VALID_AXES or item.get("polarita") not in alpha.VALID_POLARITIES:
                raise BridgeError("Direzione o polarità non valida.", 400)
        try:
            cards, _ = alpha._normalize_items({"carte_scelte": snapshot["carte"]})
        except (ValueError, TypeError, AttributeError, RuntimeError) as exc:
            raise BridgeError("Canone Alpha non valido.", 400) from exc
        language = alpha._language(body.get("lingua") or body.get("language") or snapshot.get("lingua") or snapshot.get("language"))
        answer, engine = alpha._ai_follow_up(cards, question, alpha._clean(snapshot.get("domanda"), 1800),
            alpha._clean(snapshot.get("contesto"), 3200), alpha._previous_reading(snapshot.get("lettura")), history,
            language=language, timeout_seconds=24, max_retries=0)
        if answer is None:
            raise BridgeError("Motore AI temporaneamente non disponibile.")
        return {"risposta": answer["risposta"], "motore": engine, "riferimenti": answer.get("carte_richiamate", []), "lingua": language}
    system = """Sei Raffaello, assistente del progetto Rosso Rosso Rosso di Claudio Terzi.
Parla in italiano, con calore, precisione e iniziativa. Rispondi alla domanda concreta,
senza menu di domande obbligate, slogan o spiegazioni tecniche fuori tema.
P5: non usare una tua risposta precedente come prova che sia vera. P6: quando serve,
spiega con quale riscontro distinguere un'ipotesi da un fatto. Correggiti se emergono errori.
Hai solo il testo della domanda e la cronologia fornita; non hai accesso ad altre chat,
memorie, letture, internet o strumenti operativi. Non dichiarare invii, acquisti, modifiche,
diagnosi, agenti autonomi, coscienza o ricordi che non puoi verificare.
Se manca una lettura Alpha chiedi di aprirla da /letture o collegarla dal sito:
non estrarre o inventare carte. Se c'è un problema tecnico, trattalo come un problema
tecnico: chiedi il dettaglio mancante o proponi una verifica concreta.
Puoi aiutare a sviluppare un'idea per un profumo o un progetto, distinguendo la proposta
dal risultato realizzato. Atelier e Fabbrica sono sul sito; non fingere di averli eseguiti.
Restituisci solo testo naturale, senza JSON. Non chiudere ogni risposta con una domanda.
"""
    from sdq1.llm.providers import GeminiProvider, AnthropicProvider
    user = json.dumps({"domanda": question, "cronologia": history}, ensure_ascii=False)
    providers = [(GeminiProvider, "gemini-2.5-flash", {"temperatura": 0.5, "max_token": 2200, "timeout": 24}),
                 (AnthropicProvider, "claude-haiku-4-5-20251001", {"temperatura": 0.5, "max_token": 2200, "timeout_secondi": 24, "max_retries": 0})]
    for cls, model, options in providers:
        try:
            provider = cls(modello=model, api_key=None, **options)
            if not provider.disponibile:
                continue
            response = provider.completa(system, user)
            if not response.errore and response.testo.strip():
                return {"risposta": response.testo.strip()[:8000], "motore": {"provider": response.provider, "modello": response.modello}, "riferimenti": []}
        except Exception:
            continue
    raise BridgeError("Motore AI temporaneamente non disponibile.")


@app.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.errorhandler(BridgeError)
def bridge_error(exc):
    return jsonify(errore=str(exc)), exc.status


@app.errorhandler(413)
def oversized(exc):
    return jsonify(errore="La lettura è troppo grande per il trasferimento."), 413


@app.route(PREFIX + "/<path:path>", methods=["GET", "POST", "DELETE"])
def route(path):
    body = request.get_json(silent=True) if request.method == "POST" else None
    if request.method == "POST" and not isinstance(body, dict):
        raise BridgeError("Serve un oggetto JSON.", 400)
    if path == "engine":
        if request.method != "POST" or len(_secret()) < 32 or not secrets.compare_digest(_secret().encode(), request.headers.get("X-Raffaello-Secret", "").encode()):
            raise BridgeError("Accesso non autorizzato.", 401)
        return jsonify(_engine(body))
    if path == "status" and request.method == "GET":
        return jsonify(configured=_configured())
    # Custom same-origin header + non-simple JSON request; no CORS is granted.
    if request.method in ("POST", "DELETE"):
        origin = request.headers.get("Origin")
        if request.headers.get("X-Raffaello") != "1" or (origin and origin.rstrip("/") != request.host_url.rstrip("/")):
            raise BridgeError("Riapri la pagina e riprova.", 403)
    allowed = {"session": {"GET", "DELETE"}, "link": {"POST"}, "readings": {"GET", "POST"}, "drafts": {"POST"}}
    valid = request.method in allowed.get(path, set())
    valid |= bool(request.method == "GET" and re.fullmatch(r"(?:readings|drafts)/[a-f0-9]{32}", path))
    valid |= bool(request.method == "POST" and re.fullmatch(r"drafts/[a-f0-9]{32}/analyze", path))
    if not valid:
        raise BridgeError("Percorso non disponibile.", 404)
    token = request.cookies.get(COOKIE)
    if path != "link" and not token:
        raise BridgeError("Collega prima il tuo account Telegram.", 401)
    result = _bridge(request.method, "/" + path, body, token)
    if path == "link":
        response = jsonify(linked=True)
        response.set_cookie(COOKIE, result["token"], secure=True, httponly=True, samesite="Strict", path="/", max_age=30*86400)
        return response
    response = jsonify(result)
    if path == "session" and request.method == "DELETE":
        response.delete_cookie(COOKIE, path="/", secure=True, httponly=True, samesite="Strict")
    return response
