"""Archivio del catalogo — dove vivono le schede.

Su Vercel il filesystem è effimero (ogni invocazione riparte pulita),
quindi in produzione serve Redis (REDIS_URL, es. Upstash gratuito).
In locale basta il file JSON. Scelta automatica in crea_archivio().
"""

import json
import os
from typing import Dict, List


class ArchivioFile:
    """Persistenza su file JSON (sviluppo locale)."""

    effimero = False

    def __init__(self, percorso: str):
        self.percorso = percorso

    def leggi(self) -> List[Dict]:
        if not os.path.exists(self.percorso):
            return []
        with open(self.percorso, encoding="utf-8") as f:
            return json.load(f)

    def scrivi(self, schede: List[Dict]) -> None:
        os.makedirs(os.path.dirname(self.percorso) or ".", exist_ok=True)
        with open(self.percorso, "w", encoding="utf-8") as f:
            json.dump(schede, f, ensure_ascii=False, indent=2)


class ArchivioRedis:
    """Persistenza su Redis (produzione Vercel + Upstash)."""

    effimero = False

    def __init__(self, url: str, chiave: str = "custode:catalogo"):
        import redis
        self._redis = redis.from_url(url)
        self._chiave = chiave

    def leggi(self) -> List[Dict]:
        dati = self._redis.get(self._chiave)
        return json.loads(dati) if dati else []

    def scrivi(self, schede: List[Dict]) -> None:
        self._redis.set(self._chiave, json.dumps(schede, ensure_ascii=False))


def crea_archivio(percorso_file: str):
    """Redis se configurato (REDIS_URL), altrimenti file JSON.
    Su Vercel senza Redis il file finisce in /tmp: funziona ma è
    EFFIMERO — l'interfaccia lo segnala."""
    url = os.environ.get("REDIS_URL") or os.environ.get("KV_URL")
    if url:
        try:
            return ArchivioRedis(url)
        except Exception:
            pass  # redis non importabile o non raggiungibile → file
    if os.environ.get("VERCEL"):
        archivio = ArchivioFile(os.path.join("/tmp", "catalogo_custode.json"))
        archivio.effimero = True
        return archivio
    return ArchivioFile(percorso_file)
