// La Porta: il proprietario entra sempre, gli ospiti vedono solo le aree aperte.
// Esegui: node --test tests/test_porta.mjs

import assert from 'node:assert/strict';
import test from 'node:test';

import { CATALOGO, MAPPA } from '../porta/dati.mjs';
import {
  compilaCatalogo, creaHash, destinazioneSicura, firmaSessione, leggiSessione,
  chiaveSessione, normalizza, nuovaPassword, puoVedere, verificaPassword,
} from '../porta/core.mjs';
import { COOKIE, creaPorta } from '../porta/porta.mjs';

// Vettori generati con werkzeug.security.generate_password_hash (come su Vercel).
const PASSWORD = 'prova-proprietario-42';
const HASH_SCRYPT = 'scrypt:32768:8:1$jnLDo55rqP9BnVNH$96e1ad414df38f8c45259f670f6d89ff948ebdc7d4632af70a0a024145a5dd0241548e13c51dd6efa742ec466b78aaa4d4e3c9ad59aa18afaddc6a6a743a9065';
const HASH_PBKDF2 = 'pbkdf2:sha256:1000$9WsKPb7FQZobYdb6$72ea6c4b15a7fc7eac4e7040348d79b2ca30eef8cddab5fd45a329aeed1740b4';
const SEGRETO = 'segreto-di-prova-abbastanza-lungo';

const cat = compilaCatalogo(CATALOGO, MAPPA);
const OSPITE_TAROCCHI = { ruolo: 'ospite', aree: ['tarocchi'] };

function redisFinto() {
  const kv = new Map();
  let giu = false;
  const db = async (cmd, ...a) => {
    if (giu) throw new Error('Redis giù');
    switch (cmd) {
      case 'GET': return kv.has(a[0]) ? kv.get(a[0]) : null;
      case 'SET':
        if (a.slice(2).includes('NX') && kv.has(a[0])) return null;
        kv.set(a[0], a[1]); return 'OK';
      case 'DEL': return kv.delete(a[0]) ? 1 : 0;
      case 'SADD': { const s = kv.get(a[0]) || new Set(); s.add(a[1]); kv.set(a[0], s); return 1; }
      case 'SMEMBERS': return [...(kv.get(a[0]) || [])];
      case 'INCR': { const n = (kv.get(a[0]) || 0) + 1; kv.set(a[0], n); return n; }
      case 'INCRBY': { const n = (kv.get(a[0]) || 0) + Number(a[1]); kv.set(a[0], n); return n; }
      case 'SREM': { const s = kv.get(a[0]); return s && s.delete(a[1]) ? 1 : 0; }
      case 'LPUSH': { const l = kv.get(a[0]) || []; l.unshift(a[1]); kv.set(a[0], l); return l.length; }
      case 'LTRIM': { const l = kv.get(a[0]) || []; kv.set(a[0], l.slice(a[1], Number(a[2]) + 1)); return 'OK'; }
      case 'LRANGE': return (kv.get(a[0]) || []).slice(a[1], Number(a[2]) + 1);
      case 'EXPIRE': return 1;
      default: throw new Error(`comando non previsto ${cmd}`);
    }
  };
  db.spegni = () => { giu = true; };
  return db;
}

function setup({ ora = 1_800_000_000_000, redis = redisFinto() } = {}) {
  const tempo = { ora };
  const avvisi = [];
  const porta = creaPorta({
    env: { R3_PORTA_SECRET: SEGRETO, PERFUME_ARCHIVE_PASSWORD_HASH: HASH_SCRYPT },
    catalogo: CATALOGO, mappa: MAPPA, redis, ora: () => tempo.ora,
    notifica: async (t) => { avvisi.push(t); },
  });
  return { porta, redis, tempo, avvisi };
}

const BASE = 'https://claudio-ebon.vercel.app';
const req = (percorso, { metodo = 'GET', cookie, corpo, intestazioni = {} } = {}) =>
  new Request(BASE + percorso, {
    method: metodo,
    headers: { accept: 'text/html', ...(cookie ? { cookie: `${COOKIE}=${cookie}` } : {}), ...intestazioni },
    body: corpo,
  });

