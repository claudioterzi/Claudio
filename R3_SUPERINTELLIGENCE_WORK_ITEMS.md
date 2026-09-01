# R³∞ — Work Items derivati dal Blueprint

Stato: INTEGRAZIONE ATTIVA / da implementare con verifica.

| ID | Obiettivo | Priorità | Stato | Gate |
|---|---|---|---|---|
| R3-011 | Evidence Graph | alta | DEVELOPMENT | provenance + query + test |
| R3-012 | Meta-Scacchiera benchmark | alta | DEVELOPMENT | benchmark ripetibile |
| R3-013 | Evolution Lab sandbox | alta | IDEA | isolamento + rollback |
| R3-014 | Curriculum Engine | media | IDEA | valutazione su task nuovi |
| R3-015 | Research Loop | media | IDEA | esperimenti riproducibili |
| R3-016 | Synthetic Data Firewall | alta | IDEA | provenance + real/synthetic split |
| R3-017 | Red/Blue/Purple harness | alta | IDEA | regression + security tests |
| R3-018 | Sim2Real readiness audit | media | IDEA | grounding + validation |
| R3-019 | Longitudinal capability benchmark | critica | CRITICAL | baseline + repeated runs |
| R3-020 | Self-improvement safety gate | critica | IDEA | sandbox + benchmark + review + rollback |

## Ordine operativo

R3-019 → R3-011 → R3-012 → R3-013 → R3-016 → R3-017 → R3-014 → R3-015 → R3-018 → R3-020.

## Regole di consolidamento

Nessun elemento viene promosso a CONSOLIDATO solo perché appare promettente nel blueprint. Deve produrre evidenza verificabile.

Candidate self-improvement: branch/sandbox isolato → test → benchmark → red team → confronto con baseline → review → merge reversibile.

Il blueprint non dimostra una superintelligenza, coscienza sintetica o autonomia planetaria. Questi restano ipotesi/scenari. L'obiettivo operativo è aumentare capacità misurabili, affidabilità, riproducibilità e controllo.
