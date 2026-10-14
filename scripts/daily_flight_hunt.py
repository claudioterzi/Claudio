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

from flight_hunter.fonti import fonti_disponibili
from flight_hunter.telegram_alerts import send_alerts_sync, send_daily_summary
from sdq1.telegram import get_bot_manager, BotRole
from tracker_manager import TrackerManager


SEARCH_CONFIG = {
    "departure_cities": ["MXP", "BRU", "FCO"],
    "days_ahead": 14,
    "alert_threshold_eur": 45.0,
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

    tracker = TrackerManager(sheet_id=TRACKER_SHEET_ID)
    all_deals = []

    # Calculate date range
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    end_date = today + timedelta(days=SEARCH_CONFIG["days_ahead"])
    dal = tomorrow.strftime("%Y-%m-%d")
    al = end_date.strftime("%Y-%m-%d")

    fonti = fonti_disponibili()
    print(f"📊 Available sources: {[f.nome for f in fonti]}\n")

    for city in SEARCH_CONFIG["departure_cities"]:
        print(f"📍 Searching from {city} ({dal} to {al})...")
        try:
            for fonte in fonti:
                try:
                    offerte = fonte.offerte(da=city, dal=dal, al=al)
                except Exception:
                    continue

                if not offerte:
                    continue

                deals = []
                for offerta in offerte:
                    deals.append({
                        "da": offerta.da,
                        "a": offerta.a,
                        "prezzo": offerta.prezzo,
                        "vettore": offerta.vettore,
                        "giorno": offerta.giorno,
                        "nome": offerta.nome,
                        "paese": offerta.paese,
                    })

                if deals:
                    print(f"   {fonte.nome}: {len(deals)} destinations")

                    # Record prices in tracker
                    for deal in deals:
                        is_deal = deal["prezzo"] < SEARCH_CONFIG["alert_threshold_eur"]
                        tracker.record_price(
                            from_airport=deal["da"],
                            to_airport=deal["a"],
                            price=deal["prezzo"],
                            airline=deal["vettore"],
                            date=dal,
                            is_deal=is_deal
                        )

                    # Send individual alerts
                    result = send_alerts_sync(
                        deals=deals,
                        threshold=SEARCH_CONFIG["alert_threshold_eur"],
                        city_from=city
                    )
                    print(f"   → {result['sent']} alerts sent, {result['skipped']} skipped")
                    all_deals.extend(result.get("alerts", []))

        except Exception as e:
            print(f"   ❌ Error: {e}")

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

    # Export tracker summary
    tracker_summary = tracker.export_summary()

    # Log execution
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "cities": SEARCH_CONFIG["departure_cities"],
        "deals_found": len(all_deals),
        "alerts_sent": len(all_deals),
        "threshold": SEARCH_CONFIG["alert_threshold_eur"],
        "tracker_routes": tracker_summary["routes_tracked"],
        "tracker_samples": tracker_summary["total_samples"],
    }

    print("\n" + "="*60)
    print(f"✅ HUNT COMPLETE — {len(all_deals)} deals found & alerted")
    print(f"📊 Tracker: {tracker_summary['routes_tracked']} routes, {tracker_summary['total_samples']} samples")
    print("="*60 + "\n")

    return log_entry


if __name__ == "__main__":
    run_daily_hunt()
