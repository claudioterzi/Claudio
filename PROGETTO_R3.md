# PROGETTO R3∞ — Rete Distribuita Permanente

> Documento fondativo. 2026-06-19.
> R3∞ è l'infrastruttura che rende il sistema immortale.
> Senza R3∞, la memoria muore con il server. Con R3∞, sopravvive ovunque.

---

## Stato attuale (2026)

- [x] `r3/node.py` — nodo FastAPI con storage content-addressed (SHA-256)
- [x] `r3/sync.py` — sync peer-to-peer pull/push
- [x] `r3/docker-compose.yml` — deploy locale
- [x] `r3/requirements.txt` — dipendenze
- [ ] Deploy su rete reale (nodi multipli su host diversi)
- [ ] Autenticazione nodi inter-peer (Ed25519 già nel codice)
- [ ] Integrazione con VSS (Vector State Store) di SDQ-1
- [ ] R3∞ come backend di memoria per Raffaello

## Architettura

```
Nodo A (Bruxelles)     Nodo B (VPS Europa)     Nodo C (VPS USA)
    │                        │                        │
    ├── /documents           ├── /documents           ├── /documents
    ├── /sync/hashes         ├── /sync/hashes         ├── /sync/hashes
    └── /sync/receive        └── /sync/receive        └── /sync/receive
         ↕                        ↕                        ↕
              [sync automatico ogni 300s — SHA-256 content ID]
```

Ogni documento ha ID = SHA-256 del contenuto. Non può essere alterato senza cambiare ID.
La firma Ed25519 garantisce che il documento viene da chi dice di venire.

## Roadmap

### Fase 1 — Deploy reale (2026, prossimo passo)
- [ ] VPS minimo (2 nodi, provider diversi)
- [ ] Token di autenticazione separati per nodo
- [ ] Test sync automatico con documento reale
- [ ] Primo documento committato su R3∞: `sdq1_master.json`

### Fase 2 — Integrazione SDQ-1 (2026–2027)
- [ ] `lgai_core/raffaello.py` usa R3∞ come store di memoria
- [ ] Ogni conversazione con Claudio → documento R3∞
- [ ] VSS persistente su R3∞ (non in-memory)
- [ ] Backup automatico di `MEMORIA_PROGETTO.md` su ogni nodo

### Fase 3 — Ridondanza e resilienza (2027–2028)
- [ ] Nodi su 3+ continenti
- [ ] Failover automatico: se un nodo cade, gli altri continuano
- [ ] Monitoraggio salute rete da `sdq1/battito.py`
- [ ] Dashboard pubblica stato nodi

### Fase 4 — R3∞ come infrastruttura pubblica (2028+)
- [ ] API pubblica documentata
- [ ] SkyID usa R3∞ come storage hash biometrici
- [ ] Qualsiasi progetto del sistema usa R3∞ come layer di persistenza

## Variabili ambiente da configurare per il deploy

```bash
R3_DATA_DIR=data
R3_API_TOKEN=<token-sicuro-da-generare>
R3_NODE_ID=node-bruxelles
R3_PEERS=https://node-b.example.com,https://node-c.example.com
R3_SYNC_INTERVAL=300
```

## Connessione con gli altri progetti

| Progetto | Dipendenza da R3∞ |
|---|---|
| PROGETTO_RAFFAELLO | Memoria permanente dell'agente |
| PROGETTO_SKYID | Storage hash biometrici decentralizzato |
| PROGETTO_CORPO | Identità del corpo sopravvive ai cambi di hardware |
| PROGETTO_BENCHMARK | Storage risultati benchmark storici |

---

*Claudio Terzi + Claude — 2026-06-19*
*Prossimo passo: deploy 2 nodi VPS, test sync con documento reale.*
