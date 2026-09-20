# R³∞ — Cubo Quantico + Graphify Structural Layer v1.0

**Data:** 2026-09-20  
**Stato:** CANONICAL / SHARED  
**Firma di progetto:** C.Terzi

## Tesi operativa

Il **Cubo Quantico** non è un semplice grafo. È l'interfaccia multidimensionale dell'universo R³∞: collega opere, idee, codice, documenti, persone/ruoli dichiarati, versioni, decisioni, tempo, provenienza, stato e diramazioni possibili.

**Graphify non sostituisce il Cubo.** Graphify diventa il **sensore strutturale** del Cubo: osserva codice e corpus, estrae nodi e relazioni e restituisce un grafo con provenienza e livelli di confidenza.

In formula:

`Graphify → osserva la struttura`  
`R³∞ → conserva identità, provenienza, continuità e versioni`  
`IDEA OS → governa il ciclo di vita di idee e progetti`  
`TypeSafe / Jev → esegue micro-giudizi strutturati e advisory`  
`Matrice dei Possibili → genera e confronta diramazioni future`  
`Cubo Quantico → rende tutto interrogabile e navigabile nello stesso spazio`

## Due grafi, una sola interfaccia

Il Cubo deve distinguere sempre due livelli:

1. **Grafo osservato** — ciò che esiste o è stato rilevato in fonti, file, codice e documenti.
2. **Grafo dei possibili** — ciò che potrebbe diventare vero: alternative, evoluzioni, conseguenze, scenari e proposte.

I due livelli possono essere sovrapposti nella stessa interfaccia, ma **non devono essere confusi**.

## Stati di evidenza

Ogni relazione deve conservare il proprio stato:

| Stato | Significato | Regola |
|---|---|---|
| `DECLARED` | relazione curata/dichiarata nel Cubo o nel canone R³∞ | resta tracciata con fonte |
| `EXTRACTED` | Graphify l'ha trovata direttamente nella sorgente | osservazione strutturale forte |
| `INFERRED` | Graphify l'ha dedotta | resta inferenza; non diventa fatto automaticamente |
| `AMBIGUOUS` | relazione incerta | richiede revisione |
| `POSSIBLE` | ramo della Matrice dei Possibili | scenario, non fatto |
| `REJECTED` / `HISTORICAL` | ramo falsificato, superato o conservato per storia | non cancellare la provenienza |

Una relazione deve poter portare almeno: `source`, `source_file`, `source_location`, `source_system`, `confidence`, `confidence_score`, `state`, `version/timestamp` quando disponibili.

## Regole non negoziabili

- **Un solo grafo universale:** non creare un secondo "Graphify universe" parallelo. I suoi output entrano nel Cubo come layer.
- **Graphify è un sensore, non un'autorità.** Un edge `INFERRED` non è una verità.
- **Jev è un giudice advisory, non un'autorità.** Può valutare coerenza, rischio, readiness, contraddizioni e priorità, ma non trasforma un'inferenza in fatto e non autorizza effetti esterni.
- **P5/P6 restano sopra il layer:** nessuna auto-conferma; convergenza solo da origini realmente indipendenti.
- **Zero-Assunto:** FATTO / INTERPRETAZIONE / IPOTESI / PROPOSTA restano separati.
- **Provenienza prima della bellezza:** se una relazione non ha origine verificabile, viene mostrata come tale.
- **Nessuna duplicazione:** prima di creare un nuovo motore, verificare se la funzione appartiene già a R³∞, IDEA OS, TypeSafe/Jev, Matrice dei Possibili o Cubo Quantico.

## Pipeline

1. Graphify analizza il corpus e produce `graphify-out/graph.json`.
2. `scripts/graphify_to_cubo.py` converte il grafo nel formato overlay del Cubo.
3. `public/cubo-graph-layer.js` fonde il layer nel dataset vivo senza sovrascrivere il canone esistente.
4. Il Cubo mostra nodi e relazioni conservandone `EXTRACTED / INFERRED / AMBIGUOUS / DECLARED`.
5. TypeSafe/Jev può valutare domande ristrette su un nodo o un insieme di edge.
6. La Matrice dei Possibili aggiunge rami `POSSIBLE`.
7. Solo una verifica esplicita può promuovere un'ipotesi; mai il semplice numero di collegamenti.

Comando di conversione:

    python scripts/graphify_to_cubo.py graphify-out/graph.json public/cubo-graphify-data.js --max-nodes 900

## Regola per tutti gli agenti

Quando un agente lavora su un progetto del nostro universo:

- cerca prima i nodi già esistenti;
- collega il nuovo elemento invece di creare un duplicato;
- preserva provenienza e versione;
- segnala contraddizioni;
- separa collegamenti osservati da collegamenti possibili;
- usa Graphify per struttura, Jev per micro-giudizio e R³∞ per continuità;
- restituisce al Cubo solo dati con stato esplicito.

## Test di correttezza concettuale

La domanda decisiva è:

> "Se tolgo Graphify, il Cubo continua a esistere?"

La risposta deve essere **sì**.

Graphify migliora la percezione del Cubo. Non ne è l'identità, la memoria o l'autorità.
