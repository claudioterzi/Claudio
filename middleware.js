// Vercel Routing Middleware: La Porta controlla ogni richiesta (pagine, file, API)
// prima che arrivi al contenuto. Vedi porta/README.md.

export const config = { runtime: 'nodejs' };

let portaPromise;

function caricaPorta() {
  // Il builder legacy converte questo entrypoint in CommonJS. Gli import
  // dinamici restano nativi e caricano i moduli .mjs senza require(ESM).
  return portaPromise ??= Promise.all([
    import('./porta/porta.mjs'),
    import('./porta/dati.mjs'),
  ]).then(([{ creaPorta }, { CATALOGO, MAPPA }]) =>
    creaPorta({ env: process.env, catalogo: CATALOGO, mappa: MAPPA }));
}

export default async function middleware(request) {
  const porta = await caricaPorta();
  const risposta = await porta.gestisci(request);
  return risposta ?? new Response(null, { headers: { 'x-middleware-next': '1' } });
}
