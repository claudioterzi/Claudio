# Atelier personale — flacone, cliente e formula

Concept e direzione creativa: **Claudio Terzi**. Asset grafico originale generato per Terzi Parfums.

## Esperienza

L’Atelier chiede il nome del cliente e l’intenzione. La creazione viene inviata con POST, senza mettere il nome del cliente nell’URL. Il risultato mostra fotografia del flacone, etichetta con nome della creazione e cliente, formula, ingrandimento, download PNG, stampa dell’etichetta e download JSON della scheda.

Il flacone di base è sempre disponibile, senza chiamate API aggiuntive. Nome, cliente e numero di serie sono composti da HTML/canvas, non affidati alla resa tipografica del modello. Il PNG scaricato include l’etichetta personale. Il design è una visualizzazione di progetto, non una fotografia di un prodotto già fabbricato.

## Registro

Ogni creazione archiviata ha un numero `TP-<UUID>` univoco, data UTC, cliente, intenzione, formula completa e impronta SHA-256 del documento formula. Il numero completo privilegia l’unicità rispetto alla brevità. La chiave primaria impedisce la sovrascrittura: reinviare la stessa richiesta restituisce la formula già registrata. Una nuova richiesta crea una nuova versione con un nuovo numero.

Archivio privato: `/atelier/archivio`, con accesso tramite password e ricerca per seriale. I record non vengono salvati nel repository pubblico. In locale si usa SQLite; su Vercel il salvataggio richiede Redis. Il codice non usa un database temporaneo come archivio permanente: senza salvataggio confermato mostra **FORMULA NON ARCHIVIATA**, non assegna un seriale alla scheda e permette di scaricare la bozza.

La persistenza del servizio Redis richiede un piano/configurazione senza espulsione automatica delle formule e un backup del servizio. Il codice non sostituisce un backup. Le immagini personalizzate sono in cache per 30 giorni; la formula non ha scadenza applicativa. Scaricare il PNG per conservarlo separatamente.

## Attivazione sul server

Configurare i valori nel gestore segreti di Vercel, mai in chat o nel repository:

| Variabile | Uso |
|---|---|
| `REDIS_URL` (oppure `KV_URL`) | Archivio condiviso durevole e limite immagini |
| `PERFUME_ARCHIVE_PASSWORD` | Password riservata dell’archivio clienti |
| `PERFUME_ARCHIVE_SECRET` | Segreto casuale di almeno 32 caratteri per firmare l’accesso |
| `OPENAI_API_KEY` | Chiave del progetto OpenAI per le immagini personalizzate |
| `PERFUME_IMAGES_ENABLED=1` | Attivazione esplicita delle chiamate immagini |
| `OPENAI_IMAGE_MODEL` | Opzionale; default `gpt-image-2` |
| `PERFUME_IMAGES_DAILY_LIMIT` | Opzionale; default 10 tentativi al giorno, condivisi tra istanze |
| `PERFUME_DB_PATH` | Solo locale: percorso SQLite fuori dai file pubblici |

La configurazione effettiva dei segreti Vercel non è leggibile/modificabile dal collegamento GitHub usato in questa sessione. Non è stata creata una chiave API né provisionata un’istanza Redis. Il motore LLM delle formule mantiene la configurazione esistente.

## Immagini via API

Il pulsante “Crea il ritratto olfattivo” compare solo con formula archiviata e configurazione immagini attiva. L’endpoint riceve un token firmato della creazione, legge la formula sul server e modifica l’immagine di riferimento con una palette scelta dalla famiglia olfattiva. Non invia al servizio immagini il nome del cliente, l’intenzione personale, la formula o il seriale. L’etichetta viene applicata nel browser.

La richiesta usa Images Edit, output WebP 1024×1024 e qualità alta. [Riferimento ufficiale OpenAI](https://developers.openai.com/api/reference/resources/images/methods/edit). La geometria richiesta al modello resta soggetta a variazioni; la corrispondenza dell’etichetta con il flacone va verificata nelle prime generazioni reali. La [guida OpenAI](https://developers.openai.com/api/docs/guides/image-generation) segnala che richieste complesse possono richiedere fino a due minuti: il server attuale ha 60 secondi, quindi la chiamata ha un timeout di 45 secondi senza retry automatico. Se scade, resta visibile il flacone Atelier. Per generazioni sistematicamente più lunghe serve un worker con coda.

Il limite giornaliero e il blocco per formula sono atomici in Redis. Un timeout può consumare un tentativo e avere un costo presso il fornitore. Il codice non avvia automaticamente una nuova generazione quando si ricarica un’immagine già in cache.

## Verifica

Test locali: persistenza SQLite dopo riapertura; unicità; immutabilità; reinvio senza ricomporre; escaping del nome; nessuna falsa conferma su Vercel senza archivio; accesso riservato; token immagini non valido respinto; cache senza chiamata al fornitore; API immagini disattivata senza configurazione. Il test del fornitore immagini reale non è stato eseguito: la chiave non è disponibile nell’ambiente di lavoro.

## Asset e prompt

`public/images/terzi-atelier.webp`, derivato dal PNG originale creato con lo strumento integrato ImageGen, non tramite la chiave API del sito.

Prompt: fotografia di prodotto quadrata di un flacone scultoreo in cristallo ambrato fumé, tappo nero e collare in ottone, fondo antracite, luce dorata di taglio e riflesso sottile; bottiglia intera e centrata; etichetta “TERZI PARFUMS” e “ATELIER”; nessun altro marchio o nome inventato.
