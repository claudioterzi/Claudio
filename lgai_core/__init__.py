"""
LGAI - Life Game AI System
Core intelligence and calculation engine
"""

__version__ = "1.1.0"
__author__ = "Claudio"

from .libro_oracolo import LibroOracolo, CartaOracolo
from .guard_protocol import GuardLockingProtocol, GuardState, GuardStatus, LockedAction
from .raffaello import RaffaelloIdentity, RAFFAELLO_SYSTEM_PROMPT

__all__ = [
    "GuardLockingProtocol",
    "GuardState",
    "GuardStatus",
    "LockedAction",
    "RaffaelloIdentity",
    "RAFFAELLO_SYSTEM_PROMPT",
]

__all__ += ["LibroOracolo", "CartaOracolo"]
