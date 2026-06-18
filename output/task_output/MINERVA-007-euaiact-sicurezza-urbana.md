# MINERVA-007 — EU AI Act: Obblighi per Sistemi Sicurezza Urbana con Droni
*Completato automaticamente da Agente Orario SDQ-1 — 2026-06-18*

---

## 1. EU AI Act: Struttura e Tempistica

L'EU AI Act è entrato in vigore il **1 agosto 2024** (Regolamento UE 2024/1689). L'applicazione è graduale:

| Data | Cosa entra in vigore |
|------|---------------------|
| **Agosto 2024** | Entrata in vigore ufficiale |
| **Febbraio 2025** | Divieti sistemi AI a rischio inaccettabile (Art. 5) |
| **Agosto 2025** | GPAI models, governance, sandboxes |
| **Agosto 2026** | **TUTTO il resto** incluso Annex III (alto rischio) → deadline per sistema Minerva |
| **Agosto 2027** | Sistemi AI già sul mercato (embedded in prodotti esistenti) |

**Urgenza per Minerva:** Se il sistema viene lanciato prima di agosto 2026, deve essere conforme entro quella data.

---

## 2. Classificazione Sistema Minerva

Il Sistema Minerva (rete droni + AI per sicurezza urbana predittiva) cade sotto **MULTIPLE categorie** dell'EU AI Act:

### Categoria: ALTO RISCHIO (Annex III)

**Annex III, Punto 6 — Law Enforcement:**
> "AI systems intended to be used by or on behalf of competent authorities [...] for:
> (a) the individual risk assessment of natural persons in order to assess the risk of a natural person for offending or reoffending [...];
> (b) polygraphs and similar tools;
> (c) the evaluation of the reliability of evidence;
> (d) predicting the occurrence or reoccurrence of an actual or potential criminal offence [...];
> (e) profiling of natural persons as referred to in Article 4(4) of GDPR [...];
> (f) crime analytics regarding natural persons [...]"

**Annex III, Punto 1 — Biometric Identification:**
> "Real-time remote biometric identification systems" — se Minerva include facial recognition in tempo reale nello spazio pubblico, questo è **VIETATO** (non solo alto rischio).

### Conclusione classificazione Minerva

| Componente Minerva | Categoria AI Act |
|-------------------|-----------------|
| Predictive policing (identificazione anomalie comportamentali) | **ALTO RISCHIO** (Annex III, punto 6d) |
| Object detection in tempo reale (veicoli, persone) | **RISCHIO LIMITATO** (non Annex III se non biometrico) |
| Facial recognition real-time in pubblico | **VIETATO** (Art. 5, comma 1d) |
| Coordinamento multi-drone autonomo | **RISCHIO LIMITATO** (se non decisionale su persone) |
| Risk scoring individuale (chi è pericoloso) | **ALTO RISCHIO** (Annex III, punto 6a) |
| Analisi anomalie aggregate (zona, non persona) | **MINIMO** (no classificazione individuale) |

---

## 3. Sistemi VIETATI per Minerva (Art. 5 — Inaccettable Risk)

L'articolo 5 vieta **categoricamente**, senza eccezioni:

### 3.1 Biometric categorization in base a caratteristiche sensibili
> "Sistemi AI che categorizzano individui in base a caratteristiche biometriche (es. etnia, genere, opinioni politiche, religione) inferite da immagini"

**Impatto Minerva:** Qualsiasi analisi delle caratteristiche fisiche dei soggetti ripresi per inferire appartenenza a gruppi è **vietata**.

### 3.2 Real-time remote biometric identification in spazi pubblici
> "L'uso in tempo reale di sistemi di identificazione biometrica a distanza per l'applicazione della legge in spazi pubblici"

**Impatto Minerva:** Il riconoscimento facciale in tempo reale tramite droni su spazi pubblici è **vietato**, salvo eccezioni tassative (ricerca terroristi, scomparsi, vittime, prevenzione attacchi imminenti — richiede autorizzazione giudiziaria preventiva).

**Eccezioni Art. 5, comma 2** (solo per LE — Law Enforcement):
- Ricerca persone scomparse
- Prevenzione attacco terroristico imminente
- Identificazione autore di reato specifico (lista tassativa)

