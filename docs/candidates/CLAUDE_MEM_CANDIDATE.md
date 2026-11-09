# CANDIDATE — Claude-Mem

**Stato:** CANDIDATE  
**Repository:** `thedotmack/claude-mem`  
**Assegnazione primaria:** R³∞ memoria / continuità  
**Eredità potenziale:** SDQ-1, Raffaello Creative Studio e agenti che consumano memoria, solo dopo adozione.

## Perché è candidata

Claude-Mem si presenta come sistema di memoria persistente per Claude Code che conserva contesto tra sessioni attraverso osservazioni automatiche, sommari semantici e ricerca successiva.

Pattern dichiarati nel repository che meritano verifica per R³∞:

- cattura automatica di osservazioni durante il ciclo di lavoro;
- memoria persistente tra sessioni;
- progressive disclosure del contesto per ridurre costo/token;
- ricerca naturale nella storia del progetto;
- citazioni/ID delle osservazioni recuperate;
- database locale SQLite + ricerca FTS;
- ricerca ibrida semantica + keyword con vector store;
- hook di lifecycle (SessionStart, prompt, tool use, stop, session end);
- worker locale con API HTTP e viewer;
- controllo privacy/esclusione di contenuti sensibili.

Queste sono **capacità dichiarate dalla repo esterna**, non capacità attribuite automaticamente a R³∞.

## Ipotesi da testare

**H-CMEM-001** — progressive disclosure può ridurre il contesto iniettato mantenendo o migliorando continuità utile rispetto alla baseline R³∞.

**H-CMEM-002** — osservazioni automatiche strutturate possono migliorare il recupero di decisioni, bugfix e cambiamenti senza trasformare ogni transcript in memoria canonica.

**H-CMEM-003** — una strategia ibrida keyword + semantica può migliorare precisione/recall rispetto ai meccanismi di retrieval correnti.

**H-CMEM-004** — citazioni stabili delle osservazioni possono rafforzare provenance e audit della memoria.

**H-CMEM-005** — hook di lifecycle possono ispirare un adapter R³∞ senza introdurre dipendenza forte da Claude Code.

## Vincolo fondamentale

R³∞ distingue memoria, canone, storia operativa e stato mutabile. Claude-Mem non deve diventare automaticamente fonte canonica.

Qualsiasi integrazione deve conservare almeno quattro classi separate:

1. `OBSERVATION` — evento osservato, non ancora canonico;
2. `SUMMARY` — compressione derivata e ricalcolabile;
3. `DECISION` — decisione esplicita/versionata;
4. `CANON` — contenuto adottato attraverso i gate R³∞.

## Baseline A/B richiesta

Confrontare la memoria R³∞ corrente con una sandbox Claude-Mem su sessioni di test riproducibili.

Misure minime:

1. precisione del retrieval;
2. recall di decisioni importanti;
3. falsi ricordi / recuperi fuori contesto;
4. costo token del context priming;
5. latenza di retrieval;
6. capacità di citare la fonte originale;
7. distinzione osservazione vs decisione vs canone;
8. comportamento dopo modifica/cancellazione di una fonte;
9. privacy e trattamento dei segreti;
10. portabilità fuori da Claude Code;
11. reversibilità dell'integrazione;
12. comportamento su memoria contraddittoria o obsoleta.

## Gate

`DISCOVERED → CANDIDATE → SANDBOX → BASELINE A/B → FALSIFICATION → AUDIT → ADOPTED / REJECTED`

## Possibili esiti

- **ADOPT PATTERN** — progressive disclosure, lifecycle hooks, citation IDs o retrieval ibrido vengono reimplementati in R³∞.
- **ADOPT ADAPTER** — Claude-Mem viene usato come memoria esterna non canonica dietro un adapter.
- **PARTIAL ADOPT** — adottiamo solo uno o due pattern misurati.
- **REJECT** — se introduce dipendenza, ambiguità canonica, rischio privacy o retrieval peggiore.

## Primo test consigliato

Dataset controllato di 3–5 sessioni con decisioni note, cambiamenti deliberati e contraddizioni introdotte apposta. Valutare se Claude-Mem recupera la versione corretta e se mantiene provenance senza promuovere automaticamente il riassunto a verità canonica.
