"""Orchestratori SDQ-1.

`crea_orchestratore` seleziona l'implementazione in base a
`config.orchestratore["tipo"]`:

  - "gerarchico" (default) → pipeline fissa
  - "dinamico"             → pianificazione per capacità (protocollo→piattaforma)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .gerarchico import EsecuzioneGrafo, OrchestratoreGerarchico

if TYPE_CHECKING:  # evita import circolari a runtime
    from ..agents.base import AgenteBase
    from ..config.loader import SDQ1Config
    from ..persistence.store import StatoStore


def crea_orchestratore(
    config: "SDQ1Config",
    agenti: "dict[str, AgenteBase]",
    stato: "StatoStore | None" = None,
) -> OrchestratoreGerarchico:
    tipo = str(config.orchestratore.get("tipo", "gerarchico")).lower()
    if tipo == "dinamico":
        from .dinamico import OrchestratoreDinamico

        return OrchestratoreDinamico(config, agenti, stato=stato)
    return OrchestratoreGerarchico(config, agenti, stato=stato)


__all__ = [
    "crea_orchestratore",
    "OrchestratoreGerarchico",
    "EsecuzioneGrafo",
]
