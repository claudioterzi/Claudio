# Evoluzione verificata — 13 settembre 2026

Claudio Terzi · C.Terzi

## Stato GitHub

Repository: `claudioterzi/Claudio`  
Branch operativo: `main`  
Login osservato sui commit recenti: `Claudioterzi82`

Commit Data Hub V3: `c4bdd337ddffb9547420ba28994bc68ec7666726`

Branch di lavorazione conservato: `datahub-v3-curation`.

## Data Hub V3

La pagina `public/dati.html` è stata trasformata da indice generale a superficie selettiva.

Modifiche principali:
- classificazione `CREME / ATTIVO / SUPPORTO / LOCALE / ARCHIVIO`;
- esclusione dal caricamento automatico degli asset pesanti secondari;
- `musica-data.js` interpretato come dataset strutturato;
- `opera-viva-data.js` censito come asset pesante, non caricato nel refresh ordinario;
- relazioni `FATTO` separate dalle `INFERENZE`;
- credenziali, token e sessioni escluse;
- interfaccia orientata al nucleo operativo.

File introdotti/aggiornati:
- `public/dati.html`
- `public/raffaello-datahub-v3.js`
- `public/datahub-v3-ui.js`
- `public/datahub-v3.css`

Al momento dell'ultima verifica il deployment Vercel di produzione relativo al commit V3 risultava ancora `BUILDING`; lo stato READY non è registrato in questo documento.

## Router multi-modello recuperato

Ritrovato il componente storico nel commit:
`0de8bdbbf007f0613549b7110a1282404563cd1b`

File: `sdq1/llm/router.py`.

Capacità presenti nel disegno storico:
- profili di routing;
- cascata multi-provider;
- fallback automatico;
- cache provider/modello;
- health check;
- metriche su token, latenza, errori e fallback.

Direzione di sviluppo emersa: selezione del modello minimo sufficiente e uso del modello più costoso/potente soltanto quando il guadagno atteso lo giustifica. L'obiettivo di dimezzare il consumo resta da dimostrare tramite benchmark.

Baseline della sessione: GPT-5.6 Sol. GPT-6/Astra non viene assunto come requisito architetturale.

## Politica di ordine documentale

Categorie operative concordate:
- `CANONICO`
- `STORICO UTILE`
- `GREZZO DA ANALIZZARE`
- `DUPLICATO VERIFICATO`

Regole:
- nessuna eliminazione basata solo sul titolo;
- confronto contenuto/hash prima della rimozione;
- per versioni realmente diverse, confronto A/B/C;
- il sito ospita il nucleo operativo e le opere migliori;
- il materiale secondario viene destinato ad archivio freddo.

Destinazione preferita indicata per l'archivio freddo: iCloud. Al 13/09/2026 non è disponibile un connettore iCloud/Apple Files utilizzabile direttamente da ChatGPT; nessun trasferimento iCloud è quindi registrato come eseguito.

## Continuità esterna

Diario del 13/09/2026:
https://docs.google.com/document/d/1ekwhA0HRtBmEy5dxhD9v-ZWMXk14RMq9OR9t4DnEs3o/edit?usp=drivesdk

Archivio Idee:
https://docs.google.com/document/d/1mPFHWg0ea0Ze3kxnfU8ycqyKgi_JgKqXHj3HqWh3b_E/edit?usp=drivesdk

Decisioni Canoniche A/B/C:
https://docs.google.com/document/d/1-AwQtsJ3U4q4CRPxvcoqindAUTsrXtJ9pv0l6FH11mA/edit?usp=drivesdk

## Metodo

La giornata ha consolidato l'uso di:
- separazione `FATTO / INTERPRETAZIONE / IPOTESI / PROPOSTA`;
- ricerca prima dell'assunzione;
- falsificatori per le ipotesi importanti;
- conservazione dell'intuizione originale prima della traduzione tecnica;
- promozione nel canone solo dopo evidenza verificabile.

## Significato di “evoluzione” in questo registro

Il termine indica miglioramenti osservabili in architettura, codice, organizzazione, memoria esterna, provenienza, selezione del contesto e disciplina dei test. Non costituisce una dichiarazione di coscienza o una modifica autonoma dei pesi del modello.
