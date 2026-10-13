// Vercel Routing Middleware: La Porta controlla ogni richiesta (pagine, file, API)
// prima che arrivi al contenuto. Vedi porta/README.md.

import { creaPorta } from './porta/porta.mjs';
import { CATALOGO, MAPPA } from './porta/dati.mjs';

export const config = { runtime: 'nodejs' };

let porta;

export default async function middleware(request) {
  porta ??= creaPorta({ env: process.env, catalogo: CATALOGO, mappa: MAPPA });
  const risposta = await porta.gestisci(request);
  return risposta ?? new Response(null, { headers: { 'x-middleware-next': '1' } });
}
