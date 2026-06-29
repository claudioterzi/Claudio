"""Configurazione R³∞ — QSTP v11.0 APQ+.

Parametri e preset del motore. Nessuna dipendenza esterna.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class ConfigR3:
    """Parametri del motore R³∞ (QSTP = Quantum State Transition Protocol)."""
    qstp_versione: str = "v11.0-APQ+"
    n_scacchiera: int = 8           # scacchiera quantica n×n
    soglia_collasso: float = 0.66   # soglia per il collasso di un nodo dominante
    max_iterazioni: int = 64        # limite di sicurezza del loop continuo
    seed: int = 7                   # determinismo
    kill_switch_attivo: bool = True # se False, il kill switch è disabilitato
    preset: str = "equilibrio"

    def con(self, **kw) -> "ConfigR3":
        """Ritorna una copia con i campi indicati sostituiti."""
        return replace(self, **kw)


# Preset pronti (QSTP v11.0 APQ+).
PRESET: dict[str, dict] = {
    "equilibrio": {"soglia_collasso": 0.66, "max_iterazioni": 64},
    "audace":     {"soglia_collasso": 0.50, "max_iterazioni": 128},
    "prudente":   {"soglia_collasso": 0.80, "max_iterazioni": 32},
}


def carica_preset(nome: str = "equilibrio", **override) -> ConfigR3:
    """Costruisce una ConfigR3 da un preset, con eventuali override."""
    base = PRESET.get(nome, PRESET["equilibrio"])
    return ConfigR3(preset=nome, **{**base, **override})
