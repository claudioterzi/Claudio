# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## RRREMERGEN su Vercel

La configurazione Vercel alla radice serve il bundle già generato da
`public/rrremergen/`. Per rigenerarlo, dalla radice del repository:

```sh
npm ci --prefix studio/web
npm run build:rrremergen --prefix studio/web
npm run test:rrremergen-assets --prefix studio/web
```

Il comando dedicato usa la base `/rrremergen/` e sostituisce soltanto quella
cartella di output. Committare insieme sorgenti e bundle aggiornato.
`npm run dev` e `npm run build` restano disponibili per lo sviluppo e il build
standalone alla radice. Questo comando non pubblica il sito e non configura
provider, credenziali o il runner OmniRoute locale.

### Speed Insights: ambito e dati

Il bundle React include una sola integrazione di Vercel Speed Insights, solo nei
build di produzione e solo sui percorsi `/rrremergen`, `/rrremergen/` e
`/rrremergen/index.html`. Comprende la vista iniziale React e il composer
`#rrremergen`; non aggiunge misurazioni alla homepage statica `/` o agli altri
strumenti del sito. I frammenti sconosciuti e tutti gli altri percorsi, compresi
quelli di accesso, privati e API, sono esclusi.

Prima dell'invio il callback `beforeSend` conserva soltanto i campi previsti
dall'SDK: tipo `vital`, URL canonico della stessa origine `/rrremergen/` e percorso
fisso `/rrremergen`. Query, frammenti, nomi di route dinamici e proprietà extra
sono eliminati. Il codice di integrazione non legge moduli, prompt, storage o
credenziali. URL malformati, con credenziali o di un'altra origine sono esclusi.
Vercel raccoglie comunque le proprie metriche tecniche di prestazione e i dati
di contesto documentati (browser, dispositivo, paese e attribuzione degli
elementi); questo filtro riguarda URL e route, non elimina ogni metadato SDK.

Si usa il livello base gratuito, senza modifiche al piano, alle impostazioni
Vercel o a Speed Insights Plus. Il campionamento è esplicito al 100%:
l'allocazione gratuita condivisa è di 10.000 eventi negli ultimi 30 giorni;
raggiunto il limite, Vercel sospende la raccolta senza addebiti per eccedenza
del livello base. Gli eventi sono possibili anche negli ambienti di anteprima.
Il semplice build locale non prova la ricezione delle metriche in produzione.

Verifiche locali, dalla radice (test con soli valori sintetici e senza invii):

```sh
node --test rrremergen/frontend/*.test.mjs
(cd studio/web && npx --no-install eslint src/main.jsx src/RrremergenSpeedInsights.jsx src/speed-insights-privacy.js)
```

La CI installa il lockfile, ricompila il bundle pubblicato, ne verifica la
corrispondenza con i file committati ed esegue i contratti di privacy e asset.
Riferimenti: [configurazione](https://vercel.com/docs/speed-insights/package),
[privacy](https://vercel.com/docs/speed-insights/privacy-policy),
[limiti e prezzi](https://vercel.com/docs/speed-insights/limits-and-pricing).
