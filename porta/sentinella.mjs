// La Sentinella: scopre chi forza la Porta, lo espelle e gli serve un'esca.
// Il proprietario è immune: con la sua sessione la Sentinella non interviene.

export const SOGLIA_BANDO = 10;
export const SOGLIA_OSPITE = 15;
const DURATA_BANDO_S = 86_400;
const FINESTRA_PUNTI_S = 3_600;
const RISERVA_PROPRIETARIO = 3; // tentativi di password del proprietario da un indirizzo bandito, per ora

export const PUNTI = {
  trappola: 10,
  percorso_sospetto: 10,
  cookie_falso: 4,
  login_fallito: 1,
  ospite_fuori_pagina: 1,
  ospite_fuori_file: 3,
};

// Percorsi che nessun visitatore legittimo di questo sito chiede: solo gli scanner.
export const TRAPPOLA = new RegExp(
  '^/(?:wp-admin|wp-login\\.php|wp-content|wp-includes|xmlrpc\\.php|phpmyadmin|pma|myadmin|'
  + 'admin\\.php|administrator|\\.env(?:\\..*)?|\\.git|\\.svn|\\.hg|\\.aws|\\.ssh|\\.htaccess|\\.htpasswd|'
  + 'config\\.php|configuration\\.php|server-status|actuator|vendor/phpunit|cgi-bin|'
  + 'backup\\.(?:zip|sql|tar\\.gz)|db\\.sql|dump\\.sql|database\\.sql|\\.DS_Store|id_rsa|shell\\.php)(?:/|$)',
  'i',
);

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[c]));

// ---------------------------------------------------------------- esche

const ENV_FINTO = `# configurazione di produzione
APP_ENV=production
APP_DEBUG=false
DB_HOST=127.0.0.1
DB_USER=raffaello
DB_PASSWORD=bel-tentativo-ma-no
SECRET_KEY=la-casa-si-e-spostata
AWS_ACCESS_KEY_ID=AKIA-TI-STO-GUARDANDO
AWS_SECRET_ACCESS_KEY=riprova-tra-mille-anni
ADMIN_EMAIL=nessuno@da.nessuna.parte
`;

function htmlEsca(titolo, corpo) {
  return `<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>${esc(titolo)}</title><style>body{font-family:Georgia,serif;background:#0c0c0e;color:#e8e4d8;
max-width:560px;margin:4rem auto;padding:0 1rem;line-height:1.6}h1{color:#c9a84c;font-weight:normal}
input{display:block;width:100%;margin:.4rem 0;padding:.5rem}em{color:#8d877a}</style></head>
<body>${corpo}</body></html>`;
}

