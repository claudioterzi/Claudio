"""OCCHIO — motori di conteggio fotografico.

Doppia strategia (vedi studio CUSTODE-001):
- motore semantico: un VLM (Claude vision) conta e nomina gli oggetti
  di una zona restituendo JSON strutturato. Implementato qui.
- motore denso (CountGD++ / Grounding DINO + SAM2) per scene molto
  affollate: previsto in v1, stessa interfaccia ContatoreVisivo.

Come tutto SDQ-1: la dipendenza `anthropic` è opzionale, senza API key
si usa il ContatoreStub (utile per test e demo).
"""

import base64
import json
import os
from typing import Dict, Optional

from custode.modelli import Zona, ConteggioZona

PROMPT_CONTEGGIO = """Sei un perito inventariale. Osserva la foto di questa zona:
"{descrizione}".

Conta OGNI oggetto visibile, anche il più piccolo. Rispondi SOLO con JSON:
{{"quantita": {{"nome-oggetto-singolare": numero, ...}}, "note": "osservazioni su stato, danni, oggetti spostati"}}

Regole: nomi in italiano, minuscoli, singolari (es. "forchetta": 6).
Se un oggetto è parzialmente coperto ma riconoscibile, contalo e dillo nelle note."""


class ContatoreVisivo:
    """Interfaccia comune dei motori di conteggio."""

    def conta(self, zona: Zona, percorso_foto: str) -> ConteggioZona:
        raise NotImplementedError


class ContatoreStub(ContatoreVisivo):
    """Contatore finto: restituisce conteggi predefiniti per zona.
    Serve per test, demo e sviluppo senza API key."""

    def __init__(self, risposte: Optional[Dict[str, Dict[str, int]]] = None):
        self.risposte = risposte or {}

    def conta(self, zona: Zona, percorso_foto: str) -> ConteggioZona:
        return ConteggioZona(
            zona_id=zona.id,
            quantita=dict(self.risposte.get(zona.id, {})),
            note="conteggio simulato (stub)",
            foto=percorso_foto,
        )


class ContatoreClaude(ContatoreVisivo):
    """Motore semantico: Claude vision con output JSON strutturato."""

    def __init__(self, modello: str = "claude-sonnet-5"):
        import anthropic  # opzionale: ImportError gestito da crea_contatore
        self._client = anthropic.Anthropic()
        self._modello = modello

    def conta(self, zona: Zona, percorso_foto: str) -> ConteggioZona:
        with open(percorso_foto, "rb") as f:
            dati = base64.standard_b64encode(f.read()).decode()
        media = "image/png" if percorso_foto.lower().endswith(".png") else "image/jpeg"
        risposta = self._client.messages.create(
            model=self._modello,
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image",
                     "source": {"type": "base64", "media_type": media, "data": dati}},
                    {"type": "text",
                     "text": PROMPT_CONTEGGIO.format(descrizione=zona.descrizione)},
                ],
            }],
        )
        testo = risposta.content[0].text.strip()
        if testo.startswith("```"):
            testo = testo.strip("`").removeprefix("json").strip()
        dati_json = json.loads(testo)
        return ConteggioZona(
            zona_id=zona.id,
            quantita={k: int(v) for k, v in dati_json.get("quantita", {}).items()},
            note=dati_json.get("note", ""),
            foto=percorso_foto,
        )


def crea_contatore(**kwargs) -> ContatoreVisivo:
    """Claude vision se disponibile (libreria + ANTHROPIC_API_KEY),
    altrimenti stub — stesso schema di fallback di sdq1.llm."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return ContatoreClaude()
        except ImportError:
            pass
    return ContatoreStub(**kwargs)
