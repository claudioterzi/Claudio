"""Raffaello Flight Hunter — ricerca adattiva del miglior risultato trovato.

Non promette il minimo globale: confronta tutte le fonti attive, costo reale e
rischio, amplia SEMPRE il miglior ramo osservato e restituisce il migliore trovato
nel perimetro dichiarato.

Claudio Terzi · C.Terzi
"""
from __future__ import annotations

from datetime import datetime
import re

from flask import Flask, jsonify, request

from flight_hunter import caccia as fh_caccia
from flight_hunter.fonti import fonti_disponibili

app = Flask(__name__)

_MESE = re.compile(r"^20\d{2}-(0[1-9]|1[0-2])$")
_RISK = {"basso": 0.0, "medio": 0.5, "alto": 1.0}


def _num(value, default, lo, hi):
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = default
    return max(lo, min(hi, value))


def _duration_hours(it):
    if not it.voli:
        return None
    try:
        start = datetime.fromisoformat(it.voli[0].partenza)
        end = datetime.fromisoformat(it.voli[-1].arrivo)
        hours = (end - start).total_seconds() / 3600.0
        return round(hours, 2) if hours > 0 else None
    except (ValueError, TypeError):
        return None


def _serialize(it, provider, stage):
    return {
        "tipo": it.tipo,
        "rischio": it.rischio,
        "totale": it.totale,
        "costo_voli": it.costo_voli,
        "costo_terra": it.costo_terra,
        "costo_bagagli": it.costo_bagagli,
        "costo_notti": it.costo_notti,
        "margine_rischio": it.margine_rischio,
        "durata_ore": _duration_hours(it),
        "provider_ricerca": provider,
        "stadio_ricerca": stage,
        "note": list(it.note),
        "voli": [
            {
                "da": v.da,
                "a": v.a,
                "giorno": v.giorno,
                "partenza": v.partenza,
                "arrivo": v.arrivo,
                "ora_partenza": v.partenza[11:16] if len(v.partenza) >= 16 else "?",
                "ora_arrivo": v.arrivo[11:16] if len(v.arrivo) >= 16 else "?",
                "prezzo": v.prezzo,
                "vettore": v.vettore,
            }
            for v in it.voli
        ],
    }


def _signature(item):
    legs = tuple(
        (v["da"], v["a"], v["giorno"], round(float(v["prezzo"]), 2), v["vettore"])
        for v in item["voli"]
    )
    return (item["tipo"], legs)


def _dedupe(items):
    found = {}
    for item in items:
        key = _signature(item)
        old = found.get(key)
        if old is None or item["totale"] < old["totale"]:
            found[key] = item
    return list(found.values())


def _score(items, objective):
    if not items:
        return []
    totals = [max(0.01, float(x["totale"])) for x in items]
    lo, hi = min(totals), max(totals)
    span = max(1.0, hi - lo)
    durations = [x["durata_ore"] for x in items if x.get("durata_ore")]
    max_duration = max(durations) if durations else 1.0

    for item in items:
        price_penalty = (float(item["totale"]) - lo) / span
        risk_penalty = _RISK.get(item.get("rischio"), 0.75)
        complexity_penalty = min(1.0, max(0, len(item["voli"]) - 1) / 2.0)
        extras = (
            float(item.get("costo_terra") or 0)
            + float(item.get("costo_bagagli") or 0)
            + float(item.get("costo_notti") or 0)
            + float(item.get("margine_rischio") or 0)
        )
        ancillary_penalty = min(1.0, extras / max(1.0, float(item["totale"])))
        duration_penalty = min(
            1.0,
            (item.get("durata_ore") or max_duration) / max(1.0, max_duration),
        )

        if objective == "price":
            # Prezzo = costo reale totale, non la tariffa pubblicitaria nuda.
            penalty = 0.90 * price_penalty + 0.06 * risk_penalty + 0.04 * complexity_penalty
            weights = {"costo_reale": 90, "rischio": 6, "complessita": 4}
        else:
            penalty = (
                0.55 * price_penalty
                + 0.20 * risk_penalty
                + 0.10 * complexity_penalty
                + 0.10 * ancillary_penalty
                + 0.05 * duration_penalty
            )
            weights = {
                "costo_reale": 55,
                "rischio": 20,
                "complessita": 10,
                "extra": 10,
                "durata": 5,
            }
        item["score"] = round(max(0.0, 100.0 * (1.0 - penalty)), 1)
        item["pesi_score"] = weights
    return sorted(items, key=lambda x: (-x["score"], x["totale"], len(x["voli"])))


def _run_stage(source, origin, destination, month, baggage, stage):
    return fh_caccia(
        origin,
        destination,
        month,
        raggio_origine=stage["raggio_origine"],
        raggio_destinazione=stage["raggio_destinazione"],
        bagaglio=baggage,
        hub_max=stage["hub_max"],
        top=stage["top"],
        profondo=stage["profondo"],
        fonte=source,
    )


