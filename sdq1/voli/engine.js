/*
 * engine.js — Motore di caccia prezzi voli (Protocollo Rosso Rosso Rosso).
 *
 * Non segue i blog di offerte: interroga direttamente il motore di Google
 * Flights e legge i prezzi reali. Pensato per girare dietro il proxy di
 * egress dell'ambiente Claude: il TLS del browser viene resettato dal proxy,
 * quindi ogni richiesta è instradata attraverso lo stack di rete di Node
 * (route.fetch), che fa terminare il TLS sul CA bundle giusto.
 *
 * Uso:
 *   node engine.js '{"legs":[{"from":"Brussels","to":"Sao Paulo","date":"February 15, 2027"},
 *                            {"from":"Sao Paulo","to":"Paris","date":"March 1, 2027"}]}'
 *
 * Output (stdout, JSON su una riga):
 *   {"ok":true,"min_eur":179,"offers":[{"price_eur":179,"summary":"..."}],"query":{...}}
 *
 * Richiede: playwright (Chromium in PLAYWRIGHT_BROWSERS_PATH) e
 * NODE_EXTRA_CA_CERTS puntato al CA bundle del proxy.
 */

const { chromium } = require('playwright');
const fs = require('fs');

// Usa il Chromium preinstallato dell'ambiente se presente (evita mismatch di
// versione tra il pacchetto npm e la build del browser scaricata).
function launchOptions() {
  const opts = { headless: true, args: ['--no-sandbox'] };
  const candidates = [process.env.PW_CHROMIUM, '/opt/pw-browsers/chromium'];
  for (const p of candidates) {
    if (p && fs.existsSync(p)) {
      opts.executablePath = p;
      break;
    }
  }
  return opts;
}

function parseArgs() {
  const raw = process.argv[2];
  if (!raw) throw new Error('manca il JSON della query come primo argomento');
  const q = JSON.parse(raw);
  if (!Array.isArray(q.legs) || q.legs.length < 1) throw new Error('query.legs mancante o vuoto');
  return q;
}

async function hunt(query) {
  const browser = await chromium.launch(launchOptions());
  const ctx = await browser.newContext({
    locale: 'en-US',
    viewport: { width: 1440, height: 900 },
    userAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
  });
  // Il proxy resetta il TLS del browser: tunnel di ogni richiesta via Node.
  await ctx.route('**/*', async (route) => {
    try {
      const resp = await route.fetch({ maxRedirects: 3 });
      await route.fulfill({ response: resp });
    } catch (e) {
      await route.abort().catch(() => {});
    }
  });
  const page = await ctx.newPage();
  const vis = (sel) => page.locator(sel).locator('visible=true');

  try {
    await page.goto('https://www.google.com/travel/flights?hl=en&curr=EUR', {
      waitUntil: 'domcontentloaded',
      timeout: 60000,
    });
    await page.waitForTimeout(3000);
    for (const label of ['Reject all', 'Accept all', 'I agree']) {
      const btn = page.locator(`button:has-text("${label}")`).first();
      if ((await btn.count()) && (await btn.isVisible().catch(() => false))) {
        await btn.click().catch(() => {});
        await page.waitForTimeout(2500);
        break;
      }
    }

    // Multi-city (una tratta per ogni leg).
    await page
      .locator('div[role="combobox"]:has-text("Round trip"), [aria-label*="Round trip"]')
      .first()
      .click();
    await page.waitForTimeout(1000);
    await page.locator('li:has-text("Multi-city"), [role="option"]:has-text("Multi-city")').first().click();
    await page.waitForTimeout(2000);

    // Aggiunge le tratte necessarie (parte con 2 righe di default).
    while ((await vis('input[aria-label^="Where from?"]').count()) < query.legs.length) {
      await page.locator('button:has-text("Add flight")').locator('visible=true').first().click();
      await page.waitForTimeout(1200);
    }

    async function fillPlace(kind, index, text) {
      await vis(`input[aria-label^="${kind}"]`).nth(index).click();
      await page.waitForTimeout(1200);
      await page.keyboard.type(text, { delay: 90 });
      await page.waitForTimeout(2800);
      const opt = page.locator('ul[role="listbox"] li[role="option"]').locator('visible=true').first();
      if (await opt.count()) {
        await opt.click().catch(async () => { await page.keyboard.press('Enter'); });
      } else {
        await page.keyboard.press('Enter');
      }
      await page.waitForTimeout(1500);
    }

    async function fillDate(index, dateText) {
      await vis('input[aria-label^="Departure"]').nth(index).click();
      await page.waitForTimeout(1500);
      await page.keyboard.type(dateText, { delay: 60 });
      await page.waitForTimeout(1200);
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1200);
      const done = page.locator('button:has-text("Done")').locator('visible=true').first();
      if (await done.count()) { await done.click().catch(() => {}); await page.waitForTimeout(1200); }
      await page.keyboard.press('Escape');
      await page.waitForTimeout(800);
    }

    for (let i = 0; i < query.legs.length; i++) {
      await fillPlace('Where from?', i, query.legs[i].from);
      await fillPlace('Where to?', i, query.legs[i].to);
      await fillDate(i, query.legs[i].date);
    }

    await page.locator('button[aria-label="Search"], button:has-text("Search")').locator('visible=true').first().click();

    // Attende il rendering dei prezzi (max ~90s).
    for (let i = 0; i < 18; i++) {
      await page.waitForTimeout(5000);
      const t = await page.evaluate(() => document.body.innerText);
      if (/€\s?\d{2,}/.test(t) || /No results|no matching flights|No flights/i.test(t)) break;
    }

    // Estrae le offerte: righe con un prezzo in euro + contesto precedente.
    const offers = await page.evaluate(() => {
      const lines = document.body.innerText.split('\n').map((l) => l.trim());
      const out = [];
      const priceRe = /^€\s?([\d.,]+)$|^([\d.,]+)\s?€$/;
      for (let i = 0; i < lines.length; i++) {
        const m = lines[i].match(priceRe);
        if (!m) continue;
        const num = parseInt((m[1] || m[2]).replace(/[.,]/g, ''), 10);
        if (!num || num < 20) continue;
        const summary = lines.slice(Math.max(0, i - 6), i).filter(Boolean).join(' · ');
        out.push({ price_eur: num, summary });
      }
      return out;
    });

    offers.sort((a, b) => a.price_eur - b.price_eur);
    const min = offers.length ? offers[0].price_eur : null;
    return { ok: true, min_eur: min, offers: offers.slice(0, 8), query };
  } finally {
    await browser.close();
  }
}

(async () => {
  try {
    const query = parseArgs();
    const result = await hunt(query);
    process.stdout.write(JSON.stringify(result));
  } catch (e) {
    process.stdout.write(JSON.stringify({ ok: false, error: e.message }));
    process.exit(1);
  }
})();
