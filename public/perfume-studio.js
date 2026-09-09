(function () {
  'use strict';
  const dataNode = document.getElementById('perfume-data');
  if (!dataNode) return;
  const data = JSON.parse(dataNode.textContent);
  const image = document.getElementById('bottle-image');
  const status = document.getElementById('image-status');
  const dialog = document.getElementById('image-dialog');
  let imageObjectUrl = null;
  function save(blob, name) {
    const url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }
  const filename = (data.serial || 'terzi-bozza').toLowerCase();
  document.getElementById('download-record').onclick = () => {
    save(new Blob([JSON.stringify(data.record, null, 2)], {type:'application/json'}), filename + '.json');
  };
  document.getElementById('print-label').onclick = () => window.print();
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
      line(data.customer || 'Atelier',920,27); line(data.serial || 'BOZZA · NON ARCHIVIATA',985,13);
      canvas.toBlob(blob => { if (blob) save(blob, filename + '.png'); }, 'image/png');
    } catch (_) { status.textContent = 'Non riesco a scaricare l’immagine adesso. Riprova.'; }
  };
  const generate = document.getElementById('generate-image');
  if (generate) generate.onclick = async () => {
    generate.disabled = true; status.textContent = 'Creo il ritratto olfattivo. La formula è già al sicuro.';
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 55000);
    try {
      const response = await fetch('/api/profumo/immagine', {method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({token:generate.dataset.token}),signal:controller.signal});
      if (!response.ok) {
        let message = 'Immagine non disponibile adesso.';
        try { message = (await response.json()).error || message; } catch (_) {}
        throw new Error(message);
      }
      if (!(response.headers.get('Content-Type') || '').startsWith('image/')) throw new Error('Risposta immagine non valida.');
      const blob = await response.blob();
      if (imageObjectUrl) URL.revokeObjectURL(imageObjectUrl);
      imageObjectUrl = URL.createObjectURL(blob); image.src = imageObjectUrl; await image.decode();
      document.getElementById('image-caption').textContent = 'Ritratto olfattivo generato · visualizzazione di progetto';
      status.textContent = 'Il ritratto è pronto. Scaricalo per conservarlo.';
      generate.textContent = 'Ricarica il ritratto';
    } catch (error) { status.textContent = error.name === 'AbortError' ? 'Il ritratto richiede più tempo. Il flacone Atelier e la formula restano disponibili.' : error.message; }
    finally { clearTimeout(timer); generate.disabled = false; }
  };
})();