### 3.3 Social scoring per autorità pubbliche
> "Valutazione o classificazione di persone fisiche basata su comportamento sociale o caratteristiche"

**Impatto Minerva:** Qualsiasi sistema che assegna un "punteggio di rischio" individuale basato su comportamento osservato è **vietato**.

### 3.4 Predictive policing individuale
> "Sistemi che fanno valutazioni del rischio individuale per valutare il rischio di commissione di reati futuri, basati unicamente su profilazione"

**Impatto Minerva:** Il modulo di predictive policing individuale è **vietato** se si basa su profilazione comportamentale senza elementi concreti.

---

## 4. Requisiti per Sistemi Alto Rischio (Annex III)

Se Minerva mantiene funzionalità di alto rischio (predictive anomaly detection, supporto decisionale LE), deve rispettare **tutti** i seguenti requisiti prima di agosto 2026:

### 4.1 Risk Management System (Art. 9)
- Sistema documentato di gestione rischi per l'intero ciclo di vita
- Valutazione e mitigazione dei rischi specifici per ogni deploy
- Testing su situazioni reali

### 4.2 Data Governance (Art. 10)
- Dataset di training documentati, bias valutati
- Dati rappresentativi della popolazione monitorata
- Procedure di data management e governance

### 4.3 Technical Documentation (Art. 11)
- Documentazione tecnica completa prima della messa in servizio
- Aggiornabile per ogni modifica sostanziale
- Conservata per 10 anni post-mercato

### 4.4 Record-keeping & Logging (Art. 12)
- Log automatici di tutte le operazioni (data, ora, input, output, decisioni)
- Capacità di tracciare ogni decisione ad alto rischio
- Conservazione log almeno per durata operativa + 6 mesi

