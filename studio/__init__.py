"""Raffaello Creative Studio — layer creativo/commerciale di SDQ-1."""

from .generators import (
    GeneratoreImmagini,
    GeneratoreCanzoni,
    GeneratoreTraduzioni,
    GeneratoreVideoScript,
    GeneratorePromptEngineering,
)
from .capabilities import CapabilityRecord, OPENMONTAGE_CAPABILITY

__all__ = [
    "GeneratoreImmagini",
    "GeneratoreCanzoni",
    "GeneratoreTraduzioni",
    "GeneratoreVideoScript",
    "GeneratorePromptEngineering",
    "CapabilityRecord",
    "OPENMONTAGE_CAPABILITY",
]
