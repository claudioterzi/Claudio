# R³∞ / Letta — Cooperazione verificata, continuità ancora da provare

**Data:** 28/09/2026  
**Stato:** TRANSPORT VERIFIED / COOPERATION VERIFIED / MEMORY CONTINUITY CANDIDATE

## Risultato

Il problema HTTP 403 del probe Letta è stato isolato: Cloudflare restituiva `Error 1010 / browser_signature_banned` contro il client Python `urllib`. Non era una prova di token invalido.

Il bridge è stato migrato a `httpx`. Sul runtime Railway attivo sono poi stati verificati:
- `GET /v1/agents/` -> HTTP 200;
- enumerazione di due worker Letta;
- messaggio reale al worker configurato -> HTTP 200;
- blind probe -> `RESET/UNKNOWN` senza invenzione del payload;
- deployment Railway -> SUCCESS;
- Test Runner e Security Scan -> SUCCESS.

## Cooperazione R³ / Letta

Il servizio esistente espone ora `POST /letta/cooperate`:
- autenticazione con `R3_API_TOKEN`;
- `LETTA_API_KEY` solo server-side;
- worker configurato fisso;
- prompt limitato;
- nessun agent ID arbitrario dal caller;
- risposta trattata come `DATA_ONLY / ADVISORY`.

Percorso:

```
Raffaello / peer R³
  -> bridge autenticato
  -> worker Letta configurato
  -> risposta advisory
  -> verifica/provenienza R³
  -> eventuale promozione separata
```

## Cosa NON è ancora provato

Il successo del trasporto non prova che Letta conservi o condivida correttamente una memoria R³ tra worker diversi. Restano:
- Phase A: cross-agent shared-memory + negative control;
- Phase B: contamination resistance;
- Phase C: provider portability senza Letta nel recovery path.

Solo questi test possono promuovere le relative capacità.

## Provenienza

- PR #92 -> trasporto `httpx`;
- merge `ffd5ad0cee2755ae001dfa95d4aa0b2fed81a4eb`;
- fix import `a61fd4515f724cb9efb75d823b786af02573e1e3`;
- PR #93 -> bridge cooperativo autenticato;
- merge `0726b226a127e2209bc5c5cd80fc91db3709d6e0`;
- Railway cooperation deployment `f954b425-ae46-4877-8822-8a6bcd9d98bb`.

Evidenza machine-readable: `docs/evidenze/R3_LETTA_COOPERATION_2026-09-28.json`.

Firma progetto: C.Terzi
