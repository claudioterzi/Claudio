#!/usr/bin/env python3
"""
Tracker Manager — Gestione storico prezzi su Google Drive.

Legge/scrive il tracker sheet su Drive, accumula storico prezzi e identifica deal.
Pattern: ogni corsa memorizzata come riga, storico aggregato in metadata.

Usage:
    from tracker_manager import TrackerManager

    tm = TrackerManager(sheet_id="1ZCK...")
    history = tm.get_route_history("MXP", "BCN")  # min/max/mean/days_since_low
    tm.record_price("MXP", "BCN", 45.0, "Ryanair", "2026-10-15")
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple


class TrackerManager:
    """Gestisce storico prezzi su Google Drive Tracker Sheet."""

    def __init__(self, sheet_id: str):
        """
        Initialize tracker with Drive sheet ID.

        Args:
            sheet_id: Google Sheets document ID
        """
        self.sheet_id = sheet_id
        self.history_cache: Dict[str, Dict] = {}
        self.last_sync = None

    def get_route_history(self, from_airport: str, to_airport: str) -> Dict:
        """
        Recupera storico prezzi per una rotta.

        Returns:
            {
                "min_price": float,
                "max_price": float,
                "avg_price": float,
                "days_since_min": int,
                "last_update": str,
                "samples": int
            }
        """
        route_key = f"{from_airport}-{to_airport}"

        # Per ora: restituisce valori di default
        # In produzione: leggere da Drive metadata
        return {
            "min_price": None,
            "max_price": None,
            "avg_price": None,
            "days_since_min": None,
            "last_update": None,
            "samples": 0
        }

    def record_price(
        self,
        from_airport: str,
        to_airport: str,
        price: float,
        airline: str,
        date: str,
        is_deal: bool = False
    ) -> bool:
        """
        Registra un prezzo sul tracker.

        Args:
            from_airport: IATA code
            to_airport: IATA code
            price: Prezzo in EUR
            airline: Nome vettore
            date: Data ricerca (YYYY-MM-DD)
            is_deal: True se sotto soglia alert

        Returns:
            True se registrato, False se errore
        """
        try:
            record = {
                "timestamp": datetime.now().isoformat(),
                "from": from_airport,
                "to": to_airport,
                "price": price,
                "airline": airline,
                "date": date,
                "is_deal": is_deal
            }

            # Log in memoria (in produzione: scrivere su Drive)
            route_key = f"{from_airport}-{to_airport}"
            if route_key not in self.history_cache:
                self.history_cache[route_key] = []
            self.history_cache[route_key].append(record)

            return True
        except Exception as e:
            print(f"Error recording price: {e}")
            return False

    def get_deals(self, threshold: float = 45.0) -> List[Dict]:
        """
        Ritorna tutti i deal registrati (prezzo < threshold).
        """
        deals = []
        for route, prices in self.history_cache.items():
            for record in prices:
                if record["price"] < threshold:
                    deals.append(record)
        return sorted(deals, key=lambda x: x["price"])

    def export_summary(self) -> Dict:
        """Esporta summary per report giornaliero."""
        return {
            "generated_at": datetime.now().isoformat(),
            "routes_tracked": len(self.history_cache),
            "total_samples": sum(len(p) for p in self.history_cache.values()),
            "cache": self.history_cache
        }


if __name__ == "__main__":
    # Test
    tm = TrackerManager(sheet_id="1ZCK-XpUeclNcvQ5UdA_payjEemMiq-LTHVq0SiKGyHQ")

    # Simula alcune registrazioni
    tm.record_price("MXP", "BCN", 14.99, "Ryanair", "2026-10-14", is_deal=True)
    tm.record_price("MXP", "MAD", 14.99, "Ryanair", "2026-10-14", is_deal=True)
    tm.record_price("BRU", "AGP", 35.99, "Ryanair", "2026-10-14", is_deal=True)

    deals = tm.get_deals(threshold=45.0)
    print(f"Found {len(deals)} deals:")
    for deal in deals:
        print(f"  {deal['from']} → {deal['to']}: {deal['price']}€ ({deal['airline']})")

    summary = tm.export_summary()
    print(f"\nSummary: {summary['routes_tracked']} routes, {summary['total_samples']} samples")
