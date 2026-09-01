"""Schedatura rapida — due foto e la scheda si compila da sola.

Flusso pensato per essere VELOCE (≈20 secondi a oggetto):
1. foto al frontespizio del libro (o all'oggetto) → la visione estrae
   titolo, autore, ISBN, editore e stima il valore;
2. foto al tag prima di nasconderlo → la visione legge l'EPC stampato
   sull'inlay (testo o barcode) e lo associa alla scheda.

Come sempre: `anthropic` opzionale, fallback a stub per test e sviluppo.
"""

import base64
import json
import os
from typing import Dict, Optional

PROMPT_FRONTESPIZIO = """Guarda la foto: è il frontespizio di un libro oppure un oggetto di casa.
Compila la scheda inventariale. Rispondi SOLO con JSON:
{"nome": "titolo o nome oggetto", "categoria": "libro|elettronica|biancheria|arredo|cucina|oggetto",
 "campi": {"autore": "...", "isbn": "...", "editore": "...", "anno": "..."},
 "valore_eur": stima del valore di mercato in euro (numero),
 "note": "stato di conservazione e dettagli utili"}
Per gli oggetti non-libro lascia "campi" con ciò che riconosci (marca, modello).
Se un dato non è leggibile, ometti la chiave. Stima il valore con prudenza."""

PROMPT_TAG = """Nella foto c'è un'etichetta RFID (inlay). Leggi il codice EPC stampato
sull'etichetta (testo alfanumerico e/o barcode). Rispondi SOLO con JSON:
{"epc": "codice letto"} — se illeggibile: {"epc": ""}"""


class Schedatore:
    """Interfaccia della schedatura fotografica."""

    def scheda_da_foto(self, percorso_foto: str) -> Dict:
        raise NotImplementedError

    def epc_da_foto(self, percorso_foto: str) -> str:
        raise NotImplementedError


class SchedatoreStub(Schedatore):
    """Risposte predefinite per test e sviluppo senza API key."""

    def __init__(self, scheda: Optional[Dict] = None, epc: str = "EPC-STUB-0001"):
        self._scheda = scheda or {
            "nome": "Il nome della rosa", "categoria": "libro",
            "campi": {"autore": "Umberto Eco"}, "valore_eur": 35.0,
            "note": "scheda simulata (stub)"}
        self._epc = epc

    def scheda_da_foto(self, percorso_foto: str) -> Dict:
        return dict(self._scheda)

    def epc_da_foto(self, percorso_foto: str) -> str:
        return self._epc


class SchedatoreClaude(Schedatore):
    """Visione reale: Claude legge frontespizio e tag."""

    def __init__(self, modello: str = "claude-sonnet-5"):
        import anthropic
        self._client = anthropic.Anthropic()
        self._modello = modello

    def _chiedi(self, percorso_foto: str, prompt: str) -> Dict:
        with open(percorso_foto, "rb") as f:
            dati = base64.standard_b64encode(f.read()).decode()
        media = ("image/png" if percorso_foto.lower().endswith(".png")
                 else "image/jpeg")
        risposta = self._client.messages.create(
            model=self._modello, max_tokens=800,
            messages=[{"role": "user", "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": media, "data": dati}},
                {"type": "text", "text": prompt},
            ]}],
        )
        testo = risposta.content[0].text.strip()
        if testo.startswith("```"):
            testo = testo.strip("`").removeprefix("json").strip()
        return json.loads(testo)

    def scheda_da_foto(self, percorso_foto: str) -> Dict:
        return self._chiedi(percorso_foto, PROMPT_FRONTESPIZIO)

    def epc_da_foto(self, percorso_foto: str) -> str:
        return self._chiedi(percorso_foto, PROMPT_TAG).get("epc", "")


def crea_schedatore() -> Schedatore:
    """Claude vision se disponibile, altrimenti stub.
    Forzare lo stub con CUSTODE_VISIONE=stub (utile per i test)."""
    if os.environ.get("CUSTODE_VISIONE") != "stub" and \
            os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return SchedatoreClaude()
        except ImportError:
            pass
    return SchedatoreStub()
