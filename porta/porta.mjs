// La Porta — gestione richieste. Il proprietario entra sempre; gli ospiti vedono
// solo le aree aperte per loro. Redis (Upstash REST) conserva gli ospiti.

import crypto from 'node:crypto';
import {
  areeValide, chiaveNome, chiaveSessione, classifica, compilaCatalogo, creaHash,
  destinazioneSicura, firmaFalsa, firmaSessione, leggiCookie, leggiSessione, nomeValido,
  normalizza, nuovaPassword, puoVedere, verificaPassword,
} from './core.mjs';
import { TRAPPOLA, creaSentinella, esca, notificaTelegram } from './sentinella.mjs';

export const COOKIE = 'r3_porta';
const GIORNO = 86_400_000;
const DURATA_PROPRIETARIO = 30 * GIORNO;
const MAX_TENTATIVI = 10;
const FINESTRA_TENTATIVI_S = 900;

// ---------------------------------------------------------------- Redis REST

export function redisRest(env, fetchImpl = fetch) {
  const url = env.KV_REST_API_URL || env.UPSTASH_REDIS_REST_URL;
  const token = env.KV_REST_API_TOKEN || env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) return null;
  return async (...comando) => {
    const r = await fetchImpl(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(comando),
    });
    const dati = await r.json();
    if (!r.ok || dati.error) throw new Error(`Redis: ${dati.error || r.status}`);
    return dati.result;
  };
}

// ---------------------------------------------------------------- HTML

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[c]));

function pagina(titolo, corpo, stato = 200, extra = {}) {
  const html = `<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive"><title>${esc(titolo)}</title>
<style>
:root{color-scheme:dark}body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
background:#0c0c0e;color:#e8e4d8;font-family:Georgia,'Times New Roman',serif}
main{width:100%;max-width:420px;padding:2rem 1.25rem;text-align:center}
.sopra{font-size:.7rem;letter-spacing:.35em;color:#8a6f2e;text-transform:uppercase}
h1{font-size:1.9rem;color:#c9a84c;letter-spacing:.08em;font-weight:normal;margin:.8rem 0 1.4rem}
input{box-sizing:border-box;width:100%;background:#141418;border:1px solid #2a2a32;color:#e8e4d8;border-radius:8px;
padding:.7rem 1rem;font:inherit;font-size:1rem;margin:.35rem 0}
button,a.bottone{display:inline-block;margin-top:1rem;background:none;border:1px solid #8a6f2e;color:#c9a84c;
border-radius:999px;padding:.5rem 1.6rem;font:inherit;letter-spacing:.08em;cursor:pointer;text-decoration:none}
.nota{color:#7a7468;font-style:italic;font-size:.88rem;margin-top:1rem}.errore{color:#d46a5f;min-height:1.3em}
ul{list-style:none;padding:0;text-align:left}li{margin:.6rem 0}li a{color:#c9a84c}li span{color:#7a7468;font-size:.85rem;display:block}
</style></head><body><main><div class="sopra">Terzi · Claudio</div><h1>${esc(titolo)}</h1>${corpo}</main></body></html>`;
  return new Response(html, {
    status: stato,
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', ...extra },
  });
}

function json(dati, stato = 200) {
  return new Response(JSON.stringify(dati), {
    status: stato,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
  });
}

function vai(dove, extra = {}) {
  return new Response(null, { status: 303, headers: { Location: dove, 'Cache-Control': 'no-store', ...extra } });
}

function cookie(valore, maxAgeS) {
  return `${COOKIE}=${valore}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAgeS}`;
}

function paginaEntra(torna, errore = '') {
  return pagina('La Porta', `
<form method="post" action="/porta/entra" autocomplete="off">
<input name="nome" placeholder="Nome (vuoto se sei Claudio)" aria-label="Nome" maxlength="40">
<input name="password" type="password" placeholder="Password" aria-label="Password" required maxlength="200">
<input type="hidden" name="torna" value="${esc(torna)}">
<div class="errore" role="status">${esc(errore)}</div>
<button type="submit">Entra</button></form>`, errore ? 401 : 200);
}

