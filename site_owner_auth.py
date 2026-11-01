"""Server-verified owner recognition shared by Agorà, tarot readings and voice.

The owner is recognised either by a Telegram Mini App signature or by the private
browser session opened with the site password (signed cookie + Redis session).
A client flag never grants access.
"""
import hashlib
import hmac
import os

from flask import request
from itsdangerous import BadSignature

from telegram_owner_auth import telegram_owner

COOKIE = '__Host-agora' if os.getenv('VERCEL') else 'agora_owner'
PREFIX = 'agora:v1:'


def credential():
    from perfume_archive_auth import password_config
    return hmac.new(os.environ['PERFUME_ARCHIVE_SECRET'].encode(), password_config().encode(), hashlib.sha256).hexdigest()


def same_origin():
    origin = request.headers.get('Origin')
    return (request.headers.get('X-Agora') == '1'
            and request.headers.get('Sec-Fetch-Site') != 'cross-site'
            and (not origin or origin.rstrip('/') == request.host_url.rstrip('/')))


def browser_owner(client=None):
    from perfume_archive_auth import signer
    from perfume_studio import ArchiveUnavailable, _redis
    try:
        value = signer('agora-owner-v1').loads(request.cookies.get(COOKIE, ''), max_age=3600)
        if not isinstance(value, dict) or value.get('credential') != credential():
            return False
        sid = value.get('sid', '')
        if not isinstance(sid, str) or len(sid) != 43:
            return False
        client = client or _redis()
        if client is None:
            raise ArchiveUnavailable('Archivio del sito non disponibile. Riprova più tardi.')
        return bool(client.get(PREFIX + 'session:' + sid))
    except BadSignature:
        return False


def site_owner(body):
    """True only for the owner: Telegram signature or private browser session."""
    if telegram_owner(body):
        return True
    if not request.cookies.get(COOKIE) or not same_origin():
        return False
    try:
        return browser_owner()
    except Exception:
        return False
