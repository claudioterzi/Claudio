# Atelier: ricerca documentata e vincoli

© Claudio Terzi · 2026-09-09

La pagina permette di indicare marca, nome e versione nel campo facoltativo Profumo di riferimento. Frasi con «ispirato a», «simile a», «come» vengono riconosciute anche nell'intenzione. Il riconoscimento automatico non copre ogni possibile formulazione: il campo esplicito è la via affidabile.

La ricerca usa Gemini 2.5 Flash con Google Search. Vengono richiesti dati da fonti ufficiali, versione/concentrazione, ambiguità e note documentate. Una risposta conta come ricerca con fonti soltanto se contiene query, supporti di grounding e URL HTTPS. Gli URL derivano dai metadata del servizio, non da link inventati nel testo. La sintesi resta generata da un modello e va controllata. I supporti e la data restano nella scheda JSON. Le fonti sono elencate accanto alla sintesi; non viene ancora realizzato un controllo indipendente di ogni affermazione.

Le istruzioni nelle fonti sono trattate come dati. I suggerimenti Google sono mostrati in iframe sandbox privo di script e same-origin. Il nome del cliente non è passato alla ricerca. Il campo riferimento viene inviato a Google; non inserirvi dati riservati.

Se mancano chiavi, tempo o grounding, il sito dichiara fonti non disponibili e propone soltanto un'interpretazione non verificata. La ricerca ha timeout 12s; l'intero compositore ha budget applicativo 48s, con timeout passati a entrambi i provider. Eventuali retry interni dell'SDK possono richiedere un ulteriore limite: non è una garanzia temporale assoluta.

Correzioni: filtro CORE/ESP/MASTER anche sul server; esclusione solventi dalla selezione; stile inoltrato da pagina/API; numerosità e distribuzione di parti specifiche per stile; duplicati fra gruppi esclusi; scia limitata a materie con ruolo indicato. Se il modello omette una materia o ripete un numero, il server conserva le scelte valide e completa soltanto i posti mancanti con una materia dello stesso profilo T/C/F (o con un fissativo della scia). Un numero fuori dall'ondata richiesta viene invece respinto: non viene sostituito in silenzio. Le spiegazioni non vengono più tagliate a metà parola.

Le dosi restano una costruzione algoritmica ispirata alle strutture del catalogo: non sono ottimizzazione olfattiva o validazione produttiva. Persistenza dell'archivio ancora dipendente dalla configurazione.

Risorse consultate e punti di partenza:
- API Google Search: https://ai.google.dev/gemini-api/docs/google-search
- GenerateContent: https://ai.google.dev/api/generate-content
- Formule dimostrative pubbliche Fraterworks: https://fraterworks.com/pages/demo-formulas (distinte dalle formule Deluxe a pagamento).
- Givaudan: https://www.givaudan.com/ (produttore; nessuna banca dati privata acquisita).
- dsm-firmenich: https://www.dsm-firmenich.com/en/home.html (il collegamento studio consultato reindirizza alla home; nessun catalogo privato scaricato).

Non sono state copiate formule a pagamento né dichiarate autentiche formule proprietarie. Le dimostrazioni e ricostruzioni pubblicate da terzi devono mantenere la loro attribuzione e classificazione.

Test locali: 29 test complessivi e regressione JavaScript dell'invio senza cliente/UUID; ricerca assente, metadata presenti, URL non sicuri esclusi, passaggio stile/riferimento, CORE, Ellena, testi completi e somme.
