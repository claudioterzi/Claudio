"""Telegram signatures, time boundary and explicit owner authority."""
import hashlib
import hmac
import json
from urllib.parse import urlencode

import pytest

from bot.music_auth import MusicError, is_owner, owner_ids, validate_init_data

TOKEN = "123456789:synthetic-test-key-no-real-access"
NOW = 1800000000


def signed(user=None, date=NOW, **extra):
    values = {"auth_date": str(date), "user": json.dumps(user if user is not None else {"id": 17, "first_name": "Claudio"}, separators=(",", ":")), "query_id": "test-query", **extra}
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    check = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
    values["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(values)


def test_authentic_signed_user_and_exact_ttl():
    assert validate_init_data(signed(), TOKEN, now=NOW) == {"id": 17, "first_name": "Claudio"}
    assert validate_init_data(signed(date=NOW - 3600), TOKEN, now=NOW)["id"] == 17
    assert validate_init_data(signed(signature="telegram-signature-field"), TOKEN, now=NOW)["id"] == 17


@pytest.mark.parametrize("raw", ["", "hash=no", signed().replace("Claudio", "Another"), signed() + "&auth_date=1800000000", signed() + "&hash=" + "0" * 64, signed(date=NOW - 3601), signed(date=NOW + 1), "bad=%XX"])
def test_rejects_missing_tampered_duplicate_expired_future_and_bad_encoding(raw):
    with pytest.raises(MusicError) as error:
        validate_init_data(raw, TOKEN, now=NOW)
    assert error.value.status == 401


@pytest.mark.parametrize("user", [{"id": True, "first_name": "User"}, {"id": -1, "first_name": "User"}, {"id": "17", "first_name": "User"}, {"id": 2**52, "first_name": "User"}, {"id": 17}, [], {"id": 17, "first_name": ""}])
def test_user_requires_real_positive_integer_identity(user):
    with pytest.raises(MusicError):
        validate_init_data(signed(user=user), TOKEN, now=NOW)


def test_owner_fallback_never_promotes_an_open_or_multiple_allowlist(monkeypatch):
    monkeypatch.delenv("MUSIC_OWNER_IDS", raising=False)
    for raw in ("", "17,18", "17,17", "*", "17,", "invalid"):
        monkeypatch.setenv("RAFFAELLO_ALLOWED_USERS", raw)
        assert not owner_ids()
    monkeypatch.setenv("RAFFAELLO_ALLOWED_USERS", "17")
    assert is_owner(17) and not is_owner(18) and not is_owner(True)
    monkeypatch.setenv("MUSIC_OWNER_IDS", "")
    assert not owner_ids()  # Explicit empty override remains closed.
    monkeypatch.setenv("MUSIC_OWNER_IDS", "17,18")
    assert owner_ids() == frozenset({17, 18})
    monkeypatch.setenv("MUSIC_OWNER_IDS", "17,invalid")
    assert not owner_ids()
