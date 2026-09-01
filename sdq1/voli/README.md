# sdq1.voli — Caccia autonoma agli errori di prezzo voli

Agenti che **non seguono i blog di offerte**: interrogano direttamente il motore
di prenotazione (Google Flights), leggono i prezzi reali, e ti scrivono su
Telegram quando trovano una *error fare* o una promo forte.

## Pipeline

```
SCOUT-VOLI  →  VALUTATORE  →  CRONISTA
 (prezzo)      (soglia)       (Telegram)
```

- **ScoutVoli** — lancia `engine.js` (Node + Playwright) per una rotta multi-tratta
  e riporta il prezzo minimo reale + le migliori offerte.
- **ValutatoreVoli** — classifica: `error_fare` (≤55% della soglia), `promo_forte`
  (≤ soglia), `normale` (sopra soglia).
- **CronistaVoli** — invia la nota su Telegram via `sdq1.notifiche.invia`, oppure
  la stampa in dry-run se i segreti non sono configurati.

## Requisiti

1. **Node + Playwright** (Chromium):
   ```bash
   cd sdq1/voli && npm install
   ```
   Nell'ambiente Claude, Chromium è preinstallato (`PLAYWRIGHT_BROWSERS_PATH`);
   il motore imposta da sé `NODE_EXTRA_CA_CERTS` sul CA bundle del proxy.

2. **Segreti Telegram** (mai nel repo — solo `.env`/ambiente):
   ```bash
   export TELEGRAM_BOT_TOKEN=...   # da @BotFather
   export TELEGRAM_CHAT_ID=...     # id della tua chat
   ```
   Vedi `.env.example` nella root.

## Uso

```bash
python -m sdq1.voli                 # caccia tutte le rotte, invia note
python -m sdq1.voli --dry-run       # non invia, stampa soltanto
python -m sdq1.voli --tag cuba      # solo rotte con quel tag
python -m sdq1.voli --rotta BRU-GRU-CDG
```

## Esecuzione automatica giornaliera

Da cron (o da un trigger Claude che chiama questo modulo):

```cron
0 7 * * *  cd /path/Claudio && python -m sdq1.voli
```

## Rotte e soglie

Definite in `rotte.py`. Hub di partenza: Bruxelles, Parigi (+ Madrid/Lisbona).
Destinazioni: San Paolo/Brasile, Cuba, Sud America. Aggiorna le finestre di date
nel tempo.
