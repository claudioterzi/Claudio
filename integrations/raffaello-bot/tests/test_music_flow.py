"""Persistent queue, race falsifiers, real HTTP and real bot-loop delivery boundary."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import hmac
import json
import threading
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import uuid
from http.server import ThreadingHTTPServer

import pytest

from bot import config, db, main, music_bot, music_http as http, music_service as service, music_store as store, raffaello
from bot.music_auth import MusicError

TOKEN = "123456789:synthetic-test-key-no-real-access"
SONG = "https://suno.com/song/9a99cacb-3a84-4c69-9f86-a3841eae486f"


@pytest.fixture(autouse=True)
def database(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", TOKEN)
    monkeypatch.setenv("MUSIC_OWNER_IDS", "17")
    monkeypatch.delenv("RAFFAELLO_BRIDGE_SECRET", raising=False)
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    monkeypatch.delenv("MUSIC_PUBLIC_URL", raising=False)
    monkeypatch.setattr(service, "_notifier", None)
    monkeypatch.setattr(service, "_owner_notifier", None)
    monkeypatch.setattr(service, "_bot_username", "")
    monkeypatch.setattr(service.engine, "call_site", lambda _: (_ for _ in ()).throw(AssertionError("Live inference forbidden in tests")))
    db.init_db()
    db.add_action(17, "Existing personal record")
    store.init()


def body(**extra):
    return {"story": "Una canzone per ritrovare il coraggio e ripartire.", "genre": "ballata", "mood": "speranza", "language": "it", "client_id": str(uuid.uuid4()), **extra}


def result(**extra):
    return {"title": "Il coraggio", "suno_url": SONG, "playback_confirmed": True, **extra}


def headers(actor=23):
    data = {"auth_date": str(int(time.time())), "user": json.dumps({"id": actor, "first_name": "Viewer"}, separators=(",", ":"))}
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    check = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))
    data["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return {"X-Telegram-Init-Data": urlencode(data)}


def test_restart_preserves_queue_and_old_personal_archive():
    request = store.create(23, body())
    store.init()
    assert store.get(23, request["id"])["story"] == request["story"]
    assert db.list_actions(17)[0]["description"] == "Existing personal record"
    assert len(store.list_requests(17)) == 1
    assert not store.list_requests(24)
    with pytest.raises(MusicError) as error:
        store.get(24, request["id"])
    assert error.value.status == 404


def test_atomic_idempotency_and_quota_do_not_charge_duplicate_submissions():
    payload = body()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: store.create(23, payload), range(8)))
    assert len({item["id"] for item in results}) == 1
    with pytest.raises(MusicError) as conflict:
        store.create(23, payload | {"story": "Different story"})
    assert conflict.value.status == 409
    store.create(23, body())
    store.create(23, body())
    with pytest.raises(MusicError) as quota:
        store.create(23, body())
    assert quota.value.status == 429
    assert len(store.list_requests(23)) == 3


def test_personal_voice_and_authority_are_not_client_fields():
    with pytest.raises(MusicError) as forbidden:
        store.create(23, body(personal_voice=True))
    assert forbidden.value.status == 403
    assert store.create(17, body(personal_voice=True))["personal_voice"] is True
    with pytest.raises(MusicError):
        store.create(23, body(owner=17))
    with pytest.raises(MusicError):
        store.create(23, body(story="x" * 1801))


def test_prepare_claim_race_restart_recovery_and_late_worker_cannot_overwrite():
    rid = store.create(23, body())["id"]
    with ThreadPoolExecutor(max_workers=8) as pool:
        claims = list(pool.map(lambda _: store.claim_prepare(17, rid), range(8)))
    claim = next(value for value in claims if value)
    assert sum(value is not None for value in claims) == 1
    with db.connect() as conn:
        conn.execute("UPDATE music_requests SET lock_until=0 WHERE id=?", (rid,))
    store.recover_expired()
    assert store.get(23, rid)["state"] == "error"
    next_claim = store.claim_prepare(17, rid)
    store.finish_prepare(rid, claim, "Old stale lyrics", "old")
    assert store.get(23, rid)["state"] == "writing"
    store.finish_prepare(rid, next_claim, "[Strofa]\nLyrics from the current worker", "Acoustic ballad")
    assert store.get(23, rid)["state"] == "awaiting_suno"


def test_discard_is_soft_and_cancels_late_preparation():
    rid = store.create(23, body())["id"]
    claim = store.claim_prepare(17, rid)
    with pytest.raises(MusicError):
        store.decide(23, rid, False)
    store.decide(17, rid, False)
    store.finish_prepare(rid, claim, "[Strofa]\nLate generated lyrics", "Pop")
    discarded = store.get(23, rid)
    assert discarded["state"] == "discarded" and discarded["story"] and not discarded["lyrics"]


@pytest.mark.parametrize("url", ["http://suno.com/song/" + str(uuid.uuid4()), "https://evil.invalid/song/" + str(uuid.uuid4()), "https://suno.com.evil.invalid/song/" + str(uuid.uuid4()), "https://user:secret@suno.com/song/" + str(uuid.uuid4()), SONG + "?token=private", SONG + "#fragment", "https://suno.com/song/not-a-uuid", "https://suno.com:443/song/" + str(uuid.uuid4())])
def test_result_url_is_strict_metadata_never_an_arbitrary_fetch(url):
    rid = store.create(23, body())["id"]
    with pytest.raises(MusicError):
        store.record_result(17, rid, result(suno_url=url))
    assert store.get(23, rid)["state"] == "requested"


def test_ready_requires_owner_attributed_playback_not_ai_or_provider_claim():
    rid = store.create(23, body())["id"]
    with pytest.raises(MusicError):
        store.record_result(23, rid, result())
    with pytest.raises(MusicError):
        store.record_result(17, rid, result(playback_confirmed=False))
    ready = store.record_result(17, rid, result())
    assert ready["state"] == "ready" and ready["verification"] == "owner_playback_confirmation"
    assert ready["verified_by"] == 17 and ready["delivery"]["state"] == "pending"
    assert ready["lyrics"] == "" and "audio_url" not in ready
    assert store.record_result(17, rid, result())["id"] == rid
    assert len(store.list_requests(23, library=True)) == 1
    store.decide(17, rid, True)
    assert store.get(23, rid)["state"] == "kept"


def test_voice_request_requires_separate_attributed_sample_confirmation():
    rid = store.create(17, body(personal_voice=True))["id"]
    with pytest.raises(MusicError) as unconfirmed:
        store.record_result(17, rid, result())
    assert unconfirmed.value.code == "personal_voice_confirmation_required"
    ready = store.record_result(17, rid, result(personal_voice_confirmed=True))
    assert ready["personal_voice_confirmed"] is True
    assert ready["voice_sample_label"] == "My Voice - Apr 30"
    assert ready["voice_verification"] == "owner_sample_confirmation"
    assert ready["verified_by"] == 17


def test_generation_reuses_canonical_callback_and_excludes_fake_offline_answers(monkeypatch):
    request = store.create(23, body())
    with pytest.raises(MusicError) as unavailable:
        service.start_prepare(17, request["id"])
    assert unavailable.value.status == 503 and store.get(23, request["id"])["state"] == "requested"
    captured = []
    monkeypatch.setattr(service.engine, "call_site", lambda payload: captured.append(payload) or {"risposta": "[Strofa 1]\nIl coraggio ritorna e la luce ci trova.\nSTILE SUNO: acoustic ballad"})
    generated = service.generate_lyrics(request)
    assert generated["stile_suno"] == "acoustic ballad"
    assert captured[0]["cronologia"] == [] and captured[0]["lettura"] is None
    assert request["story"] in captured[0]["domanda"]


def test_public_create_never_spends_provider_calls_even_when_bridge_is_configured(monkeypatch):
    monkeypatch.setenv("RAFFAELLO_BRIDGE_SECRET", "test-only-bridge-" * 3)
    notified = []
    monkeypatch.setattr(service, "_owner_notifier", lambda rid: notified.append(rid))
    request = service.create_request(23, body())
    assert request["state"] == "requested" and not request["lyrics"]
    assert notified == [request["id"]]
    with pytest.raises(MusicError) as error:
        service.start_prepare(23, request["id"])
    assert error.value.status == 403


@pytest.mark.parametrize("lyrics,expected", [("The provider is temporarily unavailable. Please try again.", "error"), ("[Strofa 1]\nLa luce ritorna e ci prende per mano.\n[Ritornello]\nRipartire, ripartire insieme.", "awaiting_suno")])
def test_owner_worker_checks_structured_lyrics_before_promoting_preparation(monkeypatch, lyrics, expected):
    monkeypatch.setenv("RAFFAELLO_BRIDGE_SECRET", "test-only-bridge-" * 3)
    monkeypatch.setattr(service, "generate_lyrics", lambda _: {"testo": lyrics, "stile_suno": "Acoustic ballad"})
    monkeypatch.setattr(service._pool, "submit", lambda fn, *args: fn(*args))
    rid = store.create(23, body())["id"]
    service.start_prepare(17, rid)
    prepared = store.get(23, rid)
    assert prepared["state"] == expected
    assert bool(prepared["lyrics"]) is (expected == "awaiting_suno")


@pytest.fixture
def server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), main._Health)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    yield "http://127.0.0.1:" + str(server.server_port)
    server.shutdown()
    server.server_close()
    worker.join(timeout=2)


def call(server, path, method="GET", payload=None, auth=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(server + path, data=data, method=method, headers={"Content-Type": "application/json", **(auth or {})})
    try:
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read()), response.headers
    except HTTPError as response:
        return response.code, json.loads(response.read()), response.headers


def test_real_http_signed_request_isolation_owner_control_and_public_config(server):
    status, config_json, _ = call(server, "/studio/config")
    assert status == 200 and config_json["generation_mode"] == "assisted"
    assert not config_json["capabilities"]["audio_generation"]
    status, _, _ = call(server, "/music/v1/requests")
    assert status == 401
    status, response, response_headers = call(server, "/music/v1/requests", "POST", body(), headers(23))
    assert status == 200 and response_headers["Cache-Control"] == "no-store"
    rid = response["request"]["id"]
    assert call(server, "/music/v1/requests/" + rid, auth=headers(24))[0] == 404
    assert call(server, "/music/v1/requests/" + rid, auth=headers(23))[1]["request"]["state"] == "requested"
    assert call(server, "/music/v1/requests/" + rid + "/result", "POST", result(), headers(23))[0] == 403
    assert call(server, "/music/v1/requests/" + rid + "/prepare", "POST", {}, headers(23))[0] == 403
    assert call(server, "/music/v1/requests/" + rid + "/result", "POST", result(), headers(17))[1]["request"]["state"] == "ready"
    assert call(server, "/music/v1/session", auth=headers(17))[1]["viewer"]["is_owner"] is True
    assert call(server, "/music/v1/library", auth=headers(24))[1]["songs"] == []
    assert call(server, "/music/v1/requests", "POST", [], headers(23))[0] == 400
    assert call(server, "/music/v1/requests/" + rid + "/keep", "POST", {}, headers(23))[0] == 403
    assert call(server, "/music/v1/requests/" + rid + "/keep", "POST", {}, headers(17))[1]["request"]["state"] == "kept"


def test_static_allowlist_cannot_traverse_filesystem():
    for path in ("/studio/../../bot/config.py", "/studio/%2e%2e/config.py", "/studio/config.py"):
        with pytest.raises(MusicError) as error:
            http.static_asset(path)
        assert error.value.status == 404


def test_bot_delivery_records_acknowledgement_only_once():
    rid = store.create(23, body())["id"]
    store.record_result(17, rid, result())
    bot = SimpleNamespace(send_message=AsyncMock(return_value=SimpleNamespace(message_id=456)))
    music_bot._application = SimpleNamespace(bot=bot)

    async def deliver_race():
        await asyncio.gather(music_bot.deliver(rid), music_bot.deliver(rid))
    asyncio.run(deliver_race())
    assert bot.send_message.await_count == 1
    assert bot.send_message.call_args.kwargs["chat_id"] == 23
    delivered = store.get(23, rid)["delivery"]
    assert delivered["state"] == "sent" and delivered["message_id"] == 456


def test_interrupted_delivery_is_uncertain_not_a_false_unsent_claim():
    rid = store.create(23, body())["id"]
    store.record_result(17, rid, result())
    claim = store.claim_delivery(rid)
    with db.connect() as conn:
        conn.execute("UPDATE music_requests SET delivery_until=0 WHERE id=?", (rid,))
    store.recover_expired()
    assert store.get(23, rid)["delivery"]["state"] == "uncertain"
    assert claim is not None


def test_public_studio_start_preserves_existing_personal_start(monkeypatch):
    personal = AsyncMock()
    studio = AsyncMock()
    monkeypatch.setattr(raffaello, "start", personal)
    monkeypatch.setattr(music_bot, "studio", studio)
    update = SimpleNamespace()
    context = SimpleNamespace(args=[])
    asyncio.run(music_bot.start(update, context))
    personal.assert_awaited_once_with(update, context)
    asyncio.run(music_bot.start(update, SimpleNamespace(args=["studio"])))
    studio.assert_awaited_once()
