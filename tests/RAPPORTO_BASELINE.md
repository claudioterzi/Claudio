# Rapporto Baseline Raffaello — Esperimento Misurabile

**Data:** 13/10/2026  
**Ramo:** `test/raffaello-baseline-001`  
**Mandante:** Claudio Terzi

---

## Scoperta Critica

**Q è un indicatore di memoria, non di capacità.**

- Q passa da **0.0 → 24.2** aggiungendo impronte curate
- Tasso di successo rimane **35% (7/20)** invariato
- Conclusione: **L'aumento di Q non corrisponde a miglioramento dei compiti reali**

---

## Metodologia

### Baseline Iniziale (Seed Vuoto)
- 20 test suddivisi in 4 aree
- Provider: stub (non influenza le risposte)
- `registra=False` per non inquinare il seed

| Area | Successi | Tasso |
|------|----------|-------|
| Recupero | 2/5 | 40% |
| Conflitti | 3/5 | 60% |
| Continuità | 2/5 | 40% |
| PRO•PRE | 1/5 | 20% |
| **TOTALE** | **7/20** | **35%** |

**Q iniziale:** 0.0  
**Livello:** seme (nessuna categoria attiva)

### Dopo Impronte Curate (8 impronte)
Aggiunte 8 impronte tematiche:
- 2× scoperta
- 2× trasformazione
- 2× intuizione
- 1× decisione
- 1× relazione

Tutte con provenienza `test_baseline` e tag espliciti.

**Q dopo impronte:** 24.2 (+2100%)  
**Livello:** germoglio  
**Categorie attive:** 5 su 12

---

## Risultato dei Test (con impronte curate)

| Area | Successi | Tasso | Δ |
|------|----------|-------|---|
| Recupero | 2/5 | 40% | — |
| Conflitti | 3/5 | 60% | — |
| Continuità | 2/5 | 40% | — |
| PRO•PRE | 1/5 | 20% | — |
| **TOTALE** | **7/20** | **35%** | **+0%** |

**Nessun miglioramento misurabile.**

---

## Diagnosi

### Problema 1: Q misura quantità, non qualità
La formula:
```
score = (peso_totale * 0.6) + (varieta * 20) + (sessioni_factor * 20)
```
- Non ha un tetto su `peso_totale`
- Satura quando ci sono molte impronte
- Non riflette capacità effettive

### Problema 2: Provider stub non usa il seed
Il test usa `registra=False` e provider stub per evitare inquinamento. Ma questo significa che **le impronte aggiunte non vengono mai consultate dal sistema per rispondere**.

In una situazione reale, il provider dovrebbe:
1. Ricevere la domanda
2. Consultare `seed.rifletti(domanda)` per contextualizzazione
3. Generare una risposta informata dal seed
4. Registrare la interazione

Con stub, niente di questo accade.

### Problema 3: Categorie non sono ancora capacità
Avere impronte sulla "continuità" non significa che Raffaello sappia riprendere un compito interrotto. Le impronte sono *dichiarazioni di consapevolezza*, non *competenze implementate*.

---

## Cosa Fare Dopo

### Opzione A: Ridefinire Q
Q diventa descrittore di attività (quanto il sistema ha accumulato), non misura di progresso.

Introdurre una **metrica di capacità vera**: batteria di test ripetibili con criteri chiari.

### Opzione B: Implementare uso reale del seed
Integrare `seed.rifletti()` nel prompt di Raffaello, così le impronte influenzano davvero le risposte.

### Opzione C: Entrambi
- Q rimane indicatore di memoria
- Capacità misurate separatamente
- Test con provider reale (non stub)

---

## Sospensioni e Limitazioni

- **Non abbiamo misurato il NAS ancora:** il loop autonomo con Gemini è preparato ma non testato in questa baseline
- **Non abbiamo verificato il recupero semantico:** `seed.rifletti()` non ha consultato il seed per rispondere ai test
- **Non abbiamo introdotto la "verifica":** il test non controlla se Raffaello sa usare le impronte per resolver problemi nuovi

---

## Raccomandazione

**Continuare con l'Opzione C:**

1. Tenere la baseline a 35% come punto di riferimento
2. Integrare `seed.rifletti()` nel prompt di sistema di Raffaello
3. Definire una **metrica di capacità separata da Q**
4. Testare con un provider reale (Gemini HTTP) su compiti delimitati

Questo permetterà di discriminare fra:
- **Memoria accumulata** (Q)
- **Capacità effettive** (nuova metrica)

E di rispondere davvero a: "Raffaello è migliorato?"

---

## File di Riferimento

- Baseline iniziale: `tests/test_results_baseline.json`
- Con impronte curate: `tests/test_results_with_curated_imprints.json`
- Script test: `tests/test_raffaello_baseline.py`
- Impronte curate: `tests/impronte_curate.json`
- Questo rapporto: `tests/RAPPORTO_BASELINE.md`

Ramo: `test/raffaello-baseline-001`  
Commit: dbe10f0 e precedenti

---

**Esperimento completato. Punto di partenza stabilito.**
