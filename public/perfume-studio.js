(function () {
  'use strict';
  const dataNode = document.getElementById('perfume-data');
  if (!dataNode) return;
  const data = JSON.parse(dataNode.textContent);
  const image = document.getElementById('bottle-image');
  const status = document.getElementById('image-status');
  const dialog = document.getElementById('image-dialog');
  const perfume = data.record.perfume;
  const caption = document.getElementById('image-caption');
  const original = {url:image.src, caption:caption.textContent};
  const variants = [document.getElementById('bottle-sculpture'),document.getElementById('bottle-essence')];
  const originalButton = document.getElementById('bottle-original');
  const renders = new Map();
  let selected = null;
  let imageObjectUrl = null;
  function save(blob, name) {
    const url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }
  const slug = text => text.normalize('NFKD').replace(/[^a-z0-9]+/gi,'-').replace(/^-|-$/g,'').slice(0,70).toLowerCase();
  const filename = slug(data.serial || data.name+'-'+(perfume.flacone?.recipe_fingerprint||'bozza').slice(0,10));
  document.getElementById('download-record').onclick = () => {
    const record = {...data.record,presentation:{dedication:data.dedication||null,bottle:selected},
      laboratory:window.TerziLab?.snapshot?.() || null};
    save(new Blob([JSON.stringify(record, null, 2)], {type:'application/json'}), filename + '.json');
  };
  for (const [id,kind] of [['print-label','label'],['print-recipe','recipe'],['print-inspiration','inspiration']]) {
    document.getElementById(id).onclick = () => window.TerziPrint.open(kind);
  }
  function pressed(button) {
    [...variants,originalButton].filter(Boolean).forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
  }
  async function showVariant(variant) {
    [...variants,originalButton].filter(Boolean).forEach(b=>b.disabled=true);
    status.textContent = 'Disegno il vetro e la luce della tua creazione…';
    try {
      if (!renders.has(variant)) renders.set(variant,await window.TerziBottle.render(perfume,variant));
      const rendering = renders.get(variant); image.src = rendering.url; await image.decode();
      selected = rendering.spec; pressed(variants[variant]);
      image.dataset.bottleVersion = selected.label;
      caption.textContent = selected.label+' · '+(selected.renderer==='cpu-illustration'?'illustrazione compatibile dalla geometria 3D':'flacone 3D legato alla ricetta')+' · concept Claudio Terzi';
      status.textContent = 'Versione '+selected.label+' pronta. Scarica il flacone con nome'+(data.customer?' e dedica.':'.');
    } catch (_) {
      status.textContent = 'Il disegno 3D non è disponibile in questo browser. La formula e la stampa restano disponibili.';
    } finally { [...variants,originalButton].filter(Boolean).forEach(b=>b.disabled=false); }
  }
  variants.forEach((button,i)=>button.onclick=()=>showVariant(i));
  if (originalButton) originalButton.onclick=()=>{image.src=original.url;caption.textContent=original.caption;selected=null;pressed(originalButton);delete image.dataset.bottleVersion;status.textContent='Flacone originale.';};
  if (data.restored_variant) showVariant(data.restored_variant === 'Essenza' ? 1 : 0);
  else if (!perfume.esempio) showVariant(0);
  document.getElementById('enlarge').onclick = () => {
    const copy = document.getElementById('enlarge').cloneNode(true);
    copy.removeAttribute('id'); copy.querySelector('img').removeAttribute('id'); copy.tabIndex = -1;
    document.getElementById('large-bottle').replaceChildren(copy); dialog.showModal();
  };
  document.getElementById('close-dialog').onclick = () => dialog.close();
  dialog.addEventListener('click', e => { if (e.target === dialog) dialog.close(); });
  document.getElementById('download-image').onclick = async () => {
    try {
      await image.decode();
      const canvas = document.createElement('canvas'); canvas.width = canvas.height = 1600;
      const ctx = canvas.getContext('2d'); ctx.drawImage(image, 0, 0, 1600, 1600);
      ctx.fillStyle = '#171410'; ctx.fillRect(592, 747, 416, 288);
      ctx.strokeStyle = '#b29a66'; ctx.lineWidth = 2; ctx.strokeRect(592,747,416,288);
      ctx.fillStyle = '#e4c68b'; ctx.textAlign = 'center';
      function line(text, y, size) {
        ctx.font = size + 'px Georgia';
        while (ctx.measureText(text).width > 380 && size > 9) ctx.font = (--size) + 'px Georgia';
        ctx.fillText(text,800,y);
      }
      line('TERZI PARFUMS',800,24); line(data.name,860,34);
      line(data.customer ? 'Per '+data.customer : 'Atelier',920,27); line(data.serial || 'BOZZA · NON ARCHIVIATA',985,13);
      canvas.toBlob(blob => { if (blob) save(blob, filename + '-'+slug(selected?.label||'originale')+'.png'); }, 'image/png');
    } catch (_) { status.textContent = 'Non riesco a scaricare l’immagine adesso. Riprova.'; }
  };
  const generate = document.getElementById('generate-image');
  async function loadPortrait(action) {
    generate.disabled = true;
    if (action === 'generate') status.textContent = 'Creo il flacone a tema della ricetta. La formula è già al sicuro.';
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 55000);
    try {
      const response = await fetch('/api/profumo/immagine', {method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({token:generate.dataset.token, action}),signal:controller.signal});
      if (action === 'read' && response.status === 404) return;
      if (!response.ok) {
        let message = 'Immagine non disponibile adesso.';
        try { message = (await response.json()).error || message; } catch (_) {}
        throw new Error(message);
      }
      if (!(response.headers.get('Content-Type') || '').startsWith('image/')) throw new Error('Risposta immagine non valida.');
      const blob = await response.blob();
      if (imageObjectUrl) URL.revokeObjectURL(imageObjectUrl);
      imageObjectUrl = URL.createObjectURL(blob); image.src = imageObjectUrl; await image.decode();
      document.getElementById('image-caption').textContent = 'Flacone a tema generato · etichetta tipografica separata · concept Claudio Terzi';
      status.textContent = 'Il ritratto salvato è pronto. Puoi scaricarlo con nome e dedica.';
      generate.textContent = 'Ricarica il flacone salvato';
    } catch (error) { if (action === 'generate') status.textContent = error.name === 'AbortError' ? 'Il ritratto richiede più tempo. Il flacone Atelier e la formula restano disponibili.' : error.message; }
    finally { clearTimeout(timer); generate.disabled = false; }
  }
  if (generate) {
    generate.onclick = () => loadPortrait('generate');
    // Reading an existing asset never starts a paid generation.
    loadPortrait('read');
  }
})();
