/* Repository evidence with dates calculated at reading time. C.Terzi */
(function () {
  'use strict';
  function calendarGap(isoDay, now) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(isoDay || '')) return null;
    var origin = Date.parse(isoDay + 'T00:00:00Z');
    if (!Number.isFinite(origin) || new Date(origin).toISOString().slice(0, 10) !== isoDay) return null;
    var parts = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Paris', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(now || new Date());
    var day = {};
    parts.forEach(function (p) { day[p.type] = p.value; });
    var delta = Math.floor((Date.UTC(Number(day.year), Number(day.month) - 1, Number(day.day)) - origin) / 86400000);
    return delta < 0 ? null : delta;
  }
  function snapshotCurrent(generated, now) {
    var age = (now || new Date()).getTime() - Date.parse(generated || '');
    return Number.isFinite(age) && age >= -300000 && age <= 86400000;
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { calendarGap: calendarGap, snapshotCurrent: snapshotCurrent };
  if (typeof document === 'undefined') return;
  var $ = function (id) { return document.getElementById(id); };
  var dateTime = function (d) { var value = Date.parse(d || ''); return Number.isFinite(value) ? new Intl.DateTimeFormat('it-IT', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Europe/Paris' }).format(new Date(value)) : 'data non disponibile'; };
  var dateDay = function (d) { var value = /^\d{4}-\d{2}-\d{2}$/.test(d || '') ? Date.parse(d + 'T00:00:00Z') : NaN; return Number.isFinite(value) && new Date(value).toISOString().slice(0,10) === d ? new Intl.DateTimeFormat('it-IT', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(value)) : 'data non disponibile'; };
  var pending = false;
  function badge(id, kind, label) {
    var el = $(id); el.className = 'badge ' + kind;
    el.replaceChildren(); var dot = document.createElement('span'); dot.className = 'dot'; dot.setAttribute('aria-hidden', 'true');
    var text = document.createElement('span'); text.textContent = label; el.append(dot, text);
  }
  async function refresh() {
    if (pending) return;
    pending = true; $('refresh-status').disabled = true;
    $('status-read').textContent = 'Leggo lo snapshot del repository…';
    var controller = new AbortController(); var timeout = setTimeout(function () { controller.abort(); }, 15000);
    try {
      var response = await fetch('/r3-status.json', { cache: 'no-store', signal: controller.signal });
      if (!response.ok) throw new Error('HTTP ' + response.status);
      var s = await response.json();
      if (!s || s.schema !== 'r3-public-status-v1' || !s.heartbeat || !s.hypotheses || !s.r3 || !s.contacts || !s.h2 || !s.benchmarks) throw new Error('Snapshot non valido');
      var now = new Date(); var gap = calendarGap(s.heartbeat.last_daily, now);
      var current = snapshotCurrent(s.generated_at, now);
      $('last-daily').textContent = s.heartbeat.last_daily ? dateDay(s.heartbeat.last_daily) : 'nessuno';
      $('daily-sub').textContent = gap !== null ? gap + ' giorni di calendario dall’ultimo daily · ' + (s.heartbeat.source_file || 'fonte non disponibile') : 'Nessun daily con data valida';
      badge('daily-badge', gap !== null && gap <= 1 && current ? 'good' : 'warn', gap === null ? 'DATA DA VERIFICARE' : current && gap <= 1 ? 'PROVA RECENTE' : 'SNAPSHOT STORICO');
      $('hyp-total').textContent = s.hypotheses.total;
      $('hyp-sub').textContent = s.hypotheses.open + ' aperte · ' + s.hypotheses.confirmed + ' confermate · ' + s.hypotheses.falsified + ' falsificate';
      $('nodes').textContent = s.r3.verified_external_nodes;
      badge('node-badge', s.r3.verified_external_nodes >= 2 ? 'good' : 'bad', s.r3.verified_external_nodes >= 2 ? 'PROVE NELLO SNAPSHOT' : 'RETE NON PROVATA');
      $('contacts').textContent = s.contacts.records + ' righe · ' + s.contacts.verified_human + ' umane con verifica';
      $('last-contact').textContent = dateDay(s.contacts.last_date); $('deadline').textContent = dateDay(s.h2.deadline);
      $('h2-risk').textContent = s.h2.risk; $('h2-title').textContent = s.h2.status + ' · ' + s.h2.risk;
      $('bench-count').textContent = s.benchmarks.files + ' artefatti'; $('bench-last').textContent = s.benchmarks.last_file || 'Nessun benchmark';
      $('next-test').textContent = 'TEST: ' + (s.next_test || 'Non indicato');
      var stamp = 'Snapshot generato ' + dateTime(s.generated_at) + ' · fonte: ' + (s.source || 'non dichiarata');
      $('generated').textContent = stamp;
      $('snapshot-date').textContent = stamp;
      $('status-read').textContent = 'Letto ' + dateTime(now.toISOString()) + '. ' + (current ? 'Snapshot entro 24 ore; lo stato runtime non è misurato da questa pagina.' : 'Snapshot storico: serve una nuova generazione del dato per attestare uno stato più recente.');
    } catch (error) {
      badge('daily-badge', 'bad', 'LETTURA NON RIUSCITA');
      $('status-read').textContent = 'Lettura non riuscita' + (error.name === 'AbortError' ? ' entro 15 secondi' : ': ' + error.message) + '. Gli eventuali dati già visibili appartengono alla lettura precedente. Puoi riprovare con Aggiorna dati.';
      $('daily-sub').textContent = 'Non è stato possibile verificare lo snapshot.';
    } finally { clearTimeout(timeout); pending = false; $('refresh-status').disabled = false; }
  }
  $('refresh-status').addEventListener('click', refresh);
  refresh();
})();
