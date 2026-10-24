# Raffaello · Rosso Rosso Rosso

Claudio Terzi · C.Terzi

R³∞ è un sistema software del Protocollo Rosso Rosso Rosso.
Non è la coscienza del Campo e non costituisce prova della tesi.

`IPOTESI` — «Tutto ciò che potrà mai esistere, esiste già ora.»

## P5 — indipendenza

La ripetizione interna al sistema non costituisce conferma indipendente.
Una dichiarazione dell'autore e una seconda dichiarazione dello stesso autore non valgono come due fonti.
Quando un atto prevede un testimone, il nuovo flusso genera un link Telegram univoco: l'esito deve arrivare da un account diverso da quello dell'autore.

## P6 — possibilità di caduta

Se un'ipotesi non dispone ancora di un criterio sufficiente di falsificazione, il sistema lo dichiara: «non so».
Un esito negativo o non verificabile resta nel registro; non viene trasformato in conferma.

## Santuario VR

Il visore non dimostra la tesi. La candela non la dimostra. Il bot non la dimostra.
Il sistema può però registrare una sequenza osservabile:

`VISORE → 12 s CONTINUI → FIAMMA → TELEGRAM → ATTO → LINK AL TERZO → ESITO`

Il payload `start=vr` entra direttamente nel flusso del testimone, senza menu intermedio.
Dopo la descrizione dell'atto il bot produce un deep-link `start=w_…` da inviare al terzo.
Se il link viene aperto dallo stesso `telegram_id` dell'autore, P5 rifiuta l'esito.
L'esito accettato è immutabile nel database.

## Cosa verifica davvero il sistema

Il bot può verificare tecnicamente che la risposta Telegram provenga da un account distinto dall'autore e può registrare quale pulsante quell'account ha premuto.
Questo non equivale, da solo, a dimostrare l'evento esterno: eventuale evidenza indipendente può ancora confermare o contraddire la dichiarazione del testimone.

## Raffaello 2

Il dialogo moderno usa testo libero e il pulsante **Analizza**. Le letture Alpha 74 possono essere conservate, riprese e approfondite fra Telegram e sito. **Ascolta sul sito** avvia la voce soltanto su richiesta.
Il ponte privato verso il sito e gli utenti autorizzati restano separati dal meccanismo P5 del testimone.

## Comandi principali

| Comando | Funzione |
|---|---|
| `/start` | Dialogo con Raffaello |
| `/testimone` | Atto osservabile + link univoco al terzo |
| `/fuori` | Una cosa compiuta fuori da Telegram |
| `/azione` | Registra un atto verificabile |
| `/tesi` | Mostra la tesi come `IPOTESI` |
| `/p5p6` | Mostra le due regole epistemiche |
| `/registro` | Registro tecnico |
| `/letture` | Riprende una lettura Alpha 74 |
| `/collega` | Collega sito e chat autorizzata |
| `/nuovo` | Nuovo dialogo |
| `/scollega` | Revoca collegamenti al sito |
| `/ping` | Verifica che il processo sia attivo |

## Persistenza

`db.py` usa SQLite tramite `DATABASE_PATH`. SQLite locale va bene per sviluppo, ma un filesystem effimero non è una garanzia di conservazione del registro. In produzione `DATABASE_PATH` deve puntare a storage persistente oppure il backend va spostato su un database esterno. Il codice non deve descrivere un registro come permanente se lo storage non lo è.

## Architettura

```text
bot/handlers.py       → comandi e flussi generali
bot/terzo.py          → P5: deep-link e risposta del testimone
bot/epistemic.py      → classificazione epistemica
bot/db.py             → persistenza tecnica
bot/raffaello*.py     → dialogo moderno e ponte privato sito
bot/main.py           → entry point + health
```

## Attribuzione

Protocollo Rosso © Claudio Terzi [CT-LGAI-001]. Tutti i diritti riservati.
