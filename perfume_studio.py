"""Terzi Parfums: immutable formula registry, private archive and optional images.
Concept: Claudio Terzi. No customer names are sent to the image provider.
"""
from datetime import datetime, timezone
from pathlib import Path
import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import uuid

from flask import Blueprint, Response, jsonify, redirect, render_template, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

studio = Blueprint('perfume_studio', __name__)
ROOT = Path(__file__).parent


class ArchiveUnavailable(RuntimeError):
    pass


def _redis():
    url = os.getenv('REDIS_URL') or os.getenv('KV_URL')
    if not url:
        return None
    import redis
    return redis.from_url(url, socket_connect_timeout=3, socket_timeout=5)


def _db():
    if os.getenv('VERCEL'):
        raise ArchiveUnavailable('Archivio permanente non configurato')
    path = Path(os.getenv('PERFUME_DB_PATH', ROOT / 'output' / 'perfume_registry.sqlite3'))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE IF NOT EXISTS perfumes (serial TEXT PRIMARY KEY, body TEXT NOT NULL)')
    return db


def serial_for(creation_id):
    return 'TP-' + uuid.UUID(creation_id).hex.upper()


def read_record(serial):
    try:
        client = _redis()
        if client is not None:
            raw = client.get('terzi:formula:' + serial)
        else:
            with _db() as db:
                row = db.execute('SELECT body FROM perfumes WHERE serial = ?', (serial,)).fetchone()
                raw = row[0] if row else None
        return json.loads(raw) if raw else None
    except Exception as exc:
        raise ArchiveUnavailable('Archivio non disponibile') from exc