const login = (campi, ip = '1.2.3.4') => req('/porta/entra', {
  metodo: 'POST', corpo: new URLSearchParams(campi).toString(),
  intestazioni: { 'content-type': 'application/x-www-form-urlencoded', 'x-forwarded-for': ip },
});

function cookieDa(risposta) {
  const sc = risposta.headers.get('set-cookie') || '';
  return sc.split(';')[0].split('=').slice(1).join('=');
}

async function entraProprietario(porta) {
  const r = await porta.gestisci(login({ nome: '', password: PASSWORD, torna: '/' }));
  assert.equal(r.status, 303);
  return cookieDa(r);
}

async function creaOspite(porta, cookieP, dati) {
  const r = await porta.gestisci(req('/porta/api/ospiti', {
    metodo: 'POST', cookie: cookieP, corpo: JSON.stringify(dati),
    intestazioni: { 'content-type': 'application/json', 'x-porta': '1' },
  }));
  return { stato: r.status, dati: await r.json() };
}

// ------------------------------------------------------------ nucleo

test('password werkzeug: scrypt e pbkdf2 verificate, sbagliate rifiutate', () => {
  assert.equal(verificaPassword(HASH_SCRYPT, PASSWORD), true);
  assert.equal(verificaPassword(HASH_PBKDF2, PASSWORD), true);
  assert.equal(verificaPassword(HASH_SCRYPT, 'sbagliata'), false);
  assert.equal(verificaPassword('md5$x$abcd', PASSWORD), false);
  const h = creaHash('nuova-password-123');
  assert.equal(verificaPassword(h, 'nuova-password-123'), true);
  assert.match(nuovaPassword(), /^[a-z2-9]{4}-[a-z2-9]{4}-[a-z2-9]{4}$/);
});

test('sessione firmata: valida, manomessa, scaduta', () => {
  const k = chiaveSessione(SEGRETO);
  const t = firmaSessione({ r: 'p', exp: 2000 }, k);
  assert.deepEqual(leggiSessione(t, k, 1000), { r: 'p', exp: 2000 });
  assert.equal(leggiSessione(t, k, 3000), null);
  const [corpo, firma] = t.split('.');
  const falso = Buffer.from(JSON.stringify({ r: 'p', exp: 9e15 })).toString('base64url');
  assert.equal(leggiSessione(`${falso}.${firma}`, k, 1000), null);
  assert.equal(leggiSessione(`${corpo}.${firma}`, chiaveSessione('altro-segreto-lungo-123'), 1000), null);
  assert.equal(chiaveSessione('corto'), null);
});

test('percorsi sospetti normalizzati o rifiutati', () => {
  assert.equal(normalizza('/public/libro.html'), '/libro.html');
  assert.equal(normalizza('//libro.html'), '/libro.html');
  assert.equal(normalizza('/a/%2e%2e/privato.html'), null);
  assert.equal(normalizza('/%E0%A4%A'), null);
  assert.equal(destinazioneSicura('//evil.com'), '/');
  assert.equal(destinazioneSicura('https://evil.com'), '/');
  assert.equal(destinazioneSicura('/tarocchi?x=1'), '/tarocchi?x=1');
});

test('ospite Tarocchi: vede i tarocchi, non il resto', () => {
  const si = ['/tarocchi', '/index.html', '/public/index.html', '/cards/retro.svg', '/api/tarocchi/alpha-leggi', '/a74-base.css'];
  const no = ['/libro', '/libro.html', '/privato', '/dati.html', '/porta', '/api/r3-sync',
    '/formule/organo-13aff1815ecef350.json', '/raffaello-datahub-v3.js', '/file-mai-visto.json', '/a/%2e%2e/libro.html'];
  for (const p of si) assert.equal(puoVedere(OSPITE_TAROCCHI, p, cat), true, `dovrebbe vedere ${p}`);
  for (const p of no) assert.equal(puoVedere(OSPITE_TAROCCHI, p, cat), false, `non dovrebbe vedere ${p}`);
});

