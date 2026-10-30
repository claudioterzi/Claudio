"""Signed API -> SQLite -> encrypted readback -> Telegram acknowledgement -> restore.

The transport is fake; signatures, SQL, encryption, queue transitions and readback are real.
"""
import asyncio
import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import urlencode
import uuid

import pytest

from bot import config, db, music_backup as backup, music_bot, music_http as http, music_service as service, music_store as store
from test_music_backup import FakeBot, SECRET, running

TOKEN = "123456789:synthetic-test-key-no-real-access"


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", str(tmp_path / "api.sqlite"))
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", TOKEN)
    monkeypatch.setenv("MUSIC_OWNER_IDS", "17")
    for name in ("MUSIC_BACKUP_KEY", "MUSIC_BACKUP_REQUIRED", "MUSIC_BACKUP_BOOTSTRAP_EMPTY", "RAFFAELLO_BRIDGE_SECRET"):
        monkeypatch.delenv(name, raising=False)
    for name in ("_manager", "_loop", "_failure"):
        monkeypatch.setattr(backup, name, None)
    monkeypatch.setattr(service, "_notifier", None)
    monkeypatch.setattr(service, "_owner_notifier", None)
    monkeypatch.setattr(music_bot, "_integrated_callbacks", False)
    db.init_db()
    db.add_action(17, "Existing private archive")
    store.init()


def headers(actor):
    values = {"auth_date": str(int(time.time())), "user": json.dumps({"id": actor, "first_name": "Test user"})}
    key = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    check = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
    values["hash"] = hmac.new(key, check.encode(), hashlib.sha256).hexdigest()
    return {"X-Telegram-Init-Data": urlencode(values)}


def test_signed_workflow_ack_is_recoverable_from_real_encrypted_snapshot(monkeypatch):
    bot = FakeBot()
    bot.send_message = AsyncMock(return_value=SimpleNamespace(message_id=999))
    monkeypatch.setattr(music_bot, "_application", SimpleNamespace(bot=bot))
    manager = backup.TelegramMusicBackup(bot, 17, SECRET, required=True, bootstrap_empty=True)
    with running(manager):
        request = http.dispatch("POST", "/requests", headers(23), {"story": "Una canzone sul coraggio di ripartire", "client_id": str(uuid.uuid4())})["request"]
        rid = request["id"]
        assert request["state"] == "requested" and manager.generation >= 2
        asyncio.run_coroutine_threadsafe(music_bot.notify_owner(rid), backup._loop).result(10)
        assert bot.send_message.call_args.kwargs["chat_id"] == 17
        ready = http.dispatch("POST", f"/requests/{rid}/result", headers(17),
                              {"title": "Ripartire", "suno_url": "https://suno.com/song/9a99cacb-3a84-4c69-9f86-a3841eae486f", "playback_confirmed": True})["request"]
        assert ready["state"] == "ready" and ready["delivery"]["state"] == "pending"
        asyncio.run_coroutine_threadsafe(music_bot.deliver(rid), backup._loop).result(10)
        assert bot.send_message.call_args.kwargs["chat_id"] == 23
        kept = http.dispatch("POST", f"/requests/{rid}/keep", headers(17), {})["request"]
        assert kept["state"] == "kept" and kept["delivery"]["message_id"] == 999
        envelope = manager.decrypt(bot.files[bot.pinned.document.file_id])
        assert envelope["tables"]["music_requests"][0]["delivery_state"] == "sent"
        with db.connect() as conn:
            conn.execute("DELETE FROM music_requests")
            conn.execute("DELETE FROM music_quota")
        asyncio.run_coroutine_threadsafe(manager.restore(), backup._loop).result(10)
        restored = http.dispatch("GET", f"/requests/{rid}", headers(23), {})["request"]
        assert restored["state"] == "kept" and restored["owner_notice"]["state"] == "sent"
        assert db.list_actions(17)[0]["description"] == "Existing private archive"


def test_failed_remote_readback_cannot_acknowledge_a_public_submission():
    bot = FakeBot()
    manager = backup.TelegramMusicBackup(bot, 17, SECRET, required=True, bootstrap_empty=True)
    with running(manager):
        bot.fail_stage = "download"
        with pytest.raises(backup.BackupError) as failure:
            http.dispatch("POST", "/requests", headers(23), {"story": "Una nuova canzone", "client_id": str(uuid.uuid4())})
        assert failure.value.status == 503 and not manager.ready
        assert store.list_requests(23) == []
        assert db.list_actions(17)[0]["description"] == "Existing private archive"
