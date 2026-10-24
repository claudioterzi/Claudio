# INDRA e Fabbrica dei Desideri

Richiesta di Claudio Terzi: salvare la carta INDRA sul sito Vercel e collegare
il meccanismo di programmazione delle azioni della Fabbrica. Firma C.Terzi.

## Perimetro

La pagina `/indra` conserva carta, ruoli, pilota di 14 giorni, esercizi e criteri
di valutazione. I partecipanti e i risultati del pilota non sono ancora acquisiti.
Il sito propone connessioni con Raffaello/R3, Il Terzo Sguardo e SYNESIS;
non le descrive come sincronizzazioni già operative.

Il collegamento `/fabbrica?missione=indra-001#racconta` apre un brief pubblico
predefinito e modificabile. La generazione usa esclusivamente l'endpoint
preesistente `/api/fabbrica/plans` dopo il clic esplicito dell'utente.
Nessun nuovo planner, servizio, provider o archivio è introdotto.

## Riuso e stato verificato

Base di lavoro: `b32f77ed9549a018c6883fb4d2d289b138658555`.
Classificazione retroattiva: `KEEP` per schema, validazione delle dipendenze,
conferme dichiarate e archivio della Fabbrica; `PATCH` per l'ingresso da INDRA.
Le fonti storiche rimangono inalterate:

- `docs/FABBRICA_REGIA_2026-09-10.md`
- `docs/FABBRICA_DIALOGO_AI_2026-09-20.md`
- `fabbrica.py`, `public/fabbrica.js`

Il 14 ottobre 2026 alle 08:50 UTC il GET di produzione
`/api/fabbrica/status` ha restituito `ai_available: true`,
`storage_available: true`, `external_actions_available: false`.
È una verifica di configurazione/disponibilità, non una nuova prova generativa.

## Comportamento del collegamento

- Solo l'identificativo noto `indra-001` seleziona il preset. Testo arbitrario
  dall'URL non entra nel brief o nel DOM.
- L'apertura della missione non riapre l'ultimo copione al suo posto e non
  modifica piani esistenti. Un link esplicito `#copione/<id>` mantiene precedenza.
- Il brief resta modificabile anche se il servizio non è disponibile. Il GET
  di stato non sovrascrive le modifiche fatte durante l'attesa.
- La missione non avvia generazione, invii, prenotazioni o timer all'apertura.
- L'archiviazione del copione segue il comportamento esistente della Fabbrica:
  sessione privata del browser e conservazione dichiarata di 30 giorni.

## Limite dell'integrazione

Questo primo ponte è un ingresso alla pianificazione. Non esiste ancora un
registro condiviso INDRA dei copioni, un ritorno automatico delle prove,
un'assegnazione accettata dai partecipanti o un esecutore durevole di azioni
esterne. Queste capacità sono esplicitamente proposte nella pagina.

## Verifica riproducibile

`npm ci --prefix tests --ignore-scripts` seguito da
`npm run --prefix tests test:fabbrica` esegue la regressione esistente e i sei
scenari del ponte INDRA: ingresso, generazione esplicita, indisponibilità,
identificativi sconosciuti, riapertura ordinaria e precedenza del copione.
Provider e archivio sono sostituiti da fixture in questi test. Prima del commit
entrambe le suite sono PASS. Anche sintassi JavaScript, identificativi HTML,
ancore, CSS, destinazioni locali e route con/senza slash hanno superato i
controlli locali. Il runtime di questo intervento non dispone di un browser
per la verifica visuale; il rendering mobile/desktop non è stato collaudato.

Verificare inoltre route `/indra` e `/indra/`, risorsa CSS, navigazione,
layout mobile/desktop e contenuto distribuito dopo il deploy.
Rollback: revert del commit della pagina e del ponte; backend e record
preesistenti restano invariati.
