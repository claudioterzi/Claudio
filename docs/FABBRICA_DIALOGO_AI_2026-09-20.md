# Fabbrica — IA nelle microdomande

Richiesta diretta di Claudio del 20 settembre 2026: analizzare le domande dopo
la creazione del sogno e aggiungere aiuto IA a ciascuna risposta per affinarlo.
Firma: C.Terzi. Classificazione del dialogo precedente: PATCH.
Base: `405974f8cf49be868751cb8cc15812dad27c79d9`.

## Stato TypeSafe verificato prima di questa modifica

La chiave è stata configurata come Secret solo per Production nel progetto
Vercel `claudio`. Il redeploy `dpl_GXo84BNJ8yLYVcsc3mFZbVUnqs7B` della base è READY
e associato a `claudio-ebon.vercel.app`. Una nuova cena sintetica è stata generata
e riaperta: l'interfaccia riporta la valutazione TypeSafe e il percorso Cena;
i log di produzione riportano POST TypeSafe `/v1/systemone` HTTP 200 alle
03:11 UTC. Non è una misura generale di qualità o calibrazione. Il benchmark
semantico T-TS-FAB-002 resta distinto da questa prova funzionale.

## Problemi trovati e modifica

Il vecchio dialogo aggregava le risposte in un campo di testo, richiedeva poi
un secondo invio e indicizzava le risposte per posizione q1/q2/q3. Il backend
passava il piano precedente ma non una memoria esplicita delle scelte lungo
più revisioni. La scelta manuale del peso poteva essere sovrascritta durante
la digitazione.

- Ogni domanda offre «Aiutami a rispondere», una richiesta di consiglio
  facoltativa e «Affina con questa risposta». Si può anche applicare l'insieme.
- Raffaello genera spiegazione e proposte attraverso i provider già presenti.
  Scegliere una proposta la copia nel campo modificabile; solo l'azione di
  affinamento la applica al copione. Non diventa una preferenza per sola inferenza.
- Risposte e priorità sono conservate nel record privato, con provenienza
  `user_choice`, radice del sogno e revisioni testuali in ordine. Le scelte
  precedenti restano modificabili. Una domanda nuova non eredita la risposta
  della vecchia domanda nella stessa posizione.
- Bozze non applicate rimangono nel browser; scelte applicate vengono rilette
  dal server. Il rendering usa gli eventi del copione, senza MutationObserver.
- Il contesto accumulato dello stesso sogno raggiunge anche TypeSafe quando
  si rivede il piano. Gli archivi di altri sogni non vengono inviati.
- Il planner può concludere senza nuove domande quando ha i dati necessari.
  Riceve la data attuale e l'indicazione di non trasformare il sottofondo
  musicale in un musicista ingaggiato senza richiesta: due errori osservati
  nella prima prova live della base.

## Confini e verifica

Endpoint privato: POST `/api/fabbrica/plans/<id>/question-help`. Verifica
sessione proprietaria, origine, versione, appartenenza della domanda e limiti
del testo prima delle chiamate. Quota aiuti distinta (20/ora per IP/sessione,
150/giorno complessivi), deduplica e lock. Nessun contatto o acquisto.
Output a schema validato e testo semplice nel DOM. Proposte e tentativi sono
conservati server-side; la cancellazione del copione elimina atomicamente anche
i relativi aiuti/cache. I provider e i segreti non sono esposti al frontend.

Verifica locale: 34 test Python e 15 subtest; harness DOM con cena/viaggio,
proposte da scegliere, mancata sovrascrittura automatica, affinamento singolo,
vincoli persistenti, errore IA recuperabile, HTML del modello reso come testo,
assenza di risposte stale e handoff privato. Provider/Redis sono fixture:
questi test non certificano qualità generativa o operatività di produzione.
Il workflow Test Runner esegue ora anche le suite Fabbrica e il test DOM.

Limiti: massimo 32 scelte e 20 revisioni entro un contesto JSON di 24.000
caratteri. Nessuna cancellazione silenziosa della memoria quando il limite
viene raggiunto. Per record storici si conserva l'ultima revisione esplicita
disponibile; non si ricostruisce retroattivamente una cronologia non registrata.
I suggerimenti restano da valutare. Il test semantico dei 24 brief non viene
dichiarato eseguito da queste fixture. Rollback: revert della modifica al dialogo;
la configurazione TypeSafe server-side può rimanere sulla base già verificata.

## Appendice — prova online e correzione delle scadenze

PR #65 pubblicata su `32047a2bec6bbfa80f86c92d693c291472fce143`.
La prova online ha prodotto un aiuto sulla musica (HTTP 200), lasciato invariata
la risposta fino alla scelta esplicita, accettato una modifica manuale e generato
un nuovo copione con playlist jazz di due ore, tetto di 250 euro e nessun musicista.
TypeSafe ha risposto HTTP 200 anche nella revisione; la domanda già risposta è
passata fra le scelte integrate. Si tratta di un caso sintetico, non del benchmark.

RETEST/PATCH: il modello ha però copiato dal piano precedente una scadenza già
trascorsa, nonostante il prompt contenesse la data attuale. Il controllo
deterministico ora segnala come da ripianificare le date assolute trascorse nelle
microazioni ancora da svolgere, comprese quelle nei vecchi copioni riaperti.
Segnala anche date impossibili e non inventa scadenze sostitutive. Supporta date
italiane con anno, ISO e numeriche giorno/mese/anno; date relative e senza anno
restano da verificare. Le azioni dichiarate complete e i record storici rimangono
intatti. Il contesto di revisione riceve lo stesso avviso.

Verifica locale della correzione: 36 test Python e 26 subtest superati, inclusi
formati data, data odierna/futura, data impossibile, idempotenza, riapertura di un
record storico e mancata modifica dell'evidenza salvata. La verifica online di
questa correzione va registrata separatamente dopo la pubblicazione.
