# Flight Monitor Configuration Schema

This document describes the structure of the flight tracker configuration stored in Google Drive.

## Tracker Sheet Structure

### Config Section (Rows 1-10)
```
Row 1:  🛫 Flight Deals Tracker
Row 2:  Last Updated: 2026-10-14 08:15 UTC
Row 3:  Departure Cities: MXP, BRU, FCO
Row 4:  Alert Threshold: 45€
Row 5:  Frequency: daily @ 08:00 UTC
Row 6:  Historical Low Data: [stored as JSON]
Row 7:  Baseline Prices: [stored as JSON]
```

### Data Columns (Starting Row 12)
| Column | Type | Description |
|--------|------|-------------|
| A - Date | YYYY-MM-DD | Search date |
| B - From | IATA code | Departure airport |
| C - To | IATA code | Destination airport |
| D - Price | float | Price in euros |
| E - Source | string | Ryanair / Travelpayouts |
| F - Status | emoji + text | 🎉 Deal / 📊 Normal / ⚠️ High |
| G - Historical Low | float | Lowest recorded price for this route |
| H - Days Since Low | integer | Days since best price |
| I - Trend | arrow | ↓ Falling / → Stable / ↑ Rising |
| J - Notes | string | Any manual notes |

## Configuration JSON (stored in Drive)

```json
{
  "version": "1.0",
  "created": "2026-10-14",
  "departure_cities": ["MXP", "BRU", "FCO"],
  "alert_threshold_eur": 45,
  "frequency": "daily",
  "frequency_time_utc": "08:00",
  "destination_scope": "all",
  "alternative_destinations": [],
  "last_run": "2026-10-14T08:15:00Z",
  "baseline_prices": {
    "MXP-BCN": 68,
    "MXP-PRG": 52,
    "BRU-AGP": 48
  },
  "historical_lows": {
    "MXP-BCN": { "price": 45, "date": "2026-09-30" },
    "MXP-PRG": { "price": 38, "date": "2026-10-13" }
  },
  "active": true
}
```

## Deal Detection Logic

A flight is flagged as a **DEAL** (🎉) if:
- Price < alert_threshold_eur, OR
- Price < historical_low for that route

A flight is flagged as **HIGH** (⚠️) if:
- Price > baseline by 50% or more

Otherwise: **NORMAL** (📊)

## Persistence Across Sessions

The Google Drive sheet is the single source of truth. Between sessions:
1. Config survives unchanged
2. Historical price data accumulates (never deleted)
3. Alerts are idempotent (same alert sent if re-run same day)
4. User can manually edit sheet (add notes, flag routes as "interested", etc.)
