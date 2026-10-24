---
name: flight-hunter-automation
description: |
  Automate daily flight price monitoring, cheap deal detection, and price history tracking from your favorite cities.
  
  Use this skill whenever the user wants to:
  - Set up automated daily/recurring flight searches from home cities or departure points
  - Track and monitor flight prices over time with automatic alerting when deals appear
  - Get notified when flight prices drop below a budget threshold or hit new lows
  - Manage a persistent "flight wish list" with automatic price tracking across sessions
  - Create automated flight price reports and export deal summaries to Google Drive
  - Query price history for specific routes and get trend analysis
  - Coordinate multi-city flight searches (Milan, Brussels, Rome, etc.) with unified alert management
  - Set up price watchers for specific routes (e.g., track MXP→Barcelona deals)
  
  The skill integrates with the SDQ-1 flight_hunter module and uses Google Drive as the "source of truth" for
  persistent tracking. It coordinates Ryanair (real-time) + Travelpayouts (broader coverage) to find the best deals.
  
  Triggers on keywords: "flight hunt", "track flights", "monitor prices", "flight alerts", "cheap flights",
  "flight deals", "automate flight search", "price watcher", "set up search", "recurring flight", "daily search".
  
  Works best in recurring mode (daily searches) or as a one-time setup. Pairs well with the /loop skill for
  scheduling automated runs.
---

## How this skill works

This skill sets up a **recurring flight deal monitor** that:

1. **Searches daily** from your preferred departure cities
2. **Tracks prices** — stores results in Google Drive (the "source of truth" for SDQ-1)
3. **Alerts on deals** — notifies when a price is < 45€ OR below the historical low for that route
4. **Exports summaries** — creates/updates a sheet with today's best deals and price trends
5. **Uses both sources** — Ryanair (real-time) + Travelpayouts (cached, broader coverage)

## Typical workflow

**First time:**
```
User: "Set up a daily flight search from Milan and Brussels. Alert me if I find anything under 50€."

Claude with skill:
1. Creates a Google Drive sheet (SDQ-1 Flights Tracker)
2. Stores search config: cities=["MXP", "BRU"], alert_threshold=50, frequency=daily
3. Runs initial search to populate baseline prices
4. Returns sheet link and first results
```

**Recurring (daily):**
```
User: "Run today's flight hunt" (or scheduled via /loop)

Claude with skill:
1. Loads config from Drive sheet
2. Searches from [MXP, BRU] using flight_hunter
3. Compares against yesterday's prices
4. Alerts: "🎉 DEAL: MXP→BCN 42€ (under threshold!)"
5. Updates Drive sheet with new data and trends
```

**Management:**
```
User: "Add Rome to my searches" / "Lower alert to 35€"

Claude with skill:
1. Updates config in Drive sheet
2. Adds ROM to active cities
3. Next run picks up the change
```

---

## Implementation guide

### Prerequisites
- Google Drive access (configured in project settings)
- flight_hunter module available (SDQ-1/Claudio project)
- TRAVELPAYOUTS_TOKEN and/or Ryanair API (auto-detected)

### Step 1: Initialize the monitor

1. **Ask the user:**
   - Which cities? (use IATA codes: MXP=Milan, BRU=Brussels, FCO=Rome, etc.)
   - Alert threshold in €? (default 45)
   - Frequency? (daily, 3x/week, or on-demand)
   - Destination coverage? (all=worldwide discovery, or specific list)

2. **Create a tracker sheet on Google Drive** in the SDQ-1 folder:
   - Sheet name: `🛫 Flight Deals — {date}`
   - Columns: `Date | From | To | Price € | Source | Status (🎉 Deal / 📊 Normal / ⚠️ High) | Historical Low | Trend`
   - Config section (top): departure cities, alert threshold, last run

3. **Run baseline search**
   - Call flight_hunter for each departure city
   - Store all prices to establish baseline
   - Return top 10 deals to the user

### Step 2: Daily/recurring execution

1. **Load config** from Drive sheet (departure cities, threshold, etc.)
2. **Run searches** using flight_hunter.motore or flight_hunter.oracolo
3. **Compare against baseline**
   - If price < threshold → 🎉 DEAL (alert)
   - If price < historical low → 📊 NEW LOW (highlight)
   - Otherwise → normal
4. **Update Drive sheet** with new data
5. **Send alert** if any deals found (in chat or Telegram if configured)

### Step 3: Management & updates

- User says "add/remove cities" → update config in Drive sheet
- User says "lower alert to X€" → update threshold
- User says "show history for MXP→BCN" → pull data from sheet and summarize

---

## Key patterns

### Google Drive as memory
All config and historical data live in Drive. This means:
- Config survives between sessions ✓
- Price history is queryable (chart trends, find patterns) ✓
- Easy for Claudio to review in his daily workflow ✓
- Matches SDQ-1 rule: Drive is the "source of truth" / "posto madre"

### Graceful degradation
- If Travelpayouts token missing → use Ryanair only
- If search fails → use yesterday's cached data
- If Drive is unreachable → store locally and sync on next run

### Multi-source coordination
When both Ryanair and Travelpayouts have prices:
- Show both (source attribution)
- Alert triggers on either (most aggressive)
- User can filter by source if they prefer one

---

## What the user gets

When everything works:

```
🎯 Today's Flight Hunt — Milan & Brussels
Run time: 08:00 UTC

🎉 DEALS (under 45€):
  MXP→PRG  38€ Ryanair   (was 52€ yesterday)
  BRU→AGP  42€ Travelpayouts (new low! was 48€)

📊 Normal pricing:
  MXP→BCN  68€ Ryanair
  MXP→VIE  71€ Travelpayouts
  BRU→CDG  55€ Ryanair

📈 Sheet updated: https://drive.google.com/...

Next run: tomorrow 08:00
```

---

## Testing & iteration

Test cases should cover:
1. **First-time setup** — new user, zero history
2. **Deal detection** — price drops, new low alerts
3. **Multi-city** — searching from 2+ cities, coordinating results
4. **No deals** — normal pricing day, sheet updates without alerts

See `evals/evals.json` for specific prompts.
