"""No live Telegram, provider, credentials or private database: real isolated SQLite and fake PTB."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import copy
import hashlib
import json
import threading
from types import SimpleNamespace as NS
import uuid

import pytest

from bot import db, music_store as store
from bot import music_backup as backup

OWNER = 17
SECRET = "synthetic-backup-key-no-live-access-" * 2


class FakeBot:
    id = 777

    def __init__(self):
        self.pinned = None
        self.files = {}
        self.events = []
        self.fail_stage = None
        self.collision = False
        self.next_id = 100
        self.wait_send = None
        self.on_download = None

    def message(self, token, *, caption="", sender=777, owner=OWNER, file_name=backup.FILENAME):
        mid = self.next_id
        self.next_id += 1
        fid = "synthetic-file-" + str(mid)
        self.files[fid] = bytes(token)
        return NS(message_id=mid, from_user=NS(id=sender, is_bot=True),
                  chat=NS(id=owner, type="private"), caption=caption,
                  document=NS(file_id=fid, file_name=file_name, file_size=len(token)))

    async def get_chat(self, owner):
        self.events.append("get_chat")
        if self.fail_stage == "get_chat":
            raise OSError("synthetic transport failure")
        return NS(id=owner, type="private", pinned_message=self.pinned)

    async def send_document(self, **kwargs):
        self.events.append("send_document")
        if self.wait_send is not None:
            await self.wait_send.wait()
        if self.fail_stage == "send_document":
            raise OSError("synthetic transport failure")
        return self.message(kwargs["document"].getvalue(), caption=kwargs["caption"],
                            owner=kwargs["chat_id"], file_name=kwargs["filename"])

    async def get_file(self, fid):
        self.events.append("get_file")
        if self.fail_stage == "get_file":
            raise OSError("synthetic transport failure")
        bot = self
        class File:
            file_size = len(bot.files[fid])
            async def download_as_bytearray(self):
                bot.events.append("download")
                if bot.fail_stage == "download":
                    return bytearray(b"corrupted")
                if bot.on_download is not None:
                    bot.on_download()
                return bytearray(bot.files[fid])
        return File()

    async def pin_chat_message(self, owner, mid, **kwargs):
        self.events.append("pin")
        if self.fail_stage == "pin":
            raise OSError("synthetic transport failure")
        fid = "synthetic-file-" + str(mid)
        # Uploaded metadata is rebuilt from the encrypted envelope, like Telegram readback.
        envelope = backup.TelegramMusicBackup(self, OWNER, SECRET).decrypt(self.files[fid])
        self.pinned = NS(message_id=mid, from_user=NS(id=self.id, is_bot=True),
                         chat=NS(id=owner, type="private"), caption=backup.TelegramMusicBackup.caption(envelope),
                         document=NS(file_id=fid, file_name=backup.FILENAME, file_size=len(self.files[fid])))
        if self.collision:
            self.pinned.message_id = mid + 1


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATABASE_PATH", str(tmp_path / "music.sqlite"))
    monkeypatch.setenv("MUSIC_OWNER_IDS", str(OWNER))
    for name in ("MUSIC_BACKUP_KEY", "MUSIC_BACKUP_REQUIRED", "MUSIC_BACKUP_BOOTSTRAP_EMPTY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(backup, "_manager", None)
    monkeypatch.setattr(backup, "_loop", None)
    monkeypatch.setattr(backup, "_failure", None)
    db.init_db()
    db.add_action(OWNER, "Private legacy action excluded from music export")
    store.init()


def create(actor=23):
    return store.create(actor, {"story": "Una canzone di prova", "genre": "ballata", "mood": "speranza",
                                "language": "it", "client_id": str(uuid.uuid4()), "personal_voice": False})


def manager(bot=None, **kwargs):
    return backup.TelegramMusicBackup(bot or FakeBot(), OWNER, SECRET, **kwargs)


@contextmanager
def running(manager):
    loop = asyncio.new_event_loop()
    started = threading.Event()
    def run():
        asyncio.set_event_loop(loop)
        started.set()
        loop.run_forever()
    thread = threading.Thread(target=run)
    thread.start()
    started.wait(3)
    backup._manager, backup._loop = manager, loop
    try:
        asyncio.run_coroutine_threadsafe(manager.restore(), loop).result(5)
        yield manager
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join(5)
        loop.close()
        backup._manager, backup._loop = None, None


def test_selective_roundtrip_keeps_legacy_and_quota():
    request = create()
    with db.connect() as conn:
        conn.execute("INSERT INTO music_generation_quota VALUES (?,?,?)", (OWNER, 123, 2))
    snapshot = backup.export_snapshot(OWNER)
    assert set(snapshot) == set(backup.TABLE_COLUMNS)
    assert "Private legacy" not in json.dumps(snapshot)
    with db.connect() as conn:
        conn.execute("DELETE FROM music_requests")
    backup.import_snapshot(snapshot, OWNER)
    assert store.internal(request["id"])["story"] == request["story"]
    assert backup.export_snapshot(OWNER) == snapshot
    assert db.list_actions(OWNER)[0]["description"].startswith("Private legacy")


@pytest.mark.parametrize("tamper", [
    lambda s: s.update(actions=[]),
    lambda s: s["music_requests"][0].update(requester=True),
    lambda s: s["music_requests"][0].update(unexpected="field"),
    lambda s: s["music_requests"][0].update(delivery_state="invented"),
    lambda s: s["music_requests"][0].update(personal_voice=1),
    lambda s: s["music_requests"][0].update(personal_voice_confirmed=1),
    lambda s: s["music_requests"][0].update(state="ready"),
    lambda s: s["music_requests"][0].update(delivery_state="sent"),
    lambda s: s["music_requests"].append(copy.deepcopy(s["music_requests"][0])),
])
def test_invalid_snapshot_never_clears_database(tamper):
    create()
    before = backup.export_snapshot(OWNER)
    candidate = copy.deepcopy(before)
    tamper(candidate)
    with pytest.raises(backup.BackupError):
        backup.import_snapshot(candidate, OWNER)
    assert backup.export_snapshot(OWNER) == before
    assert len(db.list_actions(OWNER)) == 1


def test_fernet_hash_owner_schema_types_and_wrong_key():
    create()
    m = manager()
    snapshot = backup.export_snapshot(OWNER)
    envelope = m.envelope(snapshot, 1)
    token = m.encrypt(envelope)
    assert m.decrypt(token) == envelope
    assert b"Una canzone" not in token
    cases = [
        envelope | {"owner_id": 18},
        envelope | {"owner_id": True},
        envelope | {"generation": True},
        envelope | {"version": True},
        envelope | {"snapshot_sha256": "0" * 64},
        envelope | {"unexpected": "field"},
    ]
    for altered in cases:
        with pytest.raises(backup.BackupError):
            m.decrypt(m.encrypt(altered))
    with pytest.raises(backup.BackupError):
        backup.TelegramMusicBackup(FakeBot(), OWNER, SECRET + "different").decrypt(token)
    duplicate = backup._json(envelope).replace(b'"version":1', b'"version":1,"version":1')
    with pytest.raises(backup.BackupError):
        m.decrypt(m._cipher.encrypt(duplicate))


def test_size_caps_apply_to_ciphertext_and_plaintext():
    m = manager(max_bytes=400)
    envelope = m.envelope(backup.export_snapshot(OWNER), 1)
    with pytest.raises(backup.BackupError) as error:
        m.encrypt(envelope)
    assert error.value.code == "backup_oversize"
    with pytest.raises(backup.BackupError):
        m.decrypt(b"x" * 401)
    large = m._cipher.encrypt(b"x" * 401)
    with pytest.raises(backup.BackupError):
        m.decrypt(large)
    with pytest.raises(backup.BackupError):
        manager(max_bytes=backup.MAX_BYTES + 1)


def test_upload_readback_pin_and_restart_restore():
    m = manager(bootstrap_empty=True, required=True)
    asyncio.run(m.restore())
    assert m.bot.events == ["get_chat", "get_chat", "send_document", "get_file", "download", "get_chat", "pin", "get_chat"]
    assert m.ready and m.generation == 1 and not m.bootstrap_empty
    request = create()
    snapshot = backup.export_snapshot(OWNER)
    asyncio.run(m.persist(snapshot))
    assert m.generation == 2
    with db.connect() as conn:
        conn.execute("DELETE FROM music_requests")
        conn.execute("DELETE FROM music_quota")
    fresh = manager(m.bot, required=True)
    assert asyncio.run(fresh.restore()) == {"restored": True, "bootstrapped_empty": False, "generation": 2}
    assert fresh.ready
    assert store.internal(request["id"])["story"] == request["story"]
    assert len(db.list_actions(OWNER)) == 1


@pytest.mark.parametrize("stage", ["send_document", "get_file", "download", "pin"])
def test_transport_failure_never_marks_backup_ready(stage):
    bot = FakeBot()
    bot.fail_stage = stage
    m = manager(bot, bootstrap_empty=True)
    with pytest.raises(backup.BackupError):
        asyncio.run(m.restore())
    assert not m.ready and m.generation == 0


def test_pin_collision_after_upload_fails_closed():
    bot = FakeBot()
    bot.collision = True
    m = manager(bot, bootstrap_empty=True)
    with pytest.raises(backup.BackupError):
        asyncio.run(m.restore())
    assert not m.ready


def test_foreign_pin_during_upload_is_not_overwritten():
    m = manager(bootstrap_empty=True)
    asyncio.run(m.restore())
    old_pin_calls = m.bot.events.count("pin")
    foreign = m.bot.message(b"private-owner-document", caption="different namespace", sender=OWNER)
    m.bot.on_download = lambda: setattr(m.bot, "pinned", foreign)
    with pytest.raises(backup.BackupError) as error:
        asyncio.run(m.persist(backup.export_snapshot(OWNER)))
    assert error.value.code == "backup_pointer_collision"
    assert m.bot.pinned is foreign
    assert m.bot.events.count("pin") == old_pin_calls
    assert not m.ready


@pytest.mark.parametrize("foreign", ["sender", "owner", "filename", "caption", "document", "corrupt"])
def test_foreign_or_corrupt_pin_never_bootstraps_or_changes_rows(foreign):
    create()
    before = backup.export_snapshot(OWNER)
    m = manager(bootstrap_empty=True, required=True)
    envelope = m.envelope(before, 1)
    token = m.encrypt(envelope)
    message = m.bot.message(token, caption=m.caption(envelope))
    if foreign == "sender":
        message.from_user.id = 123
    elif foreign == "owner":
        message.chat.id = 18
    elif foreign == "filename":
        message.document.file_name = "different.json"
    elif foreign == "caption":
        message.caption = "not a music backup"
    elif foreign == "document":
        message.document = None
    else:
        m.bot.files[message.document.file_id] = b"invalid"
    m.bot.pinned = message
    with pytest.raises(backup.BackupError):
        asyncio.run(m.restore())
    assert backup.export_snapshot(OWNER) == before
    assert "send_document" not in m.bot.events
    assert not m.ready


def test_missing_pin_requires_explicit_empty_bootstrap_and_flag_is_consumed():
    m = manager(required=True)
    with pytest.raises(backup.BackupError) as error:
        asyncio.run(m.restore())
    assert error.value.code == "backup_missing"
    create()
    bootstrap = manager(bootstrap_empty=True)
    with pytest.raises(backup.BackupError):
        asyncio.run(bootstrap.restore())
    assert not bootstrap.bootstrap_empty
    assert "send_document" not in bootstrap.bot.events


def test_config_is_optional_and_requires_exactly_one_owner_and_independent_key(monkeypatch):
    assert backup.from_environment(FakeBot()) is None
    assert backup.status()["ready"]
    monkeypatch.setenv("MUSIC_BACKUP_REQUIRED", "1")
    with pytest.raises(backup.BackupError):
        backup.from_environment(FakeBot())
    monkeypatch.setenv("MUSIC_BACKUP_KEY", "too-short")
    with pytest.raises(backup.BackupError):
        backup.from_environment(FakeBot())
    monkeypatch.setenv("MUSIC_BACKUP_KEY", SECRET)
    monkeypatch.setenv("MUSIC_OWNER_IDS", "17,18")
    with pytest.raises(backup.BackupError):
        backup.from_environment(FakeBot())
    monkeypatch.setenv("MUSIC_OWNER_IDS", str(OWNER))
    one = backup.from_environment(FakeBot())
    monkeypatch.setenv("BOT_TOKEN", "rotated-synthetic-token")
    two = backup.from_environment(FakeBot())
    token = one.encrypt(one.envelope(backup.export_snapshot(OWNER), 1))
    assert two.decrypt(token)["owner_id"] == OWNER


def test_mutation_ack_waits_for_remote_backup_and_failure_restores_only_music():
    m = manager(bootstrap_empty=True)
    with running(m):
        request = backup.mutate(create)
        assert m.generation == 2
        before = backup.export_snapshot(OWNER)
        m.bot.fail_stage = "send_document"
        with pytest.raises(backup.BackupError):
            backup.mutate(create)
        assert backup.export_snapshot(OWNER) == before
        assert store.internal(request["id"])["story"] == request["story"]
        assert len(db.list_actions(OWNER)) == 1
        assert not m.ready
        with pytest.raises(backup.BackupError):
            backup.mutate(create)


def test_already_observed_external_effect_is_not_rolled_back():
    m = manager(bootstrap_empty=True)
    with running(m):
        m.bot.fail_stage = "send_document"
        with pytest.raises(backup.BackupError):
            backup.mutate(create, rollback_on_failure=False)
        assert len(backup.export_snapshot(OWNER)["music_requests"]) == 1
        # An external ACK can still be recorded locally after readiness closes.
        with pytest.raises(backup.BackupError):
            backup.mutate(create, rollback_on_failure=False)
        assert len(backup.export_snapshot(OWNER)["music_requests"]) == 2
        assert not m.ready


def test_concurrent_writes_have_ordered_snapshots_and_no_redundant_backup_for_reads():
    m = manager(bootstrap_empty=True)
    with running(m):
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda actor: backup.mutate(create, actor), range(23, 29)))
        assert len({row["id"] for row in results}) == 6
        assert m.generation == 7
        _, remote = asyncio.run_coroutine_threadsafe(m._download(m.bot.pinned), backup._loop).result(5)
        assert remote["tables"] == backup.export_snapshot(OWNER)
        previous = m.generation
        assert backup.mutate(store.internal, results[0]["id"])["id"] == results[0]["id"]
        assert m.generation == previous


def test_mutation_on_bot_loop_is_rejected_before_sql():
    async def scenario():
        m = manager(bootstrap_empty=True)
        await m.restore()
        backup._manager, backup._loop = m, asyncio.get_running_loop()
        with pytest.raises(backup.BackupError) as error:
            backup.mutate(create)
        assert error.value.code == "backup_worker_thread_required"
        assert not backup.export_snapshot(OWNER)["music_requests"]
    asyncio.run(scenario())


def test_invalid_local_snapshot_closes_readiness_before_callback():
    m = manager(bootstrap_empty=True)
    called = []
    with running(m):
        with db.connect() as conn:
            conn.execute("ALTER TABLE music_quota ADD COLUMN unexpected TEXT")
        with pytest.raises(backup.BackupError) as error:
            backup.mutate(lambda: called.append(True))
        assert error.value.code == "backup_local_snapshot_invalid"
        assert not called and not m.ready


def test_external_ack_is_preserved_even_if_initial_snapshot_is_invalid():
    m = manager(bootstrap_empty=True)
    called = []
    with running(m):
        with db.connect() as conn:
            conn.execute("ALTER TABLE music_quota ADD COLUMN unexpected TEXT")
        with pytest.raises(backup.BackupError):
            backup.mutate(lambda: called.append("external_accepted"), rollback_on_failure=False)
        assert called == ["external_accepted"] and not m.ready


def test_cancellation_and_external_invalidation_cannot_reopen_readiness():
    async def scenario():
        m = manager(bootstrap_empty=True)
        await m.restore()
        m.bot.wait_send = asyncio.Event()
        task = asyncio.create_task(m.persist(backup.export_snapshot(OWNER)))
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not m.ready and m.reason == "backup_cancelled"
        await m.restore()
        m.bot.wait_send = asyncio.Event()
        late = asyncio.create_task(m.persist(backup.export_snapshot(OWNER)))
        await asyncio.sleep(0)
        m.fail("backup_timeout")
        m.bot.wait_send.set()
        with pytest.raises(backup.BackupError):
            await late
        assert not m.ready
    asyncio.run(scenario())
