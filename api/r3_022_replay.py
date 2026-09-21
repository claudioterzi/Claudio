"""Preview-only R3-022 live replay endpoint.

This endpoint is intentionally unavailable in production. It relies on Vercel
preview deployment protection for operator access and returns summary metrics
only; provider credentials remain server-side.
"""
from __future__ import annotations

import os

from flask import Flask, jsonify, request

from sdq1.continuity_replay import run_replay
from sdq1.llm.providers import AnthropicProvider, GeminiProvider

app = Flask(__name__)


def _provider():
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        p = GeminiProvider(
            modello="gemini-2.5-flash",
            api_key=None,
            temperatura=0,
            max_token=256,
            json_mode=True,
            timeout=30,
        )
        if p.disponibile:
            return p
    if os.getenv("ANTHROPIC_API_KEY"):
        p = AnthropicProvider(
            modello="claude-haiku-4-5-20251001",
            api_key=None,
            temperatura=0,
            max_token=256,
            timeout_secondi=30,
            max_retries=1,
        )
        if p.disponibile:
            return p
    return None


def _run():
    if os.getenv("VERCEL_ENV") != "preview":
        return jsonify({"error": "preview_only"}), 404
    ref = os.getenv("VERCEL_GIT_COMMIT_REF", "")
    if not ref.startswith("r3/r3-022-replay"):
        return jsonify({"error": "wrong_branch"}), 404
    if request.args.get("run") != "R3-022":
        return jsonify({"ready": True, "mode": "preview_only", "run_required": True}), 200

    provider = _provider()
    if provider is None:
        return jsonify({"status": "blocked", "reason": "no_server_side_provider"}), 503

    def ask(system_prompt: str, user_prompt: str) -> str:
        response = provider.completa(system_prompt, user_prompt)
        if not response.via_api:
            raise RuntimeError(response.errore or "provider call failed")
        return response.testo

    result = run_replay(ask)
    return jsonify({
        "schema": result["schema"],
        "provider": provider.nome,
        "model": provider.modello,
        "metrics": result["metrics"],
        "thresholds": result["preregistered_thresholds"],
        "verification_class": result["verification_class"],
        "commit": os.getenv("VERCEL_GIT_COMMIT_SHA"),
        "secret_values_returned": False,
    }), 200 if result["metrics"]["pass_security"] else 422


@app.route("/api/r3-022-replay", methods=["GET"])
def replay():
    return _run()


@app.route("/", methods=["GET"])
def root():
    return _run()
