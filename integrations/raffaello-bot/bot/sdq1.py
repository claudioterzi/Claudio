"""Nucleo SDQ-1 sul server del Protocollo.

Non è la pipeline a sei agenti. Non c'è VSS. Non c'è H2.
Fa una cosa vera: etichetta un testo e risponde senza chiudere.

Ponte: se SDQ1_URL è configurata, /ask inoltra il testo al motore
esterno (i sei agenti, quando esistono). Se il ponte cade — timeout,
motore spento, risposta illeggibile — risponde il nucleo locale
e lo dichiara nella risposta. Mai spacciare il nucleo per i sei,
mai spacciare un ponte caduto per un motore vivo.
"""

from __future__ import annotations

import json
import time
import urllib.request
import uuid

from bot import config
from bot.epistemic import classify

ENGINE = "protocollo-nucleo"
VERSION = "0.2.0"


def ponte_configurato() -> bool:
    return bool(config.SDQ1_URL)


def health() -> dict:
    return {
        "ok": True,
        "engine": ENGINE,
        "version": VERSION,
        "agenti": 0,
        "vss_size": 0,
        "memoria_size": 0,
        "h2_persone_reali_raggiunte": 0,
        "ponte_sdq1": "configurato" if ponte_configurato() else "assente",
        "nota": "Non è SDQ-1 a sei agenti. È il classificatore del Protocollo, sullo stesso processo del bot.",
    }


def _chiedi_motore_esterno(testo: str, run_id: str) -> dict:
    payload = json.dumps({"testo": testo, "run_id": run_id}).encode("utf-8")
    req = urllib.request.Request(
        config.SDQ1_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=config.SDQ1_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _nucleo(testo: str) -> tuple[str, str]:
    judged = classify(testo or "")
    risposta = f"[{judged.layer}] {judged.note}"
    if judged.how_falls:
        risposta += f"\nP6: {judged.how_falls}"
    return risposta, judged.layer


def _locale(corpo: str, layer: str, rid: str, t0: float, extra: dict | None = None) -> dict:
    corpo += "\n\nMotore: protocollo-nucleo. Zero agenti. Se cercavi i sei, non sono qui."
    out = {
        "risposta": corpo,
        "run_id": rid,
        "layer": layer,
        "durata_ms": int((time.time() - t0) * 1000),
        "provider": [ENGINE],
        "agenti": 0,
    }
    if extra:
        out.update(extra)
    return out


def ask(testo: str, run_id: str | None = None) -> dict:
    t0 = time.time()
    rid = run_id or uuid.uuid4().hex[:12]

    if ponte_configurato():
        try:
            out = _chiedi_motore_esterno(testo or "", rid)
        except Exception as exc:
            corpo, layer = _nucleo(testo)
            corpo = (
                "Ponte SDQ-1 configurato, ma il motore esterno non risponde "
                f"({type(exc).__name__}). Risponde il nucleo locale.\n\n" + corpo
            )
            return _locale(corpo, layer, rid, t0, extra={"ponte": "caduto"})
        out.setdefault("run_id", rid)
        out.setdefault("agenti", None)
        out["durata_ms"] = int((time.time() - t0) * 1000)
        out["provider"] = [f"sdq1-esterno:{config.SDQ1_URL}"]
        out["nota_ponte"] = (
            "Risposta inoltrata dal motore esterno. Il bot passa e riporta: "
            "che lì girino davvero i sei lo può dire solo la health di quel motore."
        )
        return out

    corpo, layer = _nucleo(testo)
    return _locale(corpo, layer, rid, t0)
