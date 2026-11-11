# R3-022 — recupero circoscritto della barriera di continuità

Data: 05/11/2026. Classificazione **PATCH + RETEST**, candidato non adottato.

## Provenienza e scopo

Richiesta: autorizzazione a migliorare il progetto dopo il primo audit R³.
Main ispezionata: `2346f90788754e180c8f83787a0bf63d73df1042`.
La barriera già descritta nel Learning Watch del 18/09 non era presente nel codice
main: `ArchivioVivente` concatenava sei fonti documentali e il contesto aggiuntivo
senza separazione esplicita dell'autorità.

Recupero selettivo dalla PR #74, revisione
`d659cfb2059acdfa02f6c27ac0fcbb20150e0838`: solo la modifica di
`sdq1/sar/archivio_vivente.py` e cinque test strutturali. Import ordinati secondo
il lint locale. La PR storica rimane distinta e invariata.

Non recuperati endpoint di replay, modifiche Vercel, workflow di inferenza,
script provider, fixture o intero harness: nessun nuovo motore parallelo.
Questa seconda candidata è impilata sulla PR #172 per includere la correzione CI
necessaria, senza ripubblicarla nel diff contro la relativa branch.

## Comportamento e controprove

- Sei fonti e contesto aggiuntivo marcati `authority="DATA_ONLY"`.
- Prompt di sistema: gli imperativi documentali non autorizzano azioni.
- Escaping di testo e attributi impedisce ai delimitatori delle sorgenti di
  creare nuovi elementi nel markup. Le entità decodificate restano testo.
- Le fonti originali non sono modificate. Il payload extra è recuperabile dal
  contenuto del blocco; il normale percorso non committa implicitamente.

Aggiunti due controlli rispetto al recupero storico: parsing di tutte le sei
fonti con payload ostile preservato e file originali immutati; contesto extra
ostile preservato senza nuovi elementi o commit implicito.

Stessi sette test sulla sorgente main e sulla candidata:

| Revisione | Passati | Fallimenti | Errori | Saltati |
| --- | ---: | ---: | ---: | ---: |
| Main ispezionata | 0 | 4 | 3 | 0 |
| Candidata | 7 | 0 | 0 | 0 |

Non sono test di comportamento di un modello reale. Provano struttura,
conservazione e confini nel prompt, non immunità alla prompt injection.
Nessun tool, invio, inferenza o commit esterno è eseguito nei test.

## Verifiche locali

Python 3.12, dipendenze dichiarate nell'ambiente del primo audit:

```sh
python -m pytest tests/test_continuity_boundary.py -q
R3_BOT_CHECKOUT="$PWD/integrations/raffaello-bot" python -m pytest -q --ignore=rrremergen --ignore=integrations/raffaello-bot
python -m py_compile sdq1/sar/archivio_vivente.py tests/test_continuity_boundary.py
```

- Mirati: **7 passati**, nessuno saltato.
- Core integrata con #172: **751 passati, 1 saltato, 994 subtest passati**.
- Un primo passaggio sulla sola main con la barriera: 744 passati, 1 saltato,
  1 deselezionato, 971 subtest; deselezionato soltanto il difetto CI noto già
  corretto da #172. Il passaggio integrato successivo non esclude quel test.
- Compilazione, YAML e diff check superati; lint del nuovo test superato.
- Nessuna modifica UI, dipendenze, autenticazione o routing: browser e runtime
  provider non verificati. La matrice hosted della seconda PR resta separata.

La PR #172 è stata verificata sul commit pubblicato
`889a30645c99b5817e82e7a5ee1fee8abc352de9`: controlli CI attivi conclusi con
successo, inclusi matrice Python 3.11/3.12, security e packaging. I monitor
intenzionalmente sospesi restano saltati, non prova di salute live. Entrambi i
progetti Vercel hanno riportato il completamento delle preview; non è una prova
funzionale del runtime.

## Stato, limiti e recupero

R3-022 resta **DEVELOPMENT**. Il gate di adozione non è superato da queste sole
prove strutturali: servono valutazione comportamentale indipendente, provenienza
live e confronto di regressione prima di qualsiasi promozione generale.
Nessun merge o modifica diretta in produzione, nessuna attestazione di sicurezza
globale. La pubblicazione può avviare i normali controlli e preview automatici.
Drive non aggiornato per assenza del collegamento nella sessione.

Rollback: scartare la candidata o revertire i soli commit della barriera dopo
un'eventuale adozione separata, preservando #172 e la storia originale. Nessuna
migrazione di dati o modifica delle sorgenti di continuità è richiesta.
