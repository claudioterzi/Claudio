"""Optional selective Telegram backup. A pin collision stops writes; Telegram is not a database."""
from __future__ import annotations

import asyncio
import base64
from concurrent.futures import TimeoutError as FutureTimeout
import hashlib
import hmac
from io import BytesIO
import json
import os
import re
import threading
import time
import uuid

from cryptography.fernet import Fernet, InvalidToken
from bot import db
from bot.music_auth import MusicError, owner_ids

SCHEMA = "RAFFAELLO_MUSIC_BACKUP_V1"
FILENAME = "raffaello-music-backup-v1.fernet"
MAX_BYTES = 4 * 1024 * 1024
TABLE_COLUMNS = {
    "music_requests": tuple(("id requester client_id fingerprint story genre mood language personal_voice "
        "state title lyrics style_prompt suno_url playback_confirmed verified_by verified_at created updated "
        "error_code claim_id lock_until attempts delivery_state delivery_claim delivery_until message_id "
        "delivered_at owner_notice_state owner_notice_claim owner_notice_until personal_voice_confirmed").split()),
    "music_quota": ("requester", "period", "calls"),
    "music_generation_quota": ("owner", "period", "calls"),
}
INT_COLUMNS = frozenset(("requester owner period calls personal_voice playback_confirmed verified_by "
    "verified_at created updated lock_until attempts delivery_until message_id delivered_at "
    "owner_notice_until personal_voice_confirmed").split())
NULLABLE = frozenset(("verified_by verified_at claim_id delivery_claim message_id delivered_at "
    "owner_notice_claim").split())
STATES = {"requested", "writing", "awaiting_suno", "ready", "kept", "discarded", "error"}
DELIVERY = {"none", "pending", "sending", "sent", "error", "uncertain"}
NOTICES = {"pending", "sending", "sent", "error", "uncertain"}
LIMITS = {"story": 1800, "genre": 80, "mood": 80, "language": 24, "title": 140,
          "lyrics": 7000, "style_prompt": 1000, "suno_url": 160, "error_code": 128}
_lock = threading.RLock()
_manager = None
_loop = None
_failure = None


class BackupError(MusicError):
    def __init__(self, code="backup_unavailable"):
        super().__init__("Il salvataggio dello Studio non è verificato. Riprova dopo il ripristino.", 503, code)


def _integer(value, positive=False):
    return type(value) is int and (value > 0 if positive else value >= 0) and value < 2**52


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def snapshot_hash(snapshot):
    return hashlib.sha256(_json(snapshot)).hexdigest()


