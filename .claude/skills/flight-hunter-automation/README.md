# flight-hunter-automation Skill

Automate daily flight price monitoring with alerts and Google Drive tracking.

## What's included

- **SKILL.md** — Full skill instructions for Claude
- **scripts/flight_monitor.py** — Python flight monitor implementation
- **references/CONFIG_SCHEMA.md** — Drive sheet structure and config format
- **evals/evals.json** — Test cases for skill evaluation

## Quick start

1. User: "Set up daily flight searches from Milan and Brussels, alert me under 50€"
2. Skill creates a Google Drive tracker sheet
3. Skill runs initial search
4. Skill automatically updates sheet daily with new prices and alerts

## Design principles

✓ Google Drive is the "source of truth" (SDQ-1 pattern)
✓ Works with flight_hunter module (SDQ-1/Claudio project)
✓ Graceful degradation if sources fail
✓ Multi-source (Ryanair + Travelpayouts)
✓ Survives between sessions (persistent config)

## Status

✅ SKILL.md: Complete
✅ Test cases: 3 scenarios
⏳ Evaluation: Ready to run
