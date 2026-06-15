"""SDQ-1 API minimale — BETA endpoint per sviluppatori.

Avvio:
    python api/server.py

Endpoint:
    POST /ask          — chiama l'orchestratore SDQ-1
    GET  /health       — stato provider + metriche
    GET  /futures      — lista scenari disponibili
    POST /futures/run  — esegui scenari in parallelo

Auth:
    Header: X-API-Key <chiave>
    Chiavi configurate in .env → SDQ1_API_KEYS (comma-separated)
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

# Assicura che il progetto sia nel path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sdq1.__main__ import _carica_dotenv, costruisci_sistema

_carica_dotenv()

try:
    from flask import Flask, jsonify, request, abort
except ImportError:
    print("Flask non installato. Esegui: pip install flask")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")

app = Flask(__name__)

_API_KEYS: set[str] = set(
    k.strip()
    for k in os.getenv("SDQ1_API_KEYS", "").split(",")
    if k.strip()
)
_sistema = None


def _get_sistema():
    global _sistema
    if _sistema is None:
        _sistema = costruisci_sistema()
    return _sistema


def _auth():
    if not _API_KEYS:
        return  # nessuna chiave configurata → accesso libero (dev mode)
    chiave = request.headers.get("X-API-Key", "")
    if chiave not in _API_KEYS:
        abort(401, "X-API-Key non valida o mancante")


@app.route("/monitor", methods=["GET"])
def monitor_data():
    """Restituisce lo stato live del sistema SDQ-1 in JSON — senza auth, senza LLM."""
    ROOT = Path(__file__).resolve().parent.parent
    out = {}

    # --- stato_sdq1.json ---
    stato_file = ROOT / "output" / "stato_sdq1.json"
    if stato_file.exists():
        try:
            out["stato"] = json.loads(stato_file.read_text(encoding="utf-8"))
        except Exception:
            out["stato"] = {}

    # --- registro_ipotesi.json ---
    ipotesi_file = ROOT / "registro_ipotesi.json"
    if ipotesi_file.exists():
        try:
            out["ipotesi"] = json.loads(ipotesi_file.read_text(encoding="utf-8"))
        except Exception:
            out["ipotesi"] = {}

    # --- contatti.jsonl ---
    contatti_file = ROOT / "output" / "contatti.jsonl"
    if contatti_file.exists():
        try:
            righe = [json.loads(r) for r in contatti_file.read_text(encoding="utf-8").splitlines() if r.strip()]
            umani = [v for v in righe if v.get("umano", True)]
            persone = list({v.get("persona") for v in umani if v.get("persona")})
            out["contatti"] = {
                "totale": len(righe),
                "umani": len(umani),
                "persone": persone,
                "ultima_data": righe[-1]["data"] if righe else None,
            }
        except Exception:
            out["contatti"] = {}

    # --- benchmark ---
    bench_dir = ROOT / "output" / "benchmark"
    if bench_dir.exists():
        snapshots = sorted(bench_dir.glob("*.json"))
        out["benchmark"] = {
            "n_snapshot": len(snapshots),
            "ultimo": snapshots[-1].name if snapshots else None,
        }

    import datetime
    out["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return jsonify(out)



def health():
    orch, router, memoria, stato, metrics, health_checker, vss = _get_sistema()
    riepilogo = health_checker.riepilogo()
    riepilogo["vss_size"] = vss.dimensione()
    riepilogo["memoria_size"] = memoria.dimensione()
    riepilogo["circuit_breaker"] = router.stato_circuit_breaker()
    _cf = Path("output/contatti.jsonl")
    if _cf.exists():
        righe = [json.loads(r) for r in _cf.read_text(encoding="utf-8").splitlines() if r]
        umani = [v for v in righe if v.get("umano", True)]
        persone = len({v.get("persona", v.get("nota", ""))[:40] for v in umani})
        riepilogo["h2_persone_reali_raggiunte"] = persone
    return jsonify(riepilogo)


@app.route("/ask", methods=["POST"])
def ask():
    _auth()
    body = request.get_json(force=True, silent=True) or {}
    testo = body.get("testo", "").strip()
    if not testo:
        abort(400, "Campo 'testo' obbligatorio")

    orch, router, memoria, stato, metrics, health_checker, vss = _get_sistema()
    t0 = time.monotonic()
    esecuzione = orch.esegui({"testo": testo})
    durata_ms = int((time.monotonic() - t0) * 1000)

    risposta = (esecuzione.output_finale or {}).get("risposta_finale", "")
    return jsonify({
        "risposta": risposta,
        "durata_ms": durata_ms,
        "interrotta": esecuzione.interrotta,
        "motivo_interruzione": esecuzione.motivo_interruzione,
        "provider": [
            (p.metadata or {}).get("provider") for p in esecuzione.passi
            if (p.metadata or {}).get("provider")
        ],
    })


@app.route("/futures", methods=["GET"])
def futures_list():
    from sdq1.futures import SCENARI_DEFAULT
    return jsonify([
        {
            "id": s.id,
            "titolo": s.titolo,
            "orizzonte": s.orizzonte,
            "dominio": s.dominio,
        }
        for s in SCENARI_DEFAULT
    ])


@app.route("/futures/run", methods=["POST"])
def futures_run():
    _auth()
    body = request.get_json(force=True, silent=True) or {}
    ids = body.get("scenari")  # None = tutti

    from sdq1.futures import SimulatoreScenari, SCENARI_DEFAULT
    orch, router, *_ = _get_sistema()

    def _llm_fn(sistema, utente):
        esito = router.chiama(sistema, utente, profilo="default")
        return esito.risposta.testo, esito.risposta.provider, int(esito.risposta.latenza_ms or 0)

    scenari_sel = [s for s in SCENARI_DEFAULT if ids is None or s.id in ids]
    sim = SimulatoreScenari(llm_fn=_llm_fn)
    risultati = sim.simula_parallelo(scenari_sel)
    dest = sim.salva_report(risultati)

    return jsonify({
        "n_scenari": len(risultati),
        "n_successi": sum(1 for r in risultati if r.successo),
        "report_salvato": str(dest),
        "scenari": [r.to_dict() for r in risultati],
    })


if __name__ == "__main__":
    port = int(os.getenv("SDQ1_PORT", "8000"))
    debug = os.getenv("SDQ1_DEBUG", "").lower() in ("1", "true", "yes")
    print(f"SDQ-1 API avviata su http://0.0.0.0:{port}")
    print(f"Auth: {'attiva (' + str(len(_API_KEYS)) + ' chiavi)' if _API_KEYS else 'disabilitata (dev mode)'}")
    app.run(host="0.0.0.0", port=port, debug=debug)
