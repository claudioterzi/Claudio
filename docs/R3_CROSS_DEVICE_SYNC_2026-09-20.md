# R³∞ — Persistenza cross-device automatica

Data: 2026-09-20  
Autore: Claudio Terzi · C.Terzi

## Obiettivo

Trasformare la precedente capsula cross-device manuale in una sincronizzazione
automatica senza perdere le garanzie append-only del ledger R³∞.

## Architettura

- **Browser local-first**: il ledger locale resta la sorgente immediata.
- **Storage persistente**: riuso dell'Upstash/Redis già collegato al progetto Vercel.
- **Autenticazione per dispositivo**: enrollment una tantum con la password
  proprietaria configurata lato server; il server restituisce un token casuale
  per quel browser. La password non viene memorizzata dal motore sync.
- **CAS server-side**: ogni PUT dichiara `base_revision` e `base_head`.
  Una scrittura concorrente o stantia viene rifiutata con HTTP 409.
- **Append-only**: il server accetta soltanto ledger validi che estendono
  esattamente la catena già persistita.
- **Conflitti**: due rami divergenti non vengono fusi automaticamente.
- **Trigger automatici**: avvio pagina, ritorno online, ritorno in primo piano,
  modifica locale e polling ogni 30 secondi.

## Endpoint

- `GET /api/r3-sync/health`
- `POST /api/r3-sync/enroll`
- `GET /api/r3-sync`
- `PUT /api/r3-sync`
- `POST /api/r3-sync/revoke`

## Gate FATTO

La voce canonica passa da IPOTESI a FATTO solo dopo:

1. suite JS del ledger superata;
2. test unitari API superati;
3. deploy Vercel riuscito;
4. health endpoint in produzione con Redis read/write e auth configurata;
5. verifica che richieste non autenticate al ledger siano rifiutate.

Ogni nuovo dispositivo richiede una sola autorizzazione iniziale; dopo, la
sincronizzazione è automatica e non aggira l'autenticazione.
