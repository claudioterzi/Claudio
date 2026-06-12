"""Generatore immagini via DALL-E 3 (OpenAI) o Stability AI."""

from __future__ import annotations

import os
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

_TZ_BRUSSELS = timezone(timedelta(hours=2))

DIMENSIONI_VALIDE = {
    "quadrata": "1024x1024",
    "orizzontale": "1792x1024",
    "verticale": "1024x1792",
    "square": "1024x1024",
    "landscape": "1792x1024",
    "portrait": "1024x1792",
}


class GeneratoreImmagini:
    """Genera immagini via DALL-E 3.

    Requisito: OPENAI_API_KEY in ambiente.
    Output: salva PNG in output/immagini/ e restituisce il path.
    """

    def __init__(self, output_dir: Path = Path("output/immagini")):
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _client(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("pip install openai")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY non configurata")
        return OpenAI(api_key=api_key)

    def genera(
        self,
        descrizione: str,
        stile: str = "",
        dimensione: str = "quadrata",
        qualita: str = "standard",
    ) -> dict:
        """Genera un'immagine e la salva su disco.

        Args:
            descrizione: cosa deve contenere l'immagine (in italiano)
            stile: es. "olio su tela", "fumetto", "fotorealistico", "minimalista"
            dimensione: "quadrata" | "orizzontale" | "verticale"
            qualita: "standard" | "hd"

        Returns:
            dict con path, url_originale, prompt_usato, metadati
        """
        size = DIMENSIONI_VALIDE.get(dimensione.lower(), "1024x1024")

        # Costruisce il prompt in inglese per DALL-E (funziona meglio)
        prompt_parts = [descrizione]
        if stile:
            prompt_parts.append(f"Style: {stile}")
        prompt_parts.append("High quality, professional.")
        prompt = ". ".join(prompt_parts)

        client = self._client()
        t0 = time.monotonic()
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=qualita,
            n=1,
        )
        latenza_ms = int((time.monotonic() - t0) * 1000)

        url = response.data[0].url
        prompt_rivisto = getattr(response.data[0], "revised_prompt", prompt)

        # Scarica e salva
        now = datetime.now(_TZ_BRUSSELS)
        nome = now.strftime("%Y%m%d_%H%M%S") + "_" + descrizione[:30].replace(" ", "_").replace("/", "-") + ".png"
        dest = self._output_dir / nome
        urllib.request.urlretrieve(url, dest)

        return {
            "path": str(dest),
            "url_originale": url,
            "prompt_usato": prompt,
            "prompt_rivisto_da_dalle": prompt_rivisto,
            "dimensione": size,
            "qualita": qualita,
            "latenza_ms": latenza_ms,
            "generato": now.isoformat(),
        }
