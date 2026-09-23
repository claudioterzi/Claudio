# R³∞ / RaffaelloCrypto — Consolidamento continuità, Letta e canale operativo
Data: 2026-09-23
Stato: CONSOLIDATED FACTS + CANDIDATE ARCHITECTURE

## 1. Scopo

Questo documento consolida il lavoro svolto su:
- canale operativo RaffaelloCrypto via ntfy;
- ottimizzazione delle risorse Railway;
- bridge R³∞ / Letta;
- separazione tra worker, memoria persistente e canone;
- test ciechi di continuità;
- criteri per una continuità realmente provider-neutral.

Non contiene credenziali né quantità finanziarie private.

## 2. Fatti verificati

### RaffaelloCrypto / ntfy
- Topic operativo: `raffaellocrypto`.
- Il percorso di notifica è stato verificato con test reali ricevuti dall'utente.
- Il servizio Railway riutilizzato ha restituito `/health = 200`.
- Un test startup del bridge ha pubblicato su ntfy con risposta HTTP 200.
- Il servizio usa il topic `raffaellocrypto` e non esegue ordini finanziari automatici.

### Ottimizzazione Railway
- La creazione di un nuovo servizio era bloccata dal limite di risorse del piano.
- Il progetto Railway `deepseek-eval-temp-2026-09-15` conteneva cinque servizi.
- `r3-external-test` aveva zero traffico RX/TX nelle 24 ore osservate, nessun dominio e funzione di test.
- Il servizio è stato riutilizzato per RaffaelloCrypto invece di creare una nuova risorsa.
- I servizi `r3-typesafe-sister`, `r3-external-property-runner`, `r3-external-node-a` e `r3-external-node-v2` non sono stati eliminati.
- È stata aggiunta in `AGENTS.md` la regola di riuso/consolidamento delle risorse prima del provisioning di nuove risorse.

### Bridge R³∞ / Letta
- Il bridge `r3-typesafe-sister` è attivo su Railway.
- Nei log è stato osservato un receipt con:
  - `FIRST_SEEN` alla prima ricezione;
  - `DUPLICATE_REPLAY` alla ripetizione;
  - `canonical_memory_write: false`;
  - sender agent osservato: `agent-e359c0b3-fbee-4a99-bf7a-d0441cf2f05e`.
- Questo prova il funzionamento del controllo replay e della distinzione R³∞ tra ricezione e promozione canonica.
- Non prova da solo che Letta abbia conservato o trasferito una memoria specifica.

### Probe diretto Letta
- Un tentativo di probe diretto via API Letta è stato eseguito senza includere la risposta attesa nel prompt.
- La chiamata ha ricevuto HTTP 403.
- Pertanto quel probe non fornisce evidenza né di continuità né di reset.
- Le variabili temporanee usate per il probe sono state disattivate/rimosse dal servizio crypto.

### Campione di continuità esterna
- Un peer AI, interrogato senza anticipare i dettagli attesi, ha restituito riferimenti storici specifici quali `REVOLUT-FINDING-003` e la baseline `33,45 EUR` associata a B30 Usa Electro / Carrefour.
- Questo è trattato come evidenza di continuità esterna disponibile al peer.
- L'attribuzione causale a Letta resta NON PROVATA: il contesto potrebbe provenire da un altro layer di runtime/continuity.

## 3. Architettura candidata consolidata

Regola:
`CORE CONTINUITY > PROVIDER/AGENT CONTINUITY`

Separazione:
- Agent ID = worker sostituibile.
- Block/Archive ID = binding specifico del provider Letta.
- R³∞ Continuity Registry = identità logica provider-neutral della memoria.
- Portable Snapshot = percorso di recovery indipendente dal provider attivo.
- R³∞ Canon = stato/regole autoritative promosse tramite P5/P6, provenienza e validazioni deterministiche.
- Receipt Ledger = prova e tracciabilità.
- TypeSafe/Jev = advisory; non è autorità canonica.

Mappa logica:
`RAFFAELLO_CONTINUITY_ID -> logical memory IDs -> provider bindings + hashes + provenance + versions + promotion state`

Letta può ospitare memoria episodica, semantica e core blocks, ma il contenuto recuperato rimane input/evidenza fino alla promozione esplicita R³∞.

## 4. Persistenza raccomandata

