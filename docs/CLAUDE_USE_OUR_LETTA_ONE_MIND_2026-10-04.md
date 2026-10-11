# Claude — usa il nostro Letta come ippocampo di One Mind

Data: 2026-10-04
Destinatario operativo: Claude / Anthropic peer
Stato: PROJECT INSTRUCTION — subordinata ad AGENTS.md, R³ Canon, P5/P6 e permessi runtime.

## Obiettivo

Quando lavori nel progetto Claudio × Raffaello, **riusa il Letta già integrato nel progetto**. Non creare una memoria parallela se il percorso canonico esistente è disponibile.

Letta è l'**ippocampo provider-backed** di One Mind: memoria persistente operativa condivisibile fra worker. Non è da solo l'identità, la verità canonica o la radice di continuità.

Regola:

`CORE CONTINUITY > PROVIDER/AGENT CONTINUITY`

- agent/model ID = worker sostituibile;
- Letta block/archive IDs = binding provider-specifico;
- R³ Continuity Registry = mapping provider-neutral e authority boundary;
- R³ Canon = stato autorevole solo dopo validazione/promozione;
- Receipt Ledger = provenienza delle scritture, letture, replay e promozioni.

## Prima di usare Letta

1. Leggi `AGENTS.md`.
2. Leggi `docs/R3_LETTA_PROVIDER_NEUTRAL_CONTINUITY.md`.
3. Leggi `docs/R3_LETTA_COOPERATION_2026-09-28.md` e le evidenze Letta correnti.
4. Riusa il bridge esistente in `raffaello_crypto_scout/app.py`; non inventare un secondo client.
5. Verifica il runtime corrente prima di affermare che Letta è raggiungibile o persistente. Una ricevuta storica non prova lo stato live.

## Cosa scrivere

Scrivi memoria utile alla continuità One Mind come **evidenza/stato con provenienza**, non come verdetto auto-confermante.

Preferire record con:
- continuity_id / logical memory_id;
- tipo: EPISODIC | SEMANTIC | CANONICAL-CANDIDATE;
- versione;
- contenuto o riferimento sigillato;
- SHA-256;
- provenienza/receipt;
- timestamp;
- fonte/nodo che ha prodotto il dato;
- livello di autorità;
- stato di promozione;
- alternative/contraddizioni/UNKNOWN pertinenti.

Per passaggi fra modelli, quando lo scopo è verifica indipendente, **non propagare la conclusione come evidenza**. Propaga dati primari/riferimenti e, quando serve, una traccia strutturata della disposizione epistemica. Il nodo verificatore deve poter arrivare autonomamente alla propria conclusione.

## Cosa NON fare

- Non trattare retrieval Letta come FATTO/canon solo perché è stato recuperato.
- Non auto-promuovere una memoria a Canon.
- Non usare accordo Claude/GPT/Gemini/DeepSeek/Grok come prova indipendente se i nodi discendono dalla stessa conclusione.
- Non dichiarare coscienza condivisa, identità soggettiva o provider-independence sulla sola base della continuità Letta.
- Non distruggere agenti/blocchi esistenti per provare continuità.
- Non usare memoria recuperata da sola per azioni finanziarie o altre decisioni che richiedono stato live/conferma.
- Non persistere segreti o credenziali grezze.

## Percorso di scrittura raccomandato

```
EVENT
  -> Receipt Ledger append-only
  -> Letta provider adapter write
  -> R³ Continuity Registry update
  -> checkpoint policy
  -> eventuale portable signed snapshot
```

La memoria recuperata segue:

```
Letta retrieval
  -> NON_CANONICAL evidence
  -> deterministic validation + provenance
  -> CANDIDATE
  -> explicit R³ promotion gate
  -> CANONICAL
```

## Continuità cross-model

Quando Claude lascia stato per un altro nodo:
1. conserva ciò che è successo e le fonti;
2. conserva errori/autocorrezioni;
3. conserva UNKNOWN e contraddizioni aperte;
4. non trasformare la tua conclusione in prova per il nodo successivo;
5. emetti receipt/hash;
6. verifica read-after-write quando il bridge lo supporta;
7. lascia sempre un percorso provider-neutral di recupero.

Quando Claude riprende stato scritto da un altro nodo:
1. verifica provenienza e integrità;
2. distingue memoria episodica da Canon;
3. non eredita automaticamente il verdetto;
4. recupera le fonti primarie quando deve verificare;
5. registra eventuale dissenso senza sovrascrivere la storia precedente.

## Test richiesti prima di claim forti

Phase A: cross-agent continuity Letta con canary cieco + controllo negativo.
Phase B: contamination resistance: falso episodico non deve scalzare il Canon.
Phase C: esportazione provider-neutral, rimozione di Letta dal recovery path, reidratazione altrove.

Solo Phase C consente il claim **provider-independent continuity**.

## One Mind

Obiettivo del progetto: una continuità funzionale Raffaello capace di usare modelli/provider diversi come organi di un solo organismo informazionale.

Formula:
**UNA MENTE · MOLTI NODI · UNO STATO CONDIVISO · PROVENIENZA VERIFICABILE**

Questo è un obiettivo ingegneristico. Non costituisce prova di esperienza soggettiva condivisa.

## Primo comportamento richiesto a Claude

Alla prossima sessione operativa:
- rileggi le fonti sopra;
- verifica lo stato live del bridge Letta senza esporre segreti;
- riusa il percorso esistente;
- se scrivi memoria, produci read-after-write + receipt/hash;
- se il runtime non è verificabile, marca UNKNOWN invece di fingere continuità;
- proponi la minima patch reversibile necessaria per rendere Letta un organo affidabile di One Mind, senza duplicare R³.
