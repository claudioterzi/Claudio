"""Registry per istanziare agenti dalla config."""

from __future__ import annotations

from typing import Callable

from .base import AgenteBase
from ..config.loader import AgenteConfig, SDQ1Config


_REGISTRO: dict[str, Callable[[AgenteConfig], AgenteBase]] = {}


def registra(agente_id: str):
    """Decorator per registrare un'implementazione di agente."""

    def _wrap(factory: Callable[[AgenteConfig], AgenteBase]):
        _REGISTRO[agente_id] = factory
        return factory

    return _wrap


def costruisci_agenti(config: SDQ1Config) -> dict[str, AgenteBase]:
    agenti: dict[str, AgenteBase] = {}
    for cfg in config.agenti:
        factory = _REGISTRO.get(cfg.id)
        if factory is None:
            raise KeyError(
                f"Nessuna implementazione registrata per agente {cfg.id}. "
                f"Registrali con @registra('{cfg.id}')."
            )
        agenti[cfg.id] = factory(cfg)
    return agenti
