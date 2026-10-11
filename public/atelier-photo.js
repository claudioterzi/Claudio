/* Foto private: riduzione locale, poi normale invio multipart (anche su iPhone). */
(function () {
  'use strict';
  const input = document.getElementById('foto');
  if (!input) return;
  const status = document.getElementById('foto-stato');
  const preview = document.getElementById('foto-preview');
  const figure = document.getElementById('foto-anteprima');
  const remove = document.getElementById('foto-rimuovi');
  let example = false, prepared = null, previewURL = null, sequence = 0;
  function clearPreview() { if (previewURL) URL.revokeObjectURL(previewURL); previewURL = null; }
  function reset() {
    sequence++; example = false; prepared = null; input.value = '';
    clearPreview(); preview.removeAttribute('src'); figure.hidden = true; remove.hidden = true; status.textContent = '';
  }
  async function shrink(file) {
    if (file.size > 30_000_000) throw new Error('Scegli una foto inferiore a 30 MB.');
    const url = URL.createObjectURL(file);
    try {
      const img = new Image(); img.src = url;
      await img.decode();
      if (!img.naturalWidth || !img.naturalHeight || img.naturalWidth * img.naturalHeight > 60_000_000) throw new Error('Riduci la risoluzione della foto e riprova.');
      const scale = Math.min(1, 1600 / Math.max(img.naturalWidth, img.naturalHeight));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
      canvas.height = Math.max(1, Math.round(img.naturalHeight * scale));
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', .84));
      if (!blob || blob.size > 3_000_000) throw new Error('La foto rimane troppo grande. Scegli una copia più piccola.');
      return new File([blob], 'ispirazione.jpg', {type: 'image/jpeg'});
    } finally { URL.revokeObjectURL(url); }
  }
  input.addEventListener('change', async () => {
    const file = input.files[0], turn = ++sequence;
    example = false; prepared = null; clearPreview(); figure.hidden = true; remove.hidden = !file;
    if (!file) { status.textContent = ''; return; }
    status.textContent = 'Preparo la fotografia…';
    try {
      const result = await shrink(file);
      if (turn !== sequence) return;
      prepared = result; previewURL = URL.createObjectURL(result); preview.src = previewURL;
      figure.hidden = false; document.getElementById('foto-didascalia').textContent = 'La tua ispirazione · anteprima privata';
      status.textContent = 'Foto pronta. Aggiungi un racconto, se vuoi, e chiedi a Raffaello.';
    } catch (error) {
      if (turn !== sequence) return;
      input.value = ''; remove.hidden = true;
      status.textContent = error.message.startsWith('Scegli') || error.message.startsWith('Riduci') || error.message.startsWith('La foto') ? error.message : 'Non riesco ad aprire questa immagine. Per HEIC, esporta una copia JPEG e riprova.';
    }
  });
  remove.addEventListener('click', reset);
  document.getElementById('foto-esempio').addEventListener('click', () => {
    reset(); example = true; preview.src = '/images/ispirazione-cantiere.jpg'; figure.hidden = false; remove.hidden = false;
    document.getElementById('foto-didascalia').textContent = 'L’esempio pubblico di Claudio · Il calore del ferro';
    status.textContent = 'Foto di Claudio selezionata. Premi “Chiedi a Raffaello” per comporre.';
  });
  window.TerziPhoto = {
    selected: () => example || !!input.files.length,
    async prepareInput() {
      const upload = document.createElement('input');
      if (example) { upload.type = 'hidden'; upload.name = 'foto_esempio'; upload.value = 'cantiere'; return upload; }
      if (!prepared) throw new Error('Photo not ready');
      const transfer = new DataTransfer(); transfer.items.add(prepared);
      upload.type = 'file'; upload.name = 'foto'; upload.files = transfer.files; upload.hidden = true;
      return upload;
    }
  };
})();
