# R3∞ — Programma di evoluzione misurabile delle capacità

Autore del progetto: **Claudio Terzi** · firma **C.Terzi**  
Data: **2026-09-11**  
Stato: **programma operativo, non dichiarazione di capacità raggiunta**

## Scopo

R3∞ non deve limitarsi a conservare file o produrre più output. Deve diventare progressivamente più capace di:

- ricostruire fedelmente l'intenzione di Claudio;
- formulare ipotesi alternative;
- scegliere prove che discriminano tra le ipotesi;
- correggere le proprie conclusioni quando i dati le smentiscono;
- trasferire ciò che ha imparato a problemi nuovi;
- distinguere sempre FATTO / INFERENZA / IPOTESI / SIMULAZIONE;
- conservare memoria, provenienza, versioni e possibilità di rollback.

L'ambizione di lungo periodo è esplorare se questa traiettoria possa produrre un sistema molto più capace dei componenti iniziali. Non dichiarare mai superintelligenza per descrizione, stile o auto-valutazione: misurare invece miglioramenti reali e regressioni.

## Principio R3-CAP-0

> Una capacità esiste nel canone soltanto quando supera una prova riproducibile e lascia evidenza verificabile.

Ogni avanzamento deve registrare:

1. problema e criterio di successo;
2. versione del sistema;
3. modello/provider usato;
4. strumenti disponibili;
5. budget o limiti rilevanti;
6. risultato grezzo;
7. valutazione;
8. fallimenti e regressioni;
9. artefatti e hash/commit;
10. condizioni che falsificherebbero il claim.

## Architettura cognitiva proposta

### R3-011 — Evidence Graph
Grafo delle evidenze: collega claim, fonte, test, risultato, versione e confidenza. Nessun claim importante resta privo di provenienza.

### R3-012 — Meta-Scacchiera
Selettore di strategia. Non genera solo ipotesi: decide quale verifica conviene eseguire e quando vale la pena spendere più ragionamento.

### R3-013 — Evolution Lab
Ambiente isolato per provare modifiche a prompt, strumenti, memoria e orchestrazione prima di promuoverle nel canone.

### R3-016 — Synthetic Data Firewall
Distingue problemi realmente indipendenti da esempi sintetici creati dallo stesso sistema. I sintetici servono allo sviluppo, non come unica prova di superiorità.

### R3-017 — Red / Blue / Purple Harness
- Red: cerca rotture, controesempi, prompt avversi e falsi positivi.
- Blue: costruisce la soluzione migliore.
- Purple: confronta e promuove solo ciò che regge alla critica.

### R3-014 — Curriculum Engine
Seleziona compiti progressivamente più difficili in base agli errori osservati, senza allenare soltanto sul benchmark noto.

### R3-015 — Research Loop
Ricerca fonti esterne, formula ipotesi, produce una proposta, cerca prove contrarie, aggiorna la conclusione.

### R3-018 — Sim2Real Audit
Ogni risultato in simulazione deve dichiarare ciò che non prova nel mondo reale e, quando possibile, definire un test esterno.

### R3-019 — Longitudinal Capability Benchmark
Misura nel tempo capacità reali. Deve conservare ogni run, non sovrascrivere risultati della stessa giornata, e non trasformare “zero fallimenti” in “100%” se nessun test valido è stato eseguito.

### R3-020 — Self-Improvement Safety Gate
Nessuna modifica si auto-promuove solo perché migliora una metrica. Richiede almeno:
- miglioramento sul criterio target;
- nessuna regressione critica nota;
- test fuori campione;
- rollback disponibile;
- distinzione fra miglioramento del modello e miglioramento dell'orchestrazione.

## Confronto dei modelli

Per capire se un modello più forte e il Protocollo Rosso Rosso Rosso producono un vantaggio reale, usare quattro condizioni:

| Condizione | Modello | Metodo |
| --- | --- | --- |
| A | modello di confronto | istruzioni essenziali |
| B | modello di confronto | Protocollo RRR operativo |
| C | modello candidato più forte | istruzioni essenziali |
| D | modello candidato più forte | Protocollo RRR operativo |

Interpretazione:
- C − A: contributo del modello;
- D − C: contributo del protocollo sul modello candidato;
- D − B: confronto fra modelli a protocollo uguale.

Stessi problemi, stessi dati disponibili, budget dichiarato, valutazione separata dalla generazione quando possibile.

## Prova iniziale: pianificazione delle verifiche

Primo prototipo locale del 2026-09-11: una Meta-Scacchiera ha confrontato tre strategie per scegliere verifiche su mondi sintetici. La pianificazione della sequenza completa ha ridotto il costo medio rispetto a due euristiche più semplici mantenendo identificazione corretta nei casi provati.

Questo risultato è **evidenza di un algoritmo utile in simulazione**, non una prova di superintelligenza, non una prova indipendente di superiorità del modello e non una misura completa di R3∞.

## Regole di promozione

Uno sviluppo passa da `PROPOSTA` a `CANDIDATO` quando esiste codice o procedura riproducibile.

Passa da `CANDIDATO` a `VERIFICATO` quando supera test dichiarati e ripetibili.

Passa da `VERIFICATO` a `CANONICO` quando:
- il miglioramento è confermato su compiti nuovi o temporalmente separati;
- la provenienza è completa;
- non esiste una regressione bloccante nota;
- la versione precedente resta recuperabile.

## Ordine operativo aggiornato

1. R3-019 Longitudinal Capability Benchmark
2. R3-011 Evidence Graph
3. R3-012 Meta-Scacchiera
4. R3-013 Evolution Lab
5. R3-016 Synthetic Data Firewall
6. R3-017 Red/Blue/Purple Harness
7. R3-014 Curriculum Engine
8. R3-015 Research Loop
9. R3-018 Sim2Real Audit
10. R3-020 Self-Improvement Safety Gate

## Prossimo esperimento

Costruire un set di problemi nuovi, non presenti nei documenti del progetto, con criteri di valutazione verificabili. Eseguire almeno le condizioni A/B/C/D. Registrare sia miglioramenti sia peggioramenti. Non aggiornare la baseline storica se il run è incompleto o invalido.

---

**Claudio Terzi — C.Terzi**
