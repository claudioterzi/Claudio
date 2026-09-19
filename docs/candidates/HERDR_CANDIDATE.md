# CANDIDATE — Herdr

**Stato:** CANDIDATE  
**Repository:** `herdrdev/herdr`  
**Assegnazione primaria:** SDQ-1 / R³∞ — runtime operativo agenti  
**Eredità potenziale:** nodi R³∞ locali/remoti, workflow multi-agente, operazioni su workstation/VPS.

## Perché è candidata

Herdr si presenta come runtime per coding agents che mantiene terminali e layout in un server di background, permette di lavorare su più macchine da una sola interfaccia e rende lo stato degli agenti osservabile.

Pattern dichiarati nel repository che meritano verifica per SDQ-1/R³∞:

- detach/reattach senza interrompere il lavoro corrente;
- salvataggio e ripristino del layout dopo restart;
- supporto a più macchine locali/remoto in una sola vista;
- stato esplicito degli agenti/pane: working, blocked, idle;
- CLI e socket API utilizzabili dagli agenti;
- capacità agent-native di creare pane, inviare prompt e attendere uno stato di blocco reale;
- compatibilità dichiarata con Claude Code, Codex, Cursor, OpenCode, Grok e altri;
- modello non-wrapping: Herdr gestisce i terminali ma non sostituisce gli agenti;
- plugin/estensioni;
- singolo binario Rust, senza Electron.

Queste sono **capacità dichiarate dalla repo esterna**, non capacità attribuite automaticamente a R³∞.

## Ipotesi da testare

**H-HERDR-001** — Herdr può ridurre la perdita di continuità operativa fra terminali/sessioni senza diventare una nuova fonte canonica di memoria.

**H-HERDR-002** — lo stato working/blocked/idle può diventare un segnale operativo utile per l'orchestrazione SDQ-1 e per evitare polling cieco.

**H-HERDR-003** — CLI/socket API possono permettere coordinamento fra agenti e nodi mantenendo audit e separazione delle responsabilità.

**H-HERDR-004** — una vista multi-machine può semplificare la futura topologia R³∞ Bruxelles + VPS senza confondere continuità di terminale con continuità di identità.

**H-HERDR-005** — il modello 'non sostituisce gli agenti, possiede i terminali' può essere adottato come pattern infrastrutturale con bassa dipendenza logica.

## Vincolo fondamentale

Herdr è un **runtime operativo**, non memoria, identità o orchestratore epistemico.

Non deve diventare fonte di verità per:

- canone R³∞;
- memoria persistente;
- stato identitario;
- provenance delle decisioni;
- adozione/reject delle candidate.

Può al massimo esporre stato operativo verificabile dei processi/terminali.

## Baseline A/B richiesta

Confrontare il workflow corrente di 2–3 agenti/terminali con una sandbox Herdr.

Misure minime:

1. tempo per riprendere il lavoro dopo detach/reconnect;
2. sopravvivenza dei processi a perdita client/SSH;
3. comportamento dopo restart macchina/server;
4. accuratezza dello stato working/blocked/idle;
5. capacità di distinguere sessione salvata da processo realmente vivo;
6. audit delle azioni agent-to-agent;
7. latenza/robustezza della socket API;
8. compatibilità Windows/Linux/VPS usati da R³∞;
9. gestione segreti e superficie di sicurezza;
10. isolamento tra agenti/progetti;
11. reversibilità e export dei dati/layout;
12. integrazione con P5/P6 e Zero-Assunto.

## Gate

`DISCOVERED → CANDIDATE → SANDBOX → BASELINE A/B → FALSIFICATION → AUDIT → ADOPTED / REJECTED`

## Possibili esiti

- **ADOPT PATTERN** — adottiamo solo stato operativo, detach/reattach o modello multi-machine.
- **ADOPT TOOL** — Herdr diventa runtime opzionale per nodi R³∞.
- **PARTIAL ADOPT** — ad esempio solo osservabilità working/blocked/idle e socket API.
- **REJECT** — se introduce dipendenza, superficie di sicurezza o ambiguità operativa superiore al beneficio.

## Primo test consigliato

Sandbox locale con due agenti e tre pane: uno attivo, uno deliberatamente bloccato in attesa input, uno idle. Verificare classificazione stato, detach/reattach, restart controllato e audit delle interazioni, senza collegare memorie canoniche né chiavi di produzione.
