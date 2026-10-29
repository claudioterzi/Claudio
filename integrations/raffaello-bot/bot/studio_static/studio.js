(function () {
  'use strict';

  var tg = window.Telegram && window.Telegram.WebApp;
  var initData = tg && typeof tg.initData === 'string' ? tg.initData : '';
  var catalog = window.TERZI_MUSICA || { songs: [], raffPlaylist: { songs: [] } };
  var state = { config: null, viewer: null, requests: [], songs: [], detail: null, detailId: null, requestsLoaded: false, libraryLoaded: false, loading: false, submitting: false, clientId: null, poll: null, tab: 'crea' };
  var draftKey = 'raffaello-studio-draft-v1';
  var states = {
    requested: ['Richiesta ricevuta', 'La tua idea è stata ricevuta. Il testo può essere preparato nel prossimo passaggio.'],
    writing: ['Testo in lavorazione', 'Il servizio sta preparando il testo. Puoi tornare qui per conoscere il prossimo stato.'],
    awaiting_suno: ['In attesa di Suno', 'Il testo è disponibile. La produzione su Suno è il prossimo passaggio.'],
    ready: ['Risultato disponibile', 'Il collegamento alla canzone è disponibile.'],
    kept: ['Conservata', 'Questa canzone è stata conservata nella Biblioteca.'],
    discarded: ['Scartata', 'Questa richiesta è stata scartata.'],
    error: ['Serve attenzione', 'Il servizio ha segnalato un problema. Apri il dettaglio per conoscere le azioni disponibili.']
  };

  function byId(id) { return document.getElementById(id); }
  function text(value) { return value == null ? '' : String(value); }
  function node(tag, className, value) {
    var element = document.createElement(tag);
    if (className) element.className = className;
    if (value != null) element.textContent = text(value);
    return element;
  }
  function message(id, value, error) {
    var target = byId(id);
    target.textContent = text(value);
    target.dataset.error = error ? 'true' : 'false';
  }
  function owner() { return !!(state.viewer && state.viewer.is_owner === true); }
  function capability(name) { return !!(state.config && state.config.capabilities && state.config.capabilities[name] === true); }
  function songUrl(value) {
    try {
      var url = new URL(text(value));
      return url.protocol === 'https:' && url.hostname === 'suno.com' && !url.username && !url.password && /^\/song\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/?$/i.test(url.pathname) ? url.origin + url.pathname.replace(/\/$/, '') : null;
    } catch (_) { return null; }
  }
  function playlistUrl(value) {
    try {
      var url = new URL(text(value));
      return url.protocol === 'https:' && url.hostname === 'suno.com' && !url.username && !url.password && /^\/playlist\/[0-9a-f-]{36}\/?$/i.test(url.pathname) ? url.href : null;
    } catch (_) { return null; }
  }
  function botUrl(value) {
    try {
      var url = new URL(text(value));
      return url.protocol === 'https:' && (url.hostname === 't.me' || url.hostname === 'telegram.me') && !url.username && !url.password && /^\/[a-z0-9_]{5,32}\/?$/i.test(url.pathname) ? url.href : null;
    } catch (_) { return null; }
  }
  function audioUrl(song) {
    if (song.audio_url_verified !== true && song.audio_verified !== true) return null;
    try {
      var url = new URL(text(song.audio_url));
      return url.protocol === 'https:' && !url.username && !url.password ? url.href : null;
    } catch (_) { return null; }
  }
  function externalLink(label, href, className) {
    var link = node('a', className || 'text-link', label + ' ↗');
    link.href = href;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    return link;
  }
  function formatDate(value) {
    var date = new Date(value);
    return Number.isNaN(date.getTime()) ? '' : date.toLocaleString('it-IT', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  }
  function stateInfo(request) { return states[request.state] || ['Stato da verificare', 'Questo stato non è ancora riconosciuto dallo Studio.']; }
  function statePill(request) {
    var pill = node('span', 'state-pill', stateInfo(request)[0]);
    pill.dataset.state = text(request.state);
    return pill;
  }
  function uuid() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') return window.crypto.randomUUID();
    if (!window.crypto || !window.crypto.getRandomValues) throw new Error('Il browser non supporta l’invio sicuro delle richieste.');
    var bytes = window.crypto.getRandomValues(new Uint8Array(16));
    bytes[6] = (bytes[6] & 15) | 64;
    bytes[8] = (bytes[8] & 63) | 128;
    var hex = Array.from(bytes, function (value) { return value.toString(16).padStart(2, '0'); }).join('');
    return hex.slice(0, 8) + '-' + hex.slice(8, 12) + '-' + hex.slice(12, 16) + '-' + hex.slice(16, 20) + '-' + hex.slice(20);
  }
  async function api(path, method, body, publicRoute) {
    if (!publicRoute && (!initData || !state.viewer && path !== '/session')) throw new Error('Apri lo Studio in Telegram per continuare.');
    var headers = { Accept: 'application/json' };
    if (!publicRoute) headers['X-Telegram-Init-Data'] = initData;
    if (body != null) headers['Content-Type'] = 'application/json';
    var controller = new AbortController();
    var timeout = window.setTimeout(function () { controller.abort(); }, 45000);
    var response;
    try {
      response = await fetch(publicRoute ? path : '/music/v1' + path, { method: method || 'GET', headers: headers, body: body == null ? undefined : JSON.stringify(body), credentials: 'omit', cache: 'no-store', signal: controller.signal });
    } catch (error) {
      throw new Error(error.name === 'AbortError' ? 'Il servizio non ha risposto in tempo. Aggiorna lo stato prima di riprovare.' : 'Connessione al servizio non disponibile. La tua bozza è ancora qui.');
    } finally { window.clearTimeout(timeout); }
    var data;
    try { data = await response.json(); } catch (_) { throw new Error('Il servizio ha restituito una risposta non leggibile. Riprova ad aggiornare.'); }
    if (!response.ok) {
      if (response.status === 401 && !publicRoute) {
        state.viewer = null;
        state.requests = [];
        state.songs = [];
        closeDetail();
        renderAccess();
        renderRequests();
        renderLibrary();
      }
      throw new Error(text(data.message || data.error || 'Operazione non completata.').slice(0, 240));
    }
    return data;
  }

  function setTab(name, focus) {
    if (['crea', 'richieste', 'biblioteca'].indexOf(name) === -1) name = 'crea';
    state.tab = name;
    ['crea', 'richieste', 'biblioteca'].forEach(function (tab) {
      byId('panel-' + tab).hidden = tab !== name;
      byId('tab-' + tab).setAttribute('aria-selected', tab === name ? 'true' : 'false');
      byId('tab-' + tab).tabIndex = tab === name ? 0 : -1;
    });
    if (focus) byId('tab-' + name).focus();
    if (window.history && window.history.replaceState) window.history.replaceState(null, '', '#' + name);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  function currentDraft() {
    return { story: byId('story').value.slice(0, 1800), genre: byId('genre').value, mood: byId('mood').value, language: byId('language').value };
  }
  function saveDraft() {
    state.clientId = null;
    byId('story-count').textContent = byId('story').value.length + ' / 1800';
    try { window.localStorage.setItem(draftKey, JSON.stringify(currentDraft())); byId('draft-note').textContent = 'Bozza salvata su questo dispositivo.'; }
    catch (_) { byId('draft-note').textContent = 'La bozza resta in questa pagina.'; }
  }
  function restoreDraft() {
    try {
      var draft = JSON.parse(window.localStorage.getItem(draftKey) || 'null');
      if (draft && typeof draft === 'object') {
        ['story', 'genre', 'mood', 'language'].forEach(function (name) {
          if (typeof draft[name] === 'string') byId(name).value = draft[name].slice(0, name === 'story' ? 1800 : 80);
        });
        if (!byId('language').value) byId('language').value = 'it';
      }
    } catch (_) { /* A malformed or unavailable local draft must not block the Studio. */ }
    byId('story-count').textContent = byId('story').value.length + ' / 1800';
  }
  function renderAccess() {
    var authenticated = !!state.viewer;
    var label = authenticated ? (owner() ? 'Studio di Claudio' : text(state.viewer.first_name || 'Il tuo Studio')) : 'Anteprima';
    byId('session-label').textContent = label;
    byId('personal-voice-wrap').hidden = !owner() || !capability('personal_voice');
    if (!owner() || !capability('personal_voice')) byId('personal-voice').checked = false;
    byId('access-note').hidden = authenticated;
    byId('submit-request').disabled = !authenticated || !capability('requests') || state.submitting;
    byId('refresh-requests').disabled = !authenticated || state.loading;
    var url = state.config && (botUrl(state.config.bot_url) || botUrl('https://t.me/' + text(state.config.bot_username)));
    byId('open-telegram').hidden = authenticated || !url;
    if (url) byId('open-telegram').href = url;
    if (state.config) {
      byId('mode-note').textContent = capability('lyrics_generation') ? 'Claudio avvia la preparazione del testo con Raffaello. La produzione su Suno prosegue con un passaggio assistito.' : 'La tua idea viene raccolta nello Studio. Claudio segue il testo e la produzione su Suno.';
      byId('production-note').textContent = capability('lyrics_generation') ? 'Il testo può essere preparato con Raffaello. Claudio segue la produzione su Suno, e l’ascolto compare quando è confermato.' : 'La richiesta viene raccolta nello Studio. Claudio segue il testo e la produzione su Suno; l’ascolto compare quando è confermato.';
      if (state.config.preview === true) {
        byId('session-label').textContent = 'Anteprima pubblica';
        byId('mode-note').textContent = 'Puoi esplorare lo Studio e il catalogo. Le richieste saranno abilitate dopo il collegamento al bot.';
        byId('production-note').textContent = 'Questo è lo Studio in anteprima. Il catalogo si può già ascoltare su Suno; le richieste personali richiedono il collegamento Telegram.';
        byId('open-telegram').firstChild.textContent = 'Apri il bot Telegram ';
      }
    }
  }
  function renderRequests() {
    var list = byId('request-list');
    list.replaceChildren();
    var requests = state.viewer ? state.requests : [];
    requests.forEach(function (request) {
      var card = node('button', 'request-card');
      card.type = 'button';
      var top = node('div', 'request-card-top');
      top.append(statePill(request));
      var date = formatDate(request.updated_at || request.created_at);
      if (date) { var time = node('time', '', date); time.dateTime = text(request.updated_at || request.created_at); top.append(time); }
      card.append(top, node('h3', '', request.title || 'Una storia da trasformare'), node('p', '', text(request.story).slice(0, 160) + (text(request.story).length > 160 ? '…' : '')));
      card.addEventListener('click', function () { openDetail(request.id); });
      list.append(card);
    });
    byId('requests-empty').hidden = requests.length > 0;
    byId('requests-summary').textContent = state.viewer ? (state.requestsLoaded ? requests.length + (requests.length === 1 ? ' richiesta nel tuo Studio' : ' richieste nel tuo Studio') : 'Le tue richieste non sono ancora state lette.') : 'Apri lo Studio in Telegram per vedere le tue richieste.';
    var active = requests.filter(function (request) { return ['requested', 'writing', 'awaiting_suno'].indexOf(request.state) !== -1; }).length;
    byId('active-count').hidden = active === 0;
    byId('active-count').textContent = String(active);
    schedulePoll();
  }
  function rememberRequest(request) {
    var index = state.requests.findIndex(function (existing) { return existing.id === request.id; });
    if (index === -1) state.requests.unshift(request);
    else state.requests[index] = request;
    renderRequests();
  }
  function renderSong(song, privateSong) {
    var card = node('article', 'song-card');
    var cover = node('div', 'song-cover');
    cover.setAttribute('aria-hidden', 'true');
    cover.append(node('span', 'cover-disc', 'r.'));
    card.append(cover);
    if (!privateSong) card.append(node('p', 'song-evidence', song.textStatus === 'verificato' ? 'Testo indicizzato · verificato' : 'Testo da verificare'));
    card.append(node('h3', '', song.title || 'Senza titolo'));
    var tags = Array.isArray(song.tags) ? song.tags : [];
    var styles = Array.isArray(song.styles) ? song.styles : (song.genre ? [song.genre] : []);
    card.append(node('p', 'song-tags', tags.concat(styles).slice(0, 4).join(' · ')));
    var href = songUrl(song.suno_url || song.url);
    if (href) card.append(externalLink('Ascolta su Suno', href));
    else card.append(node('p', 'song-evidence', 'Collegamento di ascolto da verificare'));
    if (privateSong && song.playback_confirmed === true) card.append(node('p', 'verified-note', 'Ascolto confermato dal proprietario'));
    var playbackUrl = audioUrl(song);
    if (playbackUrl) {
      var audio = node('audio');
      audio.controls = true;
      audio.preload = 'none';
      audio.src = playbackUrl;
      audio.setAttribute('aria-label', 'Ascolta ' + text(song.title || 'la canzone'));
      card.append(audio);
    }
    return card;
  }
  function renderLibrary() {
    byId('private-library').hidden = !state.viewer;
    var list = byId('private-songs');
    list.replaceChildren();
    if (state.viewer) state.songs.forEach(function (song) { list.append(renderSong(song, true)); });
    if (state.viewer && state.libraryLoaded && !state.songs.length) message('library-status', 'Le canzoni conservate compariranno qui.');
  }
  function renderCatalog() {
    var query = byId('catalog-search').value.trim().toLocaleLowerCase('it');
    var selected = byId('catalog-tag').value;
    var songs = Array.isArray(catalog.songs) ? catalog.songs : [];
    var visible = songs.filter(function (song) {
      var tags = Array.isArray(song.tags) ? song.tags : [];
      var styles = Array.isArray(song.styles) ? song.styles : [];
      var haystack = [song.title, song.anchor, song.note].concat(tags, styles).map(text).join(' ').toLocaleLowerCase('it');
      return (!query || haystack.indexOf(query) !== -1) && (!selected || tags.indexOf(selected) !== -1);
    });
    var grid = byId('catalog-grid');
    grid.replaceChildren();
    visible.forEach(function (song) { grid.append(renderSong(song, false)); });
    byId('catalog-count').textContent = visible.length + ' di ' + songs.length + ' brani';
    byId('catalog-empty').hidden = visible.length !== 0;
  }
  function initCatalog() {
    var songs = Array.isArray(catalog.songs) ? catalog.songs : [];
    var verified = songs.filter(function (song) { return song.textStatus === 'verificato'; }).length;
    byId('catalog-stats').textContent = songs.length ? songs.length + ' brani · ' + verified + ' testi indicizzati · ' + (songs.length - verified) + ' da verificare' : 'Il catalogo non è disponibile in questa apertura.';
    byId('teaser-count').textContent = songs.length ? songs.length + ' brani nel catalogo pubblico' : 'Archivio pubblico su Suno';
    var tags = [];
    songs.forEach(function (song) { if (Array.isArray(song.tags)) song.tags.forEach(function (tag) { if (tags.indexOf(text(tag)) === -1) tags.push(text(tag)); }); });
    tags.sort(function (a, b) { return a.localeCompare(b, 'it'); }).forEach(function (tag) { var option = node('option', '', tag); option.value = tag; byId('catalog-tag').append(option); });
    var playlist = catalog.raffPlaylist || {};
    var playlistHref = playlistUrl(playlist.url);
    if (playlistHref && Array.isArray(playlist.songs) && playlist.songs.length) {
      byId('featured-playlist').hidden = false;
      byId('playlist-link').href = playlistHref;
      playlist.songs.forEach(function (song, index) {
        var href = songUrl(song.url);
        if (!href) return;
        var link = externalLink(song.title, href, 'playlist-song');
        link.prepend(node('span', '', String(index + 1).padStart(2, '0') + ' / ' + text(song.anchor || 'RAFFAELLO').toUpperCase()));
        byId('playlist-songs').append(link);
      });
    }
    renderCatalog();
  }
  async function loadRequests(quiet) {
    if (!state.viewer || state.loading) return;
    state.loading = true;
    renderAccess();
    if (!quiet) message('requests-status', 'Lettura dello stato dal servizio…');
    try {
      var data = await api('/requests');
      if (!Array.isArray(data.requests)) throw new Error('L’elenco ricevuto non è valido.');
      state.requests = data.requests;
      state.requestsLoaded = true;
      renderRequests();
      if (state.detail && byId('request-detail').open) {
        var latest = state.requests.find(function (request) { return request.id === state.detail.id; });
        if (latest && latest.state !== state.detail.state && !(Date.parse(latest.updated_at) < Date.parse(state.detail.updated_at))) {
          state.detail = Object.assign({}, state.detail, latest);
          renderDetail();
          message('detail-status', 'Il servizio ha aggiornato lo stato: ' + stateInfo(latest)[0].toLowerCase() + '.');
        }
      }
      message('requests-status', 'Stato aggiornato alle ' + new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }) + '.');
    } catch (error) { message('requests-status', error.message + (state.requestsLoaded ? ' I dati mostrati restano quelli dell’ultima lettura riuscita.' : ''), true); }
    finally { state.loading = false; renderAccess(); schedulePoll(); }
  }
  async function loadLibrary() {
    if (!state.viewer) return;
    try {
      var data = await api('/library');
      if (!Array.isArray(data.songs)) throw new Error('La Biblioteca ricevuta non è valida.');
      state.songs = data.songs;
      state.libraryLoaded = true;
      message('library-status', '');
      renderLibrary();
    } catch (error) { message('library-status', error.message, true); }
  }
  function schedulePoll() {
    window.clearTimeout(state.poll);
    if (document.hidden || !state.viewer || state.requests.every(function (request) { return ['requested', 'writing'].indexOf(request.state) === -1; })) return;
    state.poll = window.setTimeout(function () { loadRequests(true); }, 20000);
  }

  async function submitStory(event) {
    event.preventDefault();
    if (state.submitting || !state.viewer || !capability('requests')) return;
    var draft = currentDraft();
    if (!draft.story.trim()) { byId('story').focus(); message('form-status', 'Racconta almeno un pensiero da cui partire.', true); return; }
    state.submitting = true;
    renderAccess();
    message('form-status', 'Invio della tua richiesta…');
    try {
      state.clientId = state.clientId || uuid();
      var response = await api('/requests', 'POST', { story: draft.story.trim(), genre: draft.genre || 'Libero', mood: draft.mood, language: draft.language, client_id: state.clientId, personal_voice: owner() && capability('personal_voice') && byId('personal-voice').checked });
      if (!response.request || !response.request.id) throw new Error('Il servizio non ha confermato la richiesta. Aggiorna le richieste prima di riprovare.');
      state.clientId = null;
      rememberRequest(response.request);
      message('form-status', 'Richiesta ricevuta. Puoi seguirla nella sezione Richieste.');
      await loadRequests();
      setTab('richieste');
    } catch (error) { message('form-status', error.message, true); byId('form-status').focus(); }
    finally { state.submitting = false; renderAccess(); }
  }
  function closeDetail() {
    var dialog = byId('request-detail');
    if (dialog.open) dialog.close();
    state.detail = null;
    state.detailId = null;
    byId('detail-content').replaceChildren();
    message('detail-status', '');
  }
  async function openDetail(id) {
    if (!state.viewer || !/^[0-9a-f-]{36}$/i.test(text(id))) return;
    state.detailId = id;
    var known = state.requests.find(function (request) { return request.id === id; });
    if (known) { state.detail = known; renderDetail(); }
    var dialog = byId('request-detail');
    if (!dialog.open) dialog.showModal();
    message('detail-status', 'Lettura del dettaglio…');
    try {
      var response = await api('/requests/' + encodeURIComponent(id));
      if (!response.request || response.request.id !== id) throw new Error('Il dettaglio ricevuto non corrisponde alla richiesta.');
      if (!dialog.open || state.detailId !== id) return;
      state.detail = response.request;
      renderDetail();
      message('detail-status', '');
    } catch (error) { if (dialog.open && state.detailId === id) message('detail-status', error.message, true); }
  }
  function addCopyBox(container, title, value) {
    if (!value) return;
    var box = node('section', 'lyrics-box');
    var row = node('div', 'detail-copy-row');
    row.append(node('h3', '', title));
    var copy = node('button', 'button-secondary compact', 'Copia ↗');
    copy.type = 'button';
    copy.setAttribute('aria-label', 'Copia ' + title.toLowerCase());
    copy.addEventListener('click', async function () {
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('unavailable');
        await navigator.clipboard.writeText(text(value));
        message('detail-status', title + ' copiato.');
      } catch (_) { message('detail-status', 'La copia non è disponibile. Puoi selezionare il testo qui sotto.', true); }
    });
    row.append(copy);
    box.append(row, node('pre', '', value));
    container.append(box);
  }
  function actionButton(label, action, primary) {
    var button = node('button', primary ? 'button-primary' : 'button-secondary', label);
    button.type = 'button';
    button.dataset.action = action;
    button.addEventListener('click', function () { performAction(action, {}); });
    return button;
  }
  function renderDetail() {
    var request = state.detail;
    var container = byId('detail-content');
    container.replaceChildren();
    if (!request) return;
    container.append(statePill(request));
    var title = node('h2', '', request.title || 'La tua storia');
    title.id = 'detail-title';
    container.append(title, node('p', 'detail-story', request.story), node('p', 'detail-meta', [request.genre, request.mood, formatDate(request.updated_at)].filter(Boolean).join(' · ')), node('p', 'detail-help', stateInfo(request)[1]));
    if (request.state === 'error') {
      var problem = typeof request.error === 'string' ? request.error : request.error && request.error.message || request.error_message;
      if (problem) container.append(node('p', 'live-message', text(problem).slice(0, 500)));
    }
    var href = songUrl(request.suno_url);
    if (href) container.append(externalLink('Ascolta su Suno', href, 'button-primary'));
    if (request.playback_confirmed === true) container.append(node('p', 'verified-note', 'Ascolto confermato dal proprietario su Suno.'));
    if (request.personal_voice_confirmed === true) container.append(node('p', 'verified-note', 'Uso della voce personale confermato da Claudio.'));
    if (!owner()) return;
    addCopyBox(container, 'Il testo', request.lyrics);
    addCopyBox(container, 'Lo stile per Suno', request.style_prompt);
    if (request.lyrics) container.append(externalLink('Apri Suno per produrre il brano', 'https://suno.com/create', 'button-secondary'));
    var actions = node('div', 'detail-actions');
    if (request.state === 'requested') {
      var prepare = actionButton('Prepara il testo', 'prepare', true);
      prepare.disabled = !capability('lyrics_generation');
      actions.append(prepare);
      if (!capability('lyrics_generation')) container.append(node('p', 'detail-help', 'La preparazione del testo non è al momento disponibile.'));
    }
    if (request.state === 'error' && capability('lyrics_generation')) actions.append(actionButton('Riprova il testo', 'retry', true));
    if (['ready', 'kept'].indexOf(request.state) !== -1 && request.delivery && ['error', 'uncertain', 'pending'].indexOf(request.delivery.state) !== -1) actions.append(actionButton('Riprova la consegna', 'retry', false));
    if (request.state === 'ready' && href && request.playback_confirmed === true) actions.append(actionButton('Conserva', 'keep', true));
    if (['discarded', 'kept', 'writing'].indexOf(request.state) === -1) actions.append(actionButton('Scarta', 'discard', false));
    if (actions.childElementCount) container.append(actions);
    if (['requested', 'error', 'awaiting_suno'].indexOf(request.state) !== -1 && capability('result_delivery')) renderResultForm(container, request);
  }
  function renderResultForm(container, request) {
    var form = node('form', 'result-form');
    form.append(node('h3', '', 'Collega l’ascolto'), node('p', 'detail-help', 'Dopo la produzione, apri il brano su Suno. Registra il collegamento e conferma l’ascolto.'));
    var label = node('label', '', 'Titolo della canzone');
    label.htmlFor = 'result-title';
    var title = node('input');
    title.id = 'result-title'; title.maxLength = 140; title.required = true; title.value = text(request.title);
    var urlLabel = node('label', '', 'Collegamento del brano Suno');
    urlLabel.htmlFor = 'result-url';
    var url = node('input');
    url.id = 'result-url'; url.type = 'url'; url.required = true; url.placeholder = 'https://suno.com/song/…'; url.value = songUrl(request.suno_url) || '';
    var checkLabel = node('label', 'check-field');
    var check = node('input');
    check.type = 'checkbox'; check.required = true;
    checkLabel.append(check, node('span', '', 'Ho aperto il brano e verificato l’ascolto. Questa conferma verrà attribuita a me.'));
    var submit = node('button', 'button-primary', 'Conferma il risultato');
    submit.type = 'submit';
    var voiceCheck = null;
    form.append(label, title, urlLabel, url, checkLabel);
    if (request.personal_voice === true) {
      var voiceLabel = node('label', 'check-field');
      voiceCheck = node('input'); voiceCheck.type = 'checkbox'; voiceCheck.required = true;
      voiceLabel.append(voiceCheck, node('span', '', 'Ho applicato il campione My Voice - Apr 30 nella produzione su Suno.'));
      form.append(voiceLabel);
    }
    form.append(submit);
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var href = songUrl(url.value.trim());
      if (!href || !check.checked || !title.value.trim()) { message('detail-status', 'Inserisci titolo, un collegamento Suno valido e la tua conferma di ascolto.', true); return; }
      if (voiceCheck && !voiceCheck.checked) { message('detail-status', 'Conferma anche l’applicazione della voce personale su Suno.', true); return; }
      performAction('result', { title: title.value.trim(), suno_url: href, playback_confirmed: true, personal_voice_confirmed: !!voiceCheck && voiceCheck.checked });
    });
    container.append(form);
  }
  async function performAction(action, payload) {
    if (!owner() || !state.detail) return;
    var id = state.detail.id;
    byId('detail-content').querySelectorAll('button,input').forEach(function (element) { element.disabled = true; });
    message('detail-status', action === 'prepare' ? 'Preparazione del testo richiesta al servizio…' : 'Registrazione del passaggio…');
    try {
      var response = await api('/requests/' + encodeURIComponent(id) + '/' + action, 'POST', payload);
      if (!response.request || response.request.id !== id) throw new Error('Il servizio non ha confermato lo stato di questa richiesta.');
      rememberRequest(response.request);
      if (state.detail && state.detail.id === id) { state.detail = response.request; renderDetail(); message('detail-status', 'Stato confermato: ' + stateInfo(response.request)[0].toLowerCase() + '.'); }
      await Promise.all([loadRequests(true), loadLibrary()]);
    } catch (error) { if (state.detail && state.detail.id === id) { renderDetail(); message('detail-status', error.message, true); } }
  }

  function telegramTheme() {
    document.documentElement.dataset.scheme = initData && tg && tg.colorScheme === 'light' ? 'light' : 'dark';
    var root = document.documentElement.style;
    var safe = tg && tg.safeAreaInset || {};
    var content = tg && tg.contentSafeAreaInset || {};
    [['--safe-top', safe.top], ['--safe-bottom', safe.bottom], ['--content-top', content.top], ['--content-bottom', content.bottom]].forEach(function (entry) { root.setProperty(entry[0], Math.max(0, Number(entry[1]) || 0) + 'px'); });
  }
  function bindEvents() {
    document.querySelectorAll('[data-tab]').forEach(function (button) { button.addEventListener('click', function () { setTab(button.dataset.tab); }); });
    document.querySelectorAll('[role="tab"]').forEach(function (button, index) {
      button.addEventListener('keydown', function (event) {
        var tabs = ['crea', 'richieste', 'biblioteca'];
        var next = event.key === 'ArrowRight' ? (index + 1) % 3 : event.key === 'ArrowLeft' ? (index + 2) % 3 : event.key === 'Home' ? 0 : event.key === 'End' ? 2 : null;
        if (next != null) { event.preventDefault(); setTab(tabs[next], true); }
      });
    });
    byId('song-form').addEventListener('submit', submitStory);
    ['story', 'genre', 'mood', 'language'].forEach(function (id) { byId(id).addEventListener(id === 'story' ? 'input' : 'change', saveDraft); });
    byId('personal-voice').addEventListener('change', function () { state.clientId = null; });
    document.querySelectorAll('[data-prompt]').forEach(function (button) {
      button.addEventListener('click', function () {
        if (byId('story').value.trim()) { byId('story').focus(); return; }
        byId('story').value = button.dataset.prompt;
        saveDraft(); byId('story').focus();
      });
    });
    byId('clear-draft').addEventListener('click', function () {
      byId('song-form').reset();
      state.clientId = null;
      try { window.localStorage.removeItem(draftKey); } catch (_) {}
      byId('story-count').textContent = '0 / 1800';
      byId('draft-note').textContent = 'Bozza svuotata.';
      byId('story').focus();
    });
    byId('catalog-search').addEventListener('input', renderCatalog);
    byId('catalog-tag').addEventListener('change', renderCatalog);
    byId('refresh-requests').addEventListener('click', function () { Promise.all([loadRequests(), loadLibrary()]); });
    byId('close-detail').addEventListener('click', closeDetail);
    byId('request-detail').addEventListener('cancel', function () { state.detail = null; state.detailId = null; });
    byId('open-telegram').addEventListener('click', function (event) {
      if (tg && typeof tg.openTelegramLink === 'function') { event.preventDefault(); tg.openTelegramLink(byId('open-telegram').href); }
    });
    document.addEventListener('visibilitychange', function () { if (document.hidden) window.clearTimeout(state.poll); else if (state.viewer) loadRequests(true); });
    window.addEventListener('hashchange', function () {
      var name = window.location.hash.slice(1);
      if (['crea', 'richieste', 'biblioteca'].indexOf(name) !== -1) setTab(name);
    });
  }
  async function boot() {
    restoreDraft(); bindEvents(); telegramTheme(); initCatalog(); setTab(window.location.hash.slice(1)); renderAccess();
    if (tg) {
      try { if (typeof tg.ready === 'function') tg.ready(); if (typeof tg.expand === 'function') tg.expand(); } catch (_) {}
      if (typeof tg.onEvent === 'function') { tg.onEvent('themeChanged', telegramTheme); tg.onEvent('safeAreaChanged', telegramTheme); tg.onEvent('contentSafeAreaChanged', telegramTheme); }
      if (typeof tg.requestFullscreen === 'function' && typeof tg.isVersionAtLeast === 'function' && tg.isVersionAtLeast('8.0')) {
        byId('fullscreen').hidden = false;
        byId('fullscreen').addEventListener('click', function () { try { tg.requestFullscreen(); } catch (_) { message('form-status', 'La modalità a schermo intero non è disponibile in questa apertura.', true); } });
      }
    }
    var configPromise = api('/studio/config', 'GET', null, true).then(function (config) { state.config = config; renderAccess(); }).catch(function () { message('form-status', 'La configurazione dello Studio non è disponibile. Il catalogo pubblico resta consultabile.', true); });
    var sessionPromise = initData ? api('/session').then(function (session) {
      if (!session.viewer || typeof session.viewer.is_owner !== 'boolean') throw new Error('Il servizio non ha confermato l’accesso.');
      state.viewer = session.viewer;
      renderAccess();
    }).catch(function (error) { message('form-status', error.message, true); renderAccess(); }) : Promise.resolve();
    await Promise.all([configPromise, sessionPromise]);
    if (state.viewer) await Promise.all([loadRequests(true), loadLibrary()]);
    else renderRequests();
  }
  boot();
}());
