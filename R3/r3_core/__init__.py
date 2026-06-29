"""R³∞ core — motore centrale."""
from .config import ConfigR3, PRESET, carica_preset
from .engine import RaffaelloCore, StatoCore, KillSwitchAttivato
from .pipeline import PipelinePersistente
from .protocol_rosso import ProtocolloRosso, FASI
from .scacchiera import ScacchieraQuantica, Nodo

__all__ = [
    "ConfigR3", "PRESET", "carica_preset",
    "RaffaelloCore", "StatoCore", "KillSwitchAttivato",
    "PipelinePersistente",
    "ProtocolloRosso", "FASI",
    "ScacchieraQuantica", "Nodo",
]
