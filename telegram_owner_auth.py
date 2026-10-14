"""Shared existing Telegram signature verification. No client flag grants spend."""
import hashlib,hmac,json,os,time,urllib.parse

def utente_da_init_data(init_data: str, token: str, max_eta_s: int = 86_400) -> dict | None:
    """Verifica la firma di Telegram sull'initData della Mini App e restituisce l'utente.

    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not init_data or not token or len(init_data) > 8192:
        return None
    campi = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    firma = campi.pop("hash", "")
    if len(firma) != 64 or any(c not in '0123456789abcdef' for c in firma):
        return None
    da_controllare = "\n".join(f"{k}={v}" for k, v in sorted(campi.items()))
    chiave = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    attesa = hmac.new(chiave, da_controllare.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(attesa, firma):
        return None
    try:
        if time.time() - int(campi.get("auth_date", "0")) > max_eta_s:
            return None
        return json.loads(campi.get("user", "{}"))
    except (ValueError, TypeError):
        return None

def telegram_owner(body):
    if not isinstance(body, dict): return False
    signed = body.get('initData')
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    owner = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
    if not isinstance(signed, str) or not owner: return False
    user = utente_da_init_data(signed, token)
    return isinstance(user, dict) and str(user.get('id', '')) == owner
