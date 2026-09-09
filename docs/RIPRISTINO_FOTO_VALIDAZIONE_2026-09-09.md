# Ripristino foto — validazione del testo

Concept e direzione: Claudio Terzi · © 2026 Claudio Terzi.

## Evidenza iniziale

Segnalazione utente: IMG_1069, errore generico nell’analisi della fotografia.
Versione di produzione verificata: bc71fb90aa3936fd40a321327b00f9b6f4f59589,
Vercel READY. Prova pubblica POST /profumo con foto_esempio=cantiere:
HTTP 503, 20,33 s, intestazione vision_invalid_direction_length.
La specifica foto che ha generato lo screenshot non è disponibile in questa
segnalazione; il test riproduce la stessa pagina d’errore con l’esempio pubblico.

La risposta del provider superava un controllo locale sui campi direzione o
incertezze. Il limite stilistico era anche un limite rigido di accettazione:
direzione 500 caratteri, incertezze 300. Analisi valide più lunghe potevano
essere scartate. Il codice d’errore preesistente unisce tipo e lunghezza:
la regressione di lunghezza viene verificata separatamente con fixture valide.

## Correzione

- Schema esplicito responseJsonSchema: tipi, campi obbligatori, massimo cinque
  osservazioni e cinque associazioni, senza campi estranei richiesti.
- Separati gli obiettivi di brevità dalla validazione. Conservati integralmente
  i testi validi, comprese le incertezze, entro 12.000 caratteri complessivi.
- Rimangono il limite di risposta 100 KB, maxOutputTokens 1500, controllo dei
  campi non vuoti e delle strutture. Output bloccati, troncati o senza dati
  non producono una formula. Nessun ripiego testuale simulato e nessun retry.
- analysis_version=2 identifica le nuove interpretazioni nelle schede.
- Dettagli assistenza e log contengono solo codice e ID casuale della richiesta;
  nessuna foto, intenzione, credenziale o identità cliente viene registrata.

Documentazione primaria consultata:
https://ai.google.dev/api/generate-content#v1beta.GenerationConfig
Il subset JSON Schema supportato include required, properties e maxItems;
non si presume il supporto di maxLength. Nessuna migrazione di modello o API.

## Test

56 test Python superati, inclusi 9 test foto. Nuova regressione: analisi con
campi oltre tutti i vecchi limiti conservata senza tagli e con una sola chiamata
al provider. Tipi errati, liste oltre cinque elementi e dimensioni eccessive
continuano a essere respinti. Confermati controllo dei bytes e rimozione EXIF,
chiavi normalizzate, blocchi del provider, POST nativo e replay dell’archivio.

Collaudo della nuova versione online: in corso.
