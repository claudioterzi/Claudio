# Normativa EU Droni — EASA 2026
*Aggiornato: giugno 2026*

---

## Il Framework EASA in Sintesi

L'EASA (European Union Aviation Safety Agency) regola tutti i droni nell'UE
con tre categorie di rischio crescente: **Open → Specific → Certified**.

---

## Categoria OPEN — Basso rischio, no autorizzazione

### Sottocategoria A1 — Volo vicino a persone
- Droni < 250g (classe C0) → nessuna licenza, solo registrazione operatore
- Droni 250g-900g (classe C1) → patentino online A1/A3 (test teorico gratuito)
- **Dove:** sopra persone non coinvolte, mai sopra assembramenti

### Sottocategoria A2 — Volo in prossimità di persone
- Droni 900g-4kg (classe C2)
- **Richiede:** patentino A2 (esame teorico + dichiarazione pratica) + assicurazione RC
- **Dove:** min 30m distanza orizzontale da persone (ridotto a 5m con modalità bassa velocità)

### Sottocategoria A3 — Lontano da persone
- Droni 900g-25kg (classi C3, C4)
- **Dove:** min 150m da aree residenziali, commerciali, industriali
- **Quota massima:** 120m AGL in tutte le sottocategorie Open

---

## Categoria SPECIFIC — Rischio moderato, autorizzazione richiesta

Operazioni che non rientrano in Open: volo notturno su aree urbane, oltre la linea visiva (BVLOS),
droni > 25kg, operazioni sopra assembramenti, uso di sensori speciali.

**Come si ottiene l'autorizzazione:**
1. SORA (Specific Operations Risk Assessment) — valutazione del rischio dell'operazione
2. Submission all'autorità nazionale (ENAC in Italia, DGTA in Belgio)
3. Approvazione con condizioni operative specifiche
4. Alternativa: STS (Standard Scenarios) predefiniti EASA → procedura semplificata

**Standard Scenarios più usati:**
- STS-01: VLOS urbano con drone < 3kg
- STS-02: BVLOS in area controllata con drone < 10kg

**Rilevanza per Sistema Minerva:** tutte le operazioni di sorveglianza urbana con Matrice 4T
o sistemi autonomi rientrano in Specific. Richiede SORA + autorizzazione DGTA Belgio.

---

## Categoria CERTIFIED — Alto rischio, equivalente aviazione civile

Richiesta per: droni che trasportano persone, droni cargo su aree urbane,
operazioni ad alto rischio per terzi, sistemi completamente autonomi su scala urbana.

**Richiede:** certificazione aeromobile + licenza pilota remoto professionale + 
approvazione operazioni caso per caso.

**Rilevanza per SDQ-1:** fase futura di Sistema Minerva se si scala a network autonomo
su intera città (es. Bruxelles). Da pianificare con 2-3 anni di anticipo.

---

## EU AI Act + Droni (2026)

L'EU AI Act del 2024, pienamente applicabile dal 2026, classifica i sistemi AI
sui droni in base al rischio:

| Sistema AI | Classificazione AI Act | Obbligo |
|---|---|---|
| Obstacle avoidance | Basso rischio | Solo trasparenza |
| Subject tracking | Medio rischio | Valutazione conformità |
| Riconoscimento facciale in pubblico | **Vietato** (Art. 5) | Non applicabile |
| Identificazione biometrica a distanza in tempo reale | **Vietato** (salvo eccezioni) | Solo forze dell'ordine con autorizzazione giudiziaria |
| Predizione comportamento folle/criminale | **Alto rischio** | Registrazione EUDRA + audit |

**Implicazione per Sistema Minerva:**
- Il tracking di persone specifiche in pubblico con AI è vietato senza autorizzazione giudiziaria
- Il rilevamento di anomalie comportamentali aggregate (non individui) → zona grigia, richiede legal review
- Il rilevamento termico (fonti di calore, non identità) → consentito categoria Specific

---

## Belgio — Regole Nazionali (DGTA)

L'autorità nazionale belga è la **DGTA** (Direction Générale Transport Aérien).

**Registrazione operatore:** obbligatoria su [regdrone.mobilit.belgium.be](https://regdrone.mobilit.belgium.be)

**Zona di Bruxelles:** area urbana densa → la maggior parte delle operazioni richiede
autorizzazione Specific anche sotto 120m. Il CTR (Controlled Traffic Region) di
Brussels Airport si estende su gran parte del territorio della Regione.

**Autorizzazione BVLOS Belgio:**
- Procedura tramite DGTA: ~6-12 settimane
- Richiede assicurazione RC minima € 750.000
- Per sistemi fissi (Dock) → autorizzazione di area, non per singola missione

---

## Checklist Operativa per Sistema Minerva a Bruxelles

```
□ Registrazione DGTA come operatore UAS (gratuita)
□ Patentino A2 per operazioni Standard
□ Assicurazione RC (minimo €750K per Specific)
□ SORA per le operazioni specifiche previste
□ Submission DGTA per autorizzazione Specific
□ Verifica EU AI Act compliance per il sistema di analisi
□ Legal opinion su rilevamento comportamentale aggregato
□ Eventuale notifica alla Commissione Privacy (APD belga)
   se i dati video vengono archiviati o analizzati
```

---

## Fonti

- [EASA Drone Regulations 2026 — Grupo One Air](https://www.grupooneair.com/new-easa-drone-regulations/)
- [EU EASA Categories — UAVMODEL](https://blog.uavmodel.com/eu-easa-drone-regulations-2026-open-category-c-class-markings-and-a1-a2-a3-subcategories-complete-fpv-guide/)
- [European Drone License — RotatePilot](https://rotatepilot.com/drone-pilot/european-union)
- [EASA Complete Guide — BeyondSky](https://beyondsky.xyz/blog/drone-regulations/easa-drone-regulations-complete-guide)
