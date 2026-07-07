# Enciclopedia Tecnica Pro-Pre

> Il patrimonio scientifico dell'Accademia Pro-Pre. Non un PDF statico:
> una **wikipedia privata**, costruita su dati strutturati e verificati,
> che forma i tecnici e alimenta l'IA con conoscenza validata.

## Principio architetturale: JSON-first

Ogni voce dell'enciclopedia nasce come **dato strutturato** (JSON validato
da schema), non come testo libero. Da quel dato si generano:

1. **La wiki privata** — consultazione, ricerca, collegamenti incrociati.
2. **Il manuale stampabile** — PDF/opuscoli per la formazione in aula.
3. **La base di conoscenza dell'IA** — l'IA che crea le formule legge
   le stesse schede dei tecnici: una sola fonte di verità.

Questo è il motivo per cui non si parte dal PDF: un PDF di 2.000 pagine
è un prodotto *derivato*. La sorgente è il dato.

## Struttura

```
propre/
├── README.md                  ← questo file
├── schema/
│   └── sostanza.schema.json   ← struttura obbligatoria delle schede sostanza
├── sostanze/                  ← Volume 2: una scheda JSON per sostanza
│   ├── acido_citrico.json
│   ├── acido_acetico.json
│   ├── bicarbonato_di_sodio.json
│   ├── ammoniaca.json
│   ├── perossido_di_idrogeno.json
│   ├── lanolina.json
│   └── isopropanolo.json
├── volumi/                    ← gli 8 volumi: indici ragionati + testi
│   ├── volume_1_chimica_della_pulizia.md
│   ├── volume_2_sostanze.md
│   ├── volume_3_fibre.md
│   ├── volume_4_macchie.md
│   ├── volume_5_prodotti_propre.md
│   ├── volume_6_macchina.md
│   ├── volume_7_heritage.md
│   └── volume_8_ia.md
└── wiki.html                  ← seme della wiki privata (autonomo, offline)
```

## Gli 8 volumi

| # | Volume | Contenuto | Stato |
|---|--------|-----------|-------|
| 1 | Chimica della Pulizia | Fondamenti: tensioattivi, enzimi, solventi, acidi, basi, pH, durezza, schiuma, compatibilità | Primi capitoli scritti |
| 2 | Le Sostanze | ~1.500 schede ingrediente | 7 schede complete (pilota) |
| 3 | Le Fibre | Lana, seta, cotone, lino, viscosa, sintetiche… | Indice |
| 4 | Le Macchie | Composizione, formazione, reazione, rimozione, errori | Indice |
| 5 | I Prodotti Pro-Pre | Composizione, funzione, dosaggi, casi studio | Indice |
| 6 | La Macchina | Pompa, pressione, ugelli, aspirazione, temperatura | Indice |
| 7 | Heritage | Conservazione, restauro, fibre antiche, coloranti naturali | Indice |
| 8 | IA | Come decide, come formula, come apprende | Indice |

## Ciclo di vita di una scheda

Ogni scheda porta un campo `verifica`:

- `bozza` — scritta, non ancora revisionata.
- `verificata` — revisionata da un tecnico, con data e revisore.
- `da_aggiornare` — segnalata per revisione (nuovi dati, normative, casi).

Regola: **l'IA e la formazione usano solo schede `verificata`**.
Le bozze sono visibili ma marcate chiaramente come tali.

## Come cresce (roadmap)

1. **Pilota** (fatto): schema + 7 sostanze fondamentali + wiki minima.
2. **Nucleo** (~50 sostanze): tutto ciò che entra nei prodotti Pro-Pre
   e nelle procedure standard. Priorità assoluta.
3. **Estensione** (~300): sostanze che il tecnico incontra sul campo
   (componenti delle macchie, finissaggi, coloranti).
4. **Enciclopedia** (~1.500): copertura completa, alimentata dai casi reali.
5. In parallelo: immagini (microscopio, schemi), video, casi studio,
   collegati alle schede tramite gli `id`.

## Sicurezza — regola non negoziabile

Ogni scheda DEVE compilare `incompatibilita` e `sicurezza`.
Le incompatibilità pericolose (es. ipoclorito + ammoniaca → clorammine
tossiche) sono marcate `pericolo: true` e la wiki le evidenzia in rosso.
Una scheda senza sezione sicurezza completa non può diventare `verificata`.
