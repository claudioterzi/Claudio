"""
Flight Hunter → Telegram alerts integration.

Cattura i risultati da flight_hunter e li manda via @ProtocolloRossoBot
quando ci sono deal interessanti.

Usage:
    from flight_hunter.telegram_alerts import send_alerts_for_search

    deals = motore.occasioni(origin="MXP", days=14)
    await send_alerts_for_search(deals, threshold=45)
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def send_alerts_for_search(
    deals: List[dict],
    threshold: float = 45.0,
    city_from: str = "",
    include_normal: bool = False
) -> dict:
    """
    Manda alert via Telegram per i deal trovati.

    Args:
        deals: Lista di offerte (da flight_hunter.offerte)
        threshold: Soglia alert in €
        city_from: Città di partenza (per context)
        include_normal: Se True, include anche prezzi normali (non solo deal)

    Returns:
        {"sent": int, "alerts": [list of deal dicts], "skipped": int}
    """
    from sdq1.telegram import get_bot_manager, BotRole

    manager = get_bot_manager()
    if not manager.is_configured():
        logger.warning("Telegram not configured, skipping alerts")
        return {"sent": 0, "alerts": [], "skipped": len(deals)}

    alerts = []
    sent = 0
    skipped = 0

    for deal in deals:
        price = deal.get("prezzo", float('inf'))

        # Decide se mandare alert
        is_deal = price < threshold
        if not is_deal and not include_normal:
            skipped += 1
            continue

        alert_data = {
            "from": city_from or deal.get("da", "?"),
            "to": deal.get("a", "?"),
            "price": price,
            "vettore": deal.get("vettore", "Various"),
            "giorno": deal.get("giorno", "?"),
            "status": "deal" if is_deal else "normal",
            "reason": "under_threshold" if is_deal else "tracking",
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Send via Telegram
            success = await manager.send_flight_alert(
                alert_data,
                bot_role=BotRole.PROTOCOLLO_ROSSO
            )
            if success:
                alerts.append(alert_data)
                sent += 1
                logger.info(f"Alert sent: {alert_data['from']}→{alert_data['to']} {price}€")
            else:
                skipped += 1
        except Exception as e:
            logger.error(f"Failed to send alert for {deal}: {e}")
            skipped += 1

    return {
        "sent": sent,
        "alerts": alerts,
        "skipped": skipped,
        "timestamp": datetime.now().isoformat()
    }


async def send_daily_summary(
    city_from: str,
    deals: List[dict],
    threshold: float = 45.0
) -> bool:
    """Manda un report giornaliero di tutti i deal trovati."""
    from sdq1.telegram import get_bot_manager, BotRole

    manager = get_bot_manager()
    if not manager.is_configured():
        return False

    # Filter deals below threshold
    deal_list = [d for d in deals if d.get("prezzo", float('inf')) < threshold]

    if not deal_list:
        logger.info(f"No deals below {threshold}€ from {city_from}, skipping daily summary")
        return True

    return await manager.send_daily_report(
        deal_list,
        bot_role=BotRole.PROTOCOLLO_ROSSO
    )


# Async wrapper for sync code
def send_alerts_sync(deals: List[dict], threshold: float = 45.0, city_from: str = "") -> dict:
    """Sync version of send_alerts_for_search (uses asyncio.run internally)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context, create task
            return asyncio.ensure_future(
                send_alerts_for_search(deals, threshold, city_from)
            )
        else:
            # Not in async, use run_until_complete
            return loop.run_until_complete(
                send_alerts_for_search(deals, threshold, city_from)
            )
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(
            send_alerts_for_search(deals, threshold, city_from)
        )
