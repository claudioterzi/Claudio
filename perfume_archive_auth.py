"""Private archive sessions, CSRF and shared login throttling. Claudio Terzi."""
import hashlib
import hmac
import os
import secrets
import time

from flask import request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.security import check_password_hash

SESSION_SECONDS = 3600
WINDOW_SECONDS = 900


def signer(salt='terzi-archive-v2'):
    from perfume_studio import ArchiveUnavailable
    secret = os.getenv('PERFUME_ARCHIVE_SECRET', '')
    if len(secret) < 32 or not password_config():
        raise ArchiveUnavailable('Accesso all’archivio non configurato')
    return URLSafeTimedSerializer(secret, salt=salt)


def password_config():
    return os.getenv('PERFUME_ARCHIVE_PASSWORD_HASH') or os.getenv('PERFUME_ARCHIVE_PASSWORD', '')


def password_matches(value):
    if not isinstance(value, str) or len(value) > 1024:
        return False
    encoded = os.getenv('PERFUME_ARCHIVE_PASSWORD_HASH')
    if encoded:
        try:
            return check_password_hash(encoded, value)
        except (ValueError, TypeError):
            return False
    return hmac.compare_digest(value.encode(), password_config().encode())


def _digest(value):
    return hmac.new(os.environ['PERFUME_ARCHIVE_SECRET'].encode(), value.encode(), hashlib.sha256).hexdigest()


def _session_db():
    from perfume_studio import _db
    db = _db()
    db.execute('CREATE TABLE IF NOT EXISTS archive_sessions (sid TEXT PRIMARY KEY, expires INTEGER NOT NULL)')
    return db


def new_session():
    from perfume_studio import _redis
    sid = secrets.token_urlsafe(32)
    client = _redis()
    if client is not None:
        client.set('terzi:session:' + sid, '1', ex=SESSION_SECONDS)
    else:
        with _session_db() as db:
            db.execute('DELETE FROM archive_sessions WHERE expires <= ?', (int(time.time()),))
            db.execute('INSERT INTO archive_sessions VALUES (?, ?)', (sid, int(time.time()) + SESSION_SECONDS))
    return signer().dumps({'sid': sid, 'credential': _digest(password_config())})


def session_id():
    try:
        value = signer().loads(request.cookies.get('terzi_archive', ''), max_age=SESSION_SECONDS)
        if (not isinstance(value, dict) or not isinstance(value.get('sid'), str)
                or len(value['sid']) != 43 or value.get('credential') != _digest(password_config())):
            return None
        return value['sid']
    except BadSignature:
        return None


def authorized():
    from perfume_studio import _redis
    sid = session_id()
    if not sid:
        return False
    client = _redis()
    if client is not None:
        return bool(client.get('terzi:session:' + sid))
    with _session_db() as db:
        return db.execute('SELECT 1 FROM archive_sessions WHERE sid=? AND expires>?', (sid, int(time.time()))).fetchone() is not None


def revoke_session():
    from perfume_studio import _redis
    sid = session_id()
    if not sid:
        return
    client = _redis()
    if client is not None:
        client.delete('terzi:session:' + sid)
    else:
        with _session_db() as db:
            db.execute('DELETE FROM archive_sessions WHERE sid=?', (sid,))


def csrf_token(action):
    return signer('terzi-archive-csrf-v1').dumps({'nonce': secrets.token_urlsafe(24), 'action': action})


def valid_csrf(action):
    if request.headers.get('Sec-Fetch-Site') == 'cross-site':
        return False
    origin = request.headers.get('Origin')
    if origin and origin.rstrip('/') != request.host_url.rstrip('/'):
        return False
    token = request.form.get('csrf_token', '')
    cookie = request.cookies.get('terzi_archive_csrf', '')
    if not token or len(token) > 1000 or not hmac.compare_digest(token.encode(), cookie.encode()):
        return False
    try:
        value = signer('terzi-archive-csrf-v1').loads(token, max_age=600)
        return isinstance(value, dict) and value.get('action') == action
    except BadSignature:
        return False


def allow_login():
    """Atomic shared limits: five attempts/client and thirty/archive per 15 min.

    Uses the runtime remote address; untrusted forwarding headers are ignored.
    No IP address or submitted password is stored. Storage failure closes login.
    """
    from perfume_studio import _redis, _db
    now = int(time.time())
    bucket = now // WINDOW_SECONDS
    keys = ['terzi:login:' + str(bucket) + ':' + _digest(request.remote_addr or 'unknown'),
            'terzi:login:' + str(bucket) + ':all']
    client = _redis()
    if client is not None:
        return client.eval("""
            if tonumber(redis.call('GET', KEYS[1]) or '0') >= 5 then return 0 end
            if tonumber(redis.call('GET', KEYS[2]) or '0') >= 30 then return 0 end
            for i=1,2 do redis.call('INCR', KEYS[i]); redis.call('EXPIRE', KEYS[i], 1800) end
            return 1
        """, 2, *keys) == 1
    with _db() as db:
        db.execute('CREATE TABLE IF NOT EXISTS archive_login_limits (key TEXT PRIMARY KEY, attempts INTEGER NOT NULL, expires INTEGER NOT NULL)')
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM archive_login_limits WHERE expires<=?', (now,))
        for key, limit in zip(keys, (5, 30)):
            row = db.execute('SELECT attempts FROM archive_login_limits WHERE key=?', (key,)).fetchone()
            if row and row[0] >= limit:
                return False
        for key in keys:
            db.execute('INSERT INTO archive_login_limits VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET attempts=attempts+1', (key, (bucket+2)*WINDOW_SECONDS))
    return True


def cookie(response, name, value, max_age):
    response.set_cookie(name, value, max_age=max_age, httponly=True,
                        secure=bool(os.getenv('VERCEL')), samesite='Strict', path='/atelier')
    return response
