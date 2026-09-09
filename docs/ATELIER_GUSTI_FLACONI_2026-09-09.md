# Atelier — gusti del cliente e flacone della ricetta

Concept e direzione: Claudio Terzi · © 2026 Claudio Terzi.
Ricerca tecnologica: 9 settembre 2026. Distinzione fra implementazione, collaudo e attivazione.

## Cosa cambia

- Campo facoltativo con fino a 5 profumi, uno per riga o separati da punto e virgola. Non si tronca silenziosamente una lista più lunga. Il campo prevale sull'estrazione automatica.
- Se il campo è vuoto, un modello estrae le citazioni dal racconto. Ogni nome richiede una citazione presente nel testo. Distingue preferito, ispirazione, evitare e semplice citazione. Dopo il primo insuccesso live, riusati gli adattatori del compositore con ripiego Gemini → Anthropic (6s per tentativo, senza retry SDK nella fase di riconoscimento). È fallibile: in caso di errore il campo separato rimane la via esplicita.
- La ricerca riceve solo i riferimenti, non il campo nome del cliente. Ambiguità e versioni mancanti vanno dichiarate, non risolte inventando. I gusti entrano nel prompt come criteri: tratti comuni, contrasti, aspetti da evitare e trasformazioni desiderate. La scheda mostra riferimenti riconosciuti e lettura dei gusti.
- Le formule scelgono esclusivamente nel catalogo dell'Organo Terzi: 293 materie, 7 supporti separati. Il riconoscimento di gusti non equivale a una prova olfattiva o a una formula originale di un marchio.
- La ricetta produce un brief visivo: impronta, forma, palette, luce e accenti canonici di testa/cuore/fondo/scia. Il generatore di immagini crea un originale, non modifica soltanto la tinta del vecchio flacone. Le forme di partenza sono sei direzioni artistiche, non 400 stampi unici certificati.
- Nome del profumo, cliente e seriale sono applicati come tipografia separata e stampabile. Il servizio immagini riceve descrittori pubblici del catalogo, non identità, storia personale, seriale o dosaggi esatti. La collocazione dell'etichetta sul rendering deve ancora essere verificata con immagini reali.
- Ogni tentativo di immagine ha ID e metadata salvati prima della chiamata; risultato con hash e consumo API quando fornito. Prezzo stimato non inventato. Nessuna scadenza automatica a 30 giorni; riaprire la scheda legge l'immagine esistente senza avviare una generazione a pagamento. Quota giornaliera e blocco atomico mantenuti.

## Tre skill trovate su Internet

Una skill è un metodo operativo per l'agente, non il modello che produce i pixel. Non sono stati installati pacchetti esterni né eseguiti script scaricati.

| Skill e fonte primaria | Utilità nel progetto | Limite |
|---|---|---|
| [OpenAI imagegen](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/imagegen/SKILL.md) | Brief di prodotto, generazione originale, modifiche mirate | Lo strumento disponibile nella chat non diventa automaticamente un'API del sito |
| [Anthropic frontend-design](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md) | Identità visiva della scheda, gerarchia, presentazione del profumo | Non genera da sola un'immagine né certifica qualità olfattiva |
| [Vercel web-design-guidelines](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md) | Controllo dell'interfaccia, accessibilità e usabilità | Non sostituisce test reali su iPhone o test delle API |

Per l'implementazione sono state applicate le skill disponibili Sites e AI Generation Persistence: architettura esistente preservata e immagini trattate come risultati da conservare, non semplici risposte temporanee. La skill imagegen distingue correttamente generazione nella chat e integrazione API autonoma del sito.

## Motore interno o servizio esterno?

Raccomandazione progettuale: **direzione creativa e archivio nel sito, produzione dei pixel tramite API gestita**. Non è una classifica di qualità misurata: mancano prove comparative con gli stessi brief.

