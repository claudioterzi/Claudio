# Revisione del lavoro del 9 settembre — Organo Terzi completo

Concept e direzione: Claudio Terzi · © 2026 Claudio Terzi.

## Criterio richiesto

Le formule devono scegliere fra tutte le essenze dell'organo deciso da Claudio, con identità verificabili. “Tutte disponibili” non significa mettere tutte le materie in ogni ricetta. Il catalogo descrive il progetto di organo; non misura le quantità fisiche possedute oggi.

## Catalogo verificato

Fonte dichiarata: `Organo_Terzi_300.xlsx`; dati operativi: `studio/parfums/organo_terzi_300.json`.
SHA-256: `13aff1815ecef35044352b0baa4709be5484597836e6aba25d87af17179309d5`.

- 300 voci: 104 naturali, 167 sintetiche, 22 basi e 7 solventi/supporti.
- 293 materie per la piramide; tutte raggiungono il prompt in modalità completa, comprese ESP e MASTER.
- CORE: 45 materie; CORE + ESP: 127; completo: 293. I filtri ridotti sono una scelta esplicita dell'utente.
- I 7 supporti restano nel catalogo e sono elencati nella scheda. Non sono aggiunti automaticamente: la preparazione richiede scelte di solvente e diluizione.
- La Dispensa attuale conserva spunte e consumi soltanto nel browser. Non è un inventario condiviso fra dispositivi e non viene usata come filtro implicito.

## Correzioni realizzate in questa revisione

1. Eliminato il riempimento automatico di ricette incomplete: la precedente funzione poteva inserire una materia generica e lasciare una motivazione riferita ad altre scelte.
2. Introdotti contratto JSON nel prompt, validazione rigorosa e una riscrittura completa chiesta al modello dopo una risposta non conforme. Numeri estranei, solventi, frazioni, booleani, duplicati e scia senza ruolo vengono respinti. Se la correzione fallisce, nessuna ricetta di comodo viene inventata.
3. Il modello riceve tutte le righe ammesse, con nome, famiglia, nota, forza, livello e ruolo scia; nessuna preferenza automatica per CORE. Ogni ricetta registra impronta del catalogo, quantità di materie disponibili e verifica.
4. Aggiunto il codice TRZ1 anche alle nuove creazioni, con collegamento al decodificatore e numeri dell'organo visibili accanto ai nomi.
5. Corretto il compositore locale, che poteva allargare silenziosamente l'ondata. Testate 72 combinazioni: 3 stili × 8 famiglie × 3 selezioni.
6. Allineati generatore e template dell'Atelier: rigenerare la pagina non perde più i campi e le funzioni aggiunti oggi.
7. Applicato un budget condiviso alle chiamate. Dopo l'insuccesso live, gli adattatori dei fornitori sono stati ripristinati byte per byte alla versione precedente, senza sostituire il modello. I retry interni Anthropic restano un limite: il budget applicativo non garantisce la durata assoluta della richiesta.
8. Corretta la diagnosi non dimostrata sulla ricerca: “fonti non disponibili” non prova una chiave assente. Ora si conserva il motivo tecnico senza esporre segreti.

## Riesame delle altre consegne di oggi

| Area | Evidenza controllata | Stato e limite |
|---|---|---|
| Protocollo RRR / Astra | Documento operativo e test del validatore di evidenze | Metodo e codice offline presenti; nessun benchmark di un nuovo modello dimostrato |
| Pagine e navigazione | Nuovo GET delle 17 pagine HTML pubbliche: tutte 200 | Disponibilità confermata; non collaudo di ogni servizio o di iPhone fisico |
| Canone Alpha | Test locali del catalogo e dei 592 stati | Regressione controllata; interpretazione simbolica |
| Viaggi | Test di validazione input | Non ripetute ricerche a pagamento o prenotazioni; copertura fonti già documentata |
| Libro dei 400 | 400 ricette, nomi/ID conformi al catalogo; 400 codici decodificabili | Nessuna prova olfattiva: correttezza informatica distinta dalla qualità del profumo |
| Immagini e stampa del libro | 400 riferimenti alla stessa immagine `libro-photonic.webp`; pilota Lettre de Midi N°1 già consegnato | I 400 flaconi individuali e la riscrittura completa dei testi non sono completati |
| Archivio e seriali | Test di persistenza locale e immutabilità; errore esplicito senza storage in produzione | L'archivio permanente richiede configurazione verificabile; un codice formula non è prova di registrazione |
| Immagini AI nel sito | Codice e condizioni di attivazione ispezionati | Generazione non attestata attiva; il prompt attuale varia atmosfera e tinta, non garantisce 400 geometrie individuali |
| Guest, iscrizione, pagamento | Flussi non completati nel codice pubblicato | La Soglia client non equivale ad autenticazione; quota guest e pagamento non attivati |

## Verifiche

- 34 test Python superati. Il test esaustivo inserisce a turno ciascuna delle 293 materie e verifica che la selezione non venga sostituita.
- JavaScript: invio con cliente vuoto e senza `crypto.randomUUID`, trasmissione di stile/riferimento/organo completo, identità delle 293 righe e 72 composizioni locali controllate.
- Tutte le 400 ricette del canone corrispondono ai nomi e numeri dell'Organo; tutti i 400 codici superano il round-trip.
- Prova live della revisione dell'organo: **Iris Céleste**, 12 materie, 100 parti, con ESP e MASTER (fra cui Iris/Orris butter, Hedione HC e Muscenone). Collegamento TRZ1 aperto: decodificatore con 12 righe, identità e dosi corrispondenti, totale 100. Scheda esplicitamente non archiviata. Questo test precede l'estensione delle preferenze multiple.
- Estensione successiva: riconoscimento contestuale, campo fino a 5 preferiti e progetto visivo della ricetta. Stato, confronto tecnologico e limiti in `docs/ATELIER_GUSTI_FLACONI_2026-09-09.md`.

Le quantità restano dosi algoritmiche relative; concentrazioni delle soluzioni madre, solvente, procedura e prove di laboratorio non sono ricavabili dal solo totale 100. Non viene dichiarata riproducibilità fisica completa né equivalenza con un profumo commerciale.

## Copie e accesso ai registri

La copia aggiuntiva dei sorgenti nella cartella Drive Terzi Parfums è stata respinta dal controllo automatico delle autorizzazioni; non viene dichiarata sincronizzata e non viene ritentata senza conferma dell'utente. Il repository resta la copia tecnica salvata.

L'accesso al progetto tramite il connettore Vercel restituisce HTTP 403. I registri di produzione non sono stati letti; lo stato di pubblicazione è verificabile attraverso il collegamento GitHub/Vercel. La prima prova live della revisione ha restituito indisponibilità del compositore: mantenuta la chiamata JSON compatibile, ripristinato il timeout da 26s e il catalogo compatto completo. Queste modifiche riducono le differenze rispetto al percorso precedentemente funzionante; senza registri non provano la causa del primo errore.

Riferimenti tecnici: [output strutturato Gemini](https://ai.google.dev/gemini-api/docs/generate-content/structured-output), [ricerca Google con Gemini](https://ai.google.dev/gemini-api/docs/google-search), [formule dimostrative Fraterworks](https://fraterworks.com/pages/demo-formulas). Nessuna formula privata acquisita.
