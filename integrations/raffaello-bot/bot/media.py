"""Immagini rare — non un museo, un gesto visivo."""

from __future__ import annotations

import base64
import logging
import random
from pathlib import Path

from telegram import Update

logger = logging.getLogger("protocollo.media")
_DIR = Path(__file__).resolve().parent / "media"

URL = {
    "ingresso": (
        "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429"
        "?auto=format&fit=crop&w=1200&q=80"
    ),
    "santuario": (
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64"
        "?auto=format&fit=crop&w=1200&q=80"
    ),
    "luce": (
        "https://images.unsplash.com/photo-1495616811223-4d98c6e9c869"
        "?auto=format&fit=crop&w=1200&q=80"
    ),
    "candela": (
        "https://images.unsplash.com/photo-1513553435374-5cd8d1d0c646"
        "?auto=format&fit=crop&w=1200&q=80"
    ),
    "scacchiera": (
        "https://images.unsplash.com/photo-1529699211952-734e80c4d42b"
        "?auto=format&fit=crop&w=1200&q=80"
    ),
    "libro": (
        "https://images.unsplash.com/photo-1512820790803-83ca734da794"
        "?auto=format&fit=crop&w=1200&q=80"
    ),
    "metodo": (
        "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429"
        "?auto=format&fit=crop&w=1200&q=80"
    ),
}

CAPTION = {
    "ingresso": "Il rosso non è un ornamento. È la soglia.",
    "santuario": "Qui non si regge niente.",
    "luce": "Non un'illuminazione: un'ora.",
    "candela": "Un gesto lento, intero.",
    "scacchiera": "La casa vuota non è il nulla.",
    "libro": "A pagine. Senza chiedere fede.",
    "metodo": "Il bot è il bordo, non l'abitante.",
}


def _locale(chiave: str):
    _DIR.mkdir(parents=True, exist_ok=True)
    jpg = _DIR / f"{chiave}.jpg"
    if jpg.exists() and jpg.stat().st_size > 0:
        return jpg.open("rb")
    raw = _DIR / f"{chiave}.b64"
    if raw.exists():
        try:
            jpg.write_bytes(base64.b64decode(raw.read_text(encoding="ascii")))
            return jpg.open("rb")
        except Exception:
            logger.exception("decode %s", chiave)
    return None


def _sorgente(chiave: str):
    loc = _locale(chiave)
    if loc is not None:
        return loc
    return URL.get(chiave)


async def manda(update: Update, chiave: str, *, sempre: bool = False, p: float = 0.4) -> None:
    if update.message is None:
        return
    if not sempre and random.random() > p:
        return
    src = _sorgente(chiave)
    if not src:
        return
    try:
        await update.message.reply_photo(
            photo=src,
            caption=CAPTION.get(chiave, ""),
        )
    except Exception:
        logger.exception("foto %s non inviata", chiave)
