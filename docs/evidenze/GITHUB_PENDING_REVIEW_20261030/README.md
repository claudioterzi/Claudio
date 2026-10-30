# Revisione delle PR in sospeso — 30 ottobre 2026

Richiesta di Claudio: «conferma cose in sospeso GitHub, agisci come fossi io». Inventario iniziale: 24 PR. Risultato verificato via API GitHub: **5 merge (4 su main, 1 sul ramo R3-JUDGE), 1 candidata superata chiusa, 18 PR ancora aperte**. La #166 era già stata adottata prima di questa revisione e non è ricontata.

## Integrazioni confermate

| PR | Destinazione | Merge verificato |
| --- | --- | --- |
| [#49](https://github.com/claudioterzi/Claudio/pull/49) | `main` | `3183acf996de2dfeb7ca4c90d6c11d1db4115dbe` |
| [#77](https://github.com/claudioterzi/Claudio/pull/77) | `main` | `db9144eda00b5608afaa8dcc38b5963c9149a05d` |
| [#76](https://github.com/claudioterzi/Claudio/pull/76) | `main` | `c61ebada59cc16a1e18c667950c81bf63e25bc4d` |
| [#120](https://github.com/claudioterzi/Claudio/pull/120) | `main` | `d9f5eb2c0af5590b1b35ff92cb61945090bc9e47` |
| [#115](https://github.com/claudioterzi/Claudio/pull/115) | `r3-judge-v0.1` | `6a618fb515bdf4e33fd65ef9f286535465e51cca` |

- #49 conserva una proposta storica sulla provenienza/indipendenza: non è promozione a capacità runtime.
- #77 conserva l’audit datato dei nodi e i suoi limiti: non certifica la topologia attuale.
- #76 separa esito della traiettoria e postcondizione e rifiuta tre falsi positivi riprodotti: `"false"` truthy, fonte assente, comparatore non booleano. Le etichette delle fonti restano metadati del chiamante.
- #120 adotta il contratto Evidence Graph in memoria, fonti conservate e nessuna promozione automatica di proxy/errori. La #78 è chiusa come sostituita; ramo e storia restano.
- #115 è unita soltanto a `r3-judge-v0.1`: 19 test mirati passati, nessuna attivazione provider/default.

## Prove e limiti

Per #49, #77, #76 e #120 sono archiviati in [receipt.json](receipt.json) **22 check-runs riusciti per revisione finale**. Rettifica: i messaggi di merge di #49/#77 riportano 23; le liste restituite ne contengono 22. Nessun controllo è stato disabilitato. Il vecchio blocco packaging dipendeva dal lockfile Zod 3.22.4; integrare main ha conservato la correzione Zod 4.6.6 già presente.

Test locali mirati: #76 13 passati + 18 sotto-test; #120 23 + 6; #91 10 + 4. Test combinato su albero `a2535958a015bc01a85e73ebd4c18c7f8991a8ed`: **653 passati, 1 saltato, 940 sotto-test**, log [combined-core.log](combined-core.log). Questo albero include anche #91, che resta non integrata; non è presentato come risultato esatto del main finale. La differenza rispetto a main `c61ebada59cc16a1e18c667950c81bf63e25bc4d` consiste esclusivamente nei cinque file della candidata #91.

Verifica interoperabilità R3-007→R3-011 su quattro fixture filesystem: fonti conservate 4/4; solo il match autorevole restituisce successo verificato; il mismatch è un fatto di mancata postcondizione; proxy e file mancante restano IPOTESI/OTHER ([ricevuta](source-interop.json)). Cercando i consumer nel codice non risultano altri utilizzatori produttivi del nuovo schema; il test del vecchio hash documentale passa. Fonte dichiarata, hash e CI non dimostrano autenticazione, autorità, persistenza distribuita o recovery reale.

Il main risultante `c61ebada59cc16a1e18c667950c81bf63e25bc4d` ha passato le suite core hosted Python 3.11 e 3.12: **644 test e 936 sotto-test per versione** (job 124253143273 e 124253143230). Passati anche le altre suite Python, Test Runner, packaging, sicurezza bloccante, snapshot e frontend. Verifica finale: tutti i 14 controlli completati pertinenti sono riusciti, incluso CI + Security. Dieci controlli condizionali sono saltati. Resta in esecuzione soltanto il workflow indipendente caccia. Errori osservati: nessuno. La caccia voli è un workflow separato e non è validazione di queste PR. Dettaglio in [main-checks.json](main-checks.json). Le correzioni #166 hanno conservato esattamente i tre blob benchmark/backup/RedFrag già validati.

## PR ancora aperte

La tabella distingue blocchi riprodotti, gate espliciti e revisioni ancora da completare. Non certifica che ogni riga contenga un difetto.

| PR | Stato della revisione | Verifica o intervento necessario |
| --- | --- | --- |
| [#164](https://github.com/claudioterzi/Claudio/pull/164) | BLOCCO RIPRODOTTO | Lo swap FTPS/SFTP può lasciare assente la directory attiva se fallisce il secondo rename. Recupero da verificare anche sul percorso SSH; finding Bandit nei test separato dal difetto funzionale. |
| [#134](https://github.com/claudioterzi/Claudio/pull/134) | GATE FALLITO/APERTO | Il test frontend delle route fallisce sulla revisione ispezionata; la PR richiede ancora preview protetta sulla revisione esatta. Conservare autenticazione Vercel e provare accessi owner/guest. |
| [#121](https://github.com/claudioterzi/Claudio/pull/121) | PARZIALMENTE SUPERATA | Benchmark/backup/RedFrag già adottati con #166; base Evidence Graph adottata con #120. Isolare e provare soltanto i delta residui rete/snapshot senza regressioni. |
| [#119](https://github.com/claudioterzi/Claudio/pull/119) | CANDIDATA DA RICONCILIARE | Il vecchio blocco credenziali e le ricevute backup sono datati. Aggiornare contro lo stato corrente e provare inferenza Jev autenticata senza trasformare ricevute storiche in disponibilità attuale. |
| [#117](https://github.com/claudioterzi/Claudio/pull/117) | CHECKPOINT STORICO | Descrive device offline e fatti di ottobre iniziale. Conservare le evidenze datate, riconciliare memoria/coda con PC ora acceso e modifiche recenti, senza ripristinare vecchi blocchi come stato corrente. |
| [#113](https://github.com/claudioterzi/Claudio/pull/113) | GATE RUNTIME APERTO | La PR richiede recovery autenticato da stato reale e sleep/resume Railway. Tocca r3/** e può riavviare i nodi al merge: i test locali non sostituiscono quel gate. |
| [#97](https://github.com/claudioterzi/Claudio/pull/97) | CANDIDATA MODELLO | Conservare la distinzione fra test deterministici e inferenza CLM/Jev live; riconciliare il client condiviso con #96 e completare il confronto su casi tenuti fuori dallo sviluppo prima di promozione/default. |
| [#96](https://github.com/claudioterzi/Claudio/pull/96) | CANDIDATA MODELLO | Il fixture iniziale a cinque casi non dimostra generalizzazione. Serve il confronto preregistrato più ampio; mantenere TypeSafe/Jev di default e confrontare il delta con #97. |
| [#91](https://github.com/claudioterzi/Claudio/pull/91) | CORRETTA, DRAFT MANTENUTO | Confinamento percorsi/symlink corretto; 10 test + 4 sotto-test locali, 22 check-runs success e 2 skipped. Il gate A/B del 28 settembre su token/latenza/successo/provenienza resta aperto. |
| [#88](https://github.com/claudioterzi/Claudio/pull/88) | GATE A/B APERTO | La PR TERZI dichiara esplicitamente benchmark/admission ancora necessari. Equivalenza e risparmio non sono provati dai soli test strutturali. |
| [#81](https://github.com/claudioterzi/Claudio/pull/81) | MAPPA DA RICONCILIARE | Propone una mappa del 22 settembre come ingresso obbligatorio in AGENTS. Verificare riferimenti e stati dopo #76/#120/#166 prima di renderla parte del bootstrap canonico. |
| [#80](https://github.com/claudioterzi/Claudio/pull/80) | DIPENDENZA DA AGGIORNARE | Contiene una copia precedente del verification_harness. Incorporare la versione rigorosa adottata con #76 e rieseguire i controlli BODY; simulazione software non prova hardware. |
| [#79](https://github.com/claudioterzi/Claudio/pull/79) | CONTROLLO LIVE FALLITO | La revisione ispezionata ha live-smoke fallito oltre al vecchio packaging. Diagnosticare e provare autenticazione, identità provider/modello e failover prima di ammettere il gateway. |
| [#74](https://github.com/claudioterzi/Claudio/pull/74) | CANDIDATA R3-022 | Il gate preregistrato richiede replay provider autorizzato, provenienza e misurazione degli effetti. Test sintetici non bastano a promuovere continuità o immunità a contaminazione. |
| [#63](https://github.com/claudioterzi/Claudio/pull/63) | REVISIONE COMPORTAMENTO/COSTO | Inserisce sette domande RRR in ogni judge e duplica policy nell’app. Riconciliare la policy condivisa e misurare semantica, costo e latenza prima di cambiare tutte le chiamate. |
| [#52](https://github.com/claudioterzi/Claudio/pull/52) | CONFIGURAZIONE RUNTIME DA VERIFICARE | Aggiunge r3/railway.json con path Dockerfile e start uvicorn. Richiede verifica sul rootDirectory e servizio effettivo prima di applicare configurazione datata; nessun cambio Railway eseguito. |
| [#50](https://github.com/claudioterzi/Claudio/pull/50) | GATE PREVIEW APERTO | La PR richiede Preview Vercel completa e una scena campione prima di estendere la pipeline. Revisione visuale e validazione di contenuti/capacità non concluse in questo controllo GitHub. |
| [#43](https://github.com/claudioterzi/Claudio/pull/43) | PREVIEW PRIVATA DA VALIDARE | Nuovo flusso Alpha74/feedback e route: validare preview, confini guest e conservazione dei contenuti prima di pubblicazione; nessun invito inviato. |

## Falsificatore del rilascio IONOS

Su #164 head `78ccd36510e3228de0903aea83835a065682ee96`, simulare il fallimento del secondo rename dopo aver spostato `/app` lascia il target attivo assente. La copia precedente esiste, ma non viene ripristinata automaticamente. [Ricevuta](pr164-falsifier.json). Nessuna rete o macchina IONOS è stata usata. Il finding Bandit B402 è distinto: import di ftplib nel test, mentre la connessione di produzione usa FTP_TLS, verifica TLS e `prot_p`. La discussione della PR registra entrambi e il rischio di dichiarare ripristino SSH senza controllarne il risultato.

## Grafo delle dipendenze

Graphify 0.9.97 eseguito realmente con backend `none`: adapter deterministico sui diff Git, export, cluster-only ed explain. **234 nodi, 243 archi, 16 file condivisi fra PR**. [Grafo](graph.json), [manifest delle fonti](graph_sources.json), [report generato](GRAPH_REPORT.md), [intorno del verificatore](verification-neighborhood.txt).

Il grafo descrive l’inventario iniziale con head/base esatti, non il codice finale di tutte le PR. Un arco CHANGES_FILE è una relazione estratta dal diff, non una dipendenza semantica o causale; i gruppi dell’algoritmo non autorizzano modifiche architetturali. Ha evidenziato #76↔#80 sul verificatore e #78↔#120 su Evidence Graph, poi confermati leggendo i diff. Nessuna inferenza a pagamento e nessuna pretesa di completezza semantica.

## Copertura e prossima azione

Inventariate tutte le 24 PR per stato, head, scope e CI; revisione approfondita e test sulle candidate selezionate e sui blocchi citati. Nessuna revisione umana indipendente è simulata: l’account connesso è autore delle PR. Nessun force-push, cancellazione di branch, cambio credenziali, inferenza esterna o deploy IONOS/Railway diretto. I normali hook di GitHub possono partire dai merge; un check deploy riuscito non è verifica del runtime.

Priorità residua: correggere e falsificare il recupero dello swap #164 prima di qualunque rilascio. Poi riconciliare lo stack #121 e la dipendenza #80 contro le correzioni già adottate. Mantenere separati i gate sperimentali e runtime delle altre candidate.
