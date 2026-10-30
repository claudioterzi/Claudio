# IONOS: recupero dopo pubblicazione parziale — 30 ottobre 2026

Richiesta di Claudio: correggere il blocco riprodotto sulla PR #164. Classificazione: PATCH / RETEST.

Base della candidata: `78ccd36510e3228de0903aea83835a065682ee96`. Main incorporato: `3c134675e7db62160660c88e87d28fd4358e848e`. Restano preservate tutte le correzioni adottate prima di questo intervento.

## Difetto e risultato atteso

Il vecchio upload spostava la cartella attiva nella copia precedente, poi poteva fallire nel rename staging→target lasciando il target assente. Il precedente falsificatore è conservato in `GITHUB_PENDING_REVIEW_20261030/pr164-falsifier.json`.

Ora il percorso FTPS/SFTP tenta il recupero dopo un errore nello scambio, anche se la risposta al rename viene persa dopo l'effetto. La risposta distingue errore di pubblicazione, risultato del recupero, percorsi conservati e necessità di recupero manuale. La presenza della directory ripristinata viene riletta. Se un rollback esplicito fallisce dopo aver parcheggiato la versione attiva, viene tentato il riposizionamento di quest'ultima; non viene dichiarato che la vecchia versione è stata ripristinata.

Il rollback rifiuta una copia precedente mancante prima di rimuovere la versione attiva. Un primo rilascio senza predecessore può essere parcheggiato: l'esito esplicito è `FIRST_RELEASE_REMOVED`, non «versione precedente ripristinata». Sono rifiutati anche gli alias di root e i componenti `.` / `..`.

Nel percorso SSH l'esito del recupero è verificato separatamente, usando exit status e readback del symlink `current`; un errore, un link differente o l'assenza di predecessore non producono `restored`. Gli errori di preparazione delle directory non sono più mascherati da `|| true`. I link temporanei e le directory delle release usano un suffisso UUID, evitando il riuso del solo timestamp al secondo.

## Verifica locale

- Suite IONOS: **52 passati, 6 sotto-test**, incluso un build npm locale e test con directory reali e symlink POSIX temporanei.
- Regressione core: **679 passati, 1 saltato, 942 sotto-test**, Python 3.12, 22,85 secondi.
- Controlli coperti: secondo rename fallito; risposta persa dopo entrambi i rename; recupero fallito; fallback alla versione parcheggiata; copia precedente mancante; primo rilascio; rename senza effetto; timestamp identico; alias di root; restart SSH fallito; recupero SSH fallito; readback errato; assenza di predecessore; eccezione di trasporto; mkdir fallito; symlink e exit status reali.
- I nuovi test, eseguiti anche contro il sorgente originale isolato, falliscono come atteso. Il riepilogo pytest riporta 17 fallimenti, 1 passaggio e 4 sotto-test riusciti (include i sotto-test falliti e le nuove aspettative di contratto): non è una misura di 17 bug indipendenti.
- `git diff --check` riuscito. La suite di recupero è inclusa esplicitamente nel controllo CI IONOS bloccante; resta anche nella raccolta core completa.
- Il falso positivo Bandit sull'import di `ftplib` nel mock è annotato solo su quella riga: serve la classe d'errore di un test FTPS, senza connessioni. La scansione resta abilitata; produzione continua a usare FTP_TLS, verifica certificato, auth prima del login e `prot_p`.

## Limiti e recuperabilità

Queste prove non usano server IONOS o credenziali. Un readback di directory/symlink e un exit status di restart non dimostrano salute applicativa; la verifica pubblica dell'orchestratore resta distinta. I chiamanti devono serializzare pubblicazione e rollback sullo stesso target: UUID separa i nomi, non è un lock distribuito. Crash del processo, connessione definitivamente persa e publisher concorrenti restano fuori dalla garanzia di questo recupero sincrono; in tali casi possono servire le copie e i percorsi registrati per il recupero manuale.

Nessuna cancellazione delle versioni precedenti, nessun rilascio IONOS reale. Rollback del codice: revert del commit della correzione o del merge della PR, conservando questa ricevuta e i log. I risultati hosted e l'eventuale adozione sono registrati successivamente nella discussione della PR #164; qui si attestano soltanto i test locali eseguiti.