def _uuid(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = uuid.UUID(value)
        return bool(parsed.int) and str(parsed) == value
    except ValueError:
        return False


def validate_snapshot(snapshot, owner_id):
    if not _integer(owner_id, True) or not isinstance(snapshot, dict) or set(snapshot) != set(TABLE_COLUMNS):
        raise BackupError("backup_schema_invalid")
    for table, columns in TABLE_COLUMNS.items():
        rows = snapshot[table]
        if not isinstance(rows, list) or len(rows) > 10000:
            raise BackupError("backup_schema_invalid")
        seen = set()
        clients = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != set(columns):
                raise BackupError("backup_schema_invalid")
            for column, value in row.items():
                if value is None and column in NULLABLE:
                    continue
                if column in INT_COLUMNS:
                    if not _integer(value):
                        raise BackupError("backup_schema_invalid")
                elif not isinstance(value, str) or len(value) > LIMITS.get(column, 128) or any(
                        ord(char) < 32 and char not in "\n\t" for char in value):
                    raise BackupError("backup_schema_invalid")
            actor = row.get("requester", row.get("owner"))
            if not _integer(actor, True) or (table == "music_generation_quota" and actor != owner_id):
                raise BackupError("backup_owner_invalid")
            key = row["id"] if table == "music_requests" else (actor, row["period"])
            if key in seen:
                raise BackupError("backup_schema_invalid")
            seen.add(key)
            if table != "music_requests":
                continue
            if not _uuid(row["id"]) or not _uuid(row["client_id"]) or not re.fullmatch("[0-9a-f]{64}", row["fingerprint"]):
                raise BackupError("backup_schema_invalid")
            client = (actor, row["client_id"])
            if client in clients:
                raise BackupError("backup_schema_invalid")
            clients.add(client)
            for column in ("claim_id", "delivery_claim", "owner_notice_claim"):
                if row[column] is not None and not _uuid(row[column]):
                    raise BackupError("backup_schema_invalid")
            if (row["state"] not in STATES or row["delivery_state"] not in DELIVERY
                    or row["owner_notice_state"] not in NOTICES):
                raise BackupError("backup_schema_invalid")
            if any(row[name] not in (0, 1) for name in ("personal_voice", "playback_confirmed", "personal_voice_confirmed")):
                raise BackupError("backup_schema_invalid")
            if row["verified_by"] is not None and row["verified_by"] != owner_id:
                raise BackupError("backup_owner_invalid")
            if row["personal_voice"] and actor != owner_id:
                raise BackupError("backup_owner_invalid")
            if row["personal_voice_confirmed"] and not row["personal_voice"]:
                raise BackupError("backup_schema_invalid")
            if row["message_id"] is not None and not _integer(row["message_id"], True):
                raise BackupError("backup_schema_invalid")
            if row["suno_url"] and not re.fullmatch(
                    r"https://suno\.com/song/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", row["suno_url"]):
                raise BackupError("backup_schema_invalid")
            if row["state"] in {"ready", "kept"} and (
                    row["playback_confirmed"] != 1 or row["verified_by"] != owner_id
                    or not _integer(row["verified_at"], True) or not row["suno_url"] or not row["title"]
                    or (row["personal_voice"] and row["personal_voice_confirmed"] != 1)):
                raise BackupError("backup_result_unverified")
            if row["delivery_state"] == "sent" and (
                    not _integer(row["message_id"], True) or not _integer(row["delivered_at"], True)):
                raise BackupError("backup_delivery_invalid")
    if len(_json(snapshot)) > MAX_BYTES:
        raise BackupError("backup_oversize")
    return snapshot


def _local_schema(conn):
    for table, columns in TABLE_COLUMNS.items():
        actual = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        if actual != set(columns):
            raise BackupError("backup_local_schema_mismatch")


def export_snapshot(owner_id):
    with db.connect() as conn:
        conn.execute("BEGIN")
        _local_schema(conn)
        result = {}
        for table, columns in TABLE_COLUMNS.items():
            order = "id" if table == "music_requests" else ",".join(columns[:2])
            result[table] = [dict(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY {order}")]
    return validate_snapshot(result, owner_id)


def import_snapshot(snapshot, owner_id):
    """Only constant table/column identifiers enter SQL; payload values are bound."""
    validate_snapshot(snapshot, owner_id)
    try:
        with db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            _local_schema(conn)
            for table, columns in TABLE_COLUMNS.items():
                conn.execute(f"DELETE FROM {table}")
                placeholders = ",".join("?" for _ in columns)
                conn.executemany(
                    f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                    [tuple(row[column] for column in columns) for row in snapshot[table]],
                )
    except BackupError:
        raise
    except Exception:
        raise BackupError("backup_import_failed") from None


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise BackupError("backup_schema_invalid")
        value[key] = item
    return value


class TelegramMusicBackup:
    def __init__(self, bot, owner_id, secret, *, required=False, bootstrap_empty=False, max_bytes=MAX_BYTES):
        if not _integer(owner_id, True) or not isinstance(secret, str) or len(secret) < 32:
            raise BackupError("backup_config_invalid")
        if type(max_bytes) is not int or not 0 < max_bytes <= MAX_BYTES:
            raise BackupError("backup_config_invalid")
        self.bot, self.owner_id = bot, owner_id
        self.required, self.bootstrap_empty, self.max_bytes = required, bootstrap_empty, max_bytes
        self._cipher = Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest()))
        self._io_lock = asyncio.Lock()
        self._state_lock = threading.Lock()
        self._epoch = 0
        self.ready, self.reason, self.generation, self.message_id = False, "backup_not_restored", 0, None

    def fail(self, reason):
        with self._state_lock:
            self._epoch += 1
            self.ready, self.reason = False, reason

    def envelope(self, snapshot, generation):
        validate_snapshot(snapshot, self.owner_id)
        if not _integer(generation, True):
            raise BackupError("backup_schema_invalid")
        return {"schema": SCHEMA, "version": 1, "owner_id": self.owner_id,
                "generation": generation, "created_at": int(time.time()),
                "snapshot_sha256": snapshot_hash(snapshot), "tables": snapshot}

    def encrypt(self, envelope):
        plain = _json(envelope)
        if len(plain) > self.max_bytes:
            raise BackupError("backup_oversize")
        token = self._cipher.encrypt(plain)
        if len(token) > self.max_bytes:
            raise BackupError("backup_oversize")
        return token

    def decrypt(self, token):
        if not isinstance(token, (bytes, bytearray)) or not 0 < len(token) <= self.max_bytes:
            raise BackupError("backup_oversize")
        try:
            plain = self._cipher.decrypt(bytes(token))
            if len(plain) > self.max_bytes:
                raise BackupError("backup_oversize")
            value = json.loads(plain, object_pairs_hook=_unique)
        except (InvalidToken, ValueError, TypeError, UnicodeError):
            raise BackupError("backup_corrupt") from None
        if not isinstance(value, dict) or set(value) != {
                "schema", "version", "owner_id", "generation", "created_at", "snapshot_sha256", "tables"}:
            raise BackupError("backup_schema_invalid")
        if value["schema"] != SCHEMA or type(value["version"]) is not int or value["version"] != 1:
            raise BackupError("backup_schema_invalid")
        if type(value["owner_id"]) is not int or value["owner_id"] != self.owner_id:
            raise BackupError("backup_owner_invalid")
        if not _integer(value["generation"], True) or not _integer(value["created_at"], True):
            raise BackupError("backup_schema_invalid")
        validate_snapshot(value["tables"], self.owner_id)
        digest = value["snapshot_sha256"]
        if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest) or not hmac.compare_digest(
                digest, snapshot_hash(value["tables"])):
            raise BackupError("backup_hash_mismatch")
        return value

    @staticmethod
    def caption(envelope):
        return (f"{SCHEMA} owner={envelope['owner_id']} generation={envelope['generation']} "
                f"sha256={envelope['snapshot_sha256']}")

    async def _chat(self):
        chat = await self.bot.get_chat(self.owner_id)
        if getattr(chat, "id", None) != self.owner_id or getattr(chat, "type", None) != "private":
            raise BackupError("backup_owner_invalid")
        return chat

    def _message(self, message):
        document = getattr(message, "document", None)
        sender = getattr(message, "from_user", None)
        chat = getattr(message, "chat", None)
        if (not message or not document or getattr(sender, "id", None) != self.bot.id
                or getattr(sender, "is_bot", None) is not True
                or getattr(chat, "id", None) != self.owner_id or getattr(chat, "type", None) != "private"
                or getattr(document, "file_name", None) != FILENAME
                or not _integer(getattr(message, "message_id", None), True)):
            raise BackupError("backup_foreign_pin")
        size = getattr(document, "file_size", None)
        if type(size) is not int or not 0 < size <= self.max_bytes or not getattr(document, "file_id", None):
            raise BackupError("backup_oversize")
        if not isinstance(getattr(message, "caption", None), str) or not message.caption.startswith(SCHEMA + " owner="):
            raise BackupError("backup_foreign_pin")
        return document

    async def _download(self, message):
        document = self._message(message)
        file = await self.bot.get_file(document.file_id)
        size = getattr(file, "file_size", None)
        if size is not None and (type(size) is not int or not 0 < size <= self.max_bytes):
            raise BackupError("backup_oversize")
        token = bytes(await file.download_as_bytearray())
        envelope = self.decrypt(token)
        if message.caption != self.caption(envelope):
            raise BackupError("backup_pointer_mismatch")
        return token, envelope

    async def _check_pointer(self):
        pinned = getattr(await self._chat(), "pinned_message", None)
        if self.message_id is None:
            if pinned is not None:
                raise BackupError("backup_foreign_pin")
        elif pinned is None or getattr(pinned, "message_id", None) != self.message_id:
            raise BackupError("backup_pointer_collision")
        else:
            self._message(pinned)

    async def persist(self, snapshot):
        async with self._io_lock:
            with self._state_lock:
                if not self.ready and self.reason != "backup_not_restored":
                    raise BackupError(self.reason or "backup_unavailable")
                epoch = self._epoch
            try:
                await self._check_pointer()
                envelope = self.envelope(snapshot, self.generation + 1)
                token = self.encrypt(envelope)
                message = await self.bot.send_document(
                    chat_id=self.owner_id, document=BytesIO(token), filename=FILENAME,
                    caption=self.caption(envelope), disable_notification=True,
                )
                self._message(message)
                readback, observed = await self._download(message)
                if not hmac.compare_digest(token, readback) or observed != envelope:
                    raise BackupError("backup_readback_mismatch")
                # Telegram has no compare-and-swap pin API: this narrows, but cannot remove, the race.
                await self._check_pointer()
                await self.bot.pin_chat_message(self.owner_id, message.message_id, disable_notification=True)
                pinned = getattr(await self._chat(), "pinned_message", None)
                document = self._message(pinned)
                if (pinned.message_id != message.message_id or document.file_id != message.document.file_id
                        or pinned.caption != self.caption(envelope)):
                    raise BackupError("backup_pointer_mismatch")
                with self._state_lock:
                    if self._epoch != epoch:
                        raise BackupError("backup_operation_invalidated")
                    self.generation, self.message_id = envelope["generation"], message.message_id
                    self.ready, self.reason = True, None
                return {"generation": self.generation, "snapshot_sha256": envelope["snapshot_sha256"],
                        "message_id": self.message_id}
            except BackupError as exc:
                self.fail(exc.code)
                raise
            except asyncio.CancelledError:
                self.fail("backup_cancelled")
                raise
            except Exception:
                self.fail("backup_transport_failed")
                raise BackupError(self.reason) from None

    async def restore(self):
        self.fail("backup_not_restored")
        with self._state_lock:
            allow_empty = self.bootstrap_empty
            self.bootstrap_empty = False
            epoch = self._epoch
        try:
            pinned = getattr(await self._chat(), "pinned_message", None)
            if pinned is None:
                snapshot = export_snapshot(self.owner_id)
                if not allow_empty or any(snapshot.values()):
                    raise BackupError("backup_missing")
                await self.persist(snapshot)
                return {"restored": False, "bootstrapped_empty": True, "generation": self.generation}
            _, envelope = await self._download(pinned)
            with self._state_lock:
                if self._epoch != epoch:
                    raise BackupError("backup_operation_invalidated")
                import_snapshot(envelope["tables"], self.owner_id)
                self.generation, self.message_id = envelope["generation"], pinned.message_id
                self.ready, self.reason = True, None
            return {"restored": True, "bootstrapped_empty": False, "generation": self.generation}
        except BackupError as exc:
            self.fail(exc.code)
            raise
        except asyncio.CancelledError:
            self.fail("backup_cancelled")
            raise
        except Exception:
            self.fail("backup_transport_failed")
            raise BackupError(self.reason) from None


