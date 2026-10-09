# PROGETTI VIVI — SPEC 0.1

## Scopo

La pagina `/progetti` non è più un catalogo statico. È l'indice operativo dei progetti Claudio × Raffaello.

Ogni progetto registrato deve avere:

1. uno `slug` stabile;
2. una pagina dedicata `/progetto/<slug>`;
3. uno stato esplicito;
4. una fonte tecnica/canonica;
5. capacità attuali dichiarate;
6. un prossimo passo;
7. un registro delle repo/scoperte esterne pertinenti;
8. una decisione di adozione verificabile.

## Fonte del sito

Il registro pubblico è `public/progetti-registry.js`.

L'indice `/progetti` viene renderizzato da:

- `public/progetti-vivi.html`
- `public/progetti-vivi.css`
- `public/progetti-vivi.js`

Le pagine dedicate sono renderizzate dalla shell comune:

- `public/progetto-vivo.html`
- `public/progetto-vivo.css`
- `public/progetto-vivo.js`

La shell comune evita che dieci pagine progetto divergano graficamente o logicamente; l'identità di ogni progetto vive nel registro.

## Regola GitHub Learning Lab

Una repo esterna non entra direttamente nel canone.

Flusso:

`DISCOVERED → CANDIDATE → SANDBOX → BASELINE A/B → FALSIFICATION → AUDIT → ADOPTED / REJECTED`

### DISCOVERED
È stata trovata. Nessuna dichiarazione di utilità dimostrata.

### CANDIDATE
Sono state identificate una o più idee concrete potenzialmente utili.

### SANDBOX
Le idee vengono implementate su ramo/prototipo isolato.

### BASELINE A/B
Si confronta il progetto prima/dopo con criteri espliciti.

### FALSIFICATION
Si cercano attivamente regressioni, casi limite e motivi per cui l'idea potrebbe essere peggiore.

### AUDIT
Si verificano provenance, licenza, dipendenze, costi, sicurezza e reversibilità.

### ADOPTED / REJECTED
Solo qui la capability diventa parte del progetto oppure viene scartata con motivazione.

## Raffaello Creative Studio

Le capability esterne del Creative Studio hanno un registro tecnico separato in `studio/capabilities/`.

La prima capability registrata è `calesthio/OpenMontage`, stato `CANDIDATE`.

L'integrazione corrente è intenzionalmente metadata-only: documenta ciò che abbiamo imparato e dove deve essere provato, ma non dichiara OpenMontage installato o operativo dentro SDQ-1.

Primo caso di test: `Cubo Vivo 2D`, una sola scena campione.

## Regola di continuità

La pagina progetto deve descrivere lo stato reale. Se una capability cambia stato, il registro va aggiornato nello stesso cambiamento che modifica l'implementazione o la decisione.

Nessuna pagina può dichiarare `ADOPTED`, `funzionante`, `integrato` o equivalente se la prova eseguibile non esiste.
