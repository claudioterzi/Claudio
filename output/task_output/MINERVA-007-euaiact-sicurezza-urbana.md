# MINERVA-007 — EU AI Act: Obblighi per Sistemi Sicurezza Urbana con Droni
*Task autonomo SDQ-1 — completato 2026-06-20*

---

## Riferimento normativo

**EU AI Act** — Regolamento (UE) 2024/1689, in vigore dal 2 agosto 2024.
Applicazione progressiva: sistemi ad alto rischio → **2 agosto 2026**.

Per sistemi di sicurezza urbana con droni, il testo rilevante è:
- **Annex III, punto 6** — Sistemi di identificazione biometrica
- **Annex III, punto 7** — Sistemi di infrastruttura critica
- **Articolo 5** — Pratiche vietate

---

## Classificazione del Sistema Minerva SDQ-1

Il Sistema Minerva combina droni + AI per:
- Monitoraggio urbano / sicurezza predittiva
- Analisi immagini satellite
- Rilevamento pattern anomali

**Classificazione:** **ALTO RISCHIO** (Annex III, punto 6b e 7)

Motivo: uso di AI per analisi di spazio pubblico + potenziale identificazione di persone.

---

## Pratiche VIETATE (Art. 5) — Non fare mai

| Pratica | Status |
|---|---|
| Sistemi di categorizzazione biometrica per inferire razza, religione, politica | ❌ VIETATO |
| Identificazione biometrica remota in tempo reale nello spazio pubblico (LE) | ❌ VIETATO (salvo eccezioni) |
| Sistemi di "social scoring" da parte di autorità pubbliche | ❌ VIETATO |
| Manipolazione subliminale per alterare comportamenti | ❌ VIETATO |
| Sfruttamento vulnerabilità per influenzare decisioni | ❌ VIETATO |

**Per SDQ-1/Minerva:** non implementare identificazione biometrica real-time con droni.
Il rilevamento di pattern anomali è ammesso; l'identificazione di persone specifiche non lo è.

---

## Obblighi per Sistemi Alto Rischio (Art. 9-17)

### 1. Sistema di gestione del rischio (Art. 9)
```
Obbligo: documentare rischi del sistema AI prima del deploy
Pratica:  creare MINERVA_RISK_REGISTER.md con analisi dei rischi
Scadenza: prima del deploy in produzione
```

### 2. Governance dei dati (Art. 10)
```
Obbligo: dati di training e test devono essere rappresentativi, privi di bias
Pratica:  documentare fonte dati satellite/droni e politica anti-discriminazione
Scadenza: al momento del deploy
```

### 3. Documentazione tecnica (Art. 11)
```
Obbligo: technical documentation completa (Annex IV)
Pratica:  MINERVA_TECHNICAL_DOC.md con architettura, modelli, performance
Scadenza: prima di mettere il sistema sul mercato/in uso
```

### 4. Log automatici (Art. 12)
```
Obbligo: logging automatico delle operazioni AI
Pratica:  già parzialmente presente in SDQ-1 (logging Python)
          → estendere con timestamp, input/output, decisioni
```

### 5. Trasparenza verso utenti (Art. 13)
```
Obbligo: informare gli utenti che stanno interagendo con un sistema AI
Pratica:  se Minerva ha interfaccia pubblica → banner/avviso chiaro
```

### 6. Supervisione umana (Art. 14)
```
Obbligo: gli operatori devono poter sorvegliare, interrompere, correggere il sistema
Pratica:  ogni decisione AI di Minerva deve essere revisabile da Claudio prima di azioni
```

### 7. Robustezza e cybersicurezza (Art. 15)
```
Obbligo: sistema resiliente ad errori, attacchi, manipolazioni
Pratica:  Circuit Breaker già presente in SDQ-1 router
          → aggiungere rate limiting e input validation su Minerva
```

---

## Notifica e Registrazione

Per sistemi alto rischio che **non** richiedono certificazione di terze parti:

1. **Auto-valutazione** (conformity assessment) — documentazione interna
2. **Dichiarazione EU di conformità** — documento firmato
3. **Registrazione nel database EU** — obbligatoria: ec.europa.eu/info/law/better-regulation/ai-database
   - Gratuita, fatta dall'operatore
   - Richiede: nome sistema, categoria rischio, paesi di deploy, dati di contatto

**Non richiede:** certificazione da Notified Body (solo per certi sistemi biometrici)

---

## Cosa è Permesso per Minerva

| Uso | Status | Condizione |
|---|---|---|
| Monitoraggio area pubblica per sicurezza infrastrutture | ✅ PERMESSO | Con documentazione |
| Rilevamento pattern anomali (senza ID persone) | ✅ PERMESSO | Log obbligatori |
| Analisi immagini satellite (pattern urbanistici) | ✅ PERMESSO | Nessuna restrizione |
| Alert automatici per eventi anomali | ✅ PERMESSO | Supervisione umana |
| Identificazione veicoli/strutture (non persone) | ✅ PERMESSO | Documentazione |
| Rilevamento folla anonima (conteggio, flusso) | ✅ PERMESSO | Anonimizzazione richiesta |

---

## Piano di Conformità SDQ-1/Minerva

```
Passo 1 (ora):        Creare MINERVA_RISK_REGISTER.md
Passo 2 (prima deploy): Creare MINERVA_TECHNICAL_DOC.md (Annex IV)
Passo 3 (prima deploy): Dichiarazione EU di conformità
Passo 4 (prima deploy): Registrazione database EU AI
Passo 5 (operativo):    Log automatici, revisione semestrale
```

**Stima tempo:** 2-3 giorni per documentazione completa.
**Costo:** zero (no terze parti richieste per questa categoria).

---

## Sanzioni per non conformità

| Violazione | Sanzione massima |
|---|---|
| Pratiche vietate (Art. 5) | €35M o 7% fatturato globale |
| Sistemi alto rischio non conformi | €15M o 3% fatturato |
| Informazioni false all'autorità | €7.5M o 1.5% fatturato |

Per una startup/fondazione: anche €7.5M è devastante. La conformità vale il tempo.

---

*MINERVA-007 completato — 2026-06-20*
*SDQ-1 / Claudio Terzi, Bruxelles*
