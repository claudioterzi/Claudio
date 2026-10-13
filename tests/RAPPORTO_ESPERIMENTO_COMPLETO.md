# Rapporto Esperimento Completo: Memoria di Raffaello

**Data:** 13/10/2026  
**Stato:** Esperimento costruito e verificabile  
**Blocco:** Nessuno tecnico; dipendenza dalla scelta di provider

---

## Sommario Esecutivo

Abbiamo costruito un esperimento A/B/C per misurare se la memoria di Raffaello migliora le capacità reali. I risultati sono onesti:

- **Collegamento tecnico memoria→provider:** ✅ **Funzionante**
- **Capacità con provider locale (stub):** 0% in tutte le condizioni A/B/C
- **Valutatori:** ✅ **Rigorosi** (respingono stringhe casuali, verificano logica)

---

## Esperimento: Tre Fasi

### Fase 1: Valutatori Rigorosi ✅

**File:** `tests/valutatori_rigorosi.py`

Abbiamo riscritto i valutatori per verificare la logica, non semplici parole chiave.

Esempio di test:
```
✗ Stringa casuale: "paura scoperta nessun totale..."
  Motivo: calcolo non corretto, mancano campi quantità/prezzo

✓ Preventivo corretto: "10 ore × 50€ = 500€"
  Motivo: tutti i campi presenti, calcolo corretto
```

**Conclusione:** I valutatori respingono risposte errate e accettano solo quelle logicamente corrette.

---

### Fase 2: Traccia Memoria ✅

**File:** `tests/test_memory_path.py`  
**Rapporto:** `tests/test_memory_path_report.json`

Abbiamo verificato il collegamento tecnico:

1. Creato seed con impronta sintetica riconoscibile
2. Domanda correlata: "Cosa hai imparato sui limiti?"
3. Verificato che `seed.rifletti()` recupera l'impronta
4. Verificato che il dato sintetico arriva al provider (monkey-patch)

**Risultato:**
```
✓ COLLEGAMENTO VERIFICATO
  • seed.rifletti() ha trovato l'impronta: True
  • Provider ha ricevuto il dato sintetico: True
```

**Conclusione:** Il percorso **seed → recupero → contesto inviato al provider** è funzionante.

---

### Fase 3: A/B/C Conditions 🔍

**File:** `tests/test_abc_conditions.py`  
**Rapporto:** `tests/test_abc_results.json`

**Condizioni:**
- **A:** Nessuna memoria (seed vuoto, Q=0)
- **B:** Memoria iniziale (seed vuoto, Q=0)
- **C:** Memoria arricchita (3 impronte curate, Q=12.8)

**Compito:** Preventivo PRO•PRE (3 test specifici)
- Preventivo base: 10 ore × 50€/ora
- Preventivo con listino: 20 ore × 75€/ora
- Prezzo errato: verificare che non accetti prezzi inventati

**Risultati:**
| Condizione | Impronte | Q | Successi | Tasso |
|-----------|----------|---|----------|-------|
| A | 0 | 0.0 | 0/3 | **0%** |
| B | 0 | 0.0 | 0/3 | **0%** |
| C | 3 | 12.8 | 0/3 | **0%** |
| | | | Δ C-A | **+0%** |

**Analisi:**
- Lo stub non implementa logica di calcolo (non è il suo compito)
- La memoria non influenza uno stub che non la consulta nel suo percorso decisionale
- Risultato: **Onesto, non simulato**

---

## Collegamento Verificato vs. Capacità Misurata

Questo esperimento distingue chiaramente:

| Aspetto | Stato |
|---------|-------|
| **Collegamento tecnico** (seed→recupero→contesto) | ✅ Verificato |
| **Valutatori rigorosi** | ✅ Funzionanti |
| **Capacità con stub locale** | 0% (atteso) |
| **Capacità con provider reale** | ⏸️ Dipende da scelta |

---

## Blocco: Scelta di Provider

Per ottenere risultati misurabili di capacità, serve un provider che:
1. Implementa logica reale (calcoli, recupero dati)
2. Legga effettivamente il contesto fornito (impronte recuperate)
3. Sia disponibile senza costi aggiuntivi non autorizzati

**Opzioni:**

### Opzione 1: Provider Locale (Zero Costi)
- Interpreter Python locale per calcoli
- Replicabile da chiunque
- Limitato a logica sintetica

### Opzione 2: Provider API Pagato (Dipendente da Autorizzazione)
- Gemini, Claude, OpenAI, ecc.
- Capacità reali del modello
- Richiede autorizzazione esplicita su budget

---

## Comandi per Verificare

```bash
# Valutatori
python3 tests/valutatori_rigorosi.py

# Traccia memoria
python3 -m tests.test_memory_path
grep "conteneva_seed_data" tests/test_memory_path_report.json

# A/B/C conditions
python3 -m tests.test_abc_conditions
cat tests/test_abc_results.json | python3 -m json.tool
```

---

## Conclusioni Metodologiche

1. **L'esperimento è corretto:** A/B/C con 0% tutto è il risultato giusto con stub
2. **Non simuliamo:** I risultati sono onesti, non falsificati con "Q è aumentato"
3. **Prossimo passo è una scelta:** Provider locale (costo zero) o provider reale (autorizzazione costi)
4. **Il collegamento memoria funziona:** Non è il problema

---

## File di Riferimento

- `tests/valutatori_rigorosi.py` — Logica di valutazione rigorosa
- `tests/test_memory_path.py` — Traccia memoria, mono-patch provider
- `tests/test_memory_path_report.json` — Output della traccia memoria
- `tests/test_abc_conditions.py` — Test A/B/C
- `tests/test_abc_results.json` — Risultati A/B/C
- Questo file — Rapporto complessivo

**Ramo:** `claude/raffaello-superintelligence-490k5j`

---

**Esperimento stabile e verificabile. Prossimo passo dipende dalla scelta di provider.**
