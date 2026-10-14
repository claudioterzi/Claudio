# Correzioni del sito Claudio — 14 ottobre 2026

La revisione copre i 49 problemi individuati nell'inventario di 48 pagine statiche e 7 viste server. Questo documento distingue correzioni implementate, verifiche locali e prove che richiedono l'ambiente reale.

## Correzioni

| Rilievi | Comportamento risultante | Verifica |
| --- | --- | --- |
| CORE-01, CORE-08 | Consiglio conserva la domanda fino all'esito, blocca gli invii pendenti e mostra gli errori. | `test_core_ergonomia.cjs` |
| CORE-02 | La ricerca evidenzia soltanto nodi di testo e conserva attributi ed eventi. | `test_core_ergonomia.cjs` |
| CORE-03 | La revoca cancella il token locale soltanto dopo una conferma valida del server. | `test_core_ergonomia.cjs` |
| CORE-04, ROOT-01 | Agorà legge dati versionati e mostra fonte, data, eventuale obsolescenza e retry. Eliminati attività e stati runtime inventati; aumentato il contrasto. | Test core e browser locale |
| CORE-05, MM09 | Le destinazioni private sono riconoscibili; l'accesso conserva una destinazione locale ammessa, senza parametri sensibili. | Test core |
| CORE-06, CORE-07 | Etichette associate e stato di errore/retry per il caricamento del dataset IDEA. | Test core |
| FPC-01 | Talenti ripristina il profilo senza sovrascriverlo con i valori iniziali. | Fixture e modifica/ricarica nel browser locale |
| FPC-02, FPC-04 | Catalogo Parfums navigabile da tastiera; dialogo con nome, focus e chiusura Escape. | Fixture e browser locale |
| FPC-03 | Atelier precompila la domanda; la composizione richiede un'azione esplicita. | Test profumi |
| FPC-05 | Ordinamento Organo con pulsanti e `aria-sort`. | Test profumi |
| FPC-06, FPC-07 | Dispensa e altri campi hanno etichette; scorte e consumi sono limitati ai valori ammessi. | Test profumi |
| FPC-08 | Valigia non sposta più la vista a ogni carattere di ricerca. | Test profumi |
| VS-P1-001 | Nessun TTS automatico all'apertura o al cambio lingua; gestione unica e annullabile della voce. | Test Alpha/viaggi |
| VS-P2-002 | Le carte con apostrofi usano pulsanti e listener validi. | Test Alpha/viaggi |
| VS-P2-003 | Flight Hunter riceve la precompilazione senza perdere i campi già modificati. | Test Alpha/viaggi |
| VS-P2-004 | La stesa manuale consente annullamento dell'ultima carta e nuova stesa. | Test Alpha/viaggi |
| VS-P2-005, VS-P2-007 | Richieste con timeout e annullamento; le risposte obsolete non sostituiscono l'ultima richiesta. | Test Alpha/viaggi |
| VS-P2-006 | Partì funziona anche se lo storage non è disponibile; nessuna ricerca automatica all'apertura. | Test Alpha/viaggi |
| VS-P3-008 | I percorsi Tarot precedenti portano ai renderer Alpha correnti. | Test Alpha/viaggi |
| VS-P3-009 | Inviti validati dal server e risultati ospite canonici. Il contatore locale è presentato come dimostrazione, senza fingere un limite economico server. AI/TTS richiedono la firma Telegram del proprietario. | Test ospiti e autorizzazione provider |
| MM01, MM02, MM14 | Opuscolo adattato al telefono; foglio di stampa A6, comandi esclusi dalla stampa e stato pagina accessibile. | Fixture e browser mobile; stampa fisica non eseguita |
| MM03, MM04, MM05, MM11, MM12, MM13 | Opera conserva focus e URL, etichetta la ricerca, gestisce zero risultati/errori e preferenze di movimento. Carica soltanto il documento scelto, con cache, timeout e protezione dalle risposte fuori ordine. | 19 regressioni multimedia e browser mobile |
| MM06, MM15, MM17 | Opera Viva mantiene firma e titolo scelto; reticoli invariati riusati e aggiornamento coordinato. | Test multimedia |
| MM07, MM08, MM10 | Santuario interrompe il conteggio all'uscita del puntatore, offre azioni da tastiera e una destinazione Telegram esplicita. | Test multimedia; visore Quest non disponibile |
| MM16 | Musica distingue dati mancanti e conteggi disponibili. | Test multimedia |
| ROOT-02, ROOT-03 | Impaginazione mobile e tabelle contenute; Custode ha etichette, errori riconoscibili e ritorno al sito. | Browser locale a 390 px |
| ROOT-04 | Libro con indice, ricerca e 12 capitoli caricati a richiesta; copia integrale e stampa conservate. | Test profumi, controllo dei 400 codici e browser |
| ROOT-05 | L'età dei dati è calcolata quando la pagina è letta, con date non valide/future e intervalli di calendario controllati. | 10 casi di freschezza |
| ROOT-06 | Il catalogo Cubo apre le schede anche da tastiera; mappa 3D e dataset esteso caricati soltanto su richiesta. | Browser e controllo sorgente |
| ROOT-07 | `/prova` dispone di un ritorno al sito. | Controllo sorgente e routing |

## Integrità e controlli

- 64 test Python su Agorà, inviti, autorizzazioni provider e archivio, con ulteriori sottocasi, passati localmente.
- Tutte le otto suite JavaScript della nuova verifica CI passate localmente; test core 18/18, freschezza 10 casi, Alpha/viaggi 14/14, multimedia 19/19.
- 400 ricette, 4.800 righe, 400 codici di ricostruzione, 400 immagini e relativi fingerprint verificati. Il catalogo e i dati canonici non sono rigenerati.
- I 101 documenti Opera derivano byte per byte dal corpus originale: SHA-256 `e57149489a66d5c8f57497d47c5cbd7fd527a6f0a53b7b9bae48b8ede6ca6421`.
- L'originale Libro è conservato in `public/libro-integrale.html`; provenienza, hash e capitoli derivati sono registrati in `public/libro/provenienza.json`.
- `.gitattributes` conserva i byte necessari ai fingerprint anche nei checkout Windows; `.gitignore` include esplicitamente i nuovi indici JSON.
- Le connessioni SQLite dell'archivio sono chiuse anche in caso di errore; sessioni, revoca e rotazione credenziali mantengono i controlli precedenti.

## Confini della verifica

Il browser locale usa dati sintetici e blocca le chiamate esterne e le modifiche ai servizi reali. Le prove locali non attestano invio Telegram, costo dei provider, accesso proprietario reale, ricerche presso fornitori di viaggi o stampa fisica. La mappa 3D con librerie esterne e i gesti sul visore richiedono i rispettivi ambienti. La protezione del deployment Vercel resta attiva; la separazione del codice di accesso nel browser è un controllo di interfaccia e non sostituisce l'autorizzazione del server.

Le date di Agorà sono quelle delle fonti disponibili. Una nuova veste della pagina non produce da sola nuove attività o nuovi progetti: i dati cambiano quando le fonti versionate vengono aggiornate.