### 4.5 Transparency & Information (Art. 13)
- Sistema deve indicare chiaramente che è AI
- Utenti (forze dell'ordine) devono ricevere istruzioni d'uso chiare
- Limitazioni e rischi documentati

### 4.6 Human Oversight (Art. 14)
- **Obbligo di supervisione umana** per ogni decisione ad alto rischio
- Possibilità di "stop" o override da parte dell'operatore umano
- Nessuna decisione automatica vincolante (solo supporto decisionale)

### 4.7 Accuracy, Robustness, Cybersecurity (Art. 15)
- Metriche di accuratezza definite e monitorate
- Resilienza ad adversarial attacks (droni facili da attaccare)
- Cybersecurity by design

### 4.8 Conformity Assessment (Art. 43)
- Per sistemi LE: **conformity assessment obbligatoria da notified body** (terza parte certificata)
- Costo stimato: €50.000–€200.000 per assessment completo
- Registrazione nel **database EU AI** (art. 71)

---

## 5. Facial Recognition — Regole Specifiche

| Scenario | Regola |
|----------|--------|
| FR real-time in spazio pubblico da autorità LE | **VIETATO** (salvo eccezioni Art. 5.2) |
| FR post-hoc (su video già registrato) | **ALTO RISCHIO** (Annex III) — richiede autorizzazione |
| FR per sicurezza privata (stadio, evento) | **ALTO RISCHIO** + GDPR biometrico |
| FR per riconoscimento proprietario dispositivo | **BASSO RISCHIO** (uso personale) |
| FR per catturare un ricercato specifico (mandato) | **ECCEZIONALMENTE CONSENTITO** con autorizzazione giudiziaria |

**Per Minerva:** Elimina FR real-time. Mantieni solo detection di comportamenti anomali anonimi (crowd density, unusual motion patterns) senza identificazione individuale.

---

## 6. Predictive Policing — Cosa È Legale

| Approccio | Legale? | Note |
|-----------|---------|------|
| Risk scoring individuale basato su profilazione | ❌ Vietato | Art. 5, comma 1d |
| Hotspot predittivo (zona, non persona) | ✅ Lecito | No Annex III se anonimo |
| Pattern anomalo aggregato (crowd behavior) | ✅ Lecito | Se non profila individui |
| Alert basato su evento specifico (rissa in corso) | ✅ Lecito | Rilevamento fatto, non predizione |
| Risk scoring basato su evidenza concreta | ⚠️ Lecito ma alto rischio | Annex III, supervisione obbligatoria |

**Versione Minerva conforme:** Sistema di rilevamento anomalie aggregate anonime + alert operatori umani che decidono. Niente risk scoring individuale.

---

## 7. GDPR Interplay

Il GDPR si applica in parallelo all'AI Act:

| Aspetto | Regola GDPR | Impatto Minerva |
|---------|-------------|-----------------|
| Dati biometrici (volti, impronte) | Art. 9: categorie speciali → consenso esplicito o base legale specifica | Facial recognition richiede base legale LE specifica |
| Dati di persone non sospettate | Principio di minimizzazione | Video droni devono essere cancellati se non rilevante |
| Retention video drone | Proporzionalità | Max 30-90 giorni salvo indagine |
| DPIA (Data Protection Impact Assessment) | Art. 35: obbligatorio per sorveglianza sistematica | Obbligatoria prima di ogni deploy Minerva |
| DPO (Data Protection Officer) | Art. 37: obbligatorio per trattamenti su larga scala | Necessario se Minerva monitora spazi pubblici ampi |

---

## 8. Compliance Roadmap per Minerva

### Ora (giugno 2026 — 2 mesi alla deadline)

**Azioni immediate:**
1. **Rimuovere o disabilitare** qualsiasi modulo di facial recognition real-time
2. **Rimuovere** modulo di risk scoring individuale basato su profilazione
3. **Documentare** l'architettura attuale del sistema in vista dell'assessment
4. **Nominare** un AI Responsible (persona interna o consulente)

### Entro agosto 2026

5. Completare il **Risk Management System** (documento formale)
6. Avviare la **Technical Documentation** (Annex IV)
7. Implementare **logging system** per tutte le operazioni
8. Definire **human oversight procedure** (chi approva ogni alert)
9. Eseguire **DPIA** per ogni città/area di deploy
10. Contattare un **Notified Body** per la conformity assessment (lista: https://ec.europa.eu/growth/tools-databases/nando/)

### Entro 2027

11. Ottenere **CE marking** per sistemi LE
12. **Registrazione** nel database EU AI (art. 71)
13. **Training** degli operatori (LE e gestori del sistema)

---

## 9. Costi Compliance Stimati (Startup/PMI)

| Voce | Costo stimato |
|------|--------------|
| Legal + policy review | €15.000–€30.000 |
| Technical documentation | €10.000–€25.000 |
| DPIA (per ogni città) | €5.000–€15.000 |
| Risk management system | €8.000–€20.000 |
| Notified body conformity assessment | €50.000–€200.000 |
| Logging infrastructure | €5.000–€15.000 (una tantum) |
| DPO (annual) | €20.000–€50.000/anno |
| **Totale primo anno** | **€113.000–€355.000** |

**Nota:** Queste cifre sono per un sistema "clean" senza FR e predictive policing individuale. Con quei moduli, il costo dell'assessment è molto più alto e l'approvazione incerta.

---

## 10. Versione Minerva Conforme — Architettura Suggerita

```
Sistema Minerva v2.0 (EU AI Act compliant)
│
├── LIVELLO 1 — SENSORI (droni)
│   ├── Video stream (anonimizzato in tempo reale)
│   ├── Thermal imaging
│   └── Crowd counting (numero persone, no ID)
│
├── LIVELLO 2 — ANALISI (AI, basso rischio)
│   ├── Crowd density mapping
│   ├── Unusual movement detection (aggregato)
│   ├── Object detection (veicoli, oggetti abbandonati)
│   └── NO facial recognition, NO individual tracking
│
├── LIVELLO 3 — ALERT (supporto, non decisione)
│   ├── Alert zone (area anomala, no persona specifica)
│   ├── Confidence score aggregato
│   └── Suggerimento azione (NON decisione vincolante)
│
└── LIVELLO 4 — UMANO (obbligatorio)
    ├── Operatore review ogni alert
    ├── Decisione finale sempre umana
    ├── Log ogni azione operatore
    └── Override possibile in ogni momento
```

Questa architettura evita Annex III e Art. 5, rimanendo in **rischio limitato** con requisiti compliance molto più leggeri.

---

*Fonti: EUR-Lex EU AI Act 2024/1689, EDPB Guidelines on Facial Recognition, European AI Office guidance 2025*
