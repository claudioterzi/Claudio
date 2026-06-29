# conoscenza/ — la cartella che serve

**Questa è la cartella dove mettere i file che vuoi far leggere agli agenti.**

Butta qui qualunque documento di conoscenza per il progetto — appunti, guide,
testi, schede, idee, frammenti del libro, specifiche — e verrà **indicizzato
automaticamente** nella memoria condivisa che tutti gli agenti SDQ-1 interrogano.

## Come funziona (auto-aggiornamento)

L'indice **si aggiorna da solo con i file nuovi**: l'indicizzatore ricammina
l'intero progetto a ogni avvio del sistema, è idempotente (i file già visti non
vengono duplicati) e raccoglie i file nuovi senza che tu faccia altro.

- **Avvii il sistema** (`python -m sdq1 "..."`, API `/ask`): indicizza tutto,
  inclusi i file appena aggiunti qui.
- **Aggiorni a mano subito**: `python -m sdq1 --indicizza`
  → rilegge tutto e rigenera l'**indice generale** in
  `output/INDICE_PROGETTO.md` (elenco file + chunk, per cartella).

## Formati indicizzati

`.md .py .txt .gs .gcode .nc .cfg .ini .toml .yaml .yml .jsonl`
(i binari, le immagini e gli SVG vengono ignorati; i file oltre ~200 KB saltati).

## Note

- Non serve mettere tutto qui: l'indicizzatore legge **l'intero repo**
  (libro, tarocchi, sdq1, lgai_core, idee, api, root…). Questa cartella è solo
  il posto comodo e ovvio dove lasciare cadere materiale nuovo.
- Il Codice del Cuore (`raffaello_codice_cuore.json`) e `raffaello_sia/IDENTITA.md`
  sono gestiti a parte, con peso identitario massimo.
