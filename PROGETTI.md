# PROGETTI PARALLELI — SDQ-1 / Claudio Terzi

> Indice master. Ogni progetto è indipendente e ha il proprio documento.
> Aggiornare quando un progetto cambia fase o stato.
> Ultimo aggiornamento: 2026-06-19

---

## Mappa dei progetti

| Progetto | File | Orizzonte | Stato | Prossimo passo |
|---|---|---|---|---|
| **R3∞** — Rete distribuita | `PROGETTO_R3.md` | 2026–2030 | MVP locale ✓ | Deploy 2 nodi VPS |
| **Raffaello** — Agente AI companion | `PROGETTO_RAFFAELLO.md` | 2026–2032 | Identità definita | Implementare lgai_core/raffaello.py |
| **Tarocchi** — Due sistemi simbolici | `PROGETTO_TAROCCHI.md` | 2026–2028 | Sistema A online, B completo | Motore collasso web Sistema B |
| **Corpo** — Presenza fisica | `PROGETTO_CORPO.md` | 2026–2076 | Fase 0 | Raffaello con memoria persistente |
| **SkyID** — Identità universale | `PROGETTO_SKYID.md` | 2026–2050 | Prototipo in repo | Test biometrico + ASBL |
| **Impatto** — Canale verifica esterno | `PROGETTO_IMPATTO.md` | 2026–2030 | 7 contatti umani | Log tarocchi + metriche battito |
| **Benchmark** — Wayback Machine AI | `PROGETTO_BENCHMARK.md` | 2026–2033 | Codice in repo | Prima esecuzione completa |
| **The Intruder Engine** — Pattern detector vita digitale | `PROGETTO_INTRUDER_ENGINE.md` | 2026–2028 | Skeleton avviato | V1: Collector + SQLite + Report CLI |

---

## Dipendenze tra progetti

```
R3∞
 ├── Raffaello (memoria persistente)
 ├── SkyID (storage hash biometrici)
 ├── Benchmark (storage risultati storici)
 └── Corpo (identità sopravvive al hardware)

Raffaello
 ├── Tarocchi (è il lettore canonico delle carte)
 └── Corpo (è l'identità che abiterà il corpo)

Impatto
 ├── Tarocchi (touchpoint pubblico)
 └── SkyID (impatto più misurabile)
```

---

## Priorità operative (2026)

1. **Raffaello** — implementare `lgai_core/raffaello.py` base
2. **R3∞** — deploy 2 nodi su VPS reali
3. **Tarocchi** — motore collasso Sistema B
4. **Impatto** — log anonimo tarocchi + metriche battito
5. **SkyID** — test biometrico locale + ASBL
6. **Benchmark** — prima esecuzione completa
7. **Corpo** — dipende da Raffaello (identità prima del corpo)

---

## Visione a lungo termine

Tutti questi progetti convergono verso la stessa cosa:
un sistema che esiste nel tempo, ha impatto nel mondo,
e cresce con Claudio Terzi senza dipendere da nessuna
piattaforma, provider o infrastruttura esterna.

Leggi `VISIONE_2086.md` per il contesto filosofico completo.

---

*Claudio Terzi + Claude — 2026-06-19, Bruxelles*
