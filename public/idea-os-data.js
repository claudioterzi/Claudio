/* IDEA OS — safe portfolio projection generated from the canonical Master Map.
   Source of truth remains Google Drive. Keep confidential/IP-sensitive details in canonical docs, not in this static projection. */
window.IDEA_OS_PORTFOLIO = {
  meta: {
    title: "SOCIETÀ — IDEA OS · Master Map delle idee, servizi e opportunità",
    sourceId: "1XOe_ph_V6LpVsQB1ABz2c47ta4SD_ssW6oWvjlKfyfE",
    sourceUrl: "https://docs.google.com/document/d/1XOe_ph_V6LpVsQB1ABz2c47ta4SD_ssW6oWvjlKfyfE/edit",
    snapshot: "2026-09-17",
    note: "Proiezione operativa del Master IDEA OS. I dettagli sensibili restano nei documenti canonici protetti."
  },
  ideas: [
    {
      id:"IDEA-001", title:"Audit de Cascade de Défaillance & Continuité Client", maturity:"M2–M3", status:"PORTAFOGLIO · DA PILOTARE", engine:"HUMAN GAP LAB / Communication & Conseil", horizon:"H0 → H1/H2", secure:false,
      origin:"Caso Leroy Merlin Saint-Ouen.",
      problem:"Errori, ownership gap e passaggi mal coordinati possono propagarsi lungo il percorso cliente senza un responsabile end-to-end.",
      thesis:"Ricostruire errore → propagazione → ownership gap → redesign → KPI rende la cascata osservabile e testabile.",
      buyer:"Da validare; plausibili funzioni service operations, customer experience e direzioni retail.",
      evidence:"Case study e metodologia già strutturati; pilot e baseline reali ancora necessari.",
      currentTech:"H0: audit, mappa di cascata, responsabilità, redesign e misurazione sono realizzabili oggi.",
      capability:"H1/H2 solo quando le correzioni richiedono integrazioni o sistemi non disponibili al cliente.",
      constraints:"EVIDENCE_UNCERTAINTY · ORGANIZATIONAL_OWNERSHIP · INTEGRATION", assumptions:"Il pattern osservato nel caso originario deve essere verificato su casi indipendenti.",
      nextTest:"Applicare il metodo a un caso reale limitato, definendo baseline prima dell'intervento e KPI di propagazione/recovery.",
      baseline:"Tempo di risoluzione, numero di handoff, errori downstream, contatti ripetuti, rework.",
      kpi:"Riduzione handoff inutili; tempo a owner; tempo a recovery; errori downstream intercettati.",
      falsifier:"Se la mappa non migliora diagnosi o recovery rispetto al processo ordinario, non estendere il metodo.",
      risk:"Basso/medio. Evitare affermazioni commerciali o di risparmio senza pilot.",
      relations:"RELATED a IDEA-002 e potenziale case study per IDEA-005.", dossier:null
    },
    {
      id:"IDEA-002", title:"Service Recovery Orchestrator / Failure Cascade Map", maturity:"M2", status:"PORTAFOGLIO · DA TESTARE", engine:"HUMAN GAP LAB", horizon:"H0/H1", secure:false,
      origin:"Estensione del lavoro sulla continuità cliente e sulle cascade di errore.",
      problem:"Un caso può attraversare più reparti senza un owner che misuri anche le conseguenze downstream.",
      thesis:"Un owner umano+IA segue il caso end-to-end e mantiene memoria strutturata di responsabilità, eventi e recovery.",
      buyer:"Da validare; service operations, customer care, retail operations.", evidence:"Concept M2; nessun pilot misurato registrato nel Master.",
      currentTech:"Case ledger, routing, timeline, escalation e dashboard sono prototipabili con stack corrente.", capability:"H1 per integrazioni live con CRM/ticketing e policy aziendali.",
      constraints:"ORGANIZATIONAL_OWNERSHIP · POLICY_AUTHORITY · INTEGRATION", assumptions:"Un singolo owner orchestratore deve ridurre perdita di contesto senza creare ulteriore burocrazia.",
      nextTest:"Simulare 10 casi con e senza orchestratore, misurando perdita di contesto, duplicazioni e tempo alla risoluzione.", baseline:"Workflow attuale senza owner end-to-end.",
      kpi:"Context retention; handoff; duplicate actions; recovery time; escalation corretta.", falsifier:"Se l'orchestratore aggiunge passaggi senza ridurre errori o tempo di recovery, ridurre o fermare il concept.",
      risk:"Medio per integrazione e governance; nessuna automazione decisionale irreversibile.", relations:"RELATED a IDEA-001; IDEA-009 aggiunge memoria persistente del prodotto nel post-vendita.", dossier:null
    },
    {
      id:"IDEA-003", title:"Retail Design Workflow Audit + AI Design Copilot", maturity:"M2", status:"ACTIVE · PROJECT CREATED", engine:"HUMAN GAP LAB / Opportunity Foundry", horizon:"H0/H1 → H2", secure:false,
      origin:"Progettazione dressing in negozio: interruzioni, ripresa difficile e software che non protegge le dipendenze.",
      problem:"I configuratori possono perdere vincoli, dipendenze e contesto durante interruzioni e handoff.",
      thesis:"Il valore da testare non è un semplice configuratore IA, ma INTERRUPT-RESILIENT WORKFLOW + CONSTRAINT MEMORY + DEPENDENCY PROTECTION + HUMAN HANDOFF.",
      buyer:"IPOTESI: retailer arredamento, kitchen/wardrobe design, reti vendita con configurazione complessa.",
      evidence:"Stato dell'arte aggiornato: planner retail, AI design e Visual CPQ esistono già; la distinzione proposta resta da validare sperimentalmente.",
      currentTech:"H0/H1: intervista guidata, Constraint Ledger, dependency graph, warning, resume e pre-progetto.",
      capability:"H1: catalogo/CPQ live. H2: copilot multimodale che aggiorna automaticamente il Ledger.",
      constraints:"INTERFACE_PRODUCT · INTEGRATION · EVIDENCE_UNCERTAINTY", assumptions:"La memoria dei vincoli deve migliorare il risultato più di quanto aumenti la frizione.",
      nextTest:"A/B checklist ordinaria vs Constraint Ledger su un progetto dressing con interruzioni controllate.", baseline:"Checklist/processo ordinario sullo stesso scenario.",
      kpi:"Constraint retention; incompatibilità intercettate; resume time; rework.", falsifier:"Se il Ledger non migliora i risultati o aggiunge più frizione del beneficio, non espandere verso AI copilot/enterprise.",
      risk:"Medio; originalità e vantaggi commerciali non dichiarati senza prove.", relations:"RELATED a IDEA-010 e IDEA-012.",
      dossier:{title:"PROJECT IDEA-003 — Retail Design Workflow Audit + AI Design Copilot",id:"1_qvXIeXXU-sdqEuLJQUQI7CWS1sEWbC4ulOAQdJbgDU",url:"https://docs.google.com/document/d/1_qvXIeXXU-sdqEuLJQUQI7CWS1sEWbC4ulOAQdJbgDU/edit"}
    },
    {
      id:"IDEA-004", title:"Interactive AI Voice Reports", maturity:"M3", status:"ACTIVE · PROJECT CREATED", engine:"Communication & Conseil", horizon:"H0 → H1/H2", secure:false,
      origin:"Evoluzione dei report statici verso documenti web narrabili e presentabili.",
      problem:"PDF/slides separano lettura, presentazione e narrazione; il contenuto non si adatta facilmente al modo in cui viene fruito.",
      thesis:"Un unico report web può offrire READ / LISTEN / PRESENT, con voce naturale e scorrimento controllato.",
      buyer:"Da validare; consulenza, audit, presentazioni executive, report clienti.", evidence:"M3: prototipo HTML già esistente. Va recuperato e confrontato con baseline PDF/slides.",
      currentTech:"H0: report web READ/LISTEN/PRESENT.", capability:"H1: sincronizzazione/personalizzazione. H2: presentazione adattiva in tempo reale.",
      constraints:"UX_RELIABILITY · AUDIO_QUALITY · ACCESSIBILITY", assumptions:"La modalità multimodale deve aumentare comprensione/uso senza rendere il report più fragile.",
      nextTest:"A/B prototipo HTML vs PDF/slides sullo stesso contenuto.", baseline:"PDF o slide tradizionali con identico contenuto.",
      kpi:"Completamento; comprensione; tempo di navigazione; affidabilità voce; preferenza utente; errori di presentazione.", falsifier:"Se il formato non migliora uso/comprensione o risulta meno affidabile della baseline, non trasformarlo in offerta ripetibile.",
      risk:"Basso/medio; verificare privacy e autorizzazioni quando si usano voci o contenuti cliente.", relations:"Può diventare formato nativo dei dossier IDEA OS e delle Client Intelligence Rooms.",
      dossier:{title:"PROJECT IDEA-004 — Interactive AI Voice Reports",id:"176AKepXJhraYvDkSqSkRsPA-h4vgk8W4Ttk_Qx_lfw0",url:"https://docs.google.com/document/d/176AKepXJhraYvDkSqSkRsPA-h4vgk8W4Ttk_Qx_lfw0/edit"}
    },
    {
      id:"IDEA-005", title:"Client Intelligence Room", maturity:"M1–M2", status:"PORTAFOGLIO · DA STRUTTURARE", engine:"Piattaforma società", horizon:"H0/H1", secure:false,
      origin:"Architettura della futura società.", problem:"Report, problemi, opportunità, pilot e prove di un cliente rischiano di essere dispersi fra documenti e strumenti.",
      thesis:"Una stanza privata modulare riunisce Executive Overview, Issues, Opportunities, Solutions, Reports, Failure Maps, Surveys, Verification Tools, Pilots, KPI, Media, Evidence Room e Roadmap.",
      buyer:"Aziende clienti della società; buyer specifico da validare per settore.", evidence:"Architettura concettuale; nessun pilot cliente registrato.",
      currentTech:"H0/H1: portale e modularità sono costruibili con stack corrente.", capability:"Il rischio principale è integrazione/governance, non impossibilità tecnica.",
      constraints:"ACCESS_CONTROL · DATA_GOVERNANCE · INTEGRATION", assumptions:"Il valore dipende dalla qualità dei moduli e non dalla semplice concentrazione di link.",
      nextTest:"Prototipo con un solo cliente/caso e 4 moduli essenziali; misurare reperibilità e decisioni supportate.", baseline:"Materiali separati in documenti/chat/cartelle.",
      kpi:"Tempo per trovare evidenza; duplicati; stato decisioni; completezza handoff; utilizzo moduli.", falsifier:"Se la stanza diventa un altro contenitore da mantenere senza ridurre dispersione, ridisegnare il perimetro.",
      risk:"Medio/alto per access control e confidenzialità; richiede autenticazione server-side prima di dati cliente reali.", relations:"Contenitore potenziale per IDEA-001, 003, 004, 013 e futuri dossier.", dossier:null
    },
    {
      id:"IDEA-006", title:"Opportunity Foundry", maturity:"M1–M2", status:"PORTAFOGLIO · DA STRUTTURARE", engine:"Piattaforma società", horizon:"H0/H1", secure:false,
      origin:"Architettura della futura società.", problem:"La consulenza tradizionale spesso aspetta una richiesta esplicita invece di sviluppare opportunità verificabili in anticipo.",
      thesis:"Individuare un'opportunità specifica per un'azienda e preparare preview + logica + test prima di qualunque contatto.",
      buyer:"Direzioni innovazione, strategia, prodotto, CX; da validare caso per caso.", evidence:"Metodo concettuale; valore commerciale non ancora provato.",
      currentTech:"Ricerca, scenario, mockup, test design e dossier possono essere prodotti oggi.", capability:"H1 per integrazioni/dati aziendali non pubblici.",
      constraints:"EVIDENCE_UNCERTAINTY · CONFIDENTIALITY · BUYER_FIT", assumptions:"Una preview sufficientemente specifica può ridurre ambiguità e aumentare qualità della conversazione con un potenziale cliente.",
      nextTest:"Su 3 aziende, sviluppare internamente una opportunity card senza contatto esterno e verificare qualità, specificità e falsificabilità.", baseline:"Idea generica non verificata.",
      kpi:"Assunzioni eliminate; specificità; testabilità; tempo a preview; numero di duplicati/scoperte esistenti.", falsifier:"Se la maggior parte delle opportunità si riduce a idee già note o non testabili, restringere il metodo.",
      risk:"Non contattare aziende né divulgare concept senza decisione umana/IP triage.", relations:"Motore generativo del portafoglio; usa IDEA-012 per i capability horizon.", dossier:null
    },
    {
      id:"IDEA-007", title:"GENIUS VAULT / Human Ideas × AI Development × Corporate Licensing", maturity:"M1", status:"SECURE PROJECT CARD REQUIRED", engine:"Piattaforma società", horizon:"H1/H2", secure:true,
      origin:"Architettura della futura società.", problem:"Idee di creatori esterni richiedono sviluppo e matching senza perdere provenienza, controllo o confidenzialità.",
      thesis:"Ambiente protetto per provenance, sviluppo assistito, triage e possibili percorsi di licenza/pilot/cessione/revenue share, con decisioni umane sui passaggi sensibili.",
      buyer:"Creatori e aziende potenzialmente interessate; modello contrattuale da progettare prima dell'uso reale.", evidence:"Concept M1. Nessuna promessa di protezione, human-blindness o licensing è considerata verificata.",
      currentTech:"Deposito, provenance, cifratura e workflow sono costruibili in parte oggi.", capability:"H1/H2 per garanzie forti end-to-end, confidential processing e governance multi-parte.",
      constraints:"CONFIDENTIALITY · IP · ACCESS_CONTROL · CONTRACTS", assumptions:"La fiducia dipende da architettura e governance verificabili, non dal solo posizionamento del servizio.",
      nextTest:"Prima della raccolta di idee reali: threat model, access matrix, provenance model, disclosure policy e simulazione con dati sintetici.", baseline:"Nessuna idea di terzi caricata.",
      kpi:"Accessi autorizzati; tracciabilità provenienza; leakage test; separazione tenant; auditability.", falsifier:"Se non è possibile garantire isolamento e provenance sufficienti, non accettare idee di terzi.",
      risk:"ALTO. Nessun dettaglio rivelatore di idee di terzi va pubblicato qui. Registrare solo metadata sicuri.", relations:"Usa Verification Layer e Human Gate; nessun dossier ordinario automatico per materiale confidenziale.", dossier:null
    },
    {
      id:"IDEA-008", title:"Concept igiene per quick-service restaurant", maturity:"M0–M1", status:"PORTAFOGLIO · DA VERIFICARE", engine:"Opportunity Foundry", horizon:"H0", secure:false,
      origin:"Idea Claudio: supporto/tovaglietta igienizzante consegnato insieme al menu per rinforzare il gesto di mangiare con le mani pulite.",
      problem:"Nel QSR il comportamento di igiene delle mani prima del consumo può essere discontinuo.", thesis:"Un supporto integrato nel momento del pasto potrebbe rendere il gesto più evidente e facile, ma utilità e operatività non sono ancora dimostrate.",
      buyer:"IPOTESI: catene QSR; da validare.", evidence:"NON VERIFICATO: esistenza soluzioni analoghe, sicurezza/materiale, comportamento cliente, costo per unità e fit operativo.",
      currentTech:"H0: nessuna tecnologia mancante è il blocco principale.", capability:"Non rilevante finché utilità, sicurezza, operatività e precedenti non sono verificati.",
      constraints:"SAFETY · OPERATIONS · UNIT_ECONOMICS · IP_PRIOR_ART", assumptions:"Il supporto deve cambiare comportamento senza creare rifiuti/frizione/costi incompatibili.",
      nextTest:"Ricerca precedenti + mockup non alimentare + osservazione comportamento in scenario simulato; nessun claim sanitario.", baseline:"Esperienza QSR ordinaria senza supporto.",
      kpi:"Comprensione gesto; uso spontaneo; frizione; rifiuto; costo indicativo; impatto operativo.", falsifier:"Se non cambia comportamento o crea più frizione/costo del beneficio, archiviare o riprogettare.",
      risk:"Non dichiarare originalità, proprietà brevettuale o beneficio sanitario senza prove.", relations:"Esempio Opportunity Foundry; collegabile a IDEA-012 solo se emergono capability gap reali.", dossier:null
    },
    {
      id:"IDEA-009", title:"Mirror → Fit Passport → Home Wardrobe OS", maturity:"M2", status:"ACTIVE · PROJECT CREATED", engine:"Opportunity Foundry / Human Gap Lab", horizon:"H0/H1 → H2", secure:false,
      origin:"AI Retail Conversion Mirror consolidato con Fit Passport, inventario domestico, lifecycle e memoria prodotto.",
      problem:"Prova retail, vestibilità, acquisto, possesso domestico, cura, viaggio, resale e qualità post-vendita vivono in sistemi scollegati.",
      thesis:"L'asset da testare è la continuità RETAIL → FIT → ACQUISTO → CASA → LIFECYCLE → VIAGGIO/CIRCOLARITÀ, basata su Fit Passport + Item ID + Wardrobe Ledger + Closet Twin.",
      buyer:"IPOTESI: brand moda, retailer, produttori di mobili/moduli smart e piattaforme post-vendita/quality.", evidence:"Stato dell'arte verificato: virtual try-on, AR mirrors, RFID fitting room, digital wardrobe, DPP/GS1 e RFID retail esistono; la continuità proposta resta da validare.",
      currentTech:"H0/H1: try-on, catalog/stock sync, digital wardrobe, QR/NFC/RFID, event inventory, closet mapping, outfit/travel planning. Smart Wardrobe RFID riclassificato H1.",
      capability:"H2: Fit Truth Layer cross-brand, garment digital twin, auto-reconciliation robusta, native smart furniture, federated quality intelligence privacy-preserving.",
      constraints:"INTERFACE_PRODUCT · POLICY_AUTHORITY · EVIDENCE_UNCERTAINTY · PRIVACY", assumptions:"L'identità persistente del capo deve generare utilità reale senza esporre dati personali o creare manutenzione eccessiva.",
      nextTest:"Home Pilot 30 capi × 30 giorni con tagging/inventario/spazio/uso/laundry/prestito; in parallelo mockup Retail Mirror su 20–30 SKU. Sub-test RFID: un vano, 3 modalità identità, lettura event-based.",
      baseline:"Armadio e acquisto senza ledger persistente; inventario manuale o assente.", kpi:"Precisione stock; false positive/missing; latenza; azioni manuali; riuso Product Master; mapping Product-ID; quality signal precision.",
      falsifier:"Zona RFID non confinabile, mapping non accessibile, frizione manuale eccessiva, fit non affidabile o necessità di esporre dati personali non necessari.",
      risk:"Medio. Separare rigorosamente PRODUCT MASTER / BATCH / ITEM INSTANCE / LIFE EVENTS e dati cliente privati. Nessun contatto partner autorizzato automaticamente.",
      relations:"RELATED a IDEA-002, IDEA-010, IDEA-012. Sub-moduli: Product Life Network, Defect Signal Loop, Garment Memory Network, Product Life Graph, Smart Wardrobe RFID.",
      updates:[
        "Product Life Network / Defect Signal Loop: aggregazione pseudonimizzata di difetti, resi e riparazioni; nessun recall automatico.",
        "Garment Memory Network / Product Life Graph: PRODUCT_MASTER, VARIANT, BATCH, ITEM_INSTANCE, LIFE_EVENT, DEFECT_EVENT, QUALITY_SIGNAL e DPP_RESOURCE.",
        "RFID Partner / Home Reader Path: componenti RAIN/UHF esistono; capability gap domestico riclassificato H1, non tecnologia futura generica."
      ],
      dossier:{title:"PROJECT IDEA-009 — MIRROR → FIT PASSPORT → HOME WARDROBE OS",id:"1wiLiZ-GEZy80Snsjgs1p8gIQ2GR_s4uRDZLom3GSHKQ",url:"https://docs.google.com/document/d/1wiLiZ-GEZy80Snsjgs1p8gIQ2GR_s4uRDZLom3GSHKQ/edit"}
    },
    {
      id:"IDEA-010", title:"Reality / Constraint Checker", maturity:"M2", status:"PORTAFOGLIO · DA TESTARE", engine:"R³ METHOD LAB", horizon:"H0", secure:false,
      origin:"Metodo di risoluzione vincoli.", problem:"Si tende a riparare o sostituire prima di verificare se il problema può essere risolto riconfigurando elementi e vincoli.",
      thesis:"Prima SCAMBIARE / SPOSTARE / RUOTARE / RIUTILIZZARE / RICONFIGURARE; poi ADATTARE; solo dopo RIPARARE o SOSTITUIRE. Vincoli: IMMUTABILE / INTERCAMBIABILE / DA VERIFICARE.",
      buyer:"Uso interno immediato; possibile metodo consulenziale solo dopo casi verificati.", evidence:"Principio operativo M2; performance comparativa non ancora misurata.",
      currentTech:"H0: metodo applicabile oggi.", capability:"Patch Capability Horizon: classificare il vincolo prima di ottimizzare e aprire H1–H3 solo quando necessario.",
      constraints:"CONSTRAINT_CLASSIFICATION · EVIDENCE_UNCERTAINTY", assumptions:"Una sequenza di riconfigurazione riduce interventi inutili rispetto alla soluzione immediata.",
      nextTest:"Applicare a 10 problemi fisici/digitali reali e confrontare con la prima soluzione proposta senza checker.", baseline:"Soluzione immediata non strutturata.",
      kpi:"Interventi evitati; costo/tempo evitato da verificare; vincoli correttamente classificati; rework.", falsifier:"Se non cambia qualità o costo decisionale, ridurre il metodo a checklist minima.",
      risk:"Basso; non trasformare stime di risparmio in claim senza misurazione.", relations:"RELATED a IDEA-012; applicato in IDEA-003 e IDEA-013.", dossier:null
    },
    {
      id:"IDEA-011", title:"Personal Operations Orchestrator", maturity:"M3", status:"PILOT INTERNO ATTIVO", engine:"HUMAN GAP LAB", horizon:"H0/H1", secure:false,
      origin:"Esigenza di trasformare input trasversali in una sequenza operativa semplice.", problem:"Task, idee e follow-up possono moltiplicarsi fino a perdere owner, priorità e prossimo passo.",
      thesis:"Intake trasversale → deduplicazione → owner → un solo prossimo passo → massimo 3 priorità attive.", buyer:"Uso interno chiaro; eventuale buyer esterno non validato.",
      evidence:"M3: pilot interno attivo.", currentTech:"H0/H1: orchestration, dedup e task state sono testabili oggi.", capability:"Le funzioni future restano fuori dalla top-3 fino a prova.",
      constraints:"ATTENTION_CAPACITY · STATE_CONSISTENCY · INTEGRATION", assumptions:"Limitare WIP e rendere esplicito il prossimo passo riduce perdita e switching.",
      nextTest:"Continuare pilot interno registrando per 2 settimane intake, dedup, priorità, completion e task riaperti.", baseline:"Gestione non orchestrata / più liste parallele.",
      kpi:"WIP attivo; task duplicati; completion; reopen; tempo per trovare il prossimo passo.", falsifier:"Se la regola top-3 sposta soltanto il backlog senza aumentare completion o chiarezza, rivedere il modello.",
      risk:"Medio per integrazioni con dati personali; mantenere separazione fra suggerimento e autorità esecutiva.", relations:"Supporta operativamente tutto IDEA OS.", dossier:null
    },
    {
      id:"IDEA-012", title:"Capability Horizon / Missing-Technology Design", maturity:"M1–M2", status:"ACTIVE", engine:"R³ METHOD LAB / Opportunity Foundry", horizon:"H0 come metodo · output H0–H3", secure:false,
      origin:"Conversazione Claudio × Raffaello del 17/09/2026; autore: Claudio Terzi.", problem:"I sistemi di analisi rischiano di auto-limitarsi alle tecnologie già disponibili e ottimizzare soltanto nel perimetro corrente.",
      thesis:"Separare CURRENT-TECH PATH da CAPABILITY-HORIZON PATH. Una capacità mancante resta valida solo se descrivibile in requisiti, dipendenze, rischi, prototipo e condizioni di praticabilità.",
      buyer:"IPOTESI: direzioni innovazione, strategia, R&D, design di servizi/prodotti.", evidence:"Principio formulato; stato dell'arte/originalità NON VERIFICATO. Nessuna prova esterna ancora raccolta per il metodo come tale.",
      currentTech:"H0 come metodo di ragionamento e classificazione.", capability:"I rami prodotti possono essere H0, H1, H2 o H3. MISSING TECHNOLOGY ≠ MAGIC TECHNOLOGY.",
      constraints:"EVIDENCE_UNCERTAINTY · TECH_CAPABILITY · SPECULATION_CONTROL", assumptions:"Il ramo future-tech deve produrre opzioni praticabili, non solo aumentare lo spazio narrativo.",
      nextTest:"Su 3 problemi reali, generare in parallelo CURRENT-TECH e MISSING-TECH, specificando enabling technology, dipendenze, primo prototipo e criterio di fallimento.", baseline:"Analisi limitata al solo stack disponibile oggi.",
      kpi:"Nuove opzioni praticabili; vincoli nascosti; tempo al primo prototipo; quota rami futuri convertiti in test/roadmap.", falsifier:"Se il ramo missing-tech non è traducibile in requisiti, dipendenze verificabili o traiettoria di prova, resta H3 e non entra nel piano operativo.",
      risk:"Basso per il principio generale; implementazioni specifiche da valutare separatamente. Nessun claim di unicità.", relations:"RELATED a IDEA-010; overlay globale del portafoglio.", dossier:null
    },
    {
      id:"IDEA-013", title:"CAMPO 42 · CSA Bergamo / Demand-to-Crop Farm OS", maturity:"M2", status:"ACTIVE · TEST CANDIDATE", engine:"Opportunity Foundry × Human Gap Lab × R³ Method Lab", horizon:"H0 → H1/H2", secure:false,
      origin:"Conversazione separata recuperata e fusa con IDEA OS; autore: Claudio Terzi.", problem:"Creare a Bergamo una CSA redditizia e sostenibile basata su domanda pre-impegnata, piano colturale, box settimanali e progressiva digitalizzazione.",
      thesis:"Pattern DEMAND-FIRST AGRICULTURE: domanda osservata → piano colturale → produzione → box → feedback. I numeri iniziali sono assunzioni di test, non previsioni.",
      buyer:"Inizialmente progetto imprenditoriale interno; in futuro possibile modello per operatori agricoli locali, da validare.", evidence:"Verificata l'esistenza di Banca della Terra Lombarda e strumenti CSR per sviluppo rurale/innovazione. Domanda locale, prezzi, rese, costi e terreni specifici restano NON VERIFICATI.",
      currentTech:"H0: CSA, terra, pickup, funghi e ledger.", capability:"H1: demand→crop engine, sensori, matching partner. H2: digital twin e microfarm semi-autonoma.",
      constraints:"ECONOMIC_RESOURCE · EVIDENCE_UNCERTAINTY · CURRENT_TECH", assumptions:"Concept test: 42 settimane, 100 famiglie, 0,5–0,8 ha, box 4–5 kg / 6–8 prodotti, prezzo-test 18 €: tutte ipotesi da validare.",
      nextTest:"TEST 0, 14 giorni senza affitto terreno: landing/lista attesa, esempio cassette, test prezzo/pickup, 15 interviste famiglie, 2 agronomi/orticoltori, 1 coltivatore funghi, 3 terreni candidati, piano colturale/costi v0.",
      baseline:"Nessun CAPEX e nessun terreno affittato prima della verifica della domanda.", kpi:"Interesse qualificato; conversione a pre-impegno; sostenibilità ore/costi; fattibilità piano colturale; rischio shortage/surplus.",
      falsifier:"Domanda insufficiente, ore/costi incompatibili, continuità non sostenibile, logistica che erode margine, rifiuto della standardizzazione o vincoli tecnici/normativi incompatibili.",
      risk:"Basso sul modello CSA generale; specifiche software future da valutare separatamente. Nessuna originalità assoluta rivendicata.", relations:"RELATED a IDEA-010 e IDEA-012; possibile case study IDEA-005/006.",
      dossier:{title:"CLIENT TEST 001 — CAMPO 42 · CSA Bergamo",id:"1Pgp8Z1X7xoguj4ZwOHhDzfRUI2sc8QcjKn60nwjgp9I",url:"https://docs.google.com/document/d/1Pgp8Z1X7xoguj4ZwOHhDzfRUI2sc8QcjKn60nwjgp9I/edit"}
    }
  ]
};
