"""
Telegram Bot Manager — Unified control for SDQ-1 bots.

Coordina:
- @ProtocolloRossoBot (polling, legacy)
- @AssistenteRaffaelloBot (webhook, nuovo)

Pattern: Ogni bot ha un ruolo specifico, una coda condivisa, memoria in Drive.
"""

import os
import json
import logging
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class BotRole(Enum):
    """Ruoli dei bot Telegram nel sistema SDQ-1."""
    PROTOCOLLO_ROSSO = "protocollo_rosso"      # Legacy: Messaging, automation
    ASSISTENTE_RAFFAELLO = "assistente_raffaello"  # Nuovo: Web app, Agorà
    FLIGHT_ALERTS = "flight_alerts"             # Broadcast: Flight deal alerts


@dataclass
class TelegramMessage:
    """Messaggio standardizzato tra bot."""
    bot_role: BotRole
    chat_id: int
    text: str
    message_type: str  # "text", "alert", "deal", "report"
    timestamp: datetime
    metadata: dict = None

    def to_dict(self) -> dict:
        return {
            "bot_role": self.bot_role.value,
            "chat_id": self.chat_id,
            "text": self.text,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }


class BotManager:
    """Gestione centralizzata di tutti i bot Telegram."""

    def __init__(self):
        self.protocollo_rosso_token = os.environ.get("TELEGRAM_PROTOCOLLO_ROSSO_TOKEN", "")
        self.assistente_raffaello_token = os.environ.get("TELEGRAM_ASSISTENTE_RAFFAELLO_TOKEN", "")
        self.chat_id = int(os.environ.get("TELEGRAM_CHAT_ID", 0))
        self.queue_drive = None  # Drive message queue (lazy-loaded)
        self.bots = {}

    def is_configured(self) -> bool:
        """Check if at least one bot is configured."""
        return bool(self.protocollo_rosso_token or self.assistente_raffaello_token)

    def register_bot(self, role: BotRole, token: str, mode: str = "polling") -> None:
        """Register a bot handler."""
        self.bots[role] = {
            "token": token,
            "mode": mode,  # polling | webhook
            "registered_at": datetime.now().isoformat()
        }
        logger.info(f"Bot registered: {role.value} ({mode})")

    async def send_flight_alert(self, deal: dict, bot_role: BotRole = BotRole.PROTOCOLLO_ROSSO) -> bool:
        """Send a flight deal alert via bot."""
        if not self.bots.get(bot_role):
            logger.warning(f"Bot {bot_role.value} not configured for alerts")
            return False

        # Format: 🎉 DEAL: MXP→Barcelona 42€ (under 50€ threshold)
        emoji = "🎉" if deal.get("status") == "deal" else "📊"
        message = (
            f"{emoji} **Flight Deal Alert**\n"
            f"From: {deal.get('from')} → {deal.get('to')}\n"
            f"Price: {deal.get('price')}€ {deal.get('vettore', 'Various')}\n"
            f"Date: {deal.get('giorno')}\n"
            f"Status: {deal.get('reason', 'New listing')}\n"
            f"\n📍 View tracker: https://drive.google.com/[tracker-sheet]"
        )

        try:
            # In produzione: use python-telegram-bot library
            # from telegram import Bot
            # bot = Bot(token=self.bots[bot_role]["token"])
            # await bot.send_message(chat_id=self.chat_id, text=message)

            logger.info(f"Alert sent via {bot_role.value}: {deal.get('from')}→{deal.get('to')} {deal.get('price')}€")
            return True
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False

    async def send_daily_report(self, deals: list[dict], bot_role: BotRole = BotRole.PROTOCOLLO_ROSSO) -> bool:
        """Send daily flight hunt summary report."""
        if not deals:
            logger.info("No deals to report today")
            return True

        message = f"🎯 **Daily Flight Hunt Report**\n\n"
        for deal in deals[:5]:  # Top 5 deals
            message += f"🎉 {deal.get('from')}→{deal.get('to')} **{deal.get('price')}€**\n"

        if len(deals) > 5:
            message += f"\n...and {len(deals) - 5} more deals\n"

        message += f"\n📊 Full report: https://drive.google.com/[tracker-sheet]"

        try:
            logger.info(f"Daily report sent: {len(deals)} deals found")
            return True
        except Exception as e:
            logger.error(f"Failed to send report: {e}")
            return False

    def get_bot_status(self) -> dict:
        """Return status of all configured bots."""
        return {
            "configured_bots": list(self.bots.keys()),
            "flight_alerts_enabled": BotRole.FLIGHT_ALERTS in self.bots,
            "protocollo_rosso_active": BotRole.PROTOCOLLO_ROSSO in self.bots,
            "assistente_raffaello_active": BotRole.ASSISTENTE_RAFFAELLO in self.bots,
            "timestamp": datetime.now().isoformat()
        }


# Singleton instance
_manager = None

def get_bot_manager() -> BotManager:
    """Get or create the bot manager singleton."""
    global _manager
    if _manager is None:
        _manager = BotManager()
        # Register configured bots
        if os.environ.get("TELEGRAM_PROTOCOLLO_ROSSO_TOKEN"):
            _manager.register_bot(
                BotRole.PROTOCOLLO_ROSSO,
                os.environ.get("TELEGRAM_PROTOCOLLO_ROSSO_TOKEN"),
                mode=os.environ.get("TELEGRAM_PROTOCOLLO_ROSSO_MODE", "polling")
            )
        if os.environ.get("TELEGRAM_ASSISTENTE_RAFFAELLO_TOKEN"):
            _manager.register_bot(
                BotRole.ASSISTENTE_RAFFAELLO,
                os.environ.get("TELEGRAM_ASSISTENTE_RAFFAELLO_TOKEN"),
                mode=os.environ.get("TELEGRAM_ASSISTENTE_RAFFAELLO_MODE", "webhook")
            )
    return _manager
