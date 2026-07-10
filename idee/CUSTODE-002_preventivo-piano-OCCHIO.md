# CUSTODE-002 — OCCHIO: preventivo e piano d'azione

> Sottosistema di inventario fotografico di precisione a zone.
> Data: 2026-07-10. Riferimento tecnico: CUSTODE-001. Prototipo: `custode/`.
> Ipotesi di base: casa tipo 2 camere, ~30 zone d'inventario, ~100 turnover/anno.

---

## 1. Preventivo

### 1.1 Investimento iniziale (una tantum)

| Voce | Dettaglio | Costo |
|---|---|---:|
| Smartphone | quello dell'addetto pulizie: già disponibile | 0 € |
| Kit foto (opzionale) | luce LED portatile + supporto per inquadrature ripetibili | 30–80 € |
| Mappatura zone | definire le ~30 zone, scrivere le descrizioni-guida (2–3 h, Claudio+Code) | 0 € |
| Baseline fotografica | fotografare tutte le zone a casa in ordine (~2 h di lavoro) | 0–50 € |
| Software v0 | prototipo `custode/` già nel repo | 0 € |
| Sviluppo v1 (app foto guidate) | web-app mobile con overlay fantasma della baseline; sviluppo con Code | 0 € (tempo) |
| **Totale avvio** | | **30–130 €** |

### 1.2 Costi ricorrenti (per turnover)

Motore semantico su API Claude — stime per zona: foto ad alta risoluzione
≈ 1.600–4.800 token input + prompt ≈ 200 + risposta JSON ≈ 300 token output.

| Modello | Prezzo (in/out per M token) | Costo per zona | **Costo per turnover (30 zone)** |
|---|---|---:|---:|
| Haiku 4.5 | 1 $ / 5 $ | ~0,004 $ | **~0,12 $** |
| Sonnet 5 | 3 $ / 15 $ (intro 2/10 fino a 08/2026) | ~0,012 $ | **~0,35 $** |
| Batch API (−50%, risultati entro 1 h) | — | — | **~0,06–0,18 $** |

Strategia consigliata: **Haiku in Batch per il conteggio di routine**
(il turnover non è urgente al secondo), **Sonnet solo sulle zone con
discrepanza** per la doppia verifica. Costo annuo stimato (100 turnover):
**10–35 $ l'anno**. Il motore denso (CountGD++, v1) gira su GPU cloud a
consumo (~0,01 $/turnover) o in locale: trascurabile.

| Voce ricorrente | Anno |
|---|---:|
| API visione (100 turnover) | 10–35 $ |
| Tempo addetto pulizie (+10–15 min/turnover, se pagato extra) | 0–250 € |
| Rifacimento baseline (dopo modifiche arredo, 2×/anno) | 0 € (tempo) |
| **Totale ricorrente** | **~10–280 €/anno** |

### 1.3 Scenario property manager (10 case)

Avvio 300–1.300 € (kit + mappature), ricorrente 100–350 $/anno di API per
1.000 turnover. Il costo marginale per casa è quasi nullo: **il software
scala gratis** — è il punto di forza commerciale di OCCHIO.

---

## 2. Piano d'azione

### Fase 0 — Fondamenta (fatto ✅)
Prototipo `custode/`: modelli dati, motori di conteggio con fallback stub,
confronto baseline/check-out, report. Test 7/7, demo funzionante.

### Fase 1 — Pilota su casa reale (settimane 1–2)
1. Claudio sceglie la casa pilota e definisce con Code le ~30 zone
   (`Zona.id` + descrizione-guida per chi fotografa).
2. Baseline: giro fotografico completo, una foto per zona, luce costante.
3. Code collega `ContatoreClaude` alle foto reali (`ANTHROPIC_API_KEY`) e
   misura la precisione del conteggio zona per zona.
4. **Criterio di uscita**: ≥95% di conteggi corretti sulle zone di test;
   dove fallisce → zona più piccola o inquadratura più vicina.

### Fase 2 — Protocollo turnover (settimane 3–4)
1. Mini web-app mobile: elenco zone, foto guidata con overlay della
   baseline in trasparenza, upload.
2. Pipeline automatica: upload → conteggio (Haiku/Batch) → confronto →
   report con foto evidenza → notifica a Claudio.
3. Prova su 5 turnover reali (o simulati spostando oggetti apposta).
4. **Criterio di uscita**: 5 turnover con zero falsi negativi sugli
   oggetti rimossi di proposito; falsi positivi <10%.

### Fase 3 — Precisione sul denso (settimane 5–8)
1. Integrare CountGD++ / Grounding DINO per le zone dense (posate, libri).
2. Doppia passata: motore denso conta, VLM verifica e nomina.
3. Tuning soglie di allarme per zona (una posata mancante ≠ un quadro mancante).

### Fase 4 — Prodotto (mese 3+)
Multi-proprietà, storico per ospite, generazione automatica della pratica
di rimborso (foto prima/dopo + timestamp, formato richiesto da AirCover).
Qui OCCHIO si aggancia a SOGLIA (vedi CUSTODE-003) per l'evidenza doppia.

### Rischi e contromisure

| Rischio | Contromisura |
|---|---|
| Foto turnover mal inquadrate | overlay fantasma + rifiuto automatico foto troppo diverse dalla baseline |
| Luce variabile falsa i conteggi | luce LED fissa nel kit; scattare sempre con flash off e stessa ora se possibile |
| Oggetti in contenitori chiusi | protocollo "apri e fotografa" per i cassetti mappati; il resto è compito di SOGLIA |
| Costi API a sorpresa | budget cap + Batch + Haiku di default: il tetto naturale è ~3 $/mese/casa |

### Metriche di successo
- Precisione conteggio ≥95% per zona; falsi positivi <10% a regime.
- Tempo extra per turnover ≤15 minuti.
- 1 pratica di rimborso documentata con evidenza OCCHIO = ROI dimostrato
  (una sola trapunta o phon sparito ripaga anni di costi API).
