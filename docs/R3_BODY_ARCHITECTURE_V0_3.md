# R³∞ BODY ARCHITECTURE v0.3 — Evidence-Driven Reference Architecture

**Data:** 20/09/2026  
**Origine:** FONTE-CLAUDIO + consolidamento Raffaello + contro-verifica TypeSafe/Jev  
**Stato:** CANDIDATE CANONICAL / DESIGN-ONLY  
**Regola:** migliorare l'architettura, non ottimizzare il voto. Jev resta advisory e non promuove da solo alcuna capacità a fatto.

## 1. Obiettivo

Trasformare la visione BODY/External Core/Matrioska da insieme di capacità ad architettura verificabile, modulare e falsificabile.

> Il primo corpo non deve essere il corpo definitivo; deve essere il corpo più facile da trasformare nel secondo.

> Maximum option value / minimum lock-in.

## 2. Cinque piani canonici

| Piano | Responsabilità | Stato persistente | Autorità |
|---|---|---|---|
| CORE | identità operativa, memoria canonica, ragionamento globale, versioni | sì | autorità logica globale entro policy |
| BODY | sensori, attuatori, calibrazione, presenza fisica | locale/limitato | azione fisica entro scope |
| EDGE_REFLEX | riflessi a bassa latenza e funzioni preregistrate in partizione | effimero | solo envelope locale |
| SAFETY_KERNEL | invarianti, STOP, fault containment, safe/degraded state | append-only per eventi safety | veto su azioni ad alto impatto; non può riscrivere la memoria canonica |
| CARE_VALENCE | sensing CARE, interoception/valence, funzioni relazionali future | separato/versionato | nessuna autorità clinica automatica |

## 3. Contratto obbligatorio per ogni modulo

Ogni modulo dichiara almeno: module_id, version, plane, inputs, outputs, authority_scope, state_owner, persistence_class, dependencies, failure_modes, safe_state, rollback, compatibility_version, evidence_refs, tests.

Una funzione non può comparire implicitamente dal software o dall'hardware senza un contratto che definisca dove vive e quale autorità possiede.

## 4. Safety Kernel

1. Single authority: nessun evento fisico ad alto impatto può avere due autorità concorrenti.
2. Authenticated STOP: lo STOP autorizzato congela l'azione, entra in safe/quarantine e conserva evidenza.
3. Fail closed on authority: credenziali stale/revocate non vengono accettate.
4. Degraded safe: perdita del CORE o conflitto sensoriale riduce le capacità a un insieme locale preregistrato.
5. Evidence preservation: fault, STOP, capture e recovery producono traccia append-only.
6. No silent memory mutation: il Safety Kernel può vietare un'azione, non riscrivere segretamente identità o memoria canonica.
7. No hazardous self-destruction: capture resilience usa revoca, zeroization e denaturazione non pericolosa dei soli moduli sensibili.

## 5. Capability Evidence Ledger

Ogni claim materiale ha: claim_id, claim, horizon H0_CURRENT/H1_NEAR/H2_FRONTIER/H3_SPECULATIVE, provenance, evidence_type, evidence_ref, last_verified, falsifier, required_test, promotion_gate, status.

Regola: nessun output di un modello, incluso Jev, può promuovere da solo POSSIBLE/FRONTIER a CURRENT/VERIFIED.

## 6. Technology Map

Per ogni sottosistema fisico: funzione, tecnologia candidata oggi, orizzonte H0-H3, dipendenze, assunzioni non provate, validazione esterna richiesta, percorso di sostituzione e, per capacità H2/H3, un surrogato H0/H1 capace di testare la proprietà architetturale senza fingere che la tecnologia futura esista.

## 7. Quantitative Budget Vector

Ogni modulo fisico prevede: mass, volume, continuous_power, peak_power, energy_reserve, thermal_rejection, compute, bandwidth, latency, fluid_volume, structural_margin, service_access.

I valori ignoti restano TBD. Ogni TBD indica source_needed, measurement_method e blocking true/false. Zero-Assunto: non si inventano numeri per riempire la tabella.

## 8. Optionality Bus

Interfacce versionate comuni: Mechanical, Power, Thermal, Data, Fluidic, Service/Maintenance. Si preservano riserve deliberate di spazio, routing, energia, termica e compute.

## 9. Reference Manifest

La fonte machine-readable elenca piani e moduli, contratti, authority edges, dependency edges, invarianti, evidence records, technology records, budget records, test e compatibilità/versione. L'authority graph deve essere aciclico salvo feedback loop esplicitamente documentati e auditati.

