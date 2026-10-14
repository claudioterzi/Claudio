/* Agorà: repository snapshots are evidence, never live-agent telemetry. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const tg = window.Telegram?.WebApp;
  let busy = false, feedBusy = false, portfolioBusy = false, toastTimer, snapshotRevision;
  let owner = Boolean(tg?.initData), currentRecord;
  const requestKey = 'agora.last.request.v1';
  const headers = {'Content-Type': 'application/json', 'X-Agora': '1'};
  const signed = body => ({...body, initData: tg?.initData || ''});
  async function api(path, body, method = 'POST', signal) {
    const controller = signal ? null : new AbortController();
    const timeout = controller ? setTimeout(() => controller.abort(), 15000) : null;
    try {
    const response = await fetch(path, {method, headers, credentials: 'same-origin', cache: 'no-store',
      ...(method === 'GET' ? {} : {body: JSON.stringify(signed(body || {}))}), signal: signal || controller.signal});
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data?.ok !== true) {
      if (response.status === 403 && !tg?.initData && path !== '/api/agora/session') accessState(false);
      throw new Error(data?.errore || 'Risposta del server non valida.');
    }
    return data;
    } finally { if (timeout) clearTimeout(timeout); }
  }
  function localId(value) {
    try { if (value) sessionStorage.setItem(requestKey, value); return sessionStorage.getItem(requestKey); } catch (_) { return null; }
  }
  function accessState(value) {
    owner = value; $('owner-form').hidden = value; $('owner-logout').hidden = !value || Boolean(tg?.initData);
    $('owner-status').textContent = value ? 'Accesso privato attivo. Le risposte si aprono qui; Telegram è una copia facoltativa.' : 'Accedi con la password dell’archivio privato per eseguire i comandi dal browser.';
  }
  function renderResult(record) {
    currentRecord = record;
    const result = record.risultato;
    $('result-text').textContent = result?.testo || record.errore || 'Esecuzione in corso. Il risultato non è ancora disponibile.';
    $('result-meta').textContent = dateLabel(record.data) + ' · ' + record.comando + ' · ' + record.stato + (record.telegram_richiesto ? (record.telegram_inviato ? ' · copia consegnata su Telegram' : ' · copia Telegram non confermata') : '') + (result?.note?.length ? '\n' + result.note.join('\n') : '');
    $('result-download').hidden = !result;
    $('request-recover').hidden = record.stato !== 'in_corso';
    if (record.stato === 'in_corso') showToast('Comando in corso. Puoi recuperare il risultato senza inviarlo di nuovo.', 'pending');
    else showToast(record.stato === 'completato' ? 'Risultato ricevuto dal server e archiviato. È leggibile qui.' : record.stato === 'parziale' ? 'Risultato parziale archiviato. Leggi quali risposte sono disponibili.' : 'Il comando non è riuscito. Leggi il dettaglio e conserva la domanda.', record.stato === 'completato' ? 'received' : 'error');
  }
  async function recover(id = localId()) {
    if (!id || !owner) return;
    try { const data = await api('/api/agora/richieste/' + id, {}); renderResult(data.richiesta); }
    catch (error) { showToast('Recupero non riuscito: ' + error.message, 'error'); }
  }
  async function refreshHistory() {
    if (!owner) { $('history-status').textContent = 'Accedi per consultare la cronologia privata.'; return; }
    try {
      const data = await api('/api/agora/history', {});
      $('command-history').replaceChildren(...data.richieste.map(item => {
        const button = document.createElement('button'); button.type = 'button'; button.className = 'history-button';
        button.textContent = dateLabel(item.data) + ' · ' + item.comando + ' · ' + item.stato;
        button.addEventListener('click', () => recover(item.id)); return button;
      }));
      $('history-status').textContent = data.richieste.length + ' richieste recenti. Risultati conservati per ' + data.conservazione_giorni + ' giorni nell’archivio privato del sito.';
    } catch (error) { $('history-status').textContent = 'Cronologia non disponibile: ' + error.message; }
  }
  async function initializeOwner() {
    if (tg?.initData) { accessState(true); $('telegram-copy').checked = true; await refreshHistory(); return; }
    try {
      const data = await api('/api/agora/session', null, 'GET'); accessState(data.autorizzato);
      if (!data.configurato) $('owner-status').textContent = 'Accesso privato del sito non configurato sul server.';
      if (owner) { await refreshHistory(); if (localId()) await recover(); }
    } catch (error) { accessState(false); $('owner-status').textContent = error.message; }
  }
  function showToast(message, state = 'info') {
    const toast = $('toast'); toast.textContent = message; toast.classList.add('show');
    clearTimeout(toastTimer); toastTimer = setTimeout(() => toast.classList.remove('show'), 6000);
    $('command-status').textContent = message; $('command-status').setAttribute('data-state', state);
  }
  function lock(value) {
    busy = value; $('command-status').setAttribute('aria-busy', String(value));
    document.querySelectorAll('[data-agora-command], #consiglio-send').forEach(button => { button.disabled = value; });
    $('consilioInput').readOnly = value;
    $('owner-logout').disabled = value;
  }
  async function sendCmd(command) {
    if (busy) return {sent: false, pending: true};
    if (!owner) {
      showToast('Accedi all’area privata del sito per eseguire il comando. Non è stato inviato alcun comando.'); $('owner-password').focus();
      return {sent: false};
    }
    lock(true); showToast('Esecuzione in corso. Il risultato apparirà qui.', 'pending');
    const id = Array.from(crypto.getRandomValues(new Uint8Array(16)), n => n.toString(16).padStart(2, '0')).join('');
    localId(id); $('request-recover').hidden = false;
    const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 180000);
    try {
      const data = await api('/api/agora', {comando: command, id, telegram: $('telegram-copy').checked}, 'POST', controller.signal);
      if (!data.richiesta || !data.richiesta.risultato || !['completato', 'parziale', 'errore'].includes(data.richiesta.stato)) {
        if (data.richiesta?.stato === 'in_corso') { renderResult(data.richiesta); return {sent: false, pending: true}; }
        throw new Error(data.richiesta?.errore || 'Il server non ha restituito un risultato.');
      }
      renderResult(data.richiesta); await refreshHistory();
      return {sent: data.richiesta.stato === 'completato'};
    } catch (error) {
      showToast(error.name === 'AbortError'
        ? 'Conferma non ricevuta in tempo. Il comando potrebbe essere arrivato: premi Recupera l’ultima richiesta o apri la cronologia. La domanda resta qui.'
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
  $('command-status').textContent = 'Le risposte ai comandi si aprono sul sito. Ogni esecuzione richiede la tua azione.';
  $('owner-form').addEventListener('submit', async event => {
    event.preventDefault(); $('owner-login').disabled = true;
    try { await api('/api/agora/session', {password: $('owner-password').value}); $('owner-password').value = ''; accessState(true); await refreshHistory(); }
    catch (error) { $('owner-status').textContent = error.message; }
    finally { $('owner-login').disabled = false; }
  });
  $('owner-logout').addEventListener('click', async () => {
    try { await api('/api/agora/session', {}, 'DELETE'); accessState(false); currentRecord = null; $('result-text').textContent = ''; $('result-meta').textContent = ''; $('command-history').replaceChildren(); $('result-download').hidden = true; }
    catch (error) { $('owner-status').textContent = error.message; }
  });
  $('result-download').addEventListener('click', () => {
    if (!currentRecord?.risultato) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(currentRecord, null, 2)], {type: 'application/json'}));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'agora-' + currentRecord.id + '.json'; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  $('request-recover').addEventListener('click', () => recover());
  $('history-refresh').addEventListener('click', refreshHistory); initializeOwner();
  $('consilioInput').addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); inviaConsiglio(); } });
  $('activity-refresh').addEventListener('click', () => { refreshActivity(); refreshPortfolio(); }); renderPortfolio(); refreshActivity();
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') refreshActivity(); });
  setInterval(() => { if (document.visibilityState !== 'hidden') refreshActivity(); }, 60000);
})();
