# Atelier: ricerca documentata e vincoli

© Claudio Terzi · 2026-09-09

La pagina permette di indicare fino a 5 profumi amati nel campo facoltativo ispirazioni, uno per riga o separati da punto e virgola (marca e versione se note). Il campo esplicito ha priorità. Quando è vuoto, un'estrazione semantica Gemini identifica i nomi nel racconto, con citazione testuale verificata e rapporto preferito/ispirazione/evitare/citato. I nomi devono comparire letteralmente nella citazione e nel testo; marche e versioni non vengono completate arbitrariamente. L'estrattore non usa strumenti web. Timeout, JSON non valido e nomi inventati non bloccano la composizione: si dichiara riconoscimento non disponibile e si invita a usare il campo esplicito. Nessuna frase personale catturata con regex diventa una query di ripiego.

La ricerca usa Gemini 2.5 Flash con Google Search. Vengono richiesti dati da fonti ufficiali, versione/concentrazione, ambiguità e note documentate. Una risposta conta come ricerca con fonti soltanto se contiene query, supporti di grounding e URL HTTPS. Gli URL derivano dai metadata del servizio, non da link inventati nel testo. La sintesi resta generata da un modello e va controllata. I supporti e la data restano nella scheda JSON. Le fonti sono elencate accanto alla sintesi; non viene ancora realizzato un controllo indipendente di ogni affermazione.

Le istruzioni nelle fonti sono trattate come dati. I suggerimenti Google sono mostrati in iframe sandbox privo di script e same-origin. Il campo nome del cliente non è passato alla ricerca. Il racconto viene letto dal modello per riconoscere le citazioni, ma alla fase web vengono inoltrati i nomi estratti o le righe del campo esplicito: non inserire dati riservati in quest'ultimo. Ogni riferimento deve essere trattato separatamente, incluse ambiguità e informazioni mancanti. La presenza di grounding nel dossier non garantisce che ogni profumo o ogni affermazione sia documentato: serve ancora verifica puntuale.

Se mancano chiavi, tempo o grounding, il sito dichiara fonti non disponibili e propone soltanto un'interpretazione non verificata. Il JSON registra un motivo distinto (configurazione assente, timeout, stato HTTP del provider o grounding mancante), senza credenziali o corpi di errore. Riconoscimento: timeout 6s, saltato se il campo esplicito è compilato. Ricerca: 12s. Budget applicativo condiviso: 48s; composizione: massimo 26s per chiamata. Gli adattatori dei fornitori sono rimasti alla versione ripristinata dopo l'insuccesso live della revisione precedente; i retry interni dell'SDK Anthropic restano un limite. Il budget non costituisce una garanzia temporale assoluta del runtime.

Correzioni: catalogo completo predefinito (293 materie), filtro CORE/ESP/MASTER scelto esplicitamente dall'utente e applicato anche nella modalità locale; solventi/supporti elencati separatamente; stile inoltrato da pagina/API; struttura JSON richiesta nel prompt e validata sul server per numero esatto di materie, duplicati fra gruppi e ruolo scia. Una proposta non conforme torna al modello per una riscrittura completa, con al massimo una correzione per provider entro il budget temporale. Nessuna materia è aggiunta automaticamente. Le spiegazioni non vengono tagliate a metà parola.

Le dosi restano una costruzione algoritmica ispirata alle strutture del catalogo: non sono ottimizzazione olfattiva o validazione produttiva. Persistenza dell'archivio ancora dipendente dalla configurazione.

Risorse consultate e punti di partenza:
- API Google Search: https://ai.google.dev/gemini-api/docs/google-search
- GenerateContent: https://ai.google.dev/api/generate-content
- Formule dimostrative pubbliche Fraterworks: https://fraterworks.com/pages/demo-formulas (distinte dalle formule Deluxe a pagamento).
- Givaudan: https://www.givaudan.com/ (produttore; nessuna banca dati privata acquisita).
- dsm-firmenich: https://www.dsm-firmenich.com/en/home.html (il collegamento studio consultato reindirizza alla home; nessun catalogo privato scaricato).

Non sono state copiate formule a pagamento né dichiarate autentiche formule proprietarie. Le dimostrazioni e ricostruzioni pubblicate da terzi devono mantenere la loro attribuzione e classificazione.

Test locali dopo questa estensione: 44 test complessivi, inclusi i nuovi casi di estrazione, ripiego sul secondo provider, preferenze multiple e immagini simulate. Il riconoscimento riusa gli adattatori del compositore (Gemini → Anthropic), fino a 6s per tentativo, massimo due; retry SDK disattivati per questa fase. JavaScript: trasmissione delle righe senza cliente/UUID e 72 combinazioni locali. Le prove con risposte simulate non dimostrano disponibilità dei fornitori in produzione. Prima prova con lista esplicita riuscita nella composizione, ricerca con fonti ancora indisponibile; vedere `ATELIER_GUSTI_FLACONI_2026-09-09.md`.
