"""Standalone startup never steals updates; messages use WebApp controls."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from http.server import ThreadingHTTPServer
import json
import threading
from urllib.error import HTTPError
from urllib.request import urlopen
import uuid

import pytest

from bot import db, music_bot, music_main, music_service as service, music_store as store


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", str(tmp_path / "standalone.sqlite"))
    monkeypatch.setenv("MUSIC_OWNER_IDS", "17")
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://studio.example.test")
    monkeypatch.setattr(service, "_notifier", None)
    monkeypatch.setattr(service, "_owner_notifier", None)
    db.init_db()
    store.init()


def test_standalone_lifecycle_no_polling_or_callback_buttons():
    bot = SimpleNamespace(get_me=AsyncMock(return_value=SimpleNamespace(username="ProtocolloRossoBot")),
                          set_chat_menu_button=AsyncMock(), get_updates=AsyncMock(), send_message=AsyncMock())
    app = SimpleNamespace(initialize=AsyncMock(), start=AsyncMock(), stop=AsyncMock(), shutdown=AsyncMock(),
                          updater=SimpleNamespace(start_polling=AsyncMock()), bot=bot)

    async def run():
        stop = asyncio.Event()
        stop.set()
        await music_main.run(application=app, port=0, stop_event=stop)
    asyncio.run(run())
    app.initialize.assert_awaited_once()
    app.start.assert_awaited_once()
    app.stop.assert_awaited_once()
    app.shutdown.assert_awaited_once()
    app.updater.start_polling.assert_not_called()
    bot.get_updates.assert_not_called()
    assert bot.set_chat_menu_button.call_args.kwargs["menu_button"].web_app.url == "https://studio.example.test/studio"
    assert music_bot._integrated_callbacks is False


def test_standalone_preview_starts_without_bot_credentials(monkeypatch):
    monkeypatch.setattr(music_main, "require_token", lambda: (_ for _ in ()).throw(RuntimeError("missing token")))
    monkeypatch.setattr(music_main.Application, "builder", lambda: (_ for _ in ()).throw(AssertionError("Preview must not create Telegram transport")))
    async def run():
        stop = asyncio.Event()
        stop.set()
        await music_main.run(port=0, stop_event=stop)
    asyncio.run(run())
    assert service.config()["capabilities"]["result_delivery"] is False


def test_standalone_notification_and_delivery_link_back_to_authenticated_studio(monkeypatch):
    rid = store.create(17, {"story": "Una canzone per chi ricomincia", "client_id": str(uuid.uuid4())})["id"]
    bot = SimpleNamespace(send_message=AsyncMock(return_value=SimpleNamespace(message_id=789)))
    monkeypatch.setattr(music_bot, "_application", SimpleNamespace(bot=bot))
    monkeypatch.setattr(music_bot, "_integrated_callbacks", False)
    asyncio.run(music_bot.notify_owner(rid))
    assert store.get(17, rid)["owner_notice"]["state"] == "sent"
    assert bot.send_message.call_args.kwargs["chat_id"] == 17
    store.record_result(17, rid, {"title": "Ricominciare", "suno_url": "https://suno.com/song/b4a11739-6a39-4eb8-8572-89942f2771cd", "playback_confirmed": True})
    asyncio.run(music_bot.deliver(rid))
    rows = bot.send_message.call_args.kwargs["reply_markup"].inline_keyboard
    assert any(button.web_app for row in rows for button in row)
    assert not any(button.callback_data for row in rows for button in row)
    assert store.get(17, rid)["delivery"]["state"] == "sent"


def test_standalone_http_does_not_expose_legacy_site_or_network_routes():
    server = ThreadingHTTPServer(("127.0.0.1", 0), music_main.StudioHTTP)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/health") as response:
            assert json.loads(response.read())["update_receiver"] is False
        for path in ("/ask", "/network/v1/nodes", "/raffaello/v1/session"):
            with pytest.raises(HTTPError) as error:
                urlopen(f"http://127.0.0.1:{server.server_port}" + path)
            assert error.value.code == 404
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
