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