def from_environment(bot):
    secret = os.getenv("MUSIC_BACKUP_KEY", "")
    required = os.getenv("MUSIC_BACKUP_REQUIRED", "0") == "1"
    if not secret:
        if required:
            raise BackupError("backup_key_missing")
        return None
    owners = owner_ids()
    if len(owners) != 1:
        raise BackupError("backup_owner_invalid")
    return TelegramMusicBackup(bot, next(iter(owners)), secret, required=required,
                               bootstrap_empty=os.getenv("MUSIC_BACKUP_BOOTSTRAP_EMPTY", "0") == "1")


async def startup(bot):
    """Call once after PTB initialization and store.init(), before opening HTTP/workers."""
    global _manager, _loop, _failure
    _loop, _manager, _failure = asyncio.get_running_loop(), None, None
    try:
        _manager = from_environment(bot)
        if _manager is not None:
            await _manager.restore()
    except BackupError as exc:
        _failure = exc.code
        raise
    return status()


def status():
    required = os.getenv("MUSIC_BACKUP_REQUIRED", "0") == "1"
    if _manager is None:
        configured = bool(os.getenv("MUSIC_BACKUP_KEY", ""))
        return {"configured": configured, "required": required,
                "ready": not configured and not required and _failure is None,
                "generation": 0, "reason": _failure or ("backup_not_restored" if configured else
                                                       "backup_key_missing" if required else "disabled")}
    with _manager._state_lock:
        return {"configured": True, "required": _manager.required, "ready": _manager.ready,
                "generation": _manager.generation, "reason": _manager.reason,
                "pointer_collision_possible": True}


