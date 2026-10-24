# La Soglia — I miei canali

Richiesta del proprietario, 12 ottobre 2026: creare sul sito La Soglia una pagina
per raggiungere e gestire i propri canali attraverso i collegamenti.

## Ambito e provenienza

- Base di lavoro: `76be7d82c4f9b3c2c0445191c552e769121a6d46`, progetto Vercel `claudio`.
- Instagram indicato dal proprietario e verificato sul profilo pubblico: `@claudioterzi`.
- Facebook: il riferimento `/claudioterzi` reindirizza alla Pagina `/claudio.terzi/`.
- La pagina `/canali` contiene soltanto collegamenti e informazioni d'uso. Non
  custodisce credenziali, sessioni, numeri privati, conversazioni o dati di account.
- Metricool installato nella chat; alla verifica del 12 ottobre non risultavano
  social collegati. Questa fotografia non diventa un indicatore live sul sito.
- I due WhatsApp condividono la stessa destinazione Web: la scelta dell'account
  dipende dalla sessione del browser. L'interfaccia lo rende esplicito.
- Il centro operativo locale è raggiungibile solo dal PC su cui è in esecuzione.

## Verifica e conservazione

Controllati localmente: sintassi JavaScript, diff, caricamento nel browser,
otto schede, filtro Messaggi e ritorno a Tutti, layout mobile senza overflow.
La pubblicazione richiede inoltre l'esito dei controlli della PR e la verifica
del contenuto sulla route Vercel. Nessuna pubblicazione social è parte della prova.

Retroactive Canon Overlay: **KEEP** per accessi esistenti, archivio e struttura
del sito; **PATCH** per la directory e la navigazione. Le protezioni e il percorso
legacy `/soglia` restano quelli della base. La directory non dichiara una nuova
capacità di autenticazione, invio o controllo remoto.

Rollback: revert del commit della directory; nessuna migrazione di dati.
