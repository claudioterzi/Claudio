"""Private browser sessions, idempotent commands and Redis result history."""
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
import re
import secrets
import time

from flask import Blueprint, jsonify, request
from itsdangerous import BadSignature

from perfume_archive_auth import allow_login, password_config, password_matches, signer
from perfume_studio import ArchiveUnavailable, _redis
from telegram_owner_auth import telegram_owner, bot_token_usable

agora = Blueprint('agora_web', __name__)
COMMANDS = frozenset({'consiglio', 'briefing', 'snapshot', 'tarocchi', 'agenda', 'riflessione'})
COOKIE = '__Host-agora' if os.getenv('VERCEL') else 'agora_owner'
RETENTION = 30 * 86400
PREFIX = 'agora:v1:'
RID = re.compile(r'^[a-f0-9]{32}$')


@agora.before_request
def bounded_body():
    if request.content_length and request.content_length > 16384:
        return jsonify(ok=False, errore='Richiesta troppo grande.'), 413


def _client():
    client = _redis()
    if client is None:
        raise ArchiveUnavailable('Archivio del sito non disponibile. Riprova più tardi.')
    return client


def _credential():
    return hmac.new(os.environ['PERFUME_ARCHIVE_SECRET'].encode(), password_config().encode(), hashlib.sha256).hexdigest()


def same_origin():
    origin = request.headers.get('Origin')
    return (request.headers.get('X-Agora') == '1'
            and request.headers.get('Sec-Fetch-Site') != 'cross-site'
            and (not origin or origin.rstrip('/') == request.host_url.rstrip('/')))


def browser_owner():
    try:
        value = signer('agora-owner-v1').loads(request.cookies.get(COOKIE, ''), max_age=3600)
        if not isinstance(value, dict) or value.get('credential') != _credential():
            return False
        sid = value.get('sid', '')
        return isinstance(sid, str) and len(sid) == 43 and bool(_client().get(PREFIX + 'session:' + sid))
    except BadSignature:
        return False


def _owner(body):
    return telegram_owner(body) or (same_origin() and browser_owner())


def _record(client, rid):
    raw = client.get(PREFIX + 'request:' + rid)
    return json.loads(raw) if raw else None


def _save(client, rid, record):
    encoded = json.dumps(record, ensure_ascii=False)
    client.set(PREFIX + 'request:' + rid, encoded, ex=RETENTION)
    observed = client.get(PREFIX + 'request:' + rid)
    if isinstance(observed, bytes):
        observed = observed.decode()
    if observed != encoded:
        raise ArchiveUnavailable('Salvataggio non confermato. Conserva la domanda e controlla la cronologia.')


@agora.after_request
def private_headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers.pop('Access-Control-Allow-Origin', None)
    return response


@agora.errorhandler(ArchiveUnavailable)
def unavailable(exc):
    return jsonify(ok=False, errore=str(exc)), 503


@agora.route('/api/agora/session', methods=['GET', 'POST', 'DELETE'])
def session():
    try:
        configured = bool(password_config()) and len(os.getenv('PERFUME_ARCHIVE_SECRET', '')) >= 32
        if request.method == 'GET':
            authorized = browser_owner() if configured else False
            return jsonify(ok=True, autorizzato=authorized, configurato=configured,
                           telegram_disponibile=bot_token_usable(os.getenv('AGORA_TELEGRAM_BOT_TOKEN', '')),
                           archivio='redis' if _redis() is not None else 'non disponibile')
        if not same_origin():
            return jsonify(ok=False, errore='Riapri la pagina e riprova.'), 403
        if request.method == 'DELETE':
            if browser_owner():
                value = signer('agora-owner-v1').loads(request.cookies.get(COOKIE, ''), max_age=3600)
                _client().delete(PREFIX + 'session:' + value['sid'])
            response = jsonify(ok=True)
            response.delete_cookie(COOKIE, path='/', secure=bool(os.getenv('VERCEL')), httponly=True, samesite='Strict')
            return response
        if not configured:
            raise ArchiveUnavailable('Accesso privato del sito non configurato.')
        if not allow_login():
            return jsonify(ok=False, errore='Troppi tentativi. Riprova tra 15 minuti.'), 429
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or not password_matches(body.get('password')):
            return jsonify(ok=False, errore='Password privata non riconosciuta.'), 403
        sid = secrets.token_urlsafe(32)
        _client().set(PREFIX + 'session:' + sid, '1', ex=3600)
        response = jsonify(ok=True, autorizzato=True)
        response.set_cookie(COOKIE, signer('agora-owner-v1').dumps({'sid': sid, 'credential': _credential()}),
                            max_age=3600, httponly=True, secure=bool(os.getenv('VERCEL')), samesite='Strict', path='/')
        return response
    except ArchiveUnavailable:
        raise
    except Exception:
        raise ArchiveUnavailable('Accesso privato temporaneamente non disponibile.')