test('nessun file di formule si apre a chi non ha l\'area profumi', async () => {
  const { readdirSync } = await import('node:fs');
  const formule = readdirSync(new URL('../public/formule/', import.meta.url));
  assert.ok(formule.length > 0);
  const tutteTranneProfumi = cat.ospitabili.map((a) => a.id).filter((id) => id !== 'profumi');
  const ospite = { ruolo: 'ospite', aree: tutteTranneProfumi };
  for (const f of formule) {
    for (const p of [`/formule/${f}`, `/public/formule/${f}`]) {
      assert.equal(puoVedere(ospite, p, cat), false, `${p} non deve aprirsi`);
    }
  }
});

test('le aree solo proprietario non si aprono mai, nemmeno se un ospite le avesse', () => {
  const furbo = { ruolo: 'ospite', aree: ['privato', 'tarocchi'] };
  assert.equal(puoVedere(furbo, '/privato', cat), false);
  assert.equal(puoVedere(furbo, '/porta/api/stato', cat), false);
  assert.equal(puoVedere({ ruolo: 'proprietario' }, '/privato', cat), true);
});

// ------------------------------------------------------------ flusso completo

test('senza sessione: pagine → login, API → 401, robots chiude tutto', async () => {
  const { porta } = setup();
  const r = await porta.gestisci(req('/libro'));
  assert.equal(r.status, 303);
  assert.equal(r.headers.get('location'), '/porta/entra?torna=%2Flibro');
  const api = await porta.gestisci(req('/api/raffaello/x', { intestazioni: { accept: 'application/json' } }));
  assert.equal(api.status, 401);
  const file = await porta.gestisci(req('/public/libro.html', { intestazioni: { accept: '*/*' } }));
  assert.equal(file.status, 401);
  const robots = await porta.gestisci(req('/robots.txt'));
  assert.match(await robots.text(), /Disallow: \//);
});

test('proprietario entra sempre, anche con Redis giù', async () => {
  const { porta, redis } = setup();
  redis.spegni();
  const c = await entraProprietario(porta);
  assert.equal(await porta.gestisci(req('/privato', { cookie: c })), null);
  assert.equal(await porta.gestisci(req('/libro', { cookie: c })), null);
});

test('password sbagliata: errore generico', async () => {
  const { porta } = setup();
  const r = await porta.gestisci(login({ password: 'no' }));
  assert.equal(r.status, 401);
  assert.match(await r.text(), /Nome o password non validi/);
});

test('ciclo ospite: creato dal proprietario, entra, vede solo le sue aree, revocato', async () => {
  const { porta } = setup();
  const cp = await entraProprietario(porta);

  const { stato, dati } = await creaOspite(porta, cp, { nome: 'Guido', aree: ['tarocchi', 'viaggi'], giorni: 3, situazione: 'amico curioso' });
  assert.equal(stato, 201);
  assert.match(dati.password, /^[a-z2-9]{4}-/);
  assert.equal(dati.ospite.hash, undefined, 'l\'hash non esce mai');

  const doppio = await creaOspite(porta, cp, { nome: 'guido', aree: ['tarocchi'] });
  assert.equal(doppio.stato, 409);

  const r = await porta.gestisci(login({ nome: 'Guido', password: dati.password }));
  assert.equal(r.status, 303);
  assert.equal(r.headers.get('location'), '/porta/benvenuto');
  const cg = cookieDa(r);

  const benvenuto = await porta.gestisci(req('/', { cookie: cg }));
  const html = await benvenuto.text();
  assert.match(html, /Benvenuto, Guido/);
  assert.match(html, /href="\/tarocchi"/);
  assert.doesNotMatch(html, /href="\/scritti"/);

  assert.equal(await porta.gestisci(req('/tarocchi', { cookie: cg })), null);
  assert.equal(await porta.gestisci(req('/viaggi', { cookie: cg })), null);
  assert.equal((await porta.gestisci(req('/libro', { cookie: cg }))).status, 403);
  assert.equal((await porta.gestisci(req('/porta/api/stato', { cookie: cg }))).status, 403);

  const stato2 = await porta.gestisci(req('/porta/api/stato', { cookie: cp }));
  const elenco = await stato2.json();
  assert.equal(elenco.ospiti.length, 1);
  assert.ok(!elenco.aree.some((a) => a.id === 'privato'));

  const rev = await porta.gestisci(req(`/porta/api/ospiti/${dati.ospite.id}/revoca`, {
    metodo: 'POST', cookie: cp, intestazioni: { 'x-porta': '1' },
  }));
  assert.equal(rev.status, 200);
  assert.equal((await porta.gestisci(req('/tarocchi', { cookie: cg }))).status, 303, 'dopo la revoca il cookie non vale più');
  const dinuovo = await porta.gestisci(login({ nome: 'Guido', password: dati.password }));
  assert.equal(dinuovo.status, 401);
});

test('accesso ospite scade da solo e il nome si libera', async () => {
  const { porta, tempo } = setup();
  const cp = await entraProprietario(porta);
  const { dati } = await creaOspite(porta, cp, { nome: 'Anna', aree: ['musica'], giorni: 1 });
  const cg = cookieDa(await porta.gestisci(login({ nome: 'Anna', password: dati.password })));
  assert.equal(await porta.gestisci(req('/musica', { cookie: cg })), null);
  tempo.ora += 2 * 86_400_000;
  assert.equal((await porta.gestisci(req('/musica', { cookie: cg }))).status, 303);
  const cp2 = await entraProprietario(porta);
  const di_nuovo = await creaOspite(porta, cp2, { nome: 'Anna', aree: ['musica'], giorni: 1 });
  assert.equal(di_nuovo.stato, 201);
});

test('Redis giù: gli ospiti restano fuori', async () => {
  const { porta, redis } = setup();
  const cp = await entraProprietario(porta);
  const { dati } = await creaOspite(porta, cp, { nome: 'Luca', aree: ['tarocchi'] });
  const cg = cookieDa(await porta.gestisci(login({ nome: 'Luca', password: dati.password })));
  redis.spegni();
  assert.equal((await porta.gestisci(req('/tarocchi', { cookie: cg }))).status, 303);
});

test('API proprietario: anti-CSRF e validazione', async () => {
  const { porta } = setup();
  const cp = await entraProprietario(porta);
  const senzaHeader = await porta.gestisci(req('/porta/api/ospiti', {
    metodo: 'POST', cookie: cp, corpo: JSON.stringify({ nome: 'X', aree: ['tarocchi'] }),
  }));
  assert.equal(senzaHeader.status, 403);
  assert.equal((await creaOspite(porta, cp, { nome: 'X', aree: ['privato'] })).stato, 400);
  assert.equal((await creaOspite(porta, cp, { nome: 'X', aree: [] })).stato, 400);
  assert.equal((await creaOspite(porta, cp, { nome: '<script>', aree: ['tarocchi'] })).stato, 400);
  assert.equal((await creaOspite(porta, cp, { nome: 'X', aree: ['tarocchi'], giorni: 999 })).stato, 400);
  assert.equal((await creaOspite(porta, cp, { nome: 'X', aree: ['tarocchi'], password: 'corta' })).stato, 400);
});

test('la pagina /porta/chiave produce un hash che la porta accetta', async () => {
  const { porta } = setup();
  const r = await porta.gestisci(req('/porta/chiave'));
  assert.equal(r.status, 200);
  assert.match(await r.text(), /pbkdf2:sha256:600000\$/);
  // Stesso calcolo del browser (PBKDF2-SHA256, 600000 giri, sale testuale).
  const crypto = await import('node:crypto');
  const sale = 'a1b2c3d4e5f60718293a4b5c';
  const hex = crypto.pbkdf2Sync('nuova-chiave-di-claudio', sale, 600000, 32, 'sha256').toString('hex');
  const hash = `pbkdf2:sha256:600000$${sale}$${hex}`;
  const nuova = creaPorta({ env: { R3_PORTA_SECRET: SEGRETO, R3_PORTA_OWNER_HASH: hash, PERFUME_ARCHIVE_PASSWORD_HASH: HASH_SCRYPT }, catalogo: CATALOGO, mappa: MAPPA, redis: null });
  assert.equal((await nuova.gestisci(login({ password: 'nuova-chiave-di-claudio' }))).status, 303);
  assert.equal((await nuova.gestisci(login({ password: PASSWORD }))).status, 401, 'la chiave nuova sostituisce quella dell\'archivio');
});

test('senza segreto di sessione nessuno entra (fallisce chiuso)', async () => {
  const porta = creaPorta({ env: { PERFUME_ARCHIVE_PASSWORD_HASH: HASH_SCRYPT }, catalogo: CATALOGO, mappa: MAPPA, redis: null });
  assert.equal((await porta.gestisci(login({ password: PASSWORD }))).status, 503);
  assert.equal((await porta.gestisci(req('/tarocchi'))).status, 303);
});

// ------------------------------------------------------------ Sentinella

const IP_INTRUSO = '6.6.6.6';
const daIp = (percorso, ip = IP_INTRUSO, opz = {}) =>
  req(percorso, { ...opz, intestazioni: { ...(opz.intestazioni || {}), 'x-forwarded-for': ip } });

test('trappola /.env: esca con valori finti, intruso bandito, avviso a Claudio', async () => {
  const { porta, avvisi } = setup();
  const r = await porta.gestisci(daIp('/.env'));
  assert.equal(r.status, 200);
  assert.match(await r.text(), /DB_PASSWORD=bel-tentativo-ma-no/);
  const dopo = await porta.gestisci(daIp('/tarocchi'));
  assert.match(await dopo.text(), /Raffaello ti saluta/);
  assert.equal(avvisi.length, 1);
  assert.match(avvisi[0], /bandito 6\.6\.6\.6/);
  // Un altro indirizzo non è toccato.
  assert.equal((await porta.gestisci(daIp('/tarocchi', '7.7.7.7'))).status, 303);
});

test('finto pannello WordPress: dice sempre credenziali errate', async () => {
  const { porta } = setup();
  const r = await porta.gestisci(daIp('/wp-login.php'));
  assert.match(await r.text(), /Credenziali errate/);
});

test('percorso truccato (barra codificata con ..) → esca e bando', async () => {
  const { porta } = setup();
  // %2e%2e lo risolve già il parser degli URL; %2f invece arriva intatto alla porta.
  const r = await porta.gestisci(daIp('/a%2f..%2fprivato.html'));
  assert.match(await r.text(), /Raffaello ti saluta/);
  assert.match(await (await porta.gestisci(daIp('/tarocchi'))).text(), /Raffaello ti saluta/);
});

test('cookie falsificato: tre tentativi e sei fuori', async () => {
  const { porta } = setup();
  const falso = `${Buffer.from(JSON.stringify({ r: 'p', exp: 9e15 })).toString('base64url')}.AAAA`;
  for (let i = 0; i < 2; i++) assert.equal((await porta.gestisci(daIp('/privato', IP_INTRUSO, { cookie: falso }))).status, 303);
  const terzo = await porta.gestisci(daIp('/privato', IP_INTRUSO, { cookie: falso }));
  assert.equal(terzo.status, 303, 'al terzo arriva a 12 punti e scatta il bando');
  assert.match(await (await porta.gestisci(daIp('/privato', IP_INTRUSO, { cookie: falso }))).text(), /Raffaello ti saluta/);
});

test('dieci password sbagliate: bandito; Claudio entra lo stesso dalla riserva', async () => {
  const { porta } = setup();
  for (let i = 0; i < 10; i++) await porta.gestisci(login({ nome: 'chiunque', password: 'no' }, IP_INTRUSO));
  const intruso = await porta.gestisci(login({ nome: 'chiunque', password: 'no' }, IP_INTRUSO));
  assert.match(await intruso.text(), /Raffaello ti saluta/);
  const claudio = await porta.gestisci(login({ password: PASSWORD }, IP_INTRUSO));
  assert.equal(claudio.status, 303, 'Claudio è immune anche da un indirizzo bandito');
  // La riserva è stretta: chi non conosce la password non può usarla per indovinare all'infinito.
  for (let i = 0; i < 2; i++) await porta.gestisci(login({ password: 'tentativo' }, IP_INTRUSO));
  const oltre = await porta.gestisci(login({ password: PASSWORD }, IP_INTRUSO));
  assert.match(await oltre.text(), /Raffaello ti saluta/);
});

test('il proprietario è immune: può chiedere anche le trappole', async () => {
  const { porta, avvisi } = setup();
  const cp = await entraProprietario(porta);
  assert.equal(await porta.gestisci(daIp('/.env', IP_INTRUSO, { cookie: cp })), null);
  assert.equal(await porta.gestisci(daIp('/wp-admin', IP_INTRUSO, { cookie: cp })), null);
  assert.equal(avvisi.length, 0);
});

test('ospite che fruga tra i file chiusi viene sospeso', async () => {
  const { porta, avvisi } = setup();
  const cp = await entraProprietario(porta);
  const { dati } = await creaOspite(porta, cp, { nome: 'Curioso', aree: ['tarocchi'] });
  const cg = cookieDa(await porta.gestisci(login({ nome: 'Curioso', password: dati.password }, '5.5.5.5')));
  // Qualche clic sul menu verso pagine chiuse non basta a sospenderlo.
  for (let i = 0; i < 3; i++) {
    assert.equal((await porta.gestisci(daIp('/libro', '5.5.5.5', { cookie: cg }))).status, 403);
  }
  // Chiedere file di dati chiusi uno dopo l'altro sì: 3 punti l'uno, sospeso a 15.
  const chiusi = Object.entries(MAPPA)
    .filter(([k, aree]) => !aree.includes('tarocchi') && /\.(js|json)$/.test(k))
    .map(([k]) => k).slice(0, 4);
  const esiti = [];
  for (const f of chiusi) {
    const r = await porta.gestisci(daIp(f, '5.5.5.5', { cookie: cg, intestazioni: { accept: '*/*' } }));
    esiti.push(r.status === 200 && /Raffaello ti saluta/.test(await r.text()));
  }
  assert.deepEqual(esiti, [false, false, false, true], 'al quarto file (3 + 12 = 15 punti) scatta la sospensione');
  assert.match(avvisi.at(-1), /sospeso l'ospite Curioso/);
  assert.equal((await porta.gestisci(daIp('/tarocchi', '5.5.5.5', { cookie: cg }))).status, 303, 'sessione chiusa');
});

test('Claudio vede i banditi e può sbloccarli', async () => {
  const { porta } = setup();
  await porta.gestisci(daIp('/.git/config'));
  const cp = await entraProprietario(porta);
  const st = await (await porta.gestisci(req('/porta/api/sentinella', { cookie: cp }))).json();
  assert.deepEqual(st.banditi.map((b) => b.ip), [IP_INTRUSO]);
  assert.equal(st.eventi[0].tipo, 'bando');
  const sb = await porta.gestisci(req('/porta/api/sentinella/sblocca', {
    metodo: 'POST', cookie: cp, corpo: JSON.stringify({ ip: IP_INTRUSO }),
    intestazioni: { 'content-type': 'application/json', 'x-porta': '1' },
  }));
  assert.equal(sb.status, 200);
  assert.equal((await porta.gestisci(daIp('/tarocchi'))).status, 303, 'di nuovo trattato come un visitatore qualunque');
});

test('Sentinella con Redis giù: non blocca nessuno e la Porta resta chiusa', async () => {
  const { porta, redis } = setup();
  redis.spegni();
  assert.equal((await porta.gestisci(daIp('/libro'))).status, 303);
  assert.match(await (await porta.gestisci(daIp('/.env'))).text(), /bel-tentativo/);
});
