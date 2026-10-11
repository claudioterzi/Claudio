# GPT-6 Astra - capacità documentate e applicazione R3

Ricognizione al 2026-09-09; non inventario esaustivo di ogni prodotto OpenAI.

La guida ufficiale indica `gpt-6-astra` per Responses API. Descrive strumenti
asincroni, steering durante l'esecuzione e aggiornamento del reasoning preservando
la cache. Elenca computer use, output strutturati, streaming, chiamate programmatiche,
orchestrazione, caching, ragionamento persistito, compattazione e modalità pro.
`reasoning=none` non è supportato; Fast mode non è disponibile con residenza dati EU.

Per il prompting raccomanda di esplicitare iniziativa, completamento, stile,
delegazione e proporzione dei test. L'applicazione deve eseguire gli strumenti
e gestire il lavoro pendente: leggere una guida non attiva queste funzioni nel router.

Fonte consultata: https://developers.openai.com/api/docs/guides/latest-model

## Decisioni progettuali R3 (proposte applicative)

Usare il modello per produrre candidati ancorati a fonti; usare controlli esterni
per valutare gli esiti. Partire da una baseline congelata. La stessa rubrica si
applica a tutti i provider. Non dedurre disponibilità API, costo o quota dal
modello selezionato nella chat. Non sostituire provider economici e locali con
un unico modello: preservare i ruoli del router e confrontare costo per compito.

Questa consegna integra il metodo nel protocollo e un validatore offline.
Non contiene chiamate API Astra, benchmark comparativi o promesse di accelerazione.
Persistenza documentale, memoria del runtime e memoria interna del modello sono
meccanismi distinti. L'autoriflessione qui riguarda revisione di risultati e prove.
