"""Telegram Mini App identity. Raw initData and bot credentials are never stored."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
from urllib.parse import parse_qsl


class MusicError(ValueError):
    def __init__(self, message: str, status: int = 400, code: str = "invalid_request"):
        super().__init__(message)
        self.status, self.code = status, code


def validate_init_data(raw: str | None, bot_token: str, now: int | None = None) -> dict:
    if not isinstance(raw, str) or not raw or len(raw) > 16384 or not bot_token:
        raise MusicError("Apri lo Studio dal bot Telegram.", 401, "telegram_required")
    try:
        if re.search(r"%(?![0-9a-fA-F]{2})", raw):
            raise ValueError("bad encoding")
        pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True,
                          encoding="utf-8", errors="strict", max_num_fields=20)
        if len({key for key, _ in pairs}) != len(pairs):
            raise ValueError("duplicate field")
        data = dict(pairs)
        received_hash = data.pop("hash", "")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", received_hash):
            raise ValueError("bad hash")
        check = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))
        secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received_hash.lower()):
            raise ValueError("bad signature")
        date = data.get("auth_date", "")
        if not re.fullmatch(r"[0-9]{1,12}", date):
            raise ValueError("bad date")
        age = (int(time.time()) if now is None else now) - int(date)
        if age < 0 or age > 3600:
            raise ValueError("expired or future")
        user = json.loads(data.get("user", "null"))
        if not isinstance(user, dict) or type(user.get("id")) is not int or not 0 < user["id"] < 2**52:
            raise ValueError("bad user")
        name = user.get("first_name")
        if not isinstance(name, str) or not name.strip() or len(name) > 128:
            raise ValueError("bad name")
        return {"id": user["id"], "first_name": name.strip()}
    except (ValueError, UnicodeError, TypeError) as exc:
        raise MusicError("La sessione Telegram non è valida o è scaduta. Riapri lo Studio.",
                         401, "invalid_telegram_session") from exc


def owner_ids() -> frozenset[int]:
    explicit = "MUSIC_OWNER_IDS" in os.environ
    raw = os.getenv("MUSIC_OWNER_IDS" if explicit else "RAFFAELLO_ALLOWED_USERS", "")
    parts = [part.strip() for part in raw.split(",")]
    if not parts or any(not re.fullmatch(r"[1-9][0-9]{0,15}", part) for part in parts):
        return frozenset()
    ids = frozenset(int(part) for part in parts)
    if any(uid >= 2**52 for uid in ids) or (not explicit and len(parts) != 1):
        return frozenset()
    return ids


def is_owner(user_id: int) -> bool:
    return type(user_id) is int and user_id in owner_ids()
