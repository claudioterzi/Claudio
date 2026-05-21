"""
LGAI - Life Game AI System
Core intelligence and calculation engine
"""

__version__ = "1.1.0"
__author__ = "Claudio"

from .guard_protocol import GuardLockingProtocol, GuardState, GuardStatus, LockedAction

__all__ = [
    "GuardLockingProtocol",
    "GuardState",
    "GuardStatus",
    "LockedAction",
]