def save_record(creation_id, customer, intention, perfume):
    serial = serial_for(creation_id)
    formula = json.dumps(perfume, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    record = dict(schema_version=1, serial=serial, customer=customer, intention=intention,
                  created_at=datetime.now(timezone.utc).isoformat(), perfume=perfume,
                  formula_sha256=hashlib.sha256(formula.encode()).hexdigest())
    body = json.dumps(record, ensure_ascii=False)
    try:
        client = _redis()
        if client is not None:
            # The record itself is the source of truth; a repeated POST cannot overwrite it.
            inserted = client.set('terzi:formula:' + serial, body, nx=True)
            if not inserted:
                previous = read_record(serial)
                if previous['customer'] != customer or previous['intention'] != intention:
                    raise ValueError('Identificativo già utilizzato per un’altra creazione')
                return previous
        else:
            with _db() as db:
                db.execute('INSERT OR IGNORE INTO perfumes VALUES (?, ?)', (serial, body))
                previous = json.loads(db.execute('SELECT body FROM perfumes WHERE serial = ?', (serial,)).fetchone()[0])
                if previous['customer'] != customer or previous['intention'] != intention:
                    raise ValueError('Identificativo già utilizzato per un’altra creazione')
                return previous
    except ValueError:
        raise
    except Exception as exc:
        raise ArchiveUnavailable('Salvataggio non confermato') from exc
    return record


def images_ready():
    return bool(os.getenv('OPENAI_API_KEY') and (os.getenv('REDIS_URL') or os.getenv('KV_URL'))
                and os.getenv('PERFUME_IMAGES_ENABLED') == '1')


def _image_signer():
    return URLSafeTimedSerializer(os.environ['OPENAI_API_KEY'], salt='terzi-image-v1')


def render_result(intention, perfume=None, error=None, customer='', record=None, archive_error=None):
    token = _image_signer().dumps(record['serial']) if record and images_ready() else None
    from perfume_visual import bottle_brief
    visual = perfume.get('flacone') or bottle_brief(perfume) if perfume else None
    return render_template('perfume_result.html', intention=intention, p=perfume, error=error,
                           customer=customer, record=record, archive_error=archive_error,
                           image_token=token, visual=visual)


@studio.get('/atelier/esempio')
def public_example():
    """A curated public example: reading it never starts an AI call."""
    perfume = json.loads((ROOT / 'studio/parfums/examples/cantiere.json').read_text(encoding='utf-8'))
    return render_result(perfume['esempio']['intenzione'], perfume=perfume,
                         customer='Claudio Terzi',
                         archive_error='Esempio pubblico conservato con il sito. Scarica la scheda e il codice della formula.')


def _archive_signer():
    secret = os.getenv('PERFUME_ARCHIVE_SECRET', '')
    if len(secret) < 32 or not os.getenv('PERFUME_ARCHIVE_PASSWORD'):
        raise ArchiveUnavailable('Accesso all’archivio non configurato')
    return URLSafeTimedSerializer(secret, salt='terzi-archive-v1')


def _authorized():
    try:
        return _archive_signer().loads(request.cookies.get('terzi_archive', ''), max_age=3600) == 'owner'
    except (BadSignature, SignatureExpired):
        return False


@studio.route('/atelier/archivio', methods=['GET', 'POST'])
def archive():
    try:
        signer = _archive_signer()
        if request.method == 'POST':
            supplied = request.form.get('password', '')
            if not hmac.compare_digest(supplied.encode(), os.environ['PERFUME_ARCHIVE_PASSWORD'].encode()):
                return render_template('perfume_archive.html', login=True, error='Accesso non riuscito.'), 401
            response = redirect('/atelier/archivio')
            response.set_cookie('terzi_archive', signer.dumps('owner'), max_age=3600,
                                httponly=True, secure=bool(os.getenv('VERCEL')), samesite='Strict', path='/atelier')
            return response
        if not _authorized():
            return render_template('perfume_archive.html', login=True)
        serial = request.args.get('serial', '').strip().upper()
        if serial:
            record = read_record(serial)
            if not record:
                return render_template('perfume_archive.html', error='Numero di serie non trovato.', records=[]), 404
            return render_result(record['intention'], record['perfume'], customer=record['customer'], record=record)
        # Bounded listing; records remain addressable by serial even outside the latest 100.
        client = _redis()
        if client is not None:
            keys = []
            for key in client.scan_iter(match='terzi:formula:*', count=100):
                keys.append(key)
                if len(keys) >= 100:
                    break
            records = [json.loads(raw) for raw in (client.mget(keys) if keys else []) if raw]
        else:
            with _db() as db:
                records = [json.loads(row[0]) for row in db.execute('SELECT body FROM perfumes ORDER BY rowid DESC LIMIT 100')]
        records.sort(key=lambda x: x['created_at'], reverse=True)
        return render_template('perfume_archive.html', records=records)
    except ArchiveUnavailable:
        return render_template('perfume_archive.html', error='L’archivio deve essere configurato prima di poterlo consultare.', unavailable=True), 503


@studio.after_request
def private_headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Referrer-Policy'] = 'no-referrer'
    if request.path.startswith('/api/profumo/'):
        response.headers.pop('Access-Control-Allow-Origin', None)
    return response


@studio.route('/api/profumo/immagine', methods=['POST'])
def perfume_image():
    if not images_ready():
        return jsonify(error='La creazione di immagini personalizzate non è ancora attiva.'), 503
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get('token'), str) or len(body['token']) > 1000:
        return jsonify(error='Richiesta non valida.'), 400
    try:
        serial = _image_signer().loads(body['token'], max_age=3600)
        record = read_record(serial)
        if not record:
            return jsonify(error='Formula non trovata.'), 404
    except (BadSignature, SignatureExpired):
        return jsonify(error='Riapri la formula dall’archivio per creare l’immagine.'), 403
    except ArchiveUnavailable:
        return jsonify(error='Archivio temporaneamente non disponibile.'), 503
    cache_key = 'terzi:image:' + serial
    try:
        client = _redis()
        cached = client.get(cache_key)
        if cached:
            return Response(cached, mimetype='image/webp')
        if body.get('action') == 'read':
            return jsonify(error='Nessun ritratto salvato per questa formula.'), 404
        if body.get('action', 'generate') != 'generate':
            return jsonify(error='Azione non valida.'), 400
        # Atomic lock + global UTC daily cap, shared across Vercel instances.
        quota_key = 'terzi:image-quota:' + datetime.now(timezone.utc).strftime('%Y-%m-%d')
        limit = max(1, min(100, int(os.getenv('PERFUME_IMAGES_DAILY_LIMIT', '10'))))
        admitted = client.eval("""
            if redis.call('EXISTS', KEYS[1]) == 1 then return 0 end
            if tonumber(redis.call('GET', KEYS[2]) or '0') >= tonumber(ARGV[1]) then return -1 end
            redis.call('SET', KEYS[1], '1', 'EX', 180)
            redis.call('INCR', KEYS[2]); redis.call('EXPIRE', KEYS[2], 172800)
            return 1
        """, 2, cache_key + ':lock', quota_key, limit)
        if admitted != 1:
            return jsonify(error='Immagine in preparazione: riprova tra poco.' if admitted == 0 else 'Le creazioni visive di oggi sono esaurite.'), 429
    except Exception:
        return jsonify(error='La creazione visiva non è disponibile adesso.'), 503
    from perfume_visual import bottle_brief
    # Rebuild from trusted catalogue fields even for old stored records.
    visual = bottle_brief(record['perfume'])
    prompt = visual['prompt']
    model = os.getenv('OPENAI_IMAGE_MODEL', 'gpt-image-2')
    metadata = dict(id=str(uuid.uuid4()), serial=serial, status='pending', model=model,
                    created_at=datetime.now(timezone.utc).isoformat(), visual=visual,
                    estimated_cost=None)
    try:
        client.set(cache_key + ':metadata', json.dumps(metadata, ensure_ascii=False))
        from openai import OpenAI
        with OpenAI(api_key=os.environ['OPENAI_API_KEY'], timeout=45, max_retries=0) as api:
            result = api.images.generate(model=model, prompt=prompt, size='1024x1024',
                                         quality='high', output_format='webp', n=1)
        raw = base64.b64decode(result.data[0].b64_json, validate=True)
        if len(raw) > 3_000_000 or raw[:4] != b'RIFF' or raw[8:12] != b'WEBP':
            raise ValueError('Image format or size invalid')
        # No expiry: it is an asset, not a disposable 30-day cache.
        # Production Redis must have durable persistence/backups and no eviction.
        client.set(cache_key, raw)
        usage = getattr(result, 'usage', None)
        metadata.update(status='complete', image_sha256=hashlib.sha256(raw).hexdigest(),
                        usage=usage.model_dump() if hasattr(usage, 'model_dump') else None)
        client.set(cache_key + ':metadata', json.dumps(metadata, ensure_ascii=False))
        return Response(raw, mimetype='image/webp')
    except Exception:
        try:
            metadata.update(status='error_or_unconfirmed')
            client.set(cache_key + ':metadata', json.dumps(metadata, ensure_ascii=False))
        except Exception:
            pass
        # No automatic retries after a timeout: the provider may have charged the attempt.
        return jsonify(error='Il ritratto non è pronto. La formula è salva e il flacone Atelier resta disponibile.'), 502
    finally:
        try:
            client.delete(cache_key + ':lock')
        except Exception:
            pass
