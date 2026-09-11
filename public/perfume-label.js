/* Creatore interno di immagini per le ricette · Concept Claudio Terzi · © 2026.
   L'immagine può arrivare dall'AI o dal flacone 3D, ma l'etichetta viene sempre
   composta nel browser con i dati della scheda. Se tutto il resto manca, il
   disegno procedurale produce comunque un'immagine scaricabile. */
(function (root) {
  'use strict';

  const PALETTE = [
    ['#263f4a', '#c99e49', '#9c6c35'],
    ['#3a3048', '#d2b16a', '#765083'],
    ['#223b35', '#d5bd77', '#477967'],
    ['#412c2a', '#d6a75a', '#8b4b38'],
    ['#27333e', '#bcc7bd', '#4a7f91'],
    ['#3b3025', '#dfbb73', '#9b613d'],
  ];

  function text(value, fallback) {
    const result = String(value == null ? '' : value).replace(/\s+/g, ' ').trim();
    return result || fallback;
  }

  function hash(value) {
    let h = 2166136261;
    for (const ch of text(value, 'terzi')) h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0;
    return h >>> 0;
  }

  function roundedRect(ctx, x, y, width, height, radius) {
    const r = Math.min(radius, width / 2, height / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + width - r, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + r);
    ctx.lineTo(x + width, y + height - r);
    ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
    ctx.lineTo(x + r, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  function fitFont(ctx, value, maxWidth, size, family, weight) {
    let current = size;
    do {
      ctx.font = `${weight || 'normal'} ${current}px ${family || 'Georgia, serif'}`;
      if (ctx.measureText(value).width <= maxWidth || current <= 8) return current;
      current -= 1;
    } while (current > 8);
    return current;
  }

  function wrap(ctx, value, maxWidth, maxLines, size, family, weight) {
    const words = text(value, '').split(' ');
    const lines = [];
    let line = '';
    for (const word of words) {
      const candidate = line ? `${line} ${word}` : word;
      ctx.font = `${weight || 'normal'} ${size}px ${family || 'Georgia, serif'}`;
      if (line && ctx.measureText(candidate).width > maxWidth) {
        lines.push(line);
        line = word;
      } else line = candidate;
    }
    if (line) lines.push(line);
    if (lines.length <= maxLines) return lines;
    const kept = lines.slice(0, maxLines);
    let last = kept[maxLines - 1];
    while (last.length && ctx.measureText(`${last}…`).width > maxWidth) last = last.slice(0, -1);
    kept[maxLines - 1] = `${last.trimEnd()}…`;
    return kept;
  }

  function accentNames(meta) {
    const perfume = meta && meta.perfume;
    const direct = perfume && perfume.flacone && Array.isArray(perfume.flacone.accenti)
      ? perfume.flacone.accenti : [];
    const rows = perfume && Array.isArray(perfume.ricetta) ? perfume.ricetta : [];
    const fromRows = rows.map(row => Array.isArray(row) ? row[0] : row && (row.nome || row.name)).filter(Boolean);
    return [...new Set([...direct, ...fromRows].map(value => text(value, '')).filter(Boolean))].slice(0, 4);
  }

  function metadata(meta) {
    const perfume = meta && meta.perfume;
    const fingerprint = text(meta && meta.fingerprint,
      text(perfume && perfume.flacone && perfume.flacone.recipe_fingerprint, 'bozza'));
    return {
      name: text(meta && meta.name, text(perfume && perfume.nome, 'Creazione Terzi')),
      customer: text(meta && meta.customer, 'Atelier'),
      serial: text(meta && meta.serial, `BOZZA · ${fingerprint.slice(0, 8).toUpperCase()}`),
      family: text(meta && (meta.family || meta.fam), text(perfume && perfume.fam, 'Atelier')),
      concept: text(meta && meta.concept, text(perfume && perfume.concept, 'Una traccia personale da scoprire.')),
      accents: accentNames(meta),
      fingerprint,
    };
  }

  function drawLabel(ctx, width, height, meta) {
    const info = metadata(meta);
    const labelWidth = width * .31;
    const labelHeight = height * .2;
    const left = (width - labelWidth) / 2;
    const top = height * .47;
    const pad = Math.max(10, width * .018);
    ctx.save();
    roundedRect(ctx, left, top, labelWidth, labelHeight, Math.max(5, width * .008));
    ctx.fillStyle = 'rgba(23,20,16,.95)';
    ctx.fill();
    ctx.strokeStyle = '#b29a66';
    ctx.lineWidth = Math.max(1, width / 700);
    ctx.stroke();
    roundedRect(ctx, left + pad, top + pad, labelWidth - pad * 2, labelHeight - pad * 2, Math.max(3, width * .004));
    ctx.strokeStyle = 'rgba(226,196,126,.34)';
    ctx.lineWidth = Math.max(.6, width / 1400);
    ctx.stroke();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const center = left + labelWidth / 2;
    const family = 'Georgia, Times New Roman, serif';
    const brandSize = fitFont(ctx, 'TERZI PARFUMS', labelWidth - pad * 2, width * .024, family, 'normal');
    ctx.font = `normal ${brandSize}px ${family}`;
    ctx.fillStyle = '#e4c68b';
    ctx.letterSpacing = '0.08em';
    ctx.fillText('TERZI PARFUMS', center, top + labelHeight * .18);
    const nameSize = fitFont(ctx, info.name, labelWidth - pad * 2, width * .04, family, 'normal');
    const nameLines = wrap(ctx, info.name, labelWidth - pad * 2, 3, nameSize, family, 'normal');
    ctx.font = `normal ${nameSize}px ${family}`;
    const lineHeight = nameSize * 1.12;
    const nameStart = top + labelHeight * .49 - (nameLines.length - 1) * lineHeight / 2;
    nameLines.forEach((line, index) => ctx.fillText(line, center, nameStart + index * lineHeight));
    const clientSize = fitFont(ctx, info.customer, labelWidth - pad * 2, width * .024, family, 'normal');
    ctx.font = `normal ${clientSize}px ${family}`;
    ctx.fillStyle = '#cfb982';
    ctx.fillText(info.customer, center, top + labelHeight * .78);
    const serialSize = fitFont(ctx, info.serial, labelWidth - pad * 2, width * .015, 'monospace', 'normal');
    ctx.font = `normal ${serialSize}px monospace`;
    ctx.fillStyle = '#b29a66';
    ctx.fillText(info.serial, center, top + labelHeight * .91);
    ctx.restore();
  }

  function fallbackCanvas(meta) {
    const info = metadata(meta);
    const colors = PALETTE[hash(info.fingerprint) % PALETTE.length];
    const canvas = document.createElement('canvas');
    canvas.width = 1200;
    canvas.height = 1200;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas non disponibile');
    const bg = ctx.createLinearGradient(0, 0, 1200, 1200);
    bg.addColorStop(0, colors[0]); bg.addColorStop(.55, '#0d1117'); bg.addColorStop(1, '#07090d');
    ctx.fillStyle = bg; ctx.fillRect(0, 0, 1200, 1200);
    const halo = ctx.createRadialGradient(570, 440, 40, 570, 520, 620);
    halo.addColorStop(0, `${colors[1]}55`); halo.addColorStop(1, `${colors[1]}00`);
    ctx.fillStyle = halo; ctx.fillRect(0, 0, 1200, 1200);
    for (let i = 0; i < 42; i++) {
      const x = (hash(`${info.fingerprint}:${i}:x`) % 1160) + 20;
      const y = (hash(`${info.fingerprint}:${i}:y`) % 720) + 30;
      const r = 1 + (i % 3);
      ctx.fillStyle = `rgba(226,196,126,${.18 + (i % 4) * .06})`;
      ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
    }
    const table = ctx.createLinearGradient(0, 850, 0, 1200);
    table.addColorStop(0, '#2e211b'); table.addColorStop(1, '#080a0d');
    ctx.fillStyle = table; ctx.fillRect(0, 900, 1200, 300);
    const shadow = ctx.createRadialGradient(600, 1030, 50, 600, 1030, 390);
    shadow.addColorStop(0, 'rgba(0,0,0,.75)'); shadow.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = shadow; ctx.fillRect(180, 850, 840, 350);
    const shape = hash(info.fingerprint) % 3;
    const body = { x: shape === 1 ? 315 : 285, y: 360, w: shape === 1 ? 570 : 630, h: 610, r: shape === 2 ? 90 : 42 };
    const liquid = ctx.createLinearGradient(body.x, body.y, body.x + body.w, body.y + body.h);
    liquid.addColorStop(0, '#f6d47b'); liquid.addColorStop(.24, colors[1]); liquid.addColorStop(.72, colors[2]); liquid.addColorStop(1, '#6d3c23');
    roundedRect(ctx, body.x + 17, body.y + 22, body.w - 34, body.h - 34, body.r - 12);
    ctx.fillStyle = liquid; ctx.globalAlpha = .9; ctx.fill(); ctx.globalAlpha = 1;
    roundedRect(ctx, body.x, body.y, body.w, body.h, body.r);
    const glass = ctx.createLinearGradient(body.x, body.y, body.x + body.w, body.y);
    glass.addColorStop(0, 'rgba(255,255,255,.55)'); glass.addColorStop(.1, 'rgba(255,255,255,.08)'); glass.addColorStop(.85, 'rgba(255,255,255,.03)'); glass.addColorStop(1, 'rgba(255,255,255,.48)');
    ctx.fillStyle = glass; ctx.fill(); ctx.strokeStyle = 'rgba(239,229,199,.75)'; ctx.lineWidth = 8; ctx.stroke();
    ctx.fillStyle = 'rgba(255,246,215,.26)'; roundedRect(ctx, body.x + 44, body.y + 44, 30, body.h - 90, 15); ctx.fill();
    const neckX = 492, neckY = 285, neckW = 216, neckH = 90;
    roundedRect(ctx, neckX, neckY, neckW, neckH, 22); ctx.fillStyle = '#b38b50'; ctx.fill();
    ctx.strokeStyle = 'rgba(255,233,174,.62)'; ctx.lineWidth = 4; ctx.stroke();
    const capX = 448, capY = 145, capW = 304, capH = 155;
    const cap = ctx.createLinearGradient(capX, capY, capX + capW, capY);
    cap.addColorStop(0, '#24150f'); cap.addColorStop(.48, '#6b3c22'); cap.addColorStop(1, '#20120e');
    roundedRect(ctx, capX, capY, capW, capH, 26); ctx.fillStyle = cap; ctx.fill();
    ctx.strokeStyle = '#c69d55'; ctx.lineWidth = 7; ctx.stroke();
    for (let i = 0; i < 8; i++) { ctx.strokeStyle = `rgba(218,171,99,${.12 + i * .02})`; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(capX + 28 + i * 34, capY + 16); ctx.lineTo(capX + 16 + i * 38, capY + capH - 18); ctx.stroke(); }
    ctx.fillStyle = '#c69d55'; ctx.fillRect(450, 294, 300, 18);
    return canvas;
  }

  function loadImage(source) {
    if (source && typeof source === 'object' && source.tagName === 'IMG') {
      if (source.complete && source.naturalWidth) return Promise.resolve(source);
    }
    return new Promise((resolve, reject) => {
      const image = new Image();
      let objectUrl = null;
      let src;
      if (source instanceof Blob) { objectUrl = URL.createObjectURL(source); src = objectUrl; }
      else if (source && source.toDataURL) src = source.toDataURL('image/png');
      else src = String(source);
      image.onload = () => { if (objectUrl) URL.revokeObjectURL(objectUrl); resolve(image); };
      image.onerror = () => { if (objectUrl) URL.revokeObjectURL(objectUrl); reject(new Error('Immagine sorgente non leggibile')); };
      image.src = src;
    });
  }

  function canvasBlob(canvas) {
    return new Promise((resolve, reject) => {
      if (!canvas.toBlob) { try { resolve(dataUrlBlob(canvas.toDataURL('image/png'))); } catch (error) { reject(error); } return; }
      canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('Immagine non esportabile')), 'image/png');
    });
  }

  function dataUrlBlob(dataUrl) {
    const parts = dataUrl.split(',');
    const binary = atob(parts[1]);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return new Blob([bytes], {type: 'image/png'});
  }

  async function compose(source, meta) {
    const image = await loadImage(source);
    const sourceWidth = image.naturalWidth || image.width || 1200;
    const sourceHeight = image.naturalHeight || image.height || 1200;
    const scale = Math.min(1, 1600 / Math.max(sourceWidth, sourceHeight));
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(sourceWidth * scale));
    canvas.height = Math.max(1, Math.round(sourceHeight * scale));
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas non disponibile');
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    drawLabel(ctx, canvas.width, canvas.height, meta);
    const url = canvas.toDataURL('image/png');
    return {url, blob: await canvasBlob(canvas), renderer: 'internal-label'};
  }

  function drawCardText(ctx, info, colors, x, y, width) {
    const family = 'Georgia, Times New Roman, serif';
    ctx.textAlign = 'left'; ctx.textBaseline = 'top';
    ctx.fillStyle = colors[1]; ctx.font = `normal 22px ${family}`;
    ctx.fillText('TERZI PARFUMS  ·  TAVOLA DELLA CREAZIONE', x, y);
    ctx.fillStyle = '#f3ead8';
    const titleSize = fitFont(ctx, info.name, width, 62, family, 'normal');
    const titleLines = wrap(ctx, info.name, width, 3, titleSize, family, 'normal');
    ctx.font = `normal ${titleSize}px ${family}`;
    titleLines.forEach((line, index) => ctx.fillText(line, x, y + 58 + index * (titleSize * 1.08)));
    let cursor = y + 78 + titleLines.length * (titleSize * 1.08);
    ctx.fillStyle = colors[1]; ctx.font = `normal 24px ${family}`;
    ctx.fillText(info.family.toUpperCase(), x, cursor); cursor += 48;
    ctx.fillStyle = '#d3c8b5'; ctx.font = `italic 25px ${family}`;
    const conceptLines = wrap(ctx, info.concept, width, 5, 25, family, 'italic');
    conceptLines.forEach(line => { ctx.fillText(line, x, cursor); cursor += 34; });
    cursor += 24;
    ctx.fillStyle = colors[1]; ctx.font = `normal 18px ${family}`;
    ctx.fillText('ACCENTI DELLA RICETTA', x, cursor); cursor += 32;
    ctx.fillStyle = '#d3c8b5'; ctx.font = `normal 21px ${family}`;
    const accents = info.accents.length ? info.accents.join('  ·  ') : 'Materia e memoria';
    wrap(ctx, accents, width, 3, 21, family, 'normal').forEach(line => { ctx.fillText(line, x, cursor); cursor += 30; });
    cursor += 26;
    ctx.strokeStyle = `${colors[1]}99`; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, cursor); ctx.lineTo(x + width, cursor); ctx.stroke(); cursor += 26;
    ctx.fillStyle = '#d3c8b5'; ctx.font = `normal 19px ${family}`;
    ctx.fillText(info.customer, x, cursor); cursor += 32;
    ctx.fillStyle = colors[1]; ctx.font = 'normal 16px monospace';
    ctx.fillText(info.serial, x, cursor); cursor += 34;
    ctx.fillStyle = '#f3ead8'; ctx.font = `italic 22px ${family}`;
    ctx.fillText('C.Terzi', x, cursor);
    ctx.fillStyle = '#a9a090'; ctx.font = `normal 14px ${family}`;
    ctx.fillText('Concept e direzione creativa · © Claudio Terzi', x, cursor + 34);
  }

  async function composeCard(source, meta) {
    const image = await loadImage(source);
    const info = metadata(meta);
    const colors = PALETTE[hash(info.fingerprint) % PALETTE.length];
    const canvas = document.createElement('canvas');
    canvas.width = 1600; canvas.height = 1000;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas non disponibile');
    const bg = ctx.createLinearGradient(0, 0, 1600, 1000);
    bg.addColorStop(0, colors[0]); bg.addColorStop(.5, '#0b0e14'); bg.addColorStop(1, '#17120f');
    ctx.fillStyle = bg; ctx.fillRect(0, 0, 1600, 1000);
    const glow = ctx.createRadialGradient(480, 450, 30, 500, 500, 610);
    glow.addColorStop(0, `${colors[1]}55`); glow.addColorStop(1, `${colors[1]}00`);
    ctx.fillStyle = glow; ctx.fillRect(0, 0, 960, 1000);
    ctx.save(); roundedRect(ctx, 60, 60, 780, 880, 24); ctx.clip();
    ctx.fillStyle = '#10141a'; ctx.fillRect(60, 60, 780, 880);
    const iw = image.naturalWidth || image.width || 1200, ih = image.naturalHeight || image.height || 1200;
    const scale = Math.min(740 / iw, 840 / ih);
    const dw = iw * scale, dh = ih * scale;
    ctx.drawImage(image, 450 - dw / 2, 500 - dh / 2, dw, dh);
    ctx.restore();
    roundedRect(ctx, 60, 60, 780, 880, 24); ctx.strokeStyle = `${colors[1]}aa`; ctx.lineWidth = 3; ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,.08)'; ctx.fillRect(70, 70, 8, 860);
    drawCardText(ctx, info, colors, 930, 100, 560);
    ctx.fillStyle = `${colors[1]}cc`; ctx.font = 'normal 16px monospace'; ctx.textAlign = 'right'; ctx.textBaseline = 'bottom';
    ctx.fillText('R³∞  ·  OGGETTO NARRATIVO', 1510, 950);
    const url = canvas.toDataURL('image/png');
    return {url, blob: await canvasBlob(canvas), renderer: 'tavola-grafica-interna'};
  }

  async function fromRecipe(meta) {
    let source;
    let renderer = 'fallback-procedurale';
    if (root.TerziBottle && meta && meta.perfume) {
      try {
        const rendered = await root.TerziBottle.render(meta.perfume, 0);
        source = rendered.url;
        renderer = rendered.spec && rendered.spec.renderer === 'webgl' ? 'flacone-3D' : 'flacone-3D-compatibile';
      } catch (_) { /* il fallback interno è intenzionale */ }
    }
    if (!source) source = fallbackCanvas(meta);
    const result = await compose(source, meta);
    result.renderer = renderer;
    return result;
  }

  async function fromRecipeCard(meta) {
    const bottle = await fromRecipe(meta);
    const card = await composeCard(bottle.url, meta);
    card.bottle = bottle;
    return card;
  }

  root.TerziLabel = {compose, composeBlob: (blob, meta) => compose(blob, meta), fromRecipe, fromRecipeCard, composeCard, fallbackCanvas};
})(typeof window !== 'undefined' ? window : globalThis);
