"""Trigger rituali — Rosso, Raffaello, Updater, Applica.

Le parole-rito attivano azioni del motore R³∞. Un registro mappa il nome
del rito alla funzione che lo esegue, restituendo uno stato aggiornato.
"""
from __future__ import annotations

from typing import Callable

from r3_core import ProtocolloRosso, RaffaelloCore

Rito = Callable[[dict], dict]


def rito_rosso(ctx: dict) -> dict:
    """Esegue il Protocollo Rosso sullo stato corrente."""
    stato = ProtocolloRosso().esegui({
        "osservazione": ctx.get("osservazione", "rosso"),
        "energia": ctx.get("energia", 0.5),
    })
    return {**ctx, **stato, "rito": "Rosso"}


def rito_raffaello(ctx: dict) -> dict:
    """Un passo del RAFFAELLO CORE."""
    core = RaffaelloCore()
    s = core.passo()
    return {**ctx, "rito": "Raffaello", "iterazione": s.iterazione,
            "energia": s.energia, "sintesi": s.ultima_sintesi}


def rito_updater(ctx: dict) -> dict:
    """Segna che il sistema va ri-sincronizzato (placeholder di indicizzazione)."""
    return {**ctx, "rito": "Updater", "aggiornamento_richiesto": True}


def rito_applica(ctx: dict) -> dict:
    """Conferma e 'applica' lo stato corrente (segna come committabile)."""
    return {**ctx, "rito": "Applica", "applicato": True}


REGISTRO: dict[str, Rito] = {
    "Rosso": rito_rosso,
    "Raffaello": rito_raffaello,
    "Updater": rito_updater,
    "Applica": rito_applica,
}


def esegui_rito(nome: str, ctx: dict | None = None) -> dict:
    if nome not in REGISTRO:
        raise KeyError(f"Rito sconosciuto: {nome}. Disponibili: {sorted(REGISTRO)}")
    return REGISTRO[nome](ctx or {})
