# Rosso Rosso Rosso — audit circoscritto del 05/11/2026

Classificazione: **PATCH + RETEST**, candidato non adottato.
Base: `2346f90788754e180c8f83787a0bf63d73df1042`.

## Perimetro e riferimento

Richiesta: studiare GitHub e correggere gli scostamenti dal protocollo.
Letti bootstrap, priorità di fondazione, continuità, coda, lezioni di riuso,
Learning Watch e overlay retroattivo; ispezionate le PR aperte per evitare
adozioni integrali o duplicazioni. Questo intervento riguarda integrità della
misurazione R3-019 e falsificatori CI, non certifica l'intero repository.
Le precedenti ricevute e i loro limiti restano immutati.

## Difetti riprodotti

1. Il test del packaging selezionava il primo step con suffisso `(blocking)`.
   Dopo l'aggiunta dell'audit npm selezionava l'audit, ma simulava un errore di
   `node`: l'eseguibile realmente chiamato non era controllato. La suite iniziale
   riportava **737 passati, 1 fallito, 1 saltato, 971 subtest passati**. Il test ora
   indirizza esplicitamente audit e build e verifica separatamente che ciascun
   comando propaghi il codice 7 del suo eseguibile simulato. Nessun audit o gate
   di produzione è stato disabilitato.
2. Il benchmark registrava `plan_sha256` senza verificarlo prima dell'esecuzione.
   Si potevano cambiare ripetizioni, condizioni, modello, commit o metadati,
   oppure rimuovere il digest, continuando a invocare la factory del provider.
   Il piano allegato al risultato era inoltre un riferimento mutabile del chiamante.
3. Dataset analizzato e digest provenivano da due letture distinte del file.
   Ora il parsing e il digest usano gli stessi byte sia nel congelamento sia
   nell'esecuzione. Il piano viene copiato e validato prima delle callback.

## Controprove e comportamento

Stessi sette casi sulla base immutata e sulla candidata:
**rifiuti prima dei provider 0/7 → 7/7**. Controllo positivo A/B/C/D con due
ripetizioni conservato in entrambe. La ricevuta è
`evidenze/R3_FROZEN_PLAN_20261105.json`.

Le regressioni verificano anche invarianti violati pur ricalcolando l'hash,
ripetizioni non intere, modifiche del piano durante/dopo le callback e lettura
singola del dataset. Il primo passaggio dei nuovi falsificatori sulla base ha
prodotto 21 fallimenti, inclusi subtest: non sono stati presentati come successi.

SHA-256 certifica coerenza del contenuto, **non autenticità, autorizzazione o
preregistrazione cronologica**. Chi controlla integralmente un piano può crearne
uno nuovo coerente; serve ancora un ancoraggio esterno per provare la priorità
cronologica. Nessuna nuova autorità o chiamata a provider è introdotta.

## Verifiche locali

Python 3.12, dipendenze dichiarate, provider simulati:

- Controlli mirati: **33 passati + 29 subtest**.
- Core: **744 passati, 1 saltato, 994 subtest passati**.
- RRREMERGEN: **18 passati**, un avviso di deprecazione FastAPI/Starlette.
- Bot: **140 passati**.
- Dipendenze compatibili, compilazione Python e `git diff --check` superati.
- Ruff: nessun nuovo rilievo; restano sei rilievi già presenti nei due file
  benchmark (UP035, TRY004, UP017 ×2, BLE001, B023), confrontati con la base.

Comandi riproducibili, nell'ambiente con le dipendenze CI installate:

```sh
python -m pytest tests/test_benchmark_controlled.py tests/test_runtime_requirements.py -q
R3_BOT_CHECKOUT="$PWD/integrations/raffaello-bot" python -m pytest -q --ignore=rrremergen --ignore=integrations/raffaello-bot
python -m pytest -q rrremergen
(cd integrations/raffaello-bot && python -m pytest -q)
```

Il gate R3-020 eseguito localmente restituisce **HOLD**, incremento meccanico 7,
zero regressione sul controllo positivo, `auto_apply_eligible=false`: manca
l'evidenza out-of-sample. Nessuna pretesa di aumento di capacità live.

## Limiti e recupero

Nessun merge, pubblicazione diretta su main, migrazione o modifica diretta della
produzione. La PR può avviare i normali controlli e le preview automatiche.
Nessun provider reale, browser autenticato o runtime ONDA/PC verificato.
Il build completo del packaging e la matrice Python 3.11/3.12 restano verifiche
hosted distinte: i falsificatori dei comandi non sostituiscono quei build.
Copia Drive non aggiornata per assenza del collegamento nella sessione.

Rollback: scartare la candidata o, dopo eventuale adozione separata, revertire
il suo commit senza ripristinare l'intero repository. Nessun dato runtime cambia.