// Calcola nel browser l'hash di una nuova password del proprietario (pbkdf2, formato
// werkzeug) da incollare in Vercel come R3_PORTA_OWNER_HASH. La password non lascia
// il dispositivo: la pagina non invia nulla al server.
function paginaChiave() {
  return pagina('Nuova chiave', `
<p class="nota">Scrivi la nuova password (almeno 12 caratteri). Il calcolo avviene su questo
telefono: la password non viene inviata a nessuno.</p>
<input id="p1" type="password" placeholder="Nuova password" autocomplete="new-password">
<input id="p2" type="password" placeholder="Ripetila" autocomplete="new-password">
<button id="calcola" type="button">Calcola</button>
<div class="errore" id="err" role="status"></div>
<textarea id="out" readonly hidden style="width:100%;min-height:7rem;margin-top:1rem;background:#141418;color:#c9a84c;border:1px solid #2a2a32;border-radius:8px;padding:.6rem;font-family:monospace;font-size:.8rem"></textarea>
<p class="nota" id="dopo" hidden>Copia il testo in Vercel → Settings → Environment Variables →
<b>R3_PORTA_OWNER_HASH</b> (Production), poi ripubblica.</p>
<script>
document.getElementById('calcola').onclick = async function () {
  var a = document.getElementById('p1').value, b = document.getElementById('p2').value;
  var err = document.getElementById('err'); err.textContent = '';
  if (a.length < 12) { err.textContent = 'Almeno 12 caratteri.'; return; }
  if (a !== b) { err.textContent = 'Le due password non coincidono.'; return; }
  var sale = Array.from(crypto.getRandomValues(new Uint8Array(12)), function (x) { return x.toString(16).padStart(2, '0'); }).join('');
  var chiave = await crypto.subtle.importKey('raw', new TextEncoder().encode(a), 'PBKDF2', false, ['deriveBits']);
  var bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt: new TextEncoder().encode(sale), iterations: 600000 }, chiave, 256);
  var hex = Array.from(new Uint8Array(bits), function (x) { return x.toString(16).padStart(2, '0'); }).join('');
  var out = document.getElementById('out');
  out.value = 'pbkdf2:sha256:600000$' + sale + '$' + hex; out.hidden = false;
  document.getElementById('dopo').hidden = false;
  document.getElementById('p1').value = document.getElementById('p2').value = '';
};
</script>`);
}

// ---------------------------------------------------------------- Porta

