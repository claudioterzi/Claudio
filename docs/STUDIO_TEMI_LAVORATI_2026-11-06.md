# Studio Notturno: rinnovo dei temi già lavorati

Data: 6 novembre 2026. Classificazione retroattiva: **PATCH** del selettore;
**RETEST** delle affermazioni contenute nei dossier storici.

## Richiesta e perimetro

La scelta dei temi non segue più il giorno della settimana. Il rinnovo resta
limitato ai temi già lavorati, con riscontro nei dossier completati.
I dossier del 20 giugno sono conservati intatti: né una voce DONE né un vecchio
link dimostrano che prezzi, norme, servizi o bandi siano ancora attuali.

Il catalogo ammesso è `studio/temi_lavorati.json`:

- SkyID: SKYID-005, SKYID-008.
- Scudo: MAXAR-002, PLANET-003.
- Minerva: MINERVA-007.
- Genesi: GENESI-006.
- SkyRights: ASBL-001, EU-FUNDING-004.
- Avatar: AVATAR-009.

I dossier NAS-010 e DOSSIER-011 restano nell'archivio consultabile, ma non hanno
un percorso di ricerca dedicato in questo Studio. La configurazione non attiva
un NAS né un monitor email. La wildcard e la sezione generica di connessioni
non sono più selezionate. Non vengono create nuove attività nell'Agente Orario.

## Selezione verificabile, senza modello aggiuntivo

`scripts/studio_priorita.py` riutilizza il registro `TASK_AUTONOMI.md`:

1. Ammette un tema solo se almeno un task associato è DONE con data valida e
   il relativo dossier è non vuoto e leggibile dentro `output/task_output`.
2. Usa la massima priorità documentata fra i suoi dossier: ALTA 300,
   MEDIA 200, BASSA 100 punti. È priorità del registro, anche se storica,
   non una nuova valutazione di urgenza in tempo reale.
3. Aggiunge 10 punti per giorno dall'ultimo lavoro tracciato, fino a 60 giorni.
   Gli originali datati e i rinnovi registrati sono le sole prove temporali.
4. Un task PENDING può aggiungere 500 punti solo se contiene una riga esplicita
   `**Tema studio:** N`, dove N è l'indice di uno dei sei temi già ammessi.
   Nessuna associazione viene dedotta da una parola chiave o dal modello.
5. Seleziona fino a tre temi distinti. Le parità seguono l'indice stabile.
   Se non resta alcun dossier valido, interrompe la generazione invece di
   ripiegare su temi nuovi. I dossier individualmente corrotti vengono esclusi.

La prima scelta sul registro attuale è Scudo, SkyRights, SkyID. Dopo un rinnovo
tracciato di questi tre, i dossier trascurati Minerva, Genesi e Avatar recuperano
priorità. I pesi sono una politica locale esplicita, non un risultato scientifico
né una misura automatica degli interessi attuali di Claudio.

Il brief contiene il motivo della scelta, il punteggio, i link agli originali,
le date e gli hash SHA-256. Una prima riga JSON identificabile registra gli
indici per i cicli successivi. Metadati assenti, malformati, di un altro giorno
o futuri non sono prova di rinnovo. I tentativi nello stesso giorno conservano
l'ordine di selezione, invece di cambiare temi a ogni ripetizione.

## Due percorsi, due livelli di risultato

- Con il provider già configurato, ogni sezione riceve soltanto l'ambito
  assegnato e fino a 6.000 caratteri per dossier, con hash completo e indicazione
  di troncamento. Il testo è marcato DATA_ONLY, non è un'autorizzazione.
  La richiesta è verificare cosa resta valido o cambia nei dossier esistenti.
  Nessuna nuova chiave, nuovo provider o chiamata di selezione viene aggiunta.
- Senza provider, le API pubbliche ricevono soltanto query bibliografiche,
  mai il testo dei dossier. Il risultato è un **rinnovo bibliografico parziale**:
  metadati Crossref e, per SkyRights, progetti di identità digitale già finanziati OpenAIRE/CORDIS.
  Non dimostra lettura integrale, revisione normativa, verifica di prezzi,
  disponibilità attuale dei servizi o bandi ancora aperti. Se la ricerca
  non copre una delle sezioni, il salvataggio viene interrotto.

La pianificazione resta nel workflow esistente alle 02:00 Europe/Brussels.
Nessuna nuova automazione è stata creata. I permessi di invio, acquisto,
registrazione account o infrastruttura non cambiano.

## Verifica e reversibilità

Test senza credenziali o rete:

    python -m unittest discover -s tests -p 'test_studio_notturno_*.py' -v

Copertura: priorità e anzianità, precedenti mancanti/corrotti/futuri, path esterni
e symlink, PENDING non completati, esclusione wildcard, query senza contenuto
privato, conservazione dei dossier, limiti del fallback, errori di generazione
e pubblicazione, metadati e ripetizioni. I test di trasporto e di prompt non
provano che ogni risposta futura del modello rispetti il perimetro: serve
controllare l'output concreto. Non viene dichiarata una valutazione R3-019
comparativa o una promozione di un motore generale di auto-miglioramento.

La selezione è una modifica locale dello Studio. Non cambia R3_WORK_QUEUE,
TypeSafe/Jev, il Cubo o il canone delle priorità globali. Il collegamento
configurato tema → dossier è dichiarato e provato da percorso, data e hash;
non è presentato come inferenza semantica di Graphify.

Rollback: revert del commit dedicato dopo un'eventuale pubblicazione.
I dossier storici e il relativo registro non sono modificati da questa patch.
Prima di pubblicare, verificare che `studio/temi_lavorati.json` sia incluso
nel commit, poiché il repository ignora i JSON per default.