def mutate(fn, *args, rollback_on_failure=True, **kwargs):
    """Serialize SQL + remote proof. External accepted delivery must pass rollback_on_failure=False."""
    with _lock:
        manager = _manager
        if manager is None:
            if not status()["ready"]:
                raise BackupError(status()["reason"])
            return fn(*args, **kwargs)
        if not manager.ready or _loop is None or not _loop.is_running():
            # This reserved mode is only for recording an already observed external effect.
            # Never turn an accepted send back into pending just because remote backup failed.
            if not rollback_on_failure:
                fn(*args, **kwargs)
            raise BackupError(manager.reason or "backup_loop_unavailable")
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is _loop:
            raise BackupError("backup_worker_thread_required")
        try:
            before = export_snapshot(manager.owner_id)
        except Exception:
            manager.fail("backup_local_snapshot_invalid")
            if not rollback_on_failure:
                fn(*args, **kwargs)
            raise BackupError(manager.reason) from None
        completed = False
        try:
            result = fn(*args, **kwargs)
            completed = True
            after = export_snapshot(manager.owner_id)
            if snapshot_hash(before) != snapshot_hash(after):
                future = asyncio.run_coroutine_threadsafe(manager.persist(after), _loop)
                try:
                    future.result(timeout=90)
                except FutureTimeout:
                    manager.fail("backup_timeout")
                    future.cancel()
                    raise BackupError("backup_timeout") from None
            return result
        except Exception as exc:
            # Remote acceptance may be uncertain. Readiness remains closed until a fresh restore.
            if completed:
                manager.fail(exc.code if isinstance(exc, BackupError) else "backup_local_snapshot_invalid")
            if rollback_on_failure:
                try:
                    import_snapshot(before, manager.owner_id)
                except Exception:
                    manager.fail("backup_rollback_failed")
                    raise BackupError("backup_rollback_failed") from None
            raise
