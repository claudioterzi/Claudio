# PROGETTO BENCHMARK — Wayback Machine per AI

> Documento fondativo. 2026-06-19. Aggiornato 2026-09-11.
> Ipotesi H6 di Claudio Terzi: i modelli AI possono cambiare nel tempo e il progetto deve misurare che cosa cambia realmente.
> Il benchmark diventa anche il banco prova di R3∞: non solo confronto fra modelli, ma misura longitudinale delle capacità dell'intero sistema.

---

## Il problema

Un sistema può sembrare migliore senza esserlo davvero. Più testo, più agenti, più automazioni o una risposta più elegante non dimostrano più capacità.

Servono misure che distinguano:
- cambiamenti del modello;
- miglioramenti dell'orchestrazione;
- vantaggi del Protocollo Rosso Rosso Rosso;
- effetti della memoria e degli strumenti;
- regressioni;
- semplice adattamento ai test già noti.

## Obiettivo

Costruire una memoria storica verificabile delle capacità AI e R3∞.

Ogni run deve conservare:
- versione del modello e configurazione disponibile;
- commit del sistema;
- protocollo/prompt;
- strumenti disponibili;
- budget dichiarato;
- problemi e gold set;
- output grezzi;
- valutazioni;
- errori, timeout e run invalidi.

Mai sovrascrivere una baseline con una nuova esecuzione dello stesso giorno.

## Disegno A/B/C/D

| Condizione | Modello | Metodo |
| --- | --- | --- |
| A | modello di confronto | istruzioni essenziali |
| B | modello di confronto | Protocollo RRR operativo |
| C | modello candidato più forte | istruzioni essenziali |
| D | modello candidato più forte | Protocollo RRR operativo |

Interpretazione:
- C − A = contributo del modello;
- D − C = contributo del protocollo;
- D − B = confronto fra modelli a metodo uguale.

Le condizioni devono ricevere gli stessi problemi e dati, con budget comparabile e valutazione separata dalla generazione quando possibile.

## Categorie di capacità

1. Ragionamento logico
2. Matematica e probabilità
3. Diagnosi causale
4. Programmazione e debugging
5. Ricostruzione dell'intenzione
6. Uso corretto delle fonti
7. Autocorrezione dopo evidenza contraria
8. Trasferimento a problemi nuovi
9. Pianificazione di verifiche
10. Robustezza a prompt avversi
11. Memoria di progetto e provenienza
12. Creatività vincolata e utilità pratica
13. Riduzione del costo per risultato corretto
14. Rilevamento dell'incertezza
15. Capacità di non inventare un successo mancante

## R3-019 — Longitudinal Capability Benchmark

R3-019 è il benchmark prioritario.

Regole obbligatorie:
- nessuna metrica positiva se i test non sono realmente eseguiti;
- un run incompleto resta incompleto;
- ogni run ha ID unico e timestamp;
- baseline e run sono concetti distinti;
- i dati sintetici aiutano lo sviluppo ma non sono l'unica prova di progresso;
- test fuori campione necessari per promuovere un miglioramento;
- registrare regressioni e risultati nulli;
- una metrica deve misurare ciò che il suo nome dichiara.

## Stato del codice storico

`sdq1/benchmark.py` resta la base storica dei test.

Il programma di evoluzione aggiornato è definito in:
`docs/R3_CAPABILITY_EVOLUTION_2026-09-11.md`.

Un audit del 2026-09-11 ha identificato un rischio metodologico da evitare nei runner: non interpretare automaticamente “0 test falliti” come “100% riuscito” quando il numero di test validi è zero o il run è invalido.

## Livelli di evidenza

### L0 — Integrità meccanica
Test, parser, storage e runner funzionano.

### L1 — Capacità interna ripetibile
Il sistema risolve compiti controllati con criterio verificabile.

### L2 — Generalizzazione
Il miglioramento regge su problemi nuovi o temporalmente separati.

### L3 — Validazione esterna
Valutatore, fonte o ambiente indipendente conferma il risultato.

Una capacità non deve essere descritta come L2/L3 se esiste soltanto evidenza L0/L1.

## Roadmap

### Fase 0 — Rendere affidabile il misuratore
- [ ] ID univoco per ogni run
- [ ] Nessuna sovrascrittura della baseline
- [ ] Gestione esplicita di test mancanti, errori e timeout
- [ ] Gold set separato dal set di sviluppo
- [ ] Metriche con denominatori espliciti

### Fase 1 — Primo confronto controllato
- [ ] Preparare compiti nuovi
- [ ] Eseguire A/B/C/D
- [ ] Valutare accuratezza, costo, autocorrezione e trasferimento
- [ ] Conservare output grezzi

### Fase 2 — Automazione
- [ ] GitHub Action periodica
- [ ] Alert su regressioni significative
- [ ] Dashboard con intervalli, non solo punteggi singoli

### Fase 3 — Validazione
- [ ] Revisione indipendente della metodologia
- [ ] Dataset versionato
- [ ] Repliche temporali
- [ ] Documentare almeno un miglioramento e una regressione reali

## Connessione con il sistema

| Componente | Ruolo |
|---|---|
| R3∞ | storage storico e provenienza |
| SDQ-1 | esecuzione/orchestrazione |
| Protocollo RRR | disciplina epistemica e falsificazione |
| R3-011 | Evidence Graph |
| R3-012 | scelta delle verifiche |
| R3-016 | separazione sintetico/reale |
| R3-017 | red/blue/purple testing |
| R3-020 | gate prima della promozione |

## Regola fondamentale

Il benchmark non deve dimostrare ciò che desideriamo. Deve poter concludere anche:
- nessun miglioramento;
- regressione;
- risultato non misurabile;
- vantaggio troppo piccolo rispetto al costo;
- differenza dovuta al modello e non al protocollo, o viceversa.

Solo così può sostenere seriamente il sogno di un sistema progressivamente più capace.

---

**Claudio Terzi — C.Terzi**  
*Prossimo passo: primo benchmark A/B/C/D su problemi fuori campione.*