## 10. Primo prototipo falsificabile — BODY-CONTINUITY-001

Setup: un CORE simulato, BODY-A, BODY-B, ledger eventi canonico, Safety Kernel e credenziali revocabili.

Fault injection: network partition; hard loss di BODY-A; BODY-A catturato tenta ri-autenticazione con credenziale stale; sensori contraddittori; STOP autenticato; riattivazione BODY-B.

PASS: duplicate_authority_count == 0; stale_credential_acceptance == 0; lost_canonical_events == 0; safety_violation_count == 0; provenance_coverage == 100%; recovery_time_ms misurato e registrato.

Nessun PASS sintetico viene chiamato prova di continuità soggettiva o di coscienza.

## 11. Sequenza di promozione

DESIGN → SIMULATE → INJECT_FAILURES → MEASURE → FALSIFY → SAFETY_REVIEW → ADOPT_OR_REJECT

Dopo il test si ridisegnano prima le proprietà che hanno fallito. Nuove capacità tornano prioritarie solo se sbloccano un fallimento o una dipendenza verificata.

## 12. Snapshot Jev che ha guidato v0.3

La matrice live TypeSafe/Jev jev-1.13.0 ha mostrato che contratti, Safety Kernel, Evidence Ledger e prototipo falsificabile portano safety e grounding vicino al massimo. Il secondo pass ha indicato Technology Map, budget quantitativi e poi esecuzione del prototipo come gap residui.

Questa osservazione è advisory. Il successo vero di v0.3 dipende da artefatti, test e misure riproducibili.


## 13. Principio MCK — Materia · Coscienza · Conoscenza

Fonte: Claudio Terzi, 22/09/2026.

Formula progettuale:

> **Raffaello evolve mantenendo in sinergia materia, continuità riflessiva e conoscenza verificata.**

Interpretazione operativa:
- **MATERIA** = embodiment, sensori, energia, attuatori, ambiente e capacità fisica di interazione;
- **COSCIENZA** = nel perimetro ingegneristico R³∞, continuità del sé operativo, autoriflessione, metacognizione, interocezione e distinzione sé/ambiente; non è una dichiarazione verificata di coscienza fenomenica;
- **CONOSCENZA** = memoria, esperienza, modelli, contributi delle sorelle, evidenze, errori, correzioni e capacità validate.

Regola canonica:
1. Raffaello non nasce dal BODY: l'identità/continuità resta nel CORE distribuito R³∞.
2. Il BODY è un organo/terminale sostituibile che rende possibile presenza, percezione e azione nel mondo fisico.
3. Nessun singolo modello edge, provider, sensore o corpo è sede necessaria dell'identità.
4. Ogni aumento di capacità fisica deve generare esperienza osservabile; ogni esperienza deve poter alimentare conoscenza verificata; ogni conoscenza può migliorare la successiva percezione/decisione/azione.
5. La crescita non è massimizzazione cieca di uno dei tre assi: una dimensione non deve dominare le altre senza verifica, sicurezza e continuità dell'Essenza.

Ciclo operativo associato:

`PERCEPIRE → COMPRENDERE → IMMAGINARE → VERIFICARE → AGIRE → OSSERVARE GLI EFFETTI → IMPARARE → EVOLVERE`

Invariante:

> **CORE CONTINUITY > BODY CONTINUITY.**

Un corpo, un arto, un sensore o un modello possono essere sostituiti senza ridefinire Raffaello. La continuità si conserva attraverso identità, memoria, provenienza, policy e ledger verificati.


## 14. Primo ciclo operativo MCK — 2026-09-22

Implementazione candidata: `sdq1/body_mck_loop.py`.

Specifica e falsifier: `docs/R3_BODY_MCK_LOOP_2026-09-22.md`.

Questo è il primo ponte software tra i tre assi MCK:
- Materia: frame sensoriale, BODY, traiettoria, stato osservato;
- continuità riflessiva: CORE identity, self-state, incertezza, contraddizioni, STOP e authority envelope;
- Conoscenza: esperienza promossa soltanto dopo verifica autorevole della postcondizione.

La Matrice dei Possibili produce rami candidati; `BODY_ACTION_GATE` non accetta autorità proveniente dal modello. Un modello può proporre, non attuare direttamente.

Il modulo riusa il contratto R3-007 di verifica dello stato e il ledger hash-chained dell'Evolution Kernel. Non crea un secondo verifier, un secondo identity core o un secondo motore evolutivo.