export function creaPorta({
  env, catalogo, mappa, redis = undefined, ora = () => Date.now(), notifica = undefined,
}) {
  const cat = compilaCatalogo(catalogo, mappa);
  const chiave = chiaveSessione(env.R3_PORTA_SECRET || env.PERFUME_ARCHIVE_SECRET);
  const hashProprietario = env.R3_PORTA_OWNER_HASH || env.PERFUME_ARCHIVE_PASSWORD_HASH || '';
  const db = redis === undefined ? redisRest(env) : redis;
  const avvisa = notifica ?? notificaTelegram(env);
  const sentinella = creaSentinella({ db, notifica: avvisa, ora });

  async function ospite(id) {
    if (!db || !/^[a-f0-9]{16}$/.test(id || '')) return null;
    const raw = await db('GET', `porta:ospite:${id}`);
    return raw ? JSON.parse(raw) : null;
  }

  // Sessione valida per questa richiesta, ricontrollando revoca e scadenza dell'ospite.
  // { falso: true } quando il cookie porta una firma che non è nostra.
  async function sessione(request) {
    const token = leggiCookie(request.headers.get('cookie'), COOKIE);
    const dati = leggiSessione(token, chiave, ora());
    if (!dati) return token && firmaFalsa(token, chiave) ? { falso: true } : null;
    if (dati.r === 'p') return { ruolo: 'proprietario' };
    if (dati.r !== 'o') return null;
    let rec;
    try {
      rec = await ospite(dati.id);
    } catch {
      return null; // Redis giù: gli ospiti restano fuori, il proprietario no.
    }
    if (!rec || rec.revocato || rec.scade <= ora() || rec.creato !== dati.v) return null;
    return { ruolo: 'ospite', id: rec.id, nome: rec.nome, aree: rec.aree };
  }

  async function troppiTentativi(ip) {
    if (!db) return false;
    try {
      const n = await db('INCR', `porta:tentativi:${ip}`);
      if (n === 1) await db('EXPIRE', `porta:tentativi:${ip}`, FINESTRA_TENTATIVI_S);
      return n > MAX_TENTATIVI;
    } catch {
      return false;
    }
  }

  // soloProprietario: l'indirizzo è bandito, resta aperta solo la riserva di Claudio.
  async function entra(request, ip, { soloProprietario = false } = {}) {
    const url = new URL(request.url);
    if (request.method === 'GET') return paginaEntra(destinazioneSicura(url.searchParams.get('torna')));
    if (request.method !== 'POST') return new Response(null, { status: 405 });
    if (!chiave) return pagina('Porta non configurata', '<p class="nota">Manca il segreto delle sessioni sul server.</p>', 503);
    const form = new URLSearchParams(await request.text());
    const nome = (form.get('nome') || '').trim();
    const password = form.get('password') || '';
    const torna = destinazioneSicura(form.get('torna'));

    if (!soloProprietario && await troppiTentativi(ip)) {
      return pagina('Aspetta un momento', '<p class="nota">Troppi tentativi. Riprova tra un quarto d\'ora.</p>', 429);
    }
    // Il proprietario non dipende da Redis: entra anche se il database è giù.
    if (!nome && hashProprietario && verificaPassword(hashProprietario, password)) {
      const token = firmaSessione({ r: 'p', exp: ora() + DURATA_PROPRIETARIO }, chiave);
      return vai(torna, { 'Set-Cookie': cookie(token, DURATA_PROPRIETARIO / 1000) });
    }
    if (soloProprietario) return null;
    await sentinella?.colpisci(ip, 'login_fallito', '/porta/entra');
    if (nome && db && nomeValido(nome)) {
      try {
        const id = await db('GET', `porta:nome:${chiaveNome(nome)}`);
        const rec = id ? await ospite(id) : null;
        if (rec && !rec.revocato && rec.scade > ora() && verificaPassword(rec.hash, password)) {
          const token = firmaSessione({ r: 'o', id: rec.id, v: rec.creato, exp: rec.scade }, chiave);
          const maxAge = Math.max(1, Math.floor((rec.scade - ora()) / 1000));
          return vai('/porta/benvenuto', { 'Set-Cookie': cookie(token, maxAge) });
        }
      } catch {
        // cade sull'errore generico
      }
    }
    return paginaEntra(torna, 'Nome o password non validi.');
  }

  function benvenuto(s) {
    const aree = cat.ospitabili.filter((a) => s.aree.includes(a.id));
    const voci = aree.map((a) => `<li><a href="${esc(a.ingresso)}">${esc(a.nome)}</a><span>${esc(a.descrizione)}</span></li>`).join('');
    return pagina(`Benvenuto, ${s.nome}`, `<p class="nota">Claudio ha aperto per te queste parti:</p><ul>${voci}</ul>
<form method="post" action="/porta/esci"><button type="submit">Esci</button></form>`);
  }

  function negato() {
    return pagina('Porta chiusa', `<p class="nota">Questa parte non è aperta per te.</p>
<a class="bottone" href="/porta/benvenuto">Torna alle tue parti</a>`, 403);
  }

  // ------------------------------------------------ API del proprietario

  function vista(rec) {
    const { hash, ...resto } = rec;
    return { ...resto, attivo: !rec.revocato && rec.scade > ora() };
  }

  async function api(request, percorso) {
    // Anti-CSRF: un form di un altro sito non può impostare intestazioni personalizzate.
    if (request.method !== 'GET' && request.headers.get('x-porta') !== '1') {
      return json({ errore: 'richiesta non valida' }, 403);
    }
    if (!db) return json({ errore: 'archivio ospiti non configurato (Redis)' }, 503);

    if (percorso === '/porta/api/stato' && request.method === 'GET') {
      const ids = (await db('SMEMBERS', 'porta:ospiti')) || [];
      const ospiti = [];
      for (const id of ids) {
        const rec = await ospite(id);
        if (rec) ospiti.push(vista(rec));
      }
      ospiti.sort((a, b) => b.creato - a.creato);
      const aree = cat.ospitabili.map(({ id, nome, descrizione, sensibilita }) => ({ id, nome, descrizione, sensibilita }));
      return json({ aree, ospiti });
    }

    if (percorso === '/porta/api/ospiti' && request.method === 'POST') {
      let corpo;
      try {
        corpo = await request.json();
      } catch {
        return json({ errore: 'JSON non valido' }, 400);
      }
      const nome = typeof corpo.nome === 'string' ? corpo.nome.trim() : '';
      if (!nomeValido(nome)) return json({ errore: 'Nome non valido (max 40 caratteri, lettere e numeri).' }, 400);
      if (!areeValide(corpo.aree, cat)) return json({ errore: 'Scegli almeno un\'area tra quelle concedibili.' }, 400);
      const giorni = Number(corpo.giorni ?? 7);
      if (!Number.isInteger(giorni) || giorni < 1 || giorni > 365) return json({ errore: 'Durata tra 1 e 365 giorni.' }, 400);
      let password = typeof corpo.password === 'string' ? corpo.password : '';
      if (password && password.length < 10) return json({ errore: 'Password di almeno 10 caratteri, o lasciala vuota.' }, 400);
      password = password || nuovaPassword();

      const chiaveN = `porta:nome:${chiaveNome(nome)}`;
      const id = crypto.randomBytes(8).toString('hex');
      if ((await db('SET', chiaveN, id, 'NX')) !== 'OK') {
        const precedente = await ospite(await db('GET', chiaveN));
        if (precedente && !precedente.revocato && precedente.scade > ora()) {
          return json({ errore: 'Esiste già un ospite attivo con questo nome.' }, 409);
        }
        await db('SET', chiaveN, id); // il precedente è scaduto: il nome si libera
      }
      const adesso = ora();
      const rec = {
        id, nome, aree: [...new Set(corpo.aree)], creato: adesso, scade: adesso + giorni * GIORNO,
        situazione: typeof corpo.situazione === 'string' ? corpo.situazione.slice(0, 2000) : '',
        revocato: false, hash: creaHash(password),
      };
      await db('SET', `porta:ospite:${id}`, JSON.stringify(rec));
      await db('SADD', 'porta:ospiti', id);
      return json({ ospite: vista(rec), password }, 201);
    }

    if (percorso === '/porta/api/sentinella' && request.method === 'GET') {
      return json(sentinella ? await sentinella.stato() : { eventi: [], banditi: [] });
    }
    if (percorso === '/porta/api/sentinella/sblocca' && request.method === 'POST') {
      let corpo;
      try {
        corpo = await request.json();
      } catch {
        return json({ errore: 'JSON non valido' }, 400);
      }
      if (typeof corpo.ip !== 'string' || !/^[0-9a-fA-F:.]{2,45}$/.test(corpo.ip)) {
        return json({ errore: 'indirizzo non valido' }, 400);
      }
      await sentinella.sblocca(corpo.ip);
      return json({ ok: true });
    }

    const m = percorso.match(/^\/porta\/api\/ospiti\/([a-f0-9]{16})\/revoca$/);
    if (m && request.method === 'POST') {
      const rec = await ospite(m[1]);
      if (!rec) return json({ errore: 'ospite non trovato' }, 404);
      rec.revocato = true;
      rec.revocato_il = ora();
      await db('SET', `porta:ospite:${rec.id}`, JSON.stringify(rec));
      const chiaveN = `porta:nome:${chiaveNome(rec.nome)}`;
      if ((await db('GET', chiaveN)) === rec.id) await db('DEL', chiaveN);
      return json({ ospite: vista(rec) });
    }
    return json({ errore: 'non trovato' }, 404);
  }

  // ------------------------------------------------ ingresso di ogni richiesta

  // Restituisce una Response, oppure null per lasciar passare la richiesta.
  async function gestisci(request) {
    const url = new URL(request.url);
    const percorso = url.pathname;
    const ip = (request.headers.get('x-forwarded-for') || 'ignoto').split(',')[0].trim();
    const s = await sessione(request);

    // Il proprietario è immune alla Sentinella.
    if (s?.ruolo === 'proprietario') {
      if (percorso === '/porta/esci') return vai('/porta/entra', { 'Set-Cookie': cookie('', 0) });
      if (percorso === '/porta/chiave') return paginaChiave();
      if (percorso.startsWith('/porta/api/')) return api(request, percorso);
      return null;
    }

    // Sentinella: trappole, percorsi truccati, indirizzi banditi, cookie falsificati.
    if (sentinella) {
      if (TRAPPOLA.test(percorso)) {
        await sentinella.colpisci(ip, 'trappola', percorso);
        return esca(percorso);
      }
      if (normalizza(percorso) === null) {
        await sentinella.colpisci(ip, 'percorso_sospetto', percorso);
        return esca(percorso);
      }
      if (await sentinella.bandito(ip)) {
        const tentaProprietario = percorso === '/porta/entra' && request.method === 'POST';
        if (tentaProprietario && await sentinella.riservaProprietario(ip)) {
          const r = await entra(request, ip, { soloProprietario: true });
          if (r) return r;
        }
        if (percorso === '/porta/entra' && request.method === 'GET') return paginaEntra('/');
        return esca(percorso);
      }
      if (s?.falso) await sentinella.colpisci(ip, 'cookie_falso', percorso);
    }

    if (percorso === '/robots.txt') {
      return new Response('User-agent: *\nDisallow: /\n', { headers: { 'Content-Type': 'text/plain' } });
    }
    if (percorso === '/porta/entra') return entra(request, ip);
    if (percorso === '/porta/chiave') return paginaChiave();
    if (percorso === '/porta/esci') return vai('/porta/entra', { 'Set-Cookie': cookie('', 0) });

    if (s?.ruolo !== 'ospite') {
      const vuoleHtml = request.method === 'GET' && (request.headers.get('accept') || '').includes('text/html');
      if (vuoleHtml) return vai(`/porta/entra?torna=${encodeURIComponent(percorso + url.search)}`);
      return json({ errore: 'accesso richiesto' }, 401);
    }

    if (percorso === '/porta/benvenuto' || percorso === '/') return benvenuto(s);
    if (puoVedere(s, percorso, cat)) return null;

    if (sentinella) {
      const pagina_ = (request.headers.get('accept') || '').includes('text/html');
      const troppo = await sentinella.colpisciOspite(s, ip, pagina_ ? 'ospite_fuori_pagina' : 'ospite_fuori_file', percorso);
      if (troppo) {
        await sospendi(s, ip);
        return esca(percorso);
      }
    }
    return negato();
  }

  async function sospendi(s, ip) {
    try {
      const rec = await ospite(s.id);
      if (!rec || rec.revocato) return;
      rec.revocato = true;
      rec.revocato_il = ora();
      rec.motivo = 'sentinella';
      await db('SET', `porta:ospite:${rec.id}`, JSON.stringify(rec));
      const chiaveN = `porta:nome:${chiaveNome(rec.nome)}`;
      if ((await db('GET', chiaveN)) === rec.id) await db('DEL', chiaveN);
      await avvisa(`🛡 Sentinella: ho sospeso l'ospite ${rec.nome} (frugava fuori dalle sue aree, da ${ip}).`);
    } catch {
      // se Redis è giù la sessione dell'ospite non vale comunque
    }
  }

  return { gestisci, classifica: (p) => classifica(p, cat) };
}
