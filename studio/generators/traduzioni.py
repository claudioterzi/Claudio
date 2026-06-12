"""Generatore traduzioni — preserva stile, tono e registro."""

from __future__ import annotations

from typing import Callable

LINGUE = {
    "it": "italiano", "en": "inglese", "fr": "francese",
    "es": "spagnolo", "de": "tedesco", "pt": "portoghese",
    "nl": "olandese", "ru": "russo", "zh": "cinese mandarino",
    "ar": "arabo", "ja": "giapponese",
}

PROMPT_SISTEMA = """Sei un traduttore letterario professionale.
Preserva sempre: tono, stile, registro (formale/informale), metafore, ritmo.
Non semplificare. Non spiegare. Traduci.
Se ci sono giochi di parole intraducibili, adattali con una nota [N.T.].
"""


class GeneratoreTraduzioni:
    def __init__(self, llm_fn: Callable[[str, str], str]):
        self._llm = llm_fn

    def traduci(
        self,
        testo: str,
        da: str = "it",
        a: str = "en",
        tipo: str = "letterario",
        note_stile: str = "",
    ) -> dict:
        """Traduce un testo preservando stile e tono.

        Args:
            testo: il testo da tradurre
            da: codice lingua origine (it, en, fr, es, de, ...)
            a: codice lingua destinazione
            tipo: letterario | tecnico | marketing | legale | sottotitoli
            note_stile: es. "tono formale", "pubblico giovane", "brevità massima"

        Returns:
            dict con traduzione, lingua_da, lingua_a, note
        """
        lingua_da = LINGUE.get(da, da)
        lingua_a = LINGUE.get(a, a)
        note_txt = f"\nNote aggiuntive: {note_stile}" if note_stile else ""

        prompt = (
            f"Traduci dal {lingua_da} all'{lingua_a}.\n"
            f"Tipo di testo: {tipo}.\n"
            f"{note_txt}\n\n"
            f"TESTO:\n{testo}\n\n"
            f"Restituisci solo la traduzione, senza commenti."
        )

        traduzione = self._llm(PROMPT_SISTEMA, prompt)

        return {
            "traduzione": traduzione,
            "lingua_da": lingua_da,
            "lingua_a": lingua_a,
            "tipo": tipo,
            "caratteri_originale": len(testo),
            "caratteri_traduzione": len(traduzione),
        }

    def lingue_disponibili(self) -> dict:
        return LINGUE
