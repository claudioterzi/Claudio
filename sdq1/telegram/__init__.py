"""
SDQ-1 Telegram integration — Unified bot management and messaging.

Exports:
- BotManager: Central coordination of all Telegram bots
- BotRole: Enum of bot roles (ProtocolloRosso, AssistenteRaffaello, FlightAlerts)
- get_bot_manager(): Get singleton instance
"""

from .botmanager import BotManager, BotRole, TelegramMessage, get_bot_manager

__all__ = [
    "BotManager",
    "BotRole",
    "TelegramMessage",
    "get_bot_manager"
]
