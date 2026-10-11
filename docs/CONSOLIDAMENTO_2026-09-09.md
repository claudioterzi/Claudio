# Consolidamento Terzi Parfums

© Claudio Terzi · 9 settembre 2026

Questo documento riunisce lo stato verificato del lavoro sul sito `claudio-ebon.vercel.app` e sul repository `Claudioterzi/Claudio`.

Revisione successiva dello stesso giorno: vedere `REVISIONE_ORGANO_COMPLETO_2026-09-09.md`. Corretto il completamento automatico e verificata l'intera selezione delle materie.

## Atelier di Raffaello

- Il cliente è facoltativo: il nome può comparire sull'etichetta, ma non blocca la creazione.
- Il campo **Profumo di riferimento** accetta marca, nome e versione. Il server passa il riferimento a una ricerca separata e bounded; il nome del cliente non viene inviato alla ricerca.
- La ricerca Gemini con Google Search è considerata documentata solo con query, grounding supports e URL HTTPS. In assenza di chiave o grounding la scheda mostra esplicitamente che l'interpretazione non è verificata.
- Le risorse tecniche pubbliche sono attribuite: documentazione Google, Fraterworks demo formulas, Givaudan e dsm-firmenich. Non sono state copiate formule proprietarie o formule Deluxe a pagamento.
- Sono disponibili gli stili Carles, Ellena e Roudnitska, con conteggi e distribuzioni distinti.
- Il server applica davvero l'ondata scelta: CORE, CORE + ESP oppure organo completo. I solventi sono esclusi dalla selezione.
- Le proposte incomplete, duplicate o con materie esterne vengono respinte dal validatore e rimandate al modello per una riscrittura completa. Il riempimento automatico introdotto nel primo consolidamento è stato rimosso: poteva cambiare la ricetta senza aggiornare la motivazione.
- Le dosi sono una costruzione didattica deterministica su 100 parti; non costituiscono una formula produttiva o una validazione olfattiva.

## Archivio, flacone e codici

- Le creazioni possono avere nome cliente, seriale UUID e impronta SHA-256 quando l'archivio persistente è configurato.
- Il flacone grafico è disponibile nella scheda; la generazione di immagini AI resta subordinata alle chiavi e ai flag di produzione.
- Il formato `TRZ1` collega ogni ricetta alle essenze dell'istantanea immutabile dell'Organo e permette il controllo di catalogo, checksum e somma 1000.
- Il Libro dei 400 contiene il codice di ricostruzione di ogni ricetta e collega ogni voce alla pagina di decodifica.
- Il PDF pilota stampabile di Lettre de Midi N°1 documenta il primo modello di pagina e il registro delle formule.

## Verifiche eseguite

- `python -m unittest discover -s tests -q`: 34 test superati nella revisione successiva, inclusa copertura di tutte le 293 materie e decodifica delle 400 ricette.
- `node tests/test_atelier_submission.cjs`: superato; invio senza cliente e senza `crypto.randomUUID` disponibile.
- Prova live del 9 settembre: riferimento `Chanel N° 5 Eau de Parfum`, stile Ellena, sola ondata CORE. Risultato: `L'Aube Claire`, 8 materie, 100 parti, livello CORE, testa/cuore/fondo/scia completi.
- La prova live ha mostrato “Fonti non disponibili…”. Quel messaggio non prova l'assenza di una chiave: la precedente attribuzione alla configurazione non era verificata. La revisione aggiunge motivi tecnici distinti, senza esporre credenziali.

## Configurazione necessaria per attivare tutto

- `GOOGLE_API_KEY` oppure `GEMINI_API_KEY`: ricerca del riferimento con fonti.
- `REDIS_URL` o `KV_URL`: archivio permanente dei seriali in produzione.
- Chiave OpenAI e `PERFUME_IMAGES_ENABLED=1`: ritratto AI del flacone, con i limiti descritti nella documentazione dello Studio.
- Password e segreto dell'archivio proprietario: da impostare esclusivamente nelle variabili dell'ambiente, mai nel repository.

Stato del consolidamento: codice, documentazione e deploy sono allineati sul ramo `main`; il sito è utilizzabile anche quando le integrazioni opzionali non sono configurate.
