"""POST /api/porta-consiglio {situazione} → aree proposte per un ospite.

Raggiungibile solo dal proprietario: il middleware della Porta chiude /api/porta*
a chiunque altro. È un consiglio, non crea né modifica accessi.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from porta.consiglio import consiglia  # noqa: E402

app = Flask(__name__)


@app.route("/api/porta-consiglio", methods=["POST"])
@app.route("/", methods=["POST"])
def consiglio():
    if request.headers.get("x-porta") != "1":
        return jsonify({"errore": "richiesta non valida"}), 403
    dati = request.get_json(silent=True) or {}
    situazione = dati.get("situazione")
    if not isinstance(situazione, str) or not situazione.strip():
        return jsonify({"errore": "Descrivi la situazione dell'ospite."}), 400
    return jsonify(consiglia(situazione))
