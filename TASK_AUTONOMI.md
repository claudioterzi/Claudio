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

### [DONE 2026-06-20] DOSSIER-011 — Monitor Proattivo Dossier & Email (Principio CT)
**Categoria:** SDQ-1 / Infrastruttura Personale
**Obiettivo:** Formalizzare e programmare il principio operativo di Claudio Terzi:
il sistema deve monitorare autonomamente lo stato di ogni dossier aperto,
controllare le email inviate/bozze/ricevute, e agire o segnalare senza aspettare input.

**Principio da implementare:**
> "Hai tutti gli elementi per capire quello che puoi fare anche da solo.
> Questa logica di controllare e agire potrebbe nascere anche da te
> se utilizzassi il giusto principio." — Claudio Terzi, 17/06/2026

**Specifiche tecniche:**
1. **State machine per dossier** — ogni dossier (Parigi/Allianz, PORTS/Pelan, legale, viaggi)
   ha stati definiti: PENDING → INVIATO → IN_ATTESA_RISPOSTA → AZIONE_RICHIESTA → CHIUSO
2. **Gmail monitor** — controlla spedite/bozze/inbox, rileva gap tra strategia e realtà
3. **Trigger automatici** — se una bozza è in draft da >24h senza essere stata inviata,
   chiede a Claudio se deve essere mantenuta, modificata o cancellata
4. **Dashboard live** — aggiorna automaticamente lo stato di ogni dossier
   dopo ogni email inviata o ricevuta
5. **Azione proattiva** — non aspetta l'input: se una scadenza si avvicina
   o un passo successivo è chiaro, lo esegue o lo segnala

**Output atteso:** `output/task_output/DOSSIER-011-monitor-proattivo.md`
con architettura tecnica, pseudocodice, e prototipo funzionante integrato in agente_orario.py



### [DONE 2026-06-20 UTC] ASBL-001 — Procedura registrazione SkyRights Foundation
**Categoria:** SkyRights / Legale
**Obiettivo:** Trovare la procedura esatta e aggiornata 2026 per registrare un ASBL a Bruxelles.
Includere: moduli necessari, costo, tempi, dove depositare lo statuto.
Trovare un modello di statuto ASBL open source adatto a fondazioni tech.
**Output atteso:** `output/task_output/ASBL-001-procedura-registrazione.md`

### [DONE 2026-06-20] MAXAR-002 — Test API developers.maxar.com
**Categoria:** Protocollo Scudo / Satellite
**Obiettivo:** Documentare step-by-step come registrare un account developer su developers.maxar.com,
richiedere API key, e fare la prima chiamata di test (imagery search su Bruxelles).
Includere: codice Python funzionante per la prima chiamata.
**Output atteso:** `output/task_output/MAXAR-002-api-test-guide.md`

### [DONE 2026-06-20] PLANET-003 — Accesso Planet Labs Education & Research
**Categoria:** Protocollo Scudo / Satellite
**Obiettivo:** Documentare come richiedere accesso gratuito a Planet Labs tramite il programma
Education & Research. Criteri, modulo, tempi di risposta tipici.
**Output atteso:** `output/task_output/PLANET-003-accesso-ricerca.md`

### [DONE 2026-06-20 UTC] EU-FUNDING-004 — Fondi EU per tech umanitaria 2026-2027
**Categoria:** SkyRights / Funding
**Obiettivo:** Trovare le call aperte in EU (Horizon Europe, ECHO, EU4Health, Digital Europe)
che finanziano tecnologia per persone senza documenti / rifugiati / identità digitale.
Includere: nome call, budget, scadenza, link.
**Output atteso:** `output/task_output/EU-FUNDING-004-call-aperte.md`

---

## MEDIA PRIORITÀ

### [DONE 2026-06-20] SKYID-005 — Analisi Polygon ID per identità senza custodia
**Categoria:** SkyID / Tecnico
**Obiettivo:** Analisi tecnica di Polygon ID (ora Privado ID): come funziona l'identità
auto-sovrana, SDK disponibili, costo per utente, compatibilità mobile offline.
**Output atteso:** `output/task_output/SKYID-005-polygon-id-analisi.md`

