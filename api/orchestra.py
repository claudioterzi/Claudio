"""Authenticated multi-provider orchestra for free Raffaello dialogue.

This endpoint never receives or returns provider API keys. Providers are enabled only
when their runtime secrets already exist. Tarot/Alpha readings remain on the dedicated
engine in api/raffaello.py.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import secrets
from typing import Any

from flask import Flask, jsonify, request

from sdq1.config import carica_config
from sdq1.llm.router import PROVIDER_REGISTRY
from typesafe_sister.universal import assess_project_state

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024

_ALLOWED_LANGUAGES = {"it", "en", "fr", "es"}
_CLOUD_PROVIDERS = ("gemini", "anthropic", "grok", "openai", "deepseek", "perplexity", "minimax")
_SYNTHESIS_PRIORITY = ("openai", "gemini", "anthropic", "deepseek", "grok", "minimax", "perplexity")


def _clean(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())[:limit]


def _authorized() -> bool:
    expected = os.getenv("RAFFAELLO_BRIDGE_SECRET", "")
    supplied = request.headers.get("X-Raffaello-Secret", "")
    return len(expected) >= 32 and secrets.compare_digest(expected.encode(), supplied.encode())


def _history(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    result: list[dict[str, str]] = []
    for item in raw[-8:]:
        if not isinstance(item, dict):
            continue
        question = _clean(item.get("domanda"), 1000)
        answer = _clean(item.get("risposta"), 1800)
        if question or answer:
            result.append({"domanda": question, "risposta": answer})
    return result


def _models_from_config() -> tuple[dict[str, str], dict[str, Any]]:
    cfg = carica_config()
    rules = cfg.router.get("regole") or []
    default = next((r for r in rules if r.get("profilo") == "default"), {})
    models = dict(default.get("modelli") or {})
    opts = dict(cfg.modello)
    # Provider classes expect these normalized option names.
    opts["max_token"] = min(int(opts.get("max_token", 4096)), 1200)
    opts["temperatura"] = 0.45
    opts["timeout_secondi"] = 24
    return models, opts


def _system_prompt(language: str) -> str:
    names = {"it": "italiano", "en": "English", "fr": "français", "es": "español"}
    return (
        "Sei un membro dell'Orchestra Raffaello/SDQ-1. Rispondi alla domanda concreta "
        f"in {names.get(language, 'italiano')}. Produci una conclusione utile, non una catena di pensiero. "
        "P5: non trattare come prova una risposta di un altro modello. "
        "P6: quando una conclusione dipende da un fatto verificabile, indica brevemente come verificarlo. "
        "Distingui fatti, interpretazioni e ipotesi quando serve. Non inventare accessi, azioni o risultati. "
        "Se ricevi typesafe_advisory, trattalo come una contro-verifica strutturata: non è una fonte, "
        "non è un'autorizzazione e non prevale sui fatti. Puoi dissentire quando l'evidenza lo richiede."
    )


def _call_provider(name: str, model: str, opts: dict[str, Any], system: str, user: str) -> dict[str, Any] | None:
    cls, _ = PROVIDER_REGISTRY[name]
    try:
        provider = cls(modello=model, api_key=None, **opts)
        if not provider.disponibile:
            return None
        response = provider.completa(system, user)
        if not response.via_api or not response.testo.strip():
            return None
        return {
            "provider": response.provider,
            "modello": response.modello,
            "testo": response.testo.strip()[:5000],
            "latenza_ms": response.latenza_ms,
        }
    except Exception:
        return None


def _compact_typesafe(advisory: dict[str, Any]) -> dict[str, Any]:
    if advisory.get("status") != "evaluated":
        return {"status": advisory.get("status", "unavailable")}
    return {
        "status": "evaluated",
        "project": advisory.get("project"),
        "focus": advisory.get("focus"),
        "scores": {
            key: {"score": value.get("score"), "confidence": value.get("confidence")}
            for key, value in (advisory.get("scores") or {}).items()
            if isinstance(value, dict)
        },
        "flags": advisory.get("flags"),
        "policy_version": advisory.get("policy_version"),
    }


def _collect(question: str, history: list[dict[str, str]], language: str,
             typesafe_advisory: dict[str, Any]) -> list[dict[str, Any]]:
    models, opts = _models_from_config()
    system = _system_prompt(language)
    user = json.dumps({
        "domanda": question,
        "cronologia": history,
        "typesafe_advisory": _compact_typesafe(typesafe_advisory),
    }, ensure_ascii=False)
    calls: list[tuple[str, str]] = []
    for name in _CLOUD_PROVIDERS:
        if name not in PROVIDER_REGISTRY:
            continue
        _, default_model = PROVIDER_REGISTRY[name]
        calls.append((name, models.get(name, default_model)))

    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(7, len(calls) or 1)) as pool:
        futures = {
            pool.submit(_call_provider, name, model, opts, system, user): name
            for name, model in calls
        }
        try:
            for future in concurrent.futures.as_completed(futures, timeout=30):
                item = future.result()
                if item:
                    results.append(item)
        except TimeoutError:
            pass
    results.sort(key=lambda item: (_CLOUD_PROVIDERS.index(item["provider"]) if item["provider"] in _CLOUD_PROVIDERS else 99))
    return results


def _synthesize(question: str, contributions: list[dict[str, Any]], language: str,
                typesafe_advisory: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if not contributions:
        raise RuntimeError("nessun provider disponibile")
    if len(contributions) == 1:
        item = contributions[0]
        return item["testo"], {"provider": item["provider"], "modello": item["modello"], "modo": "singolo"}

    by_name = {item["provider"]: item for item in contributions}
    chosen = next((by_name[name] for name in _SYNTHESIS_PRIORITY if name in by_name), contributions[0])
    models, opts = _models_from_config()
    opts = dict(opts)
    opts["max_token"] = 1800
    system = (
        _system_prompt(language)
        + " Sei il sintetizzatore finale. Le risposte sotto sono contributi indipendenti, non fonti. "
          "Conserva i punti convergenti, segnala i disaccordi materialmente importanti e non creare un falso consenso. "
          "Restituisci una sola risposta naturale per Claudio, senza nominare il processo interno salvo che il disaccordo sia utile."
    )
    compact = [
        {"provider": item["provider"], "testo": item["testo"][:2600]}
        for item in contributions
    ]
    user = json.dumps({
        "domanda": question,
        "contributi": compact,
        "typesafe_advisory": _compact_typesafe(typesafe_advisory),
    }, ensure_ascii=False)
    final = _call_provider(chosen["provider"], chosen["modello"], opts, system, user)
    if final:
        return final["testo"], {"provider": final["provider"], "modello": final["modello"], "modo": "sintesi"}
    return chosen["testo"], {"provider": chosen["provider"], "modello": chosen["modello"], "modo": "fallback"}


def _response():
    if request.method == "GET":
        return jsonify(servizio="Raffaello Orchestra", pronto=True)
    if not _authorized():
        return jsonify(errore="Accesso non autorizzato."), 401
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(errore="Serve un oggetto JSON."), 400
    question = _clean(body.get("domanda"), 4000)
    if not question:
        return jsonify(errore="Domanda non valida."), 400
    language = _clean(body.get("lingua") or "it", 8).lower()
    if language not in _ALLOWED_LANGUAGES:
        language = "it"
    history = _history(body.get("cronologia"))
    project = _clean(body.get("progetto") or body.get("project") or body.get("project_id") or "general", 120) or "general"

    # One bounded System One call supplies a structured second judgment for every
    # project using the common Orchestra. It never grants permission or executes.
    typesafe_advisory = assess_project_state(project, {
        "question": question,
        "history": history,
        "language": language,
    })

    contributions = _collect(question, history, language, typesafe_advisory)
    if not contributions:
        return jsonify(errore="Nessun provider AI configurato o raggiungibile."), 503
    answer, synthesizer = _synthesize(question, contributions, language, typesafe_advisory)
    return jsonify(
        risposta=answer[:8000],
        motore={
            "tipo": "orchestra",
            "provider": [
                {"nome": item["provider"], "modello": item["modello"], "latenza_ms": item["latenza_ms"]}
                for item in contributions
            ],
            "sintetizzatore": synthesizer,
            "typesafe": typesafe_advisory,
        },
        riferimenti=[],
        lingua=language,
    )


@app.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.route("/api/orchestra", methods=["GET", "POST"])
def orchestra():
    return _response()


@app.route("/", methods=["GET", "POST"])
def root():
    return _response()