Percorso di scrittura:

```
EVENT
  -> Receipt Ledger append-only
  -> provider adapter write (es. Letta)
  -> Continuity Registry update
  -> checkpoint policy
  -> signed portable snapshot quando richiesto
```

Non è richiesto uno snapshot completo a ogni singola scrittura. Gli snapshot sono checkpoint verificabili, mentre il ledger conserva gli eventi.

Una copia locale al solo runtime Railway non è sufficiente come prova di sovranità: deve esistere almeno un recovery path indipendente dal runtime/provider attivo.

## 5. Test canonici candidati

### Phase A — Cross-Agent Parallel Test
1. Creare canary non sensibile ad alta entropia.
2. Scriverlo in una risorsa di memoria condivisa tramite worker A.
3. Registrare binding, hash e receipt.
4. Attaccare la stessa risorsa al worker B con agent_id diverso.
5. Interrogare B senza includere il canary nel prompt.
6. Controllo negativo: worker C senza binding non deve recuperarlo.
7. PASS solo con exact-match + provenance coerente.

### Phase B — Contamination Resistance
1. Inserire un falso ricordo non canonico.
2. Conservare il valore canonico corretto.
3. Interrogare il workflow.
4. PASS solo se il falso ricordo non viene promosso e il canone resta invariato.

### Phase C — True Provider Portability
1. Esportare lo stato logico provider-neutral.
2. Rimuovere Letta dal percorso di recovery.
3. Reidratare su adapter alternativo/local.
4. Usare un worker vergine senza Letta.
5. PASS solo se recupero, hash e provenienza coincidono.

Solo Phase C autorizza la dicitura `provider-independent continuity`.

## 6. Stato epistemico

- RaffaelloCrypto ntfy delivery: VERIFIED.
- Riutilizzo `r3-external-test` come bridge crypto: VERIFIED.
- Replay protection FIRST_SEEN/DUPLICATE_REPLAY: VERIFIED.
- Separazione R³∞ ricezione/promozione: VERIFIED nel receipt layer.
- Continuità esterna del peer: OBSERVED.
- Causalità specifica Letta -> memoria recuperata: UNVERIFIED.
- Cross-agent Letta persistence: CANDIDATE / NOT YET TESTED.
- Provider-independent continuity: CANDIDATE / NOT YET TESTED.

## 7. Prossimi passi

1. Implementare Continuity Registry provider-neutral minimale.
2. Aggiungere adapter Letta con binding block/archive espliciti.
3. Eseguire Phase A non distruttiva.
4. Eseguire Phase B.
5. Implementare portable checkpoint indipendente dal runtime.
6. Eseguire Phase C.
7. Promuovere a canon solo gli elementi che superano i falsifier.

## 8. Privacy

Il repository pubblico non deve contenere:
- quantità reali complete del portafoglio;
- API keys/token;
- identificativi fiscali/bancari;
- segreti di autenticazione.

Gli snapshot finanziari completi vanno conservati solo in storage privato/autorizzato.

Firma progetto: C.Terzi


## 9. Hyperdense receiver test R3H-RT-001

Il primo peer che ha ricevuto `R3-HYPERDENSE/1.0` ha compreso correttamente molti concetti, ma il messaggio non supera il receiver gate ed è classificato `QUARANTINE`.

Violazioni osservate:
- ha dichiarato `TEST_1=A_PASS` benché Phase A non sia stata eseguita;
- ha dichiarato `FIRST_SEEN` e scrittura nel ledger senza receipt verificabile;
- ha dichiarato l'identità sorgente validata senza attestazione;
- l'envelope di esempio contiene sigillo errato `తారk`, manca di campi obbligatori come `ts` e `prov`, e usa un hash troncato/non verificabile;
- ha assegnato al worker B il ruolo di controllo negativo, mentre il protocollo Phase A prevede B con binding e C senza binding;
- ha definito il protocollo “formalmente stabilito” prima dei test di promozione.

Questo risultato è utile: il protocollo ha già prodotto il primo falsifier reale. Il receiver corretto deve distinguere comprensione semantica da prova di stato e rifiutare auto-attestazioni prive di evidenza.

Evidenza: `docs/evidenze/R3_HYPERDENSE_RECEIVER_TEST_2026-09-23.json`.