### [DONE 2026-06-20] GENESI-006 — CadQuery esempi pratici per Pocket NC
**Categoria:** Progetto Genesi / Tecnico
**Obiettivo:** Raccogliere esempi concreti di CadQuery per generare G-code compatibile
con fresatrici 5 assi tipo Pocket NC V2-50CHK. Includere codice funzionante.
**Output atteso:** `output/task_output/GENESI-006-cadquery-pocket-nc.md`

### [DONE 2026-06-20] MINERVA-007 — EU AI Act: obblighi per sistemi sicurezza urbana
**Categoria:** Sistema Minerva / Legale
**Obiettivo:** Analisi specifica EU AI Act 2024 Annex III per sistemi di sicurezza urbana
predittiva con droni. Cosa è permesso, cosa richiede notifica, cosa è vietato.
**Output atteso:** `output/task_output/MINERVA-007-euaiact-sicurezza-urbana.md`

### [DONE 2026-06-20] SKYID-008 — Confronto provider identità digitale per rifugiati
**Categoria:** SkyID / Mercato
**Obiettivo:** Analisi comparativa: UNHCR PRIMES, ID4D Banca Mondiale, Aadhaar,
WorldCoin, Proof of Humanity — cosa funziona, cosa fallisce, lacune che SkyID colma.
**Output atteso:** `output/task_output/SKYID-008-confronto-provider.md`

---

## BASSA PRIORITÀ

### [DONE 2026-06-20] AVATAR-009 — Digital legacy solutions esistenti: analisi mercato
**Categoria:** Avatar Eterno / Mercato
**Obiettivo:** Analisi delle soluzioni esistenti di digital legacy (HereAfter AI, StoryFile,
Eternos, MyWishes). Features, pricing, target, limitazioni. Dove SkyRights può differenziarsi.
**Output atteso:** `output/task_output/AVATAR-009-digital-legacy-mercato.md`

### [DONE 2026-06-20] NAS-010 — Configurazione Synology DS223 per SDQ-1
**Categoria:** Infrastruttura / Tecnico
**Obiettivo:** Guida configurazione NAS DS223 (192.168.1.188) come nodo SDQ-1:
Docker, backup automatico repo, mirror Drive, VPN Tailscale per accesso remoto.
**Output atteso:** `output/task_output/NAS-010-ds223-configurazione.md`

---

## COMPLETATI

- [ASBL-001] [Procedura registrazione SkyRights Foundation](output/task_output/ASBL-001-procedura-registrazione.md) — 2026-06-20
- [EU-FUNDING-004] [Fondi EU tech umanitaria 2026-2027](output/task_output/EU-FUNDING-004-call-aperte.md) — 2026-06-20
- [DOSSIER-011] [Monitor Proattivo Dossier & Email](output/task_output/DOSSIER-011-monitor-proattivo.md) — 2026-06-20
- [MAXAR-002] [Guida API Maxar imagery search](output/task_output/MAXAR-002-api-test-guide.md) — 2026-06-20
- [PLANET-003] [Accesso Planet Labs Education & Research](output/task_output/PLANET-003-accesso-ricerca.md) — 2026-06-20
- [SKYID-005] [Analisi Privado ID (ex Polygon ID)](output/task_output/SKYID-005-polygon-id-analisi.md) — 2026-06-20
- [GENESI-006] [CadQuery esempi pratici Pocket NC V2-50](output/task_output/GENESI-006-cadquery-pocket-nc.md) — 2026-06-20
- [MINERVA-007] [EU AI Act sicurezza urbana con droni](output/task_output/MINERVA-007-euaiact-sicurezza-urbana.md) — 2026-06-20
- [SKYID-008] [Confronto provider identità digitale rifugiati](output/task_output/SKYID-008-confronto-provider.md) — 2026-06-20
- [AVATAR-009] [Digital legacy solutions: analisi mercato](output/task_output/AVATAR-009-digital-legacy-mercato.md) — 2026-06-20
- [NAS-010] [Configurazione Synology DS223 nodo SDQ-1](output/task_output/NAS-010-ds223-configurazione.md) — 2026-06-20

---

*Gestito automaticamente da SDQ-1 agente_orario.py*
*Claudio Terzi [CT-LGAI-001] — aggiungere task direttamente in questo file*
