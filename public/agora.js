/* Agorà: repository snapshots are evidence, never live-agent telemetry. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const tg = window.Telegram?.WebApp;
  let busy = false, feedBusy = false, portfolioBusy = false, toastTimer, snapshotRevision;
  function showToast(message, state = 'info') {
    const toast = $('toast'); toast.textContent = message; toast.classList.add('show');
    clearTimeout(toastTimer); toastTimer = setTimeout(() => toast.classList.remove('show'), 6000);
    $('command-status').textContent = message; $('command-status').setAttribute('data-state', state);
  }
  function lock(value) {
    busy = value; $('command-status').setAttribute('aria-busy', String(value));
    document.querySelectorAll('[data-agora-command], #consiglio-send').forEach(button => { button.disabled = value; });
    $('consilioInput').readOnly = value;
  }
  async function sendCmd(command) {
    if (busy) return {sent: false, pending: true};
    if (!tg?.initData) {
      showToast('Per inviare, apri Agorà dal menu del bot Telegram. Qui non è stato inviato alcun comando.');
      return {sent: false};
    }
    lock(true); showToast('Invio in corso. Attendi la conferma prima di riprovare.', 'pending');
    const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 45000);
    try {
      const response = await fetch('/api/agora', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, credentials: 'same-origin',
        signal: controller.signal, body: JSON.stringify({comando: command, initData: tg.initData})
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data || data.ok !== true) throw new Error(data?.errore || 'Il server non ha confermato la ricezione.');
      showToast('Comando ricevuto dal server. Controlla la chat Telegram per la risposta.', 'received');
      return {sent: true};
    } catch (error) {
      showToast(error.name === 'AbortError'
        ? 'Conferma non ricevuta in tempo. Il comando potrebbe essere arrivato: controlla la chat prima di riprovare. La domanda resta qui.'
        : 'Invio non confermato: ' + (error.message || 'rete non disponibile') + '. La domanda resta qui.', 'error');
      return {sent: false};
    } finally { clearTimeout(timeout); lock(false); }
  }
  function toggleConsiglio() {
    if (busy) return;
    const visible = !$('consilioWrap').classList.contains('visible');
    $('consilioWrap').classList.toggle('visible', visible);
    $('btnConsiglio').setAttribute('aria-expanded', String(visible));
    if (visible) $('consilioInput').focus();
  }
  async function inviaConsiglio() {
    if (busy) return;
    const input = $('consilioInput'), question = input.value.trim();
    if (!question) { showToast('Scrivi la questione su cui deliberare.'); input.focus(); return; }
    const result = await sendCmd('/consiglio ' + question);
    if (result.sent) {
      if (input.value.trim() === question) {
        input.value = ''; $('consilioWrap').classList.remove('visible');
        $('btnConsiglio').setAttribute('aria-expanded', 'false'); $('btnConsiglio').focus();
      }
    } else { $('consilioWrap').classList.add('visible'); $('btnConsiglio').setAttribute('aria-expanded', 'true'); input.focus(); }
  }
  const validDate = value => typeof value === 'string' && Number.isFinite(Date.parse(value));
  function dateLabel(value) {
    if (!validDate(value)) return 'Data non documentata';
    const date = new Date(/^\d{4}-\d{2}-\d{2}$/.test(value) ? value + 'T00:00:00Z' : value);
    return new Intl.DateTimeFormat('it-IT', {dateStyle: 'medium', ...(/^\d{4}-\d{2}-\d{2}$/.test(value) ? {timeZone: 'UTC'} : {timeStyle: 'short', timeZone: 'Europe/Paris'})}).format(date);
  }
  function row(date, message, source, href) {
    const item = document.createElement('div'); item.className = 'log-item';
    const time = document.createElement('time'); time.className = 'log-time'; time.textContent = dateLabel(date); if (validDate(date)) time.dateTime = date;
    const body = document.createElement('div'); body.className = 'log-msg';
    const text = document.createElement(href ? 'a' : 'span'); text.textContent = message; if (href) text.href = href;
    const provenance = document.createElement('small'); provenance.textContent = source;
    body.append(text, provenance); item.append(time, body); return item;
  }
  function renderPortfolio() {
    const portfolio = window.IDEA_OS_PORTFOLIO, host = $('project-list');
    if (!portfolio || !Array.isArray(portfolio.ideas)) { $('project-status').textContent = 'Portafoglio non caricato. Ricarica la pagina per riprovare.'; return; }
    $('project-status').textContent = 'Fonte: proiezione canonica IDEA OS · snapshot ' + dateLabel(portfolio.meta?.snapshot) + '. Le date di aggiornamento dei singoli progetti non sono documentate.';
    const ideas = portfolio.ideas.filter(idea => idea.dossier && !idea.secure);
    host.replaceChildren(...ideas.map(idea => row(portfolio.meta?.snapshot, idea.id + ' · ' + idea.title, idea.status, '/idee/' + encodeURIComponent(idea.id))));
    if (!ideas.length) $('project-status').textContent += ' Nessun progetto con dossier disponibile in questa proiezione.';
  }
  function refreshPortfolio() {
    if (portfolioBusy) return;
    portfolioBusy = true;
    const script = document.createElement('script');
    script.src = '/idea-os-data.js?refresh=' + Date.now();
    const timeout = setTimeout(() => finish(false), 10000);
    let finished = false;
    function finish(ok) {
      if (finished) return; finished = true; clearTimeout(timeout); portfolioBusy = false; script.remove();
      if (ok) renderPortfolio();
      else $('project-status').textContent = 'Il portafoglio non è stato aggiornato. Restano i dati già caricati con le loro date. Premi Aggiorna per riprovare.';
    }
    script.onload = () => finish(true); script.onerror = () => finish(false); document.head.append(script);
  }
  async function refreshActivity() {
    if (feedBusy) return;
    feedBusy = true; $('activity-refresh').disabled = true; $('activity-status').textContent = 'Carico lo snapshot documentato…';
    const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch('/r3-status.json', {cache: 'no-store', signal: controller.signal});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (snapshot.schema !== 'r3-public-status-v1' || snapshot.source !== 'repository-derived' || !validDate(snapshot.generated_at)) throw new Error('Snapshot non riconosciuto');
      const age = Math.max(0, Date.now() - Date.parse(snapshot.generated_at));
      const revision = snapshot.commit + ':' + snapshot.generated_at;
      if (snapshotRevision && revision !== snapshotRevision) refreshPortfolio();
      snapshotRevision = revision;
      $('activity-status').textContent = 'Fonte: repository · snapshot ' + dateLabel(snapshot.generated_at) + (age > 86400000 ? ' · dati più vecchi di 24 ore.' : '.') + ' I servizi e gli agenti non sono verificati in tempo reale.';
      const rows = [];
      if (validDate(snapshot.heartbeat?.last_daily)) rows.push(row(snapshot.heartbeat.last_daily, 'Ultimo resoconto giornaliero registrato', snapshot.heartbeat.source_file || 'Snapshot R³∞'));
      if (validDate(snapshot.contacts?.last_date)) rows.push(row(snapshot.contacts.last_date, 'Contatti umani verificati: ' + (snapshot.contacts.verified_human ?? 'non documentati'), 'Registro contatti · ultimo dato disponibile'));
      const benchmarkDate = snapshot.benchmarks?.last_file?.match(/\d{4}-\d{2}-\d{2}/)?.[0];
      if (validDate(benchmarkDate)) rows.push(row(benchmarkDate, 'Ultimo benchmark archiviato', snapshot.benchmarks.last_file));
      rows.sort((a, b) => Date.parse(b.children[0].dateTime) - Date.parse(a.children[0].dateTime));
      $('logList').replaceChildren(...rows);
      if (!rows.length) $('activity-status').textContent += ' Nessuna attività datata presente nello snapshot.';
    } catch (error) {
      $('activity-status').textContent = 'Aggiornamento non riuscito: ' + (error.name === 'AbortError' ? 'tempo di attesa scaduto' : error.message) + '. ' + ($('logList').children.length ? 'Restano visibili gli ultimi dati caricati, con le loro date. ' : '') + 'Premi Aggiorna per riprovare.';
    } finally { clearTimeout(timeout); feedBusy = false; $('activity-refresh').disabled = false; }
  }
  window.sendCmd = sendCmd; window.toggleConsiglio = toggleConsiglio; window.inviaConsiglio = inviaConsiglio;
  if (tg) { tg.expand(); tg.setHeaderColor('#111115'); tg.setBackgroundColor('#0a0a0c'); tg.BackButton?.onClick(() => tg.close()); }
  $('command-status').textContent = tg?.initData ? 'Comandi collegati a Telegram. Ogni invio richiede la tua azione.' : 'Apri Agorà dal menu del bot Telegram per inviare. In questo browser puoi consultare i dati documentati.';
  $('consilioInput').addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); inviaConsiglio(); } });
  $('activity-refresh').addEventListener('click', () => { refreshActivity(); refreshPortfolio(); }); renderPortfolio(); refreshActivity();
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') refreshActivity(); });
  setInterval(() => { if (document.visibilityState !== 'hidden') refreshActivity(); }, 60000);
})();