export function esca(percorso) {
  const p = percorso.toLowerCase();
  if (/^\/\.env/.test(p)) {
    return new Response(ENV_FINTO, { status: 200, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
  }
  if (/^\/(wp-|xmlrpc|phpmyadmin|pma|myadmin|admin|administrator)/.test(p)) {
    return new Response(htmlEsca('Pannello di amministrazione', `<h1>Pannello di amministrazione</h1>
<form method="post"><input name="u" placeholder="utente"><input name="p" type="password" placeholder="password">
<button>Accedi</button></form><p><em>Credenziali errate. Riprova (ancora).</em></p>`), {
      status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8' },
    });
  }
  return new Response(htmlEsca('Raffaello ti saluta', `<h1>Raffaello ti saluta</h1>
<p>Hai bussato a una porta che non c'è. Il tuo passaggio è stato annotato,
la casa si è già spostata e tu stai guardando un'eco.</p>
<p>Qui non c'è niente da prendere: soltanto questa lettera, scritta apposta per te.</p>
<p><em>Torna quando sarai invitato. Con garbo feroce, R.</em></p>`), {
    status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' },
  });
}

// ---------------------------------------------------------------- sentinella

export function creaSentinella({ db, notifica = async () => {}, ora = () => Date.now() }) {
  if (!db) return null;

  async function annota(ip, tipo, percorso, punti, extra = {}) {
    const evento = { t: ora(), ip, tipo, percorso: String(percorso).slice(0, 200), punti, ...extra };
    await db('LPUSH', 'sentinella:eventi', JSON.stringify(evento));
    await db('LTRIM', 'sentinella:eventi', 0, 299);
  }

  async function bandisci(ip, motivo) {
    const gia = await db('SET', `sentinella:bando:${ip}`, JSON.stringify({ dal: ora(), motivo }), 'EX', DURATA_BANDO_S, 'NX');
    if (gia !== 'OK') return;
    await db('SADD', 'sentinella:banditi', ip);
    await annota(ip, 'bando', '-', 0, { motivo });
    await notifica(`🛡 Sentinella: bandito ${ip} per 24 ore (${motivo}). Gli sto servendo un'esca.`);
  }

  // Aggiunge punti a un indirizzo; oltre la soglia lo bandisce. Mai lancia: un guasto
  // della Sentinella non deve chiudere fuori nessuno né aprire niente.
  async function colpisci(ip, tipo, percorso) {
    try {
      const punti = PUNTI[tipo] ?? 1;
      const totale = await db('INCRBY', `sentinella:punti:${ip}`, punti);
      if (totale === punti) await db('EXPIRE', `sentinella:punti:${ip}`, FINESTRA_PUNTI_S);
      await annota(ip, tipo, percorso, punti);
      if (totale >= SOGLIA_BANDO) await bandisci(ip, tipo);
      return totale;
    } catch {
      return 0;
    }
  }

  // Ospite che fruga fuori dalle sue aree: oltre la soglia viene sospeso.
  async function colpisciOspite(ospite, ip, tipo, percorso) {
    try {
      const punti = PUNTI[tipo] ?? 1;
      const totale = await db('INCRBY', `sentinella:ospite:${ospite.id}`, punti);
      if (totale === punti) await db('EXPIRE', `sentinella:ospite:${ospite.id}`, FINESTRA_PUNTI_S);
      await annota(ip, tipo, percorso, punti, { ospite: ospite.nome });
      return totale >= SOGLIA_OSPITE;
    } catch {
      return false;
    }
  }

  async function bandito(ip) {
    try {
      return Boolean(await db('GET', `sentinella:bando:${ip}`));
    } catch {
      return false;
    }
  }

  // Il proprietario resta immune anche se il suo indirizzo è stato bandito per sbaglio:
  // pochi tentativi l'ora, così la riserva non diventa un varco per indovinare la password.
  async function riservaProprietario(ip) {
    try {
      const n = await db('INCR', `sentinella:riserva:${ip}`);
      if (n === 1) await db('EXPIRE', `sentinella:riserva:${ip}`, 3_600);
      return n <= RISERVA_PROPRIETARIO;
    } catch {
      return true;
    }
  }

  async function stato() {
    const eventi = ((await db('LRANGE', 'sentinella:eventi', 0, 49)) || []).map((e) => JSON.parse(e));
    const banditi = [];
    for (const ip of (await db('SMEMBERS', 'sentinella:banditi')) || []) {
      const raw = await db('GET', `sentinella:bando:${ip}`);
      if (raw) banditi.push({ ip, ...JSON.parse(raw) });
      else await db('SREM', 'sentinella:banditi', ip);
    }
    return { eventi, banditi };
  }

  async function sblocca(ip) {
    await db('DEL', `sentinella:bando:${ip}`);
    await db('DEL', `sentinella:punti:${ip}`);
    await db('SREM', 'sentinella:banditi', ip);
    await annota(ip, 'sblocco', '-', 0);
  }

  return { colpisci, colpisciOspite, bandito, riservaProprietario, stato, sblocca };
}

export function notificaTelegram(env, fetchImpl = fetch) {
  const token = env.TELEGRAM_BOT_TOKEN;
  const chat = env.TELEGRAM_CHAT_ID;
  if (!token || !chat) return async () => {};
  return async (testo) => {
    try {
      await fetchImpl(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: chat, text: testo }),
        signal: AbortSignal.timeout(2500),
      });
    } catch {
      // l'avviso è un di più: la Sentinella lavora anche senza
    }
  };
}
