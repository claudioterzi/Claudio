"""Temporary, fixed DeepSeek evaluation endpoint.

No user input is accepted and no credential is returned. The project-level Vercel
protection remains the outer access control. Remove after the evaluation.
"""
from __future__ import annotations

import os

from flask import Flask, jsonify

from sdq1.llm.providers import DeepSeekProvider

app = Flask(__name__)

_PROMPT = """Test di pianificazione quantitativa. Dai solo risposta finale e calcoli sintetici, non una catena di pensiero.

Devi instradare 100 richieste: 60 semplici, 30 medie, 10 critiche.
Tre modelli:
- F (Flash): costo 1 per richiesta; qualità attesa semplice 0.95, media 0.80, critica 0.60.
- P (Pro): costo 5; qualità 0.99, 0.94, 0.85.
- R (Reasoner): costo 8; qualità 0.98, 0.96, 0.96.

Vincoli di qualità MEDIA per classe:
- semplici >= 0.94
- medie >= 0.90
- critiche >= 0.95
Budget totale <= 260.

Puoi mescolare modelli dentro una stessa classe usando una regola deterministica basata su un punteggio secondario; la qualità di classe è la media attesa delle richieste di quella classe.

Trova il routing a costo minimo che rispetta tutti i vincoli. Dimostra la minimalità con pochi calcoli. Se fosse impossibile, indica la più piccola rilassazione necessaria."""


@app.route("/api/deepseek-eval", methods=["GET"])
def eval_deepseek():
    configured = bool(os.getenv("DEEPSEEK_API_KEY"))
    if not configured:
        return jsonify(configured=False, ok=False, error="DEEPSEEK_API_KEY non presente nel runtime"), 503
    provider = DeepSeekProvider(
        modello="deepseek-flash",
        api_key=None,
        max_token=1400,
        temperatura=0.0,
        timeout_secondi=45,
    )
    if not provider.disponibile:
        return jsonify(configured=True, ok=False, error="Provider non disponibile"), 503
    result = provider.completa(
        "Sei un valutatore tecnico. Risolvi il problema con calcoli controllabili e una conclusione concisa.",
        _PROMPT,
    )
    return jsonify(
        configured=True,
        ok=bool(result.via_api and result.testo.strip()),
        provider=result.provider,
        modello=result.modello,
        latenza_ms=result.latenza_ms,
        risposta=result.testo.strip()[:12000],
        errore=(result.errore or "")[:500],
    )


@app.route("/", methods=["GET"])
def root():
    return eval_deepseek()