| Sistema | Possibilità documentate | Valutazione per Terzi |
|---|---|---|
| [OpenAI Images API](https://developers.openai.com/api/docs/guides/image-generation) | Generazione ed editing; documentazione corrente con GPT Image 2.5 Sunburst e Flare, oltre a GPT Image 2 | Prima scelta d'integrazione perché il sito possiede già il percorso OpenAI. Sunburst da valutare per editing preciso, Flare per generazione rapida; nessuna migrazione di modello fatta senza prova |
| [Gemini / Nano Banana](https://ai.google.dev/gemini-api/docs/image-generation) | Generazione ed editing conversazionale, riferimenti multipli; modelli Gemini 3 con uscite ad alta risoluzione | Alternativa concreta per varianti e continuità fra immagini; richiede un adattatore immagini separato dal compositore Gemini esistente |
| [Black Forest Labs / FLUX](https://docs.bfl.ml/quick_start/introduction) | API per immagini e altre modalità, opzioni di modelli ospitati in proprio | Alternativa da valutare se si vuole controllo dell'infrastruttura; non basta aggiungere una skill e non è stato installato un modello locale |

Per un flacone nuovo conviene generare un'immagine originale. Per rispettare un vero flacone fisico, il percorso successivo è editing da fotografie proprie o autorizzate, con geometria conservata e controllo visivo. Copiare immagini di terzi dal web non garantisce né coerenza della confezione né disponibilità dei diritti d'uso. Nessun download di flaconi commerciali è stato effettuato.

Evoluzione consigliata: coda asincrona, object storage privato per i file, archivio dei metadata e controllo visivo/OCR prima di approvare immagini da stampare. Oggi l'implementazione conserva i byte nel Redis già previsto: servono persistenza, backup e assenza di eviction. Non è stato predisposto un nuovo servizio a pagamento o un nuovo storage. Il modello predefinito del sito resta `gpt-image-2`; le nuove opzioni sono documentate, non dichiarate attivate sul conto di Claudio.

## Verifiche e limiti

- 44 test Python superati, con risposte API simulate per estrazione e generazione immagini. Copertura: citazioni positive/negative, lista multipla, limiti, nomi inventati, metafore, ripiego sul secondo provider, inoltro alla composizione, HTML risultato, privacy del prompt visivo, generazione originale anziché editing, cache senza scadenza, lettura senza spesa.
- JavaScript: campo multilinea e invio POST senza cliente/UUID; 293 identità canoniche e 72 combinazioni locali; sintassi del codice immagini valida.
- Il rendering AI automatico resta condizionato a `OPENAI_API_KEY`, archivio Redis e `PERFUME_IMAGES_ENABLED=1`, oltre a disponibilità e credito del servizio. Non è stato attivato o fatturato un nuovo abbonamento. Il piano ChatGPT non configura questi parametri del sito.
- L'ultimo accesso al progetto Vercel tramite connettore era stato respinto con 403: non sono stati letti log né modificate credenziali/configurazioni. Non sono stati aggirati i blocchi. Anche la copia aggiuntiva dei sorgenti su Drive resta sospesa dopo il precedente rifiuto di autorizzazione.
- Nessun benchmark comparativo immagini, nessuna verifica di confezione fabbricabile, nessun completamento dei 400 flaconi individuali dichiarato. I codici formula e il libro preesistenti non vengono riscritti in questa modifica.
- Prima verifica online, commit `5acbe9b`: pagina con textarea pubblicata e due composizioni riuscite. **Lumière Éclatante**, lista Chanel N° 5 EDP + Dior J’adore EDP: entrambi i riferimenti presenti, 8 materie dell'organo, 100 parti, brief visivo presente. **L'Aube Irisée**, nomi nel racconto: formula riuscita, ma estrazione automatica indisponibile. Nessuno dei due casi ha fornito fonti verificate; archivio e immagini non attivi. Queste prove hanno motivato il ripiego sul secondo provider e l'etichetta esplicita «lettura ipotetica dei gusti».
- Verifica successiva al ripiego: da registrare dopo il rilascio. Non si dichiara già riuscita.
