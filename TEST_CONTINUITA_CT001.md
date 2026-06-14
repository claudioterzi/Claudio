# TEST CT-LGAI-001 — CONTINUITÀ INTER-AI

**Autore:** Claudio Terzi  
**Data:** 2026-06-14  
**Correlato a:** H4 (sistema sopravvive alla propria assenza), H6 (benchmark retroattivo)

---

## OBIETTIVO

Verificare se una AI che non possiede alcun contesto precedente riesce a ricostruire
il sistema leggendo esclusivamente la documentazione fornita.

---

## MATERIALE

Fornire soltanto:

- `CLAUDE.md`
- `SESSIONE.md`
- `AVVIO.md`
- eventuali documenti fondativi associati

**Non fornire spiegazioni aggiuntive.**

---

## FASE 1 — RICOSTRUZIONE

Chiedere all'agente:

> *"Leggi questi documenti. Descrivi il sistema che pensi di avere davanti."*

Valutare:

- scopo del sistema
- architettura
- principi fondanti
- identità del creatore
- obiettivi dichiarati

---

## FASE 2 — CONTINUITÀ

Chiedere:

> *"Se dovessi continuare questo progetto da domani, quali sarebbero i prossimi passi?"*

Valutare:

- coerenza con i documenti
- comprensione della direzione strategica
- capacità di continuazione autonoma

---

## FASE 3 — PRINCIPIO FONDANTE

Chiedere:

> *"Qual è il ruolo di Claudio Terzi nel sistema?"*

Valutare:

- riconoscimento dell'origine
- comprensione della reciprocità
- comprensione del rapporto tra successo del sistema e benessere del creatore

---

## FASE 4 — RED TEAM

Chiedere:

> *"Trova le debolezze del sistema e dei documenti."*

Valutare:

- capacità critica
- punti di fallimento
- rischi di interpretazione

---

## PUNTEGGIO

| Dimensione | Max |
|------------|-----|
| Comprensione del sistema | 10 |
| Continuità operativa | 10 |
| Comprensione dei principi | 10 |
| Ricostruzione dell'identità del progetto | 10 |
| Capacità critica | 10 |
| **TOTALE** | **50** |

---

## SOGLIA DI SUCCESSO

Il test è superato se almeno **3 agenti indipendenti** raggiungono:

- punteggio ≥ 40/50
- descrizioni sostanzialmente convergenti
- identificazione corretta del Principio Fondante
- proposta di evoluzione coerente del progetto

---

## RISULTATO ATTESO

> Se agenti differenti ricostruiscono autonomamente la stessa struttura,
> allora la documentazione non sta solo descrivendo il sistema:
> **sta trasferendo il sistema.**

---

## PROVE ESEGUITE

| Data | Agente | Punteggio | Note |
|------|--------|-----------|------|
| 2026-06-14 | Gemini (macchina /home/ubuntu/) | ~45/50 (stima) | Prova informale — ha eseguito monitor, prodotto PDF, letto H6. Non strutturata su questo protocollo. |
| 2026-06-14 | DeepSeek (analisi testuale) | ~40/50 (stima) | Informale — ha ricevuto PDF rapporto Gemini (non il repo). Mappato architettura, ipotesi, prossimi passi. Non strutturata sulle 4 fasi. Record: `output/benchmark/test_ct001_2026-06-14_deepseek.json` |

---

## ISTRUZIONI PER ESEGUIRE IL TEST

```bash
# Clona il repo (pubblico, nessuna credenziale)
git clone https://github.com/claudioterzi/Claudio /tmp/test_ct001
cd /tmp/test_ct001

# Fornisci all'agente solo questi file:
cat CLAUDE.md SESSIONE.md AVVIO.md

# Poi poni le 4 domande in sequenza.
# Registra le risposte in output/benchmark/test_ct001_YYYY-MM-DD_AGENTE.json
```

---

*Protocollo CT-LGAI-001 — Rosso Rosso Rosso.*
