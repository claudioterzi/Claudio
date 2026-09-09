# Competenze per Terzi Parfums e novità Astra

Ricerca online del 9 settembre 2026. Fonti primarie: repository degli autori e documentazione ufficiale OpenAI. Selezione riferita al sito esistente Flask/Python e JavaScript; nessuna migrazione di framework implicita. Consultare una skill aggiorna il metodo di lavoro e i documenti del progetto, non riaddestra i pesi del modello.

## Cataloghi verificati

- [OpenAI Plugins](https://github.com/openai/plugins): nuovo riferimento per plugin e skill. [OpenAI Skills](https://github.com/openai/skills) si dichiara deprecato e rimanda qui.
- [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills): linee guida per interfacce, prestazioni, gestione Vercel.
- [Anthropic Skills](https://github.com/anthropics/skills): indicazioni di direzione visiva e altri flussi creativi; compatibilità, dipendenze e licenza vanno valutate per singola skill.

I file SKILL.md di frontend-testing-debugging, web-design-guidelines, produce e ai-generation-persistence sono stati letti integralmente. Consultati anche frontend-design, le descrizioni e istruzioni iniziali di supabase-postgres-best-practices, stripe-best-practices e security-diff-scan. Le altre voci sotto sono selezionate dal catalogo e dalle skill Vercel già disponibili; non si dichiara un audit integrale di ogni pacchetto né una ricerca esaustiva dell'intero GitHub.

## Selezione applicabile

| Esigenza | Skill / fonte | Applicazione al progetto e stato |
| --- | --- | --- |
| Leggibilità e interazione su telefono | [web-design-guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) | Applicati pulsanti di almeno 44 px, focus visibile, stato asincrono, nomi accessibili e contenimento dello scorrimento nelle nuove anteprime. |
| Test delle funzioni reali | [frontend-testing-debugging](https://github.com/openai/plugins/tree/main/plugins/build-web-apps/skills/frontend-testing-debugging) | Percorso browser → clic → stato osservato; test del caricamento foto, varianti, dediche ed esportazioni. Usare il browser già disponibile. |
| Identità visiva | [frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | Direzione specifica Terzi: vetro, metallo, luce e tipografia; evitare una veste generica ripetuta. |
| Campagne e fotografie prodotto | [produce](https://github.com/openai/plugins/tree/main/plugins/creative-production/skills/produce) | Candidata per esplorare fotografie e varianti editoriali. Il relativo board non è installato: nessuna attivazione dichiarata. |
| Conservazione delle creazioni | [ai-generation-persistence](https://github.com/openai/plugins/tree/main/plugins/vercel/skills/ai-generation-persistence) | ID prima della generazione, stato, risultato e costi persistenti. Priorità futura: archivio server effettivo. Il sito segnala ancora correttamente le bozze non archiviate. |
| Pubblicazione e ripristino | [deployments-cicd](https://github.com/openai/plugins/tree/main/plugins/vercel/skills/deployments-cicd) | Commit conservativi, stato Vercel e prova del dominio pubblico. Disponibile nel plugin Vercel. |
| Diagnosi errori | [investigation-mode](https://github.com/openai/plugins/tree/main/plugins/vercel/skills/investigation-mode) | Distinguere upload, analisi, composizione e stampa. Già usata nell'indagine sulla fotografia. |
| Controllo completo del risultato | [verification](https://github.com/openai/plugins/tree/main/plugins/vercel/skills/verification) | Verificare formule, UI, risposta e dati esportati, senza dedurre successo dal solo deploy. Disponibile. |
| Archivi e immagini durevoli | [vercel-storage](https://github.com/openai/plugins/tree/main/plugins/vercel/skills/vercel-storage) | Valutare database e Blob per formule e file; richiede infrastruttura effettivamente configurata. |
| Utente, amministratore e guest | [auth](https://github.com/openai/plugins/tree/main/plugins/vercel/skills/auth) | Separare identità, ruolo e quote lato server. Una parola nel JavaScript non costituisce protezione degli archivi. |
| Database relazionale | [supabase-postgres-best-practices](https://github.com/openai/plugins/tree/main/plugins/build-web-apps/skills/supabase-best-practices) | Candidata se si sceglie Postgres: schema, connessioni, indici e isolamento dei dati. Nessuna migrazione avviata. |
| Revisione delle modifiche sensibili | [security-diff-scan](https://github.com/openai/plugins/tree/main/plugins/codex-security/skills/security-diff-scan) | Candidata prima di attivare accessi, pagamenti o archivi. Plugin Codex Security non installato; nessuna scansione di quel servizio dichiarata. |
| Ripresa di attività lunghe | [workflow](https://github.com/openai/plugins/tree/main/plugins/vercel/skills/workflow) | Candidato per stati pending/running/complete/error e ripartenza senza doppia generazione; da adattare al backend Python. |
| Pagamento singolo | [stripe-best-practices](https://github.com/openai/plugins/tree/main/plugins/build-web-apps/skills/stripe-best-practices) | Candidata per un checkout successivo; priorità rinviata da Claudio. Controllare le API Stripe correnti prima di implementare. |
| Modelli e documentazione OpenAI | OpenAI Docs, già disponibile | Verifica modello, strumenti supportati e accesso prima di modificare il motore del sito. |

React, Next.js e shadcn sono risorse utili per altri progetti ma non giustificano riscrivere questo sito Flask. Nessuna installazione indiscriminata, nuovo segreto o servizio a pagamento avviato dalla ricerca.

## Astra: novità documentate e uso concreto

La [scheda GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra) documenta ragionamento, programmazione, ricerca e uso del computer, input testuale/visivo, Structured Outputs e strumenti nella Responses API. Il modello può coordinare la generazione di immagini attraverso uno strumento; questo non equivale a un endpoint immagini già configurato nel sito.

La [guida Astra](https://developers.openai.com/api/docs/guides/latest-model) descrive tre novità pertinenti: chiamate a strumenti asincrone, nuove istruzioni durante il lavoro via WebSocket, variazione del livello di ragionamento conservando la cache. Applicazione proposta: Raffaello raccoglie il brief, ricerca i riferimenti e verifica una formula strutturata; il backend conserva gli stati e permette una ripresa. Queste funzioni API non sono ancora implementate nel sito. La ricerca non cambia il provider fotografico già funzionante.

La [guida modelli di ChatGPT Work](https://learn.chatgpt.com/docs/models) distingue scelta del modello e intensità del ragionamento: aumentare l'intensità richiede più tempo e risorse. Utilizzo nel progetto: approfondimento per diagnosi e revisione, controlli deterministici per dosi e catalogo. Il modello non può certificare la qualità olfattiva o la sicurezza produttiva con una foto.

Il [riepilogo delle novità](https://learn.chatgpt.com/docs/whats-new) del 31 agosto–4 settembre presenta Astra per flussi complessi tra codice, applicazioni e ricerca. Il [changelog](https://learn.chatgpt.com/docs/changelog) dell'8 settembre, ChatGPT iOS 1.2026.244, riporta miglioramenti alle riconnessioni e agli stati bloccati, e voce coerente con modello e ragionamento selezionati. Non è stata verificata la versione installata sull'iPhone di Claudio; questi aggiornamenti dell'app sono distinti dall'errore del sito.

## Protocollo operativo consolidato

1. Riprendere da MEMORIA_PROGETTO.md e commit corrente; mantenere la richiesta iniziale quando arrivano nuovi dettagli.
2. Riprodurre l'errore e distinguere fatti osservati, interpretazioni creative e ipotesi.
3. Conservare la formula e la sua firma; nominativi e dedica appartengono alla presentazione.
4. Applicare controlli mirati, poi prove native nel browser, quindi registrare l'esito e le limitazioni effettive.
5. Le interruzioni tecniche non dimostrano interferenze esterne. Ripartire dai risultati salvati senza reiterare chiamate costose già riuscite.

Priorità successive: archivio persistente con accessi reali; Raffaello con conversazione e stati riprendibili; fotografie AI originali con quote e conservazione; checkout quando richiesto. Le skill sono strumenti per realizzarle, non attivazioni automatiche.
