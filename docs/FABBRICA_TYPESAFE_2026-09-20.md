# Fabbrica: cene, TypeSafe e blocco della pagina — 20 settembre 2026

Richiesta diretta di Claudio: inserire TypeSafe nella funzione Vercel che organizza
cene ed esperienze e correggere il malfunzionamento. Firma progetto: C.Terzi.
Classificazione retroattiva del bridge Fabbrica/Viaggi: PATCH.
Base verificata: 59acad0cc9823d09d1a0a1c4b5e9e3792c13cea9.

## Causa riprodotta

Un POST reale di prova cena a Bruxelles ha ricevuto HTTP 200 dal backend di
produzione (log Vercel 20/09/2026 02:18 UTC). La pagina è poi diventata
inaccessibile al browser di verifica. Il vecchio bridge `fabbrica-viaggi.js`
considerava il nome della città un viaggio e riscriveva `innerHTML` nel sottoalbero
osservato dal proprio MutationObserver. Il test DOM sul sorgente originale
riproduce il ciclo (`Runaway mutation observer`); lo stesso scenario con il nuovo
bridge termina e mantiene i controlli utilizzabili. HTTP 200, da solo, non prova
la correttezza del piano né la sua riapertura sul sito reale.

## Modifica

- Aggiornamento del bridge attraverso l'evento di rendering del copione.
- Una città da sola non attiva più il suggerimento di viaggio.
- Le preferenze passano al Flight Desk nello storage locale esistente; non nei
  parametri dell'URL. Il destinatario legge anche il passaggio senza parametri.
- Budget HTML corretto, esempio cena accessibile, revisione fino a 8.000 caratteri
  per accogliere le risposte del dialogo già esistente (prima il server ne ammetteva 700).
- TypeSafe valuta brief e revisione prima della generazione, dopo quote e deduplica.
  Choice per il tipo di esperienza; Noul per dettagli mancanti, musica e viaggio.
- Il planner Gemini/Anthropic esistente riceve i suggerimenti. Probabilità,
  modello, hash dell'input e versione della policy sono conservati col copione.
  Il modello suggerisce; non autorizza contatti, prenotazioni o pagamenti.
- Trasporto TypeSafe comune in `typesafe_sister/client.py`, riusato sia dal sito
  Flask sia dalla sister API. Non è stato creato un secondo servizio di hosting.
  Chiamata HTTP conforme a https://docs.typesafe.ai/api, senza retry o redirect.
- Chiave solo server-side; nessun invio di archivi, cookie di sessione o contatti
  memorizzati. Se manca la chiave, l'API non viene chiamata. Un guasto TypeSafe
  lascia disponibile la generazione esistente e non viene presentato come una valutazione.
- Il servizio sister rifiuta token mancante o il vecchio default noto.

## Verifica locale

- `python -m pytest -q tests/test_fabbrica.py tests/test_fabbrica_typesafe.py tests/test_viaggi_validation.py`:
  28 passed, 15 subtests passed. Provider e archivio sostituiti da fixture; non è
  una misura della qualità di Jev né una prova di chiamata TypeSafe live.
- `npm ci --prefix tests && npm run --prefix tests test:fabbrica`:
  scenari DOM cena, viaggio, TypeSafe indisponibile, revisione oltre 700 caratteri,
  passaggio privato e precompilazione del Flight Desk riusciti.
- Controprova sul bridge originale: errore di ciclo riprodotto.
- `git diff --check`: riuscito.

## Configurazione e limiti

Nel progetto Vercel `claudio` serve `TYPESAFE_API_KEY` nel secret store del server
(Production e Preview se si vuole verificare anche l'anteprima). Opzionali:
`TYPESAFE_MODEL` (default `jev-latest`) e `TYPESAFE_BASE_URL` (API ufficiale).
Non serve esporre `/judge` al browser, creare un dominio Railway o passare una
chiave al frontend. Riutilizzare una chiave custodita nel secret store; non
inserirla nel repository, in documenti o in un URL.

`GET /api/fabbrica/status` riporta solo `typesafe_configured`: la presenza della
chiave non prova che sia valida. Una nuova generazione deve restituire
`assessment.status=evaluated` e poi essere riletta dallo stesso browser per la
prova completa. I vecchi copioni rimangono consultabili senza rivalutazione.

Le soglie 0,75 selezionano solo suggerimenti reversibili e sono provvisorie.
La calibrazione su brief rappresentativi e i tempi/costi reali restano da misurare.
La qualità semantica e l'attivazione live non sono certificate dai test di contratto.
Il documento Drive TYPESAFE-FABBRICA-20260920-01 descrive un candidato parallelo
non pubblicato: questa patch riusa la stessa finalità, senza dichiarare eseguite
le sue prove live. Nessuna automazione di monitoraggio sospesa viene riattivata.
