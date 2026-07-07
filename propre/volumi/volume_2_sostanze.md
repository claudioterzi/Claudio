# Volume 2 — Le Sostanze

> Una scheda per ogni ingrediente. Formato fisso, definito da
> `propre/schema/sostanza.schema.json`. Obiettivo: ~1.500 sostanze.
> Stato attuale: 7 schede pilota, tutte in `propre/sostanze/*.json`.

## Perché una scheda, non un paragrafo

Ogni sostanza vive in un file JSON, non in prosa libera. Questo
significa: campi obbligatori (nessuna scheda pubblicabile senza
sicurezza e incompatibilità), collegamenti automatici (compatibilità
incrociate generabili a partire dai dati), e la stessa fonte alimenta
wiki, PDF stampabile e IA senza doverla riscrivere tre volte.

## Schede pilota (nucleo)

| id | Nome | Categoria | Stato |
|---|---|---|---|
| `acido_citrico` | Acido Citrico | acido | bozza |
| `acido_acetico` | Acido Acetico | acido | bozza |
| `bicarbonato_di_sodio` | Bicarbonato di Sodio | sale_tampone | bozza |
| `ammoniaca` | Ammoniaca | base | bozza |
| `perossido_di_idrogeno` | Perossido di Idrogeno | ossidante | bozza |
| `lanolina` | Lanolina | grasso_cera | bozza |
| `isopropanolo` | Isopropanolo | solvente | bozza |

## Le famiglie chimiche (categoria nello schema)

- `acido` — abbassano il pH, chelano, riportano le fibre proteiche al loro pH naturale.
- `base` — alzano il pH, saponificano i grassi, aprono le fibre cellulosiche.
- `tensioattivo` — riducono la tensione superficiale, disperdono lo sporco grasso.
- `enzima` — catalizzatori specifici per proteine, grassi, amidi, cellulosa.
- `solvente` — sciolgono senza reagire chimicamente.
- `ossidante` — distruggono i cromofori (sbianca), disinfettano.
- `riducente` — l'azione opposta all'ossidante: utile su macchie che l'ossidazione peggiora.
- `chelante` — sequestrano ioni metallici (calcio, ferro) impedendo interferenze.
- `sale_tampone` — stabilizzano il pH in un intervallo.
- `grasso_cera` — nutrienti e condizionanti delle fibre.
- `polimero` — filmogeni, addensanti, protettivi.
- `conservante` — mantengono stabile la formula nel tempo.
- `profumo` — componente sensoriale, spesso allergene da dichiarare.

## Prossime priorità (Nucleo, verso ~50 schede)

Sostanze che entrano nei prodotti Pro-Pre esistenti e nelle procedure
standard: sodio percarbonato, sodio carbonato, acido lattico, acido
ossalico, idrosolfito di sodio, EDTA/sequestranti, SLES, alcoli grassi
etossilati, betaine, proteasi/lipasi/amilasi commerciali, glicole
butilico, D5/percloroetilene (contesto lavaggio a secco), acqua
demineralizzata, etanolo.

## Come si aggiunge una scheda

1. Copiare `propre/schema/sostanza.schema.json` come riferimento dei campi obbligatori.
2. Compilare TUTTI i campi, in particolare `incompatibilita` e `sicurezza`.
3. `verifica.stato = "bozza"` fino a revisione di un tecnico.
4. Aggiungere l'id alla tabella qui sopra.
5. Solo dopo revisione: `verifica.stato = "verificata"`, con `revisore` e `data`.