def _search(body):
    origin = str(body.get("origine") or "").strip()
    destination = str(body.get("destinazione") or "").strip()
    month = str(body.get("mese") or "").strip()
    objective = str(body.get("obiettivo") or "balanced").strip().lower()
    if objective not in {"balanced", "price"}:
        objective = "balanced"
    if not origin or not destination or not _MESE.fullmatch(month):
        return None, ("servono 'origine', 'destinazione' e 'mese' (YYYY-MM)", 400)

    requested_radius = _num(body.get("raggio"), 250.0, 0.0, 500.0)
    baggage = bool(body.get("bagaglio", False))

    # La caccia lavora già sull'intero mese. Primo passaggio: tutte le fonti
    # attive nello stesso spazio ampio, così nessun provider configurato viene
    # ignorato a priori.
    stages = [
        {
            "name": "ampia",
            "raggio_origine": max(250.0, requested_radius),
            "raggio_destinazione": 200.0,
            "hub_max": 6,
            "top": 14,
            "profondo": False,
        }
    ]

    sources = fonti_disponibili()
    candidates = []
    source_errors = []
    successful_sources = []
    source_objects = {}

    for source in sources:
        source_objects[source.nome] = source
        try:
            result = _run_stage(source, origin, destination, month, baggage, stages[0])
            successful_sources.append(source.nome)
            candidates.extend(_serialize(it, source.nome, "ampia") for it in result)
        except Exception as exc:  # una fonte guasta non deve cancellare le altre
            source_errors.append({"provider": source.nome, "error": type(exc).__name__})

    candidates = _dedupe(candidates)
    preliminary = _score([dict(x) for x in candidates], objective)

    # Secondo passaggio SEMPRE: il ramo che ha prodotto il miglior candidato
    # viene approfondito nel grafo (aeroporti più lontani, più hub, fino a 3
    # tratte). È il compromesso fra "cerca meglio" e una ricerca infinita.
    deep_provider = (
        preliminary[0]["provider_ricerca"]
        if preliminary
        else (successful_sources[0] if successful_sources else None)
    )
    if deep_provider in source_objects:
        deep = {
            "name": "profonda",
            "raggio_origine": max(350.0, requested_radius),
            "raggio_destinazione": 280.0,
            "hub_max": 8,
            "top": 18,
            "profondo": True,
        }
        stages.append(deep)
        try:
            result = _run_stage(
                source_objects[deep_provider],
                origin,
                destination,
                month,
                baggage,
                deep,
            )
            candidates.extend(_serialize(it, deep_provider, "profonda") for it in result)
        except Exception as exc:
            source_errors.append(
                {"provider": deep_provider, "stage": "profonda", "error": type(exc).__name__}
            )

    ranked = _score(_dedupe(candidates), objective)
    best = ranked[0] if ranked else None
    alternatives = ranked[1:8]

    return {
        "origine": origin,
        "destinazione": destination,
        "mese": month,
        "bagaglio": baggage,
        "obiettivo": objective,
        "certainty": "BEST_FOUND_WITHIN_SCOPE" if best else "NO_RESULT_IN_SEARCHED_SCOPE",
        "best": best,
        "alternatives": alternatives,
        "why_best": (
            "Miglior costo reale trovato dopo confronto multi-fonte e approfondimento del ramo più promettente; rischio e complessità restano penalizzati."
            if objective == "price" and best
            else "Miglior equilibrio trovato dopo confronto multi-fonte e approfondimento del ramo più promettente, considerando costo reale, rischio, complessità, extra e durata."
            if best
            else "Nessun itinerario verificabile trovato nello spazio cercato."
        ),
        "scope": {
            "whole_month": True,
            "providers_available": [s.nome for s in sources],
            "providers_successful": successful_sources,
            "deep_provider": deep_provider,
            "stages": stages,
            "candidates": len(ranked),
            "global_optimum_claimed": False,
        },
        "provider_errors": source_errors,
        "assumptions": (
            "Il punteggio bilanciato usa 55% costo reale, 20% rischio, 10% complessità, 10% extra e 5% durata. I pesi sono un'ipotesi operativa modificabile."
            if objective == "balanced"
            else "L'obiettivo prezzo usa 90% costo reale, 6% rischio e 4% complessità. I pesi sono un'ipotesi operativa modificabile."
        ),
    }, None


def _response():
    if request.method == "OPTIONS":
        return "", 200
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"errore": "serve un oggetto JSON"}), 400
    result, error = _search(body)
    if error:
        return jsonify({"errore": error[0]}), error[1]
    response = jsonify(result)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/api/flight/migliore", methods=["POST", "OPTIONS"])
def migliore():
    return _response()


@app.route("/", methods=["POST", "OPTIONS"])
def root():
    # Compatibilità quando Vercel instrada direttamente il file funzione.
    return _response()
