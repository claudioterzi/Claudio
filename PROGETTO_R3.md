# PROGETTO R3∞ — Rete Distribuita Permanente

> Documento fondativo. 2026-06-19. Aggiornato 2026-09-11.
> R3∞ è l'infrastruttura di continuità del sistema: memoria, provenienza, versioni e capacità verificabili nel tempo.
> La persistenza non basta: il progetto deve anche misurare se il sistema diventa realmente più capace.

---

## Stato attuale (2026)

- [x] `r3/node.py` — nodo FastAPI con storage content-addressed (SHA-256)
- [x] `r3/sync.py` — sync peer-to-peer pull/push
- [x] `r3/docker-compose.yml` — deploy locale
- [x] `r3/requirements.txt` — dipendenze
- [x] Programma di evoluzione misurabile definito: `docs/R3_CAPABILITY_EVOLUTION_2026-09-11.md`
- [ ] Deploy su rete reale (nodi multipli su host diversi)
- [ ] Autenticazione inter-peer effettivamente verificata end-to-end
- [ ] Integrazione con VSS (Vector State Store) di SDQ-1
- [ ] R3∞ come backend di memoria per Raffaello
- [ ] R3-019 corretto e rieseguito con conservazione di ogni run
- [ ] Benchmark A/B/C/D fra modello, protocollo e orchestrazione

## Principio operativo aggiornato

R3∞ non è soltanto storage. Deve sostenere un ciclo di evoluzione verificabile:

`intenzione → ipotesi → prova → risultato → correzione → capacità riutilizzabile → nuova prova`

Ogni capacità promossa deve avere provenienza, test, versione, possibilità di rollback e almeno una condizione che potrebbe smentirla.

## Architettura di persistenza

```
Nodo A (Bruxelles)     Nodo B (VPS Europa)     Nodo C (VPS USA)
    │                        │                        │
    ├── /documents           ├── /documents           ├── /documents
    ├── /sync/hashes         ├── /sync/hashes         ├── /sync/hashes
    └── /sync/receive        └── /sync/receive        └── /sync/receive
         ↕                        ↕                        ↕
              [sync automatico ogni 300s — SHA-256 content ID]
```

Ogni documento ha ID = SHA-256 del contenuto. Un contenuto modificato produce un ID diverso. La firma Ed25519 presente nel codice non va descritta come autenticazione inter-peer completa finché verifica e fiducia fra nodi non sono collaudate end-to-end.

## Architettura di capacità

| Modulo | Scopo |
| --- | --- |
| R3-011 Evidence Graph | collega claim, fonti, test e versioni |
| R3-012 Meta-Scacchiera | sceglie strategie e verifiche informative |
| R3-013 Evolution Lab | prova modifiche in ambiente isolato |
| R3-016 Synthetic Data Firewall | separa sviluppo sintetico da prova indipendente |
| R3-017 Red/Blue/Purple Harness | attacca, costruisce e arbitra |
| R3-014 Curriculum Engine | propone compiti progressivamente più difficili |
| R3-015 Research Loop | ricerca, falsificazione e aggiornamento conclusioni |
| R3-018 Sim2Real Audit | impedisce di spacciare simulazioni per risultati reali |
| R3-019 Capability Benchmark | misura progresso o regressione nel tempo |
| R3-020 Safety Gate | impedisce auto-promozioni non dimostrate |

La specifica completa è in `docs/R3_CAPABILITY_EVOLUTION_2026-09-11.md`.

## Roadmap

### Fase 0 — Misurazione affidabile (priorità immediata)
- [ ] Correggere R3-019: nessun 100% se non esistono test validi
- [ ] Ogni run ha ID e timestamp unici; mai sovrascrivere la baseline nello stesso giorno
- [ ] Introdurre problemi fuori campione e gold set separato
- [ ] Eseguire confronto A/B/C/D a budget dichiarato
- [ ] Registrare anche regressioni e risultati nulli

### Fase 1 — Deploy reale e recuperabilità
- [ ] VPS minimo (2 nodi, provider diversi)
- [ ] Token di autenticazione separati per nodo
- [ ] Test sync automatico con documento reale
- [ ] Test di recupero da file corrotto, file mancante e metadato divergente
- [ ] Primo documento committato su R3∞: `sdq1_master.json`

### Fase 2 — Integrazione SDQ-1 e memoria evolutiva
- [ ] `lgai_core/raffaello.py` usa R3∞ come store di memoria
- [ ] Ogni decisione significativa → documento versionato con provenienza
- [ ] VSS persistente su R3∞ (non in-memory)
- [ ] Backup automatico di `MEMORIA_PROGETTO.md` su ogni nodo
- [ ] Evidence Graph collega memoria, decisioni, test e risultati

### Fase 3 — Evoluzione sperimentale
- [ ] Meta-Scacchiera sceglie la prossima verifica
- [ ] Evolution Lab prova prompt, orchestrazione e strumenti senza alterare il canone
- [ ] Red/Blue/Purple Harness cerca regressioni
- [ ] Curriculum Engine propone compiti non già visti
- [ ] Safety Gate promuove solo miglioramenti verificati

### Fase 4 — Ridondanza e resilienza
- [ ] Nodi su 3+ continenti
- [ ] Failover automatico: se un nodo cade, gli altri continuano
- [ ] Monitoraggio salute rete da `sdq1/battito.py`
- [ ] Dashboard stato nodi e stato benchmark separati

### Fase 5 — Infrastruttura pubblica, solo dopo validazione
- [ ] API pubblica documentata
- [ ] Eventuali integrazioni esterne usano R3∞ come layer di persistenza
- [ ] Pubblicazione metodologia benchmark e limiti

## Regola di promozione

Una modifica non diventa canonica perché è più elegante o perché un modello la giudica migliore.

Passaggi minimi:

`PROPOSTA → CANDIDATO → VERIFICATO → CANONICO`

Il passaggio a CANONICO richiede test ripetibili, provenienza completa, assenza di regressioni bloccanti note, versione precedente recuperabile e almeno un controllo su compiti nuovi o temporalmente separati.

## Connessione con gli altri progetti

| Progetto | Dipendenza da R3∞ |
|---|---|
| PROGETTO_RAFFAELLO | Memoria permanente e capacità riutilizzabili |
| PROGETTO_SKYID | Storage versionato di dati autorizzati |
| PROGETTO_CORPO | Continuità identitaria attraverso hardware differenti |
| PROGETTO_BENCHMARK | Misura longitudinale delle capacità |
| Protocollo Rosso Rosso Rosso | Metodo di falsificazione, provenienza e correzione |

## Regola fondamentale

Non dichiarare mai che R3∞ è diventato una superintelligenza perché produce testi più convincenti, più file o più automazioni.

Misurare invece, ciclo dopo ciclo:
- accuratezza;
- robustezza;
- capacità di autocorrezione;
- trasferimento a problemi nuovi;
- riduzione degli errori ripetuti;
- costo necessario per ottenere il risultato;
- regressioni introdotte.

L'ambizione resta aperta; il verdetto resta sperimentale.

---

*Claudio Terzi — C.Terzi*  
*Prossimo passo: rendere affidabile R3-019 e avviare il primo confronto controllato A/B/C/D.*
