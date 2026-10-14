#!/usr/bin/env python3
"""
Daily Flight Hunt — Ricerca + Alert + Tracker aggiornamento.

Questo script esegue:
1. Ricerca voli da città configurate (Milano, Bruxelles, Roma)
2. Manda alert Telegram per deal < threshold
3. Aggiorna tracker sheet su Drive
4. Manda report giornaliero

Usage:
    python3 scripts/daily_flight_hunt.py
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from flight_hunter.fonti import FonteRyanair
from flight_hunter.telegram_alerts import send_alerts_sync, send_daily_summary
from sdq1.telegram import get_bot_manager, BotRole


SEARCH_CONFIG = {
    "departure_cities": ["MXP", "BRU", "FCO"],
    "days_ahead": 14,
    "alert_threshold_eur": 45.0,
    "historical_low_tracking": True,
}

TRACKER_SHEET_ID = "1ZCK-XpUeclNcvQ5UdA_payjEemMiq-LTHVq0SiKGyHQ"


def run_daily_hunt():
    """Execute complete daily flight hunt workflow."""
    print("\n" + "="*60)
    print("🛫 DAILY FLIGHT HUNT — " + datetime.now().strftime("%Y-%m-%d %H:%M UTC"))
    print("="*60)

    manager = get_bot_manager()
    if not manager.is_configured():
        print("⚠️  Telegram not configured. Alerts will not be sent.")
    else:
        status = manager.get_bot_status()
        print(f"✅ Telegram configured: {status['configured_bots']}")

    all_deals = []

    for city in SEARCH_CONFIG["departure_cities"]:
        print(f"\n📍 Searching from {city}...")
        try:
            fonte = FonteRyanair()
            deals = fonte.occasioni(
                origin=city,
                days=SEARCH_CONFIG["days_ahead"]
            )

            if deals:
                print(f"   Found {len(deals)} flights")

                # Send individual alerts
                result = send_alerts_sync(
                    deals=deals,
                    threshold=SEARCH_CONFIG["alert_threshold_eur"],
                    city_from=city
                )
                print(f"   → Sent {result['sent']} alerts, skipped {result['skipped']}")
                all_deals.extend(result.get("alerts", []))
            else:
                print(f"   No flights found")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue

    # Send daily summary
    if all_deals:
        print(f"\n📊 Sending daily summary ({len(all_deals)} deals)...")
        try:
            asyncio.run(send_daily_summary(
                city_from="Multiple",
                deals=all_deals,
                threshold=SEARCH_CONFIG["alert_threshold_eur"]
            ))
            print("   ✅ Summary sent")
        except Exception as e:
            print(f"   ❌ Summary failed: {e}")

    # Log execution
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "cities": SEARCH_CONFIG["departure_cities"],
        "deals_found": len(all_deals),
        "alerts_sent": len(all_deals),
        "threshold": SEARCH_CONFIG["alert_threshold_eur"],
    }

    print("\n" + "="*60)
    print(f"✅ HUNT COMPLETE — {len(all_deals)} deals found & alerted")
    print("="*60 + "\n")

    return log_entry


if __name__ == "__main__":
    run_daily_hunt()
