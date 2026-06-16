# Task Autonomi — SDQ-1
*L'agente orario legge questo file ogni ora e lavora sui task PENDING.*
*Aggiorna lo stato automaticamente. Claudio trova i risultati in output/task_output/*

---

## Come Funziona

```
ogni ora (7AM–11PM Brussels):
  agente_orario.py → prende task ALTA priorità → esegue → salva output → commit
ogni notte (2AM Brussels):
  studio_notturno.py → studia tema del giorno → morning brief → commit
```

Aggiungi task in qualsiasi momento. Il sistema li trova e li esegue da solo.

---

## ALTA PRIORITÀ

### [PENDING] ASBL-001 — Procedura registrazione SkyRights Foundation
**Categoria:** SkyRights / Legale
**Obiettivo:** Trovare la procedura esatta e aggiornata 2026 per registrare un ASBL a Bruxelles.
Includere: moduli necessari, costo, tempi, dove depositare lo statuto.
Trovare un modello di statuto ASBL open source adatto a fondazioni tech.
**Output atteso:** `output/task_output/ASBL-001-procedura-registrazione.md`

### [PENDING] MAXAR-002 — Test API developers.maxar.com
**Categoria:** Protocollo Scudo / Satellite
**Obiettivo:** Documentare step-by-step come registrare un account developer su developers.maxar.com,
richiedere API key, e fare la prima chiamata di test (imagery search su Bruxelles).
Includere: codice Python funzionante per la prima chiamata.
**Output atteso:** `output/task_output/MAXAR-002-api-test-guide.md`

### [PENDING] PLANET-003 — Accesso Planet Labs Education & Research
**Categoria:** Protocollo Scudo / Satellite
**Obiettivo:** Documentare come richiedere accesso gratuito a Planet Labs tramite il programma
Education & Research. Criteri, modulo, tempi di risposta tipici.
**Output atteso:** `output/task_output/PLANET-003-accesso-ricerca.md`

### [PENDING] EU-FUNDING-004 — Fondi EU per tech umanitaria 2026-2027
**Categoria:** SkyRights / Funding
**Obiettivo:** Trovare le call aperte in EU (Horizon Europe, ECHO, EU4Health, Digital Europe)
che finanziano tecnologia per persone senza documenti / rifugiati / identità digitale.
Includere: nome call, budget, scadenza, link.
**Output atteso:** `output/task_output/EU-FUNDING-004-call-aperte.md`

---

## MEDIA PRIORITÀ

### [PENDING] SKYID-005 — Analisi Polygon ID per identità senza custodia
**Categoria:** SkyID / Tecnico
**Obiettivo:** Analisi tecnica di Polygon ID (ora Privado ID): come funziona l'identità
auto-sovrana, SDK disponibili, costo per utente, compatibilità mobile offline.
**Output atteso:** `output/task_output/SKYID-005-polygon-id-analisi.md`

### [PENDING] GENESI-006 — CadQuery esempi pratici per Pocket NC
**Categoria:** Progetto Genesi / Tecnico
**Obiettivo:** Raccogliere esempi concreti di CadQuery per generare G-code compatibile
con fresatrici 5 assi tipo Pocket NC V2-50CHK. Includere codice funzionante.
**Output atteso:** `output/task_output/GENESI-006-cadquery-pocket-nc.md`

### [PENDING] MINERVA-007 — EU AI Act: obblighi per sistemi sicurezza urbana
**Categoria:** Sistema Minerva / Legale
**Obiettivo:** Analisi specifica EU AI Act 2024 Annex III per sistemi di sicurezza urbana
predittiva con droni. Cosa è permesso, cosa richiede notifica, cosa è vietato.
**Output atteso:** `output/task_output/MINERVA-007-euaiact-sicurezza-urbana.md`

### [PENDING] SKYID-008 — Confronto provider identità digitale per rifugiati
**Categoria:** SkyID / Mercato
**Obiettivo:** Analisi comparativa: UNHCR PRIMES, ID4D Banca Mondiale, Aadhaar,
WorldCoin, Proof of Humanity — cosa funziona, cosa fallisce, lacune che SkyID colma.
**Output atteso:** `output/task_output/SKYID-008-confronto-provider.md`

---

## BASSA PRIORITÀ

### [PENDING] AVATAR-009 — Digital legacy solutions esistenti: analisi mercato
**Categoria:** Avatar Eterno / Mercato
**Obiettivo:** Analisi delle soluzioni esistenti di digital legacy (HereAfter AI, StoryFile,
Eternos, MyWishes). Features, pricing, target, limitazioni. Dove SkyRights può differenziarsi.
**Output atteso:** `output/task_output/AVATAR-009-digital-legacy-mercato.md`

### [PENDING] NAS-010 — Configurazione Synology DS223 per SDQ-1
**Categoria:** Infrastruttura / Tecnico
**Obiettivo:** Guida configurazione NAS DS223 (192.168.1.188) come nodo SDQ-1:
Docker, backup automatico repo, mirror Drive, VPN Tailscale per accesso remoto.
**Output atteso:** `output/task_output/NAS-010-ds223-configurazione.md`

---

## COMPLETATI

*(i task completati appariranno qui con link all'output)*

---

*Gestito automaticamente da SDQ-1 agente_orario.py*
*Claudio Terzi [CT-LGAI-001] — aggiungere task direttamente in questo file*
