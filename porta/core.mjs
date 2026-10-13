// La Porta — nucleo puro (nessuna rete): sessioni firmate, password, permessi.
// Usato dal middleware Vercel e dai test con node:test.

import crypto from 'node:crypto';

// ---------------------------------------------------------------- permessi

export function compilaCatalogo(catalogo, mappa) {
  const aree = catalogo.aree.map((a) => ({
    ...a,
    regex: a.percorsi.map((p) => new RegExp(p)),
  }));
  return {
    aree,
    ospitabili: aree.filter((a) => !a.solo_proprietario),
    comuni: (catalogo.comuni || []).map((p) => new RegExp(p)),
    mappa: mappa || {},
  };
}

// Percorso canonico: decodificato, senza prefisso /public, senza //.
// Restituisce null se il percorso è sospetto (.., byte nulli, codifica rotta).
export function normalizza(percorso) {
  let p;
  try {
    p = decodeURIComponent(percorso);
  } catch {
    return null;
  }
  if (p.includes('\0') || p.includes('\\')) return null;
  p = p.replace(/\/{2,}/g, '/');
  if (p.split('/').some((s) => s === '..' || s === '.')) return null;
  if (p === '/public') return '/';
  if (p.startsWith('/public/')) p = p.slice('/public'.length);
  return p || '/';
}

export function classifica(percorso, cat) {
  const p = normalizza(percorso);
  if (p === null) return { soloProprietario: true, aree: [] };
  for (const a of cat.aree) {
    if (a.solo_proprietario && a.regex.some((r) => r.test(p))) {
      return { soloProprietario: true, aree: [] };
    }
  }
  const aree = new Set(cat.mappa[p] || []);
  for (const a of cat.ospitabili) {
    if (a.regex.some((r) => r.test(p))) aree.add(a.id);
  }
  const comune = cat.comuni.some((r) => r.test(p));
  return { soloProprietario: false, aree: [...aree], comune };
}

// Chiuso per default: un ospite vede solo i percorsi di un'area che gli è aperta.
export function puoVedere(sessione, percorso, cat) {
  if (!sessione) return false;
  if (sessione.ruolo === 'proprietario') return true;
  const c = classifica(percorso, cat);
  if (c.soloProprietario) return false;
  if (c.comune) return true;
  const aperte = new Set(sessione.aree || []);
  return c.aree.some((a) => aperte.has(a));
}

// ---------------------------------------------------------------- sessioni

const b64 = (buf) => Buffer.from(buf).toString('base64url');

export function chiaveSessione(segreto) {
  if (!segreto || segreto.length < 16) return null;
  return crypto.createHmac('sha256', segreto).update('r3-porta-sessione-v1').digest();
}

export function firmaSessione(dati, chiave) {
  const corpo = b64(JSON.stringify(dati));
  const firma = b64(crypto.createHmac('sha256', chiave).update(corpo).digest());
  return `${corpo}.${firma}`;
}

export function leggiSessione(token, chiave, ora = Date.now()) {
  if (!token || !chiave || token.length > 4096) return null;
  const [corpo, firma, extra] = token.split('.');
  if (!corpo || !firma || extra !== undefined) return null;
  const attesa = crypto.createHmac('sha256', chiave).update(corpo).digest();
  const data = Buffer.from(firma, 'base64url');
  if (data.length !== attesa.length || !crypto.timingSafeEqual(data, attesa)) return null;
  let dati;
  try {
    dati = JSON.parse(Buffer.from(corpo, 'base64url').toString('utf8'));
  } catch {
    return null;
  }
  if (!dati || typeof dati.exp !== 'number' || dati.exp <= ora) return null;
  return dati;
}

// true se il token porta una firma che non è nostra (manomesso o inventato).
export function firmaFalsa(token, chiave) {
  if (!token || !chiave) return false;
  const [corpo, firma] = token.split('.');
  if (!corpo || !firma) return true;
  const attesa = crypto.createHmac('sha256', chiave).update(corpo).digest();
  const data = Buffer.from(firma, 'base64url');
  return data.length !== attesa.length || !crypto.timingSafeEqual(data, attesa);
}

export function leggiCookie(header, nome) {
  for (const parte of (header || '').split(';')) {
    const i = parte.indexOf('=');
    if (i > 0 && parte.slice(0, i).trim() === nome) return parte.slice(i + 1).trim();
  }
  return null;
}

// ---------------------------------------------------------------- password

// Formato compatibile con werkzeug.security: "metodo$sale$hex".
export function verificaPassword(hash, password) {
  if (typeof hash !== 'string' || typeof password !== 'string' || password.length > 1024) {
    return false;
  }
  const [metodo, sale, atteso] = hash.split('$');
  if (!metodo || !sale || !atteso || !/^[0-9a-f]+$/i.test(atteso)) return false;
  const parti = metodo.split(':');
  let calcolato;
  try {
    if (parti[0] === 'scrypt') {
      const [N, r, p] = [Number(parti[1] || 32768), Number(parti[2] || 8), Number(parti[3] || 1)];
      if (!(N >= 2 && N <= 1 << 20 && r >= 1 && r <= 32 && p >= 1 && p <= 16)) return false;
      calcolato = crypto.scryptSync(password, sale, 64, { N, r, p, maxmem: 132 * N * r * p });
    } else if (parti[0] === 'pbkdf2') {
      const algo = parti[1] || 'sha256';
      const giri = Number(parti[2] || 600000);
      if (!['sha256', 'sha512'].includes(algo) || !(giri >= 1000 && giri <= 5_000_000)) return false;
      const lung = algo === 'sha512' ? 64 : 32;
      calcolato = crypto.pbkdf2Sync(password, sale, giri, lung, algo);
    } else {
      return false;
    }
  } catch {
    return false;
  }
  const buf = Buffer.from(atteso, 'hex');
  return buf.length === calcolato.length && crypto.timingSafeEqual(buf, calcolato);
}

export function creaHash(password) {
  const sale = crypto.randomBytes(12).toString('base64url');
  const N = 16384, r = 8, p = 1;
  const hex = crypto.scryptSync(password, sale, 64, { N, r, p, maxmem: 132 * N * r * p }).toString('hex');
  return `scrypt:${N}:${r}:${p}$${sale}$${hex}`;
}

// 12 caratteri leggibili al telefono (niente 0/o, 1/l/i): ~59 bit.
const ALFABETO = 'abcdefghjkmnpqrstuvwxyz23456789';
export function nuovaPassword() {
  const out = [];
  for (let i = 0; i < 12; i++) out.push(ALFABETO[crypto.randomInt(ALFABETO.length)]);
  return `${out.slice(0, 4).join('')}-${out.slice(4, 8).join('')}-${out.slice(8).join('')}`;
}

// ---------------------------------------------------------------- validazione

export function nomeValido(nome) {
  return typeof nome === 'string' && /^[\p{L}\p{N}][\p{L}\p{N} .'-]{0,39}$/u.test(nome.trim());
}

export function chiaveNome(nome) {
  return nome.trim().toLocaleLowerCase('it').replace(/\s+/g, ' ');
}

export function areeValide(aree, cat) {
  if (!Array.isArray(aree) || aree.length === 0) return false;
  const ok = new Set(cat.ospitabili.map((a) => a.id));
  return aree.every((a) => ok.has(a));
}

// Solo percorsi interni: niente "//host", niente schema, niente backslash.
export function destinazioneSicura(torna) {
  if (typeof torna !== 'string' || !torna.startsWith('/') || torna.startsWith('//')) return '/';
  if (/[\\\r\n]/.test(torna) || torna.length > 512) return '/';
  return torna;
}
