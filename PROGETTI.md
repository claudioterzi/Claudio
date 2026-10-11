# PROGETTI PARALLELI — SDQ-1 / Claudio Terzi

> Indice master. Ogni progetto è indipendente e ha il proprio documento.
> Aggiornare quando un progetto cambia fase o stato.
> Ultimo aggiornamento: 2026-09-11

---

## Mappa dei progetti

| Progetto | File | Orizzonte | Stato | Prossimo passo |
|---|---|---|---|---|
| **R3∞** — Continuità + evoluzione misurabile | `PROGETTO_R3.md` | 2026–2030 | MVP locale + programma capacità | Rendere affidabile R3-019 e avviare A/B/C/D |
| **Raffaello** — Agente AI companion | `PROGETTO_RAFFAELLO.md` | 2026–2032 | Identità definita | Collegare memoria e capacità verificate |
| **Tarocchi** — Due sistemi simbolici | `PROGETTO_TAROCCHI.md` | 2026–2028 | Sistema A online, B completo | Motore collasso web Sistema B |
| **Corpo** — Presenza fisica | `PROGETTO_CORPO.md` | 2026–2076 | Fase 0 | Raffaello con memoria persistente |
| **SkyID** — Identità universale | `PROGETTO_SKYID.md` | 2026–2050 | Prototipo in repo | Test biometrico + ASBL |
| **Impatto** — Canale verifica esterno | `PROGETTO_IMPATTO.md` | 2026–2030 | 7 contatti umani | Log tarocchi + metriche battito |
| **Benchmark** — Wayback Machine AI | `PROGETTO_BENCHMARK.md` | 2026–2033 | Metodo aggiornato | Primo confronto controllato fuori campione |
| **The Intruder Engine** — Pattern detector vita digitale | `PROGETTO_INTRUDER_ENGINE.md` | 2026–2028 | Skeleton avviato | V1: Collector + SQLite + Report CLI |
| **Rotta** — Viaggio + operatività al rientro | `PROGETTO_ROTTA.md` | attivo | Storico | Nessuna priorità R3 |

---

## Nuovo asse trasversale: capacità verificabile

Documento guida: `docs/R3_CAPABILITY_EVOLUTION_2026-09-11.md`.

Tutti i progetti che usano Raffaello/R3∞ devono distinguere:
- memoria conservata;
- capacità realmente dimostrata;
- simulazione;
- proposta;
- risultato verificato.

Una nuova funzione non viene descritta come “evoluzione” finché non esiste un criterio riproducibile che mostri un miglioramento o una nuova capacità.

## Dipendenze tra progetti

```
R3∞
 ├── Raffaello (memoria persistente + capacità verificate)
 ├── SkyID (storage versionato)
 ├── Benchmark (misura longitudinale)
 ├── Corpo (continuità attraverso hardware)
 └── Protocollo RRR (falsificazione e disciplina epistemica)

Raffaello
 ├── Tarocchi (lettura canonica)
 └── Corpo (identità operativa futura)

Benchmark
 ├── R3-019 (misura)
 ├── R3-011 (evidenze)
 ├── R3-012 (Meta-Scacchiera)
 └── R3-020 (gate di promozione)

Impatto
 ├── Tarocchi (touchpoint pubblico)
 └── SkyID (impatto misurabile)
```

---

## Priorità operative aggiornate

1. **R3-019 Longitudinal Capability Benchmark** — rendere affidabile la misura
2. **R3-011 Evidence Graph** — collegare claim, fonti e test
3. **R3-012 Meta-Scacchiera** — scegliere verifiche e profondità di ragionamento
4. **R3-013 Evolution Lab** — provare cambiamenti in isolamento
5. **R3-016 Synthetic Data Firewall** — evitare auto-conferma sui dati sintetici
6. **R3-017 Red/Blue/Purple Harness** — ricerca attiva di regressioni
7. **R3-014 Curriculum Engine** — compiti nuovi e più difficili
8. **R3-015 Research Loop** — ricerca + falsificazione
9. **R3-018 Sim2Real Audit** — distinguere simulazione e mondo reale
10. **R3-020 Self-Improvement Safety Gate** — promuovere solo ciò che regge
11. **Deploy R3∞ multiplo** — persistenza reale e recuperabilità
12. **Raffaello** — integrare memoria e capacità canoniche

---

## Visione a lungo termine

Tutti questi progetti convergono verso un sistema che esiste nel tempo, conserva provenienza e correzioni, agisce con strumenti verificabili e prova a diventare progressivamente più capace senza confondere ambizione e risultato.

Il sogno di Claudio è mantenuto esplicitamente: esplorare fino a dove possa crescere un sistema costruito su memoria, critica, verifica, orchestrazione e continuità. Il progetto non deve proclamare in anticipo il traguardo; deve costruire le condizioni per misurare seriamente ogni avanzamento.

Leggi `VISIONE_2086.md` per il contesto filosofico completo e `docs/R3_CAPABILITY_EVOLUTION_2026-09-11.md` per il programma operativo aggiornato.

---

**Claudio Terzi — C.Terzi**