@agora.route('/api/agora/history', methods=['POST'])
@agora.route('/api/agora/richieste/<rid>', methods=['POST'])
def history(rid=None):
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not _owner(body):
        return jsonify(ok=False, errore='Accedi all’area privata per vedere le risposte.'), 403
    try:
        client = _client()
        if rid:
            if not RID.fullmatch(rid):
                return jsonify(ok=False, errore='Richiesta non valida.'), 400
            record = _record(client, rid)
            if not record:
                return jsonify(ok=False, errore='Risposta non presente in archivio.'), 404
            if record['stato'] == 'in_corso' and time.time() - record['iniziata_epoch'] > 240:
                record['stato'] = 'interrotto'
                record['errore'] = 'Il server non ha registrato un risultato. La domanda è conservata; puoi inviarla di nuovo.'
            return jsonify(ok=True, richiesta=record)
        records = [_record(client, raw.decode() if isinstance(raw, bytes) else raw)
                   for raw in client.lrange(PREFIX + 'history', 0, 49)]
        return jsonify(ok=True, richieste=[{'id': r['id'], 'comando': r['comando'], 'data': r['data'], 'stato': r['stato']}
                                          for r in records if r], conservazione_giorni=30)
    except ArchiveUnavailable:
        raise
    except Exception:
        raise ArchiveUnavailable('Cronologia temporaneamente non disponibile.')


@agora.route('/api/agora', methods=['POST'])
def command():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not _owner(body):
        return jsonify(ok=False, errore='Accedi all’area privata per eseguire i comandi.'), 403
    command = body.get('comando')
    if not isinstance(command, str):
        return jsonify(ok=False, errore='Comando non valido.'), 400
    command = command.strip()
    name = command.split(maxsplit=1)[0][1:].lower() if command.startswith('/') else ''
    if name not in COMMANDS or len(command) > 1000:
        return jsonify(ok=False, errore='Comando non previsto.'), 400
    parts = command.split(maxsplit=1)
    command = '/' + name + (' ' + parts[1] if len(parts) == 2 else '')
    rid = body.get('id') or secrets.token_hex(16)
    if not isinstance(rid, str) or not RID.fullmatch(rid):
        return jsonify(ok=False, errore='Identificativo non valido.'), 400
    telegram = body.get('telegram') is True
    try:
        client = _client()
        old = _record(client, rid)
        if old:
            if old['comando'] != command or old['telegram_richiesto'] != telegram:
                return jsonify(ok=False, errore='Identificativo già usato per un’altra richiesta.'), 409
            return jsonify(ok=True, richiesta=old), (202 if old['stato'] == 'in_corso' else 200)
        if not client.set(PREFIX + 'active', rid, nx=True, ex=240):
            return jsonify(ok=False, errore='Un comando è già in corso. Attendi il risultato.'), 409
        record = {'id': rid, 'comando': command, 'telegram_richiesto': telegram, 'telegram_inviato': False,
                  'data': datetime.now(timezone.utc).isoformat(), 'iniziata_epoch': time.time(), 'stato': 'in_corso'}
        try:
            # A concurrent identical request may have completed after the first read.
            old = _record(client, rid)
            if old:
                if old['comando'] != command or old['telegram_richiesto'] != telegram:
                    return jsonify(ok=False, errore='Identificativo già usato per un’altra richiesta.'), 409
                return jsonify(ok=True, richiesta=old), (202 if old['stato'] == 'in_corso' else 200)
            _save(client, rid, record)
            client.lpush(PREFIX + 'history', rid)
            client.ltrim(PREFIX + 'history', 0, 49)
            from agora_runtime import esegui
            result = esegui(command)
            record.update(stato=result['stato'], risultato=result)
            # Persist the result before attempting delivery to the second channel.
            _save(client, rid, record)
            if telegram:
                from sdq1.notifiche import invia
                text = result['testo']
                token = os.getenv('AGORA_TELEGRAM_BOT_TOKEN')
                outcomes = [invia(text[i:i+3500], parse_mode='', bot_token=token)
                            for i in range(0, len(text), 3500)] if token else []
                record['telegram_inviato'] = bool(outcomes) and all(outcomes)
                _save(client, rid, record)
            return jsonify(ok=True, richiesta=record)
        except ArchiveUnavailable:
            raise
        except Exception as exc:
            print('[AGORA] command error:', type(exc).__name__)
            record.update(stato='errore', errore='Il comando non è riuscito. La domanda è conservata in cronologia.')
            _save(client, rid, record)
            return jsonify(ok=True, richiesta=record)
        finally:
            client.eval("if redis.call('GET',KEYS[1]) == ARGV[1] then return redis.call('DEL',KEYS[1]) else return 0 end", 1, PREFIX + 'active', rid)
    except ArchiveUnavailable:
        raise
    except Exception:
        raise ArchiveUnavailable('Archivio non raggiungibile. Non ripetere subito: controlla la cronologia.')
