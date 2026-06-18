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

*(nessun task pending — sistema ha eseguito tutti stanotte)*

---

## MEDIA PRIORITÀ

*(nessun task pending — sistema ha eseguito tutti stanotte)*

---

## BASSA PRIORITÀ

*(nessun task pending — sistema ha eseguito tutti stanotte)*

---

## COMPLETATI

- **[COMPLETATO] DOSSIER-011** — Monitor Proattivo Dossier & Email (Principio CT) → [output](output/task_output/DOSSIER-011-monitor-proattivo.md) *(2026-06-18)*
- **[COMPLETATO] ASBL-001** — Procedura registrazione SkyRights Foundation → [output](output/task_output/ASBL-001-procedura-registrazione.md) *(2026-06-18)*
- **[COMPLETATO] MAXAR-002** — Test API developers.maxar.com → [output](output/task_output/MAXAR-002-api-test-guide.md) *(2026-06-18)*
- **[COMPLETATO] PLANET-003** — Accesso Planet Labs Education & Research → [output](output/task_output/PLANET-003-accesso-ricerca.md) *(2026-06-18)*
- **[COMPLETATO] EU-FUNDING-004** — Fondi EU per tech umanitaria 2026-2027 → [output](output/task_output/EU-FUNDING-004-call-aperte.md) *(2026-06-18)*
- **[COMPLETATO] SKYID-005** — Analisi Privado ID per identità senza custodia → [output](output/task_output/SKYID-005-polygon-id-analisi.md) *(2026-06-18)*
- **[COMPLETATO] GENESI-006** — CadQuery esempi pratici per Pocket NC → [output](output/task_output/GENESI-006-cadquery-pocket-nc.md) *(2026-06-18)*
- **[COMPLETATO] MINERVA-007** — EU AI Act: obblighi per sistemi sicurezza urbana → [output](output/task_output/MINERVA-007-euaiact-sicurezza-urbana.md) *(2026-06-18)*
- **[COMPLETATO] SKYID-008** — Confronto provider identità digitale per rifugiati → [output](output/task_output/SKYID-008-confronto-provider.md) *(2026-06-18)*
- **[COMPLETATO] AVATAR-009** — Digital legacy solutions esistenti: analisi mercato → [output](output/task_output/AVATAR-009-digital-legacy-mercato.md) *(2026-06-18)*
- **[COMPLETATO] NAS-010** — Configurazione Synology DS223 per SDQ-1 → [output](output/task_output/NAS-010-ds223-configurazione.md) *(2026-06-18)*

---

*Gestito automaticamente da SDQ-1 agente_orario.py*
*Claudio Terzi [CT-LGAI-001] — aggiungere task direttamente in questo file*
