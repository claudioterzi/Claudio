# CANDIDATE — OmniRoute

**Stato:** CANDIDATE  
**Repository:** `diegosouzapw/OmniRoute`  
**Assegnazione primaria:** SDQ-1 / R³∞  
**Eredità potenziale:** Raffaello Creative Studio, solo se adottata a valle del router SDQ-1.

## Perché è candidata

OmniRoute si presenta come gateway AI multi-provider con un endpoint unificato. Le caratteristiche dichiarate nel repository che meritano verifica per SDQ-1 sono:

- routing multi-provider e strategie di fallback;
- scheduling consapevole delle quote;
- catalogo provider/modelli molto esteso;
- bridge multimodale per vision/audio/video;
- CLI e integrazione MCP;
- telemetria delle quote;
- meccanismi di compressione token;
- possibilità di esecuzione locale/private-first dichiarata dal progetto.

Queste sono **claim della repo esterna**, non capacità attribuite a R³∞.

## Ipotesi da testare

**H-OMNI-001** — alcuni pattern di routing/fallback di OmniRoute possono migliorare resilienza e costo del router SDQ-1 senza ridurre provenance, controllo o prevedibilità.

**H-OMNI-002** — la quota-aware scheduling può essere utile come segnale aggiuntivo nel provider selection di SDQ-1.

**H-OMNI-003** — il bridge multimodale può ridurre il numero di adapter specifici necessari al Creative Studio.

**H-OMNI-004** — la compressione token può produrre risparmio misurabile senza perdita significativa di qualità o contesto.

## Baseline A/B richiesta

Confrontare il router SDQ-1 corrente con una sandbox OmniRoute su un set fisso di richieste.

Misure minime:

1. successo/fallimento per provider;
2. latenza p50/p95;
3. costo o consumo quota;
4. qualità output secondo evaluator fissato;
5. perdita di contesto dovuta a compressione;
6. tracciabilità della scelta provider;
7. comportamento durante rate-limit/errori;
8. compatibilità con policy P5/P6 e Zero-Assunto;
9. privacy/segreti e superficie di sicurezza;
10. reversibilità dell'integrazione.

## Gate

`DISCOVERED → CANDIDATE → SANDBOX → BASELINE A/B → FALSIFICATION → AUDIT → ADOPTED / REJECTED`

Non sostituire il router SDQ-1 e non instradare traffico reale finché la candidate non supera i gate.

## Possibili esiti

- **ADOPT PATTERN** — importiamo solo algoritmi/pattern utili nel router esistente.
- **ADOPT ADAPTER** — OmniRoute resta servizio esterno dietro un adapter SDQ-1.
- **PARTIAL ADOPT** — ad esempio quota-aware scheduling o telemetry soltanto.
- **REJECT** — se complessità, sicurezza o perdita di controllo superano il beneficio.

## Primo test consigliato

Sandbox limitata a 2–3 provider già supportati da SDQ-1, con fallback forzato e quota simulata. Nessuna chiave di produzione e nessun traffico canonico.
