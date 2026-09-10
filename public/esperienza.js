(async function () {
  'use strict';
  var status = document.getElementById('experience-status');
  var id = new URLSearchParams(location.search).get('id') || 'LAVANDA';
  try {
    var response = await fetch('esperienze-olfattive.json');
    if (!response.ok) throw new Error('Caricamento non riuscito');
    var data = await response.json();
    var entry = data.entries.find(function (candidate) { return candidate.id === id; });
    if (!entry) { status.textContent = 'Codice non riconosciuto. Controlla il QR o apri il magazine dal menu.'; return; }
    document.title = entry.title + ' · Esperienze Terzi';
    document.getElementById('experience-title').textContent = entry.title;
    status.textContent = entry.id + ' · ' + entry.kind + ' · ' + entry.status;
    document.getElementById('experience-concept').textContent = entry.concept;
    document.getElementById('experience-materials').textContent = entry.materials.length ? 'Materie di riferimento: ' + entry.materials.join(', ') + '.' : '';
    var list = document.getElementById('experience-scenes');
    entry.scenes.forEach(function (scene) {
      var item = document.createElement('li'), heading = document.createElement('h3'), body = document.createElement('p');
      heading.textContent = scene.title; body.textContent = scene.text; item.append(heading, body); list.append(item);
    });
    var intention = document.getElementById('scene-intention');
    intention.value = ('Vorrei un profumo ispirato a questa scena: ' + entry.title + '. ' + entry.concept + ' Le immagini sono un’ispirazione creativa, da interpretare con il mio organo.').slice(0, 2800);
    document.getElementById('source-link').href = entry.source;
    var action = document.getElementById('atelier-scene');
    function updateLink() { action.href = 'atelier.html?scena=' + encodeURIComponent(intention.value.slice(0, 2800)); }
    updateLink(); intention.addEventListener('input', updateLink);
    document.getElementById('experience-content').hidden = false;
    var xr = document.getElementById('xr-status');
    try {
      var supported = Boolean(navigator.xr) && await navigator.xr.isSessionSupported('immersive-vr');
      xr.textContent = supported ? 'Il browser segnala supporto per sessioni VR immersive. Il documentario resta da produrre.' : 'Sessione VR non disponibile su questo browser o dispositivo. Il percorso editoriale resta leggibile.';
    } catch (_) { xr.textContent = 'Disponibilità VR non verificabile in questo browser. Il percorso editoriale resta leggibile.'; }
  } catch (_) { status.textContent = 'Il percorso non è stato caricato. Ricarica la pagina oppure torna al magazine.'; }
})();
