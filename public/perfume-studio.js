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
  const imageMeta = {
    name: data.name,
    customer: data.customer || '',
    serial: data.serial || '',
    perfume,
    fingerprint: perfume.flacone?.recipe_fingerprint || perfume.formula_code || data.serial || data.name
  };
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
      if (!window.TerziLabel) throw new Error('Creatore interno non caricato.');
      const rendered = await window.TerziLabel.compose(image.src, imageMeta);
      save(rendered.blob, filename + '-' + slug(selected?.label || 'interno') + '.png');
      status.textContent = 'Immagine con etichetta, numero e firma scaricata.';
    } catch (_) { status.textContent = 'Non riesco a scaricare l’immagine adesso. Riprova.'; }
  };

  const generate = document.getElementById('generate-image');
  function showPortrait(rendered, captionText) {
    if (imageObjectUrl) { URL.revokeObjectURL(imageObjectUrl); imageObjectUrl = null; }
    image.src = rendered.url;
    image.dataset.bottleVersion = rendered.renderer || 'creatore-interno';
    caption.textContent = captionText;
  }
  async function localPortrait() {
    if (!window.TerziLabel) throw new Error('Creatore interno non caricato. Ricarica la pagina.');
    status.textContent = 'Disegno il flacone e compongo un’etichetta esatta per questa ricetta…';
    const rendered = await window.TerziLabel.fromRecipe(imageMeta);
    showPortrait(rendered, 'Immagine interna · etichetta tipografica esatta · ' + rendered.renderer + ' · concept Claudio Terzi');
    status.textContent = 'Immagine interna pronta: formula, nome, numero e firma sono stati legati alla ricetta.';
    if (generate) generate.textContent = 'Rigenera immagine interna';
  }
  async function loadPortrait(action) {
    if (!generate) return;
    generate.disabled = true;
    const token = generate.dataset.token || '';
    if (!token) {
      try { await localPortrait(); }
      catch (error) { status.textContent = error.message || 'Il creatore interno non è disponibile adesso.'; }
      finally { generate.disabled = false; }
      return;
    }
    if (action === 'generate') status.textContent = 'Creo il ritratto AI; poi applico localmente nome, numero e firma. La formula è già al sicuro.';
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 55000);
    try {
      const response = await fetch('/api/profumo/immagine', {method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({token, action}),signal:controller.signal});
      if (action === 'read' && response.status === 404) {
        status.textContent = 'Nessun ritratto AI salvato. Il creatore interno è pronto.';
        return;
      }
      if (!response.ok) {
        let message = 'Immagine non disponibile adesso.';
        try { message = (await response.json()).error || message; } catch (_) {}
        throw new Error(message);
      }
      if (!(response.headers.get('Content-Type') || '').startsWith('image/')) throw new Error('Risposta immagine non valida.');
      const blob = await response.blob();
      if (!window.TerziLabel) throw new Error('Creatore interno non caricato.');
      const rendered = await window.TerziLabel.composeBlob(blob, imageMeta);
      showPortrait(rendered, 'Ritratto AI · etichetta tipografica esatta applicata internamente · concept Claudio Terzi');
      status.textContent = 'Ritratto AI pronto: l’etichetta è stata applicata dopo la generazione e resta legata alla ricetta.';
      generate.textContent = 'Rigenera ritratto AI';
    } catch (error) {
      if (action === 'read') {
        try {
          await localPortrait();
          status.textContent = 'Ritratto AI non disponibile; immagine interna pronta con etichetta esatta.';
        } catch (_) { status.textContent = 'Ritratto non disponibile. Il creatore interno può essere riavviato dal pulsante.'; }
      } else {
        try {
          await localPortrait();
          status.textContent = 'Ritratto AI non disponibile; immagine interna pronta con etichetta esatta.';
        } catch (_) { status.textContent = error.name === 'AbortError' ? 'Il ritratto AI richiede più tempo. Riprova: il creatore interno resta disponibile.' : (error.message || 'Immagine non disponibile adesso.'); }
      }
    } finally { clearTimeout(timer); generate.disabled = false; }
  }
  const graphicButton = document.getElementById('generate-card');
  const graphicPanel = document.getElementById('graphic-card');
  const graphicImage = document.getElementById('graphic-card-image');
  const graphicStatus = document.getElementById('graphic-card-status');
  const graphicDownload = document.getElementById('download-graphic-card');
  async function createGraphicCard() {
    if (!graphicButton) return;
    graphicButton.disabled = true;
    if (graphicStatus) graphicStatus.textContent = 'Compongo la tavola grafica della ricetta…';
    try {
      if (!window.TerziLabel) throw new Error('Creatore interno non caricato. Ricarica la pagina.');
      const card = await window.TerziLabel.fromRecipeCard(imageMeta);
      if (graphicImage) graphicImage.src = card.url;
      if (graphicPanel) graphicPanel.hidden = false;
      if (graphicDownload) {
        graphicDownload.href = card.url;
        graphicDownload.download = filename + '-tavola-grafica.png';
      }
      if (graphicStatus) graphicStatus.textContent = 'Tavola grafica pronta: immagine editoriale separata dalla ricetta.';
    } catch (error) {
      if (graphicStatus) graphicStatus.textContent = error.message || 'La tavola grafica non è disponibile adesso.';
    } finally { graphicButton.disabled = false; }
  }
  if (graphicButton) graphicButton.onclick = createGraphicCard;

  if (generate) {
    generate.onclick = () => loadPortrait('generate');
    if (generate.dataset.token) loadPortrait('read');
    else status.textContent = 'Il creatore interno è pronto: premi il pulsante per creare l’immagine etichettata.';
  }
})();
