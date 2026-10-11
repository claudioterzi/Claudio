# R³∞ — Protezione della memoria locale v1.1.0

Autore del progetto: Claudio Terzi · C.Terzi  
Data: 11 settembre 2026

## Ambito e continuità

Correzione del motore `public/r3-memory.js`, senza migrazione dei record V1,
nuovi servizi, modifiche di accesso o caricamenti di memorie personali.
La sincronizzazione server, tra dispositivi e tra chat NON è attivata.
Il canone rimane un insieme di dichiarazioni, non una verifica indipendente.

Baseline: `5ac565ebc4ddd95b047d08330216a2c362aeb7fa`.
Il blob del motore è lo stesso auditato: `3f10c3203c87d67572eb46883b5001e4e5e2b455`.

## Correzioni

1. Importazioni: controllo di schema, hash, identità e catena PRIMA della scrittura.
   File alterati, catene indipendenti o divergenti sono rifiutati senza cambiare
   il ledger. Import ripetuti e prefissi sono idempotenti; estensioni valide
   mantengono esattamente record e hash precedenti. Nessuna fusione mediante
   riscrittura degli hash. Conservare gli export separati dei rami divergenti.
2. Scritture: coda nella pagina e Web Lock esclusivo condiviso dalle schede
   compatibili dello stesso origin. Controllo della revisione prima del salvataggio.
   JSON danneggiato non è trattato come registro vuoto. Il ledger viene scritto
   in una sola operazione; un errore dei metadati non simula il fallimento del dato.
3. Negazioni: gestione esplicita e confronto di parole intere. Un conflitto candidato
   non viene classificato contemporaneamente come quasi-duplicato. Rimane
   un'euristica linguistica, non un classificatore infallibile delle contraddizioni.
4. Esportazione: aggiornamento centralizzato dopo modulo, import e comando manuale;
   il download ricostruisce il rapporto corrente, non quello conservato all'avvio.
5. Canone: priorità risolte per riferimento esplicito, identità o mappa compatibile
   delle etichette note, mai per posizione. Identità stabili al riordino; voci non
   riconosciute restano prive di priorità. Stato assente diventa IPOTESI, non FATTO.
6. Provenienza: errore HTTP/rete/formato del canone produce `incomplete: true`,
   avviso nel rapporto e nell'interfaccia. Un canone caricato ma vuoto è distinto
   da uno non disponibile. Il comando manuale ritenta il caricamento.

## Verifica riproducibile

```sh
node --check public/r3-memory.js
node tests/r3-memory-integrity.cjs
```

32 prove Node.js v22.16.0 superate, zero fallimenti. Sono dati sintetici,
DOM minimale e un gestore di lock simulato condiviso tra contesti. Comprendono
50 aggiunte concorrenti da due contesti, import alterati e divergenti,
compatibilità V1, quote, rapporti aggiornati e canone indisponibile.
I dieci test originali sulla baseline danno nuovamente quattro PASS e sei FAIL.
Non dedurre una percentuale generale di affidabilità da questa selezione.

Tentato un collaudo con Chromium/Playwright: la navigazione alla fixture locale
è stata bloccata dall'ambiente (`ERR_BLOCKED_BY_ADMINISTRATOR`) prima del primo caso.
NON è un test superato. Nessun aggiramento effettuato. Il browser autenticato di
produzione e il telefono dell'utente non sono stati collaudati.

## Limiti operativi da non nascondere

Ricaricare tutte le vecchie schede del sito prima di scrivere: la versione
precedente non partecipa al nuovo lock. Web Locks coordina solo contesti
cooperanti che condividono lo storage, non dispositivi, origini diverse o vecchio codice.
Se Web Locks manca, il motore rifiuta le scritture ed espone la sola lettura.
La catena SHA-256 rileva incoerenze, non autentica l'autore e non impedisce a un
programma con accesso al browser di riscrivere tutto. Il ledger V1 resta locale.
Limiti locali: 5.000 eventi, input massimo 8 MiB; la quota del browser può essere
inferiore. Il confronto delle coppie resta quadratico: non è un motore server
scalabile. Nessuna prova di funzionamento continuo a pagina chiusa.

## Prossimo passaggio, non realizzato da questa modifica

Registro autenticato condiviso, con identità degli eventi e dei dispositivi,
controllo degli accessi per proprietario, concorrenza transazionale, import dei
rami con provenienza, backup e ripristino verificati. La connessione delle chat
richiede inoltre uno strumento autorizzato di lettura/scrittura: non basta pubblicare
il registro. Prima di attivarlo: test di isolamento e rifiuto accessi non autorizzati.

Riferimenti tecnici: W3C Web Locks API (https://www.w3.org/TR/web-locks/);
WHATWG Web Storage (https://html.spec.whatwg.org/dev/webstorage.html).
