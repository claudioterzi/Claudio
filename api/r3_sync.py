"""R3∞ authenticated cross-device ledger sync.

Persistent Redis backend for the browser hash-chain. The server accepts only
validated append-only extensions and uses compare-and-swap semantics.

Claudio Terzi · C.Terzi
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
import re
import secrets
from typing import Any

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024

DATA_KEY = "r3:sync:ledger:v1"
DEVICE_PREFIX = "r3:sync:device:v1:"
MAX_EVENTS = 5000
MAX_BYTES = 3 * 1024 * 1024
STATES = {"FATTO", "INFERENZA", "IPOTESI", "SIMULAZIONE"}
FIELDS = (
    "id", "ts", "state", "claim", "evidence", "falsifier",
    "source", "priority", "previous_hash", "hash",
)
HEX64 = re.compile(r"^[a-f0-9]{64}$")


def _redis():
    url = os.getenv("REDIS_URL") or os.getenv("KV_URL")
    if not url:
        return None
    import redis
    return redis.from_url(url, decode_responses=True, socket_connect_timeout=3, socket_timeout=5)


def _secret() -> str:
    return os.getenv("PERFUME_ARCHIVE_SECRET", "")


def _password_configured() -> bool:
    return bool(os.getenv("PERFUME_ARCHIVE_PASSWORD_HASH") or os.getenv("PERFUME_ARCHIVE_PASSWORD"))


def _password_matches(value: Any) -> bool:
    if not isinstance(value, str) or len(value) > 1024:
        return False
    encoded = os.getenv("PERFUME_ARCHIVE_PASSWORD_HASH", "")
    if encoded:
        try:
            return check_password_hash(encoded, value)
        except (ValueError, TypeError):
            return False
    configured = os.getenv("PERFUME_ARCHIVE_PASSWORD", "")
    return bool(configured) and hmac.compare_digest(value.encode(), configured.encode())


def _client_digest(value: str) -> str:
    secret = _secret()
    if len(secret) < 32:
        raise RuntimeError("sync auth not configured")
    return hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()


def _allow_enroll(client) -> bool:
    now_bucket = int(datetime.now(timezone.utc).timestamp()) // 900
    remote = request.remote_addr or "unknown"
    keys = [
        "r3:sync:enroll:" + str(now_bucket) + ":" + _client_digest(remote),
        "r3:sync:enroll:" + str(now_bucket) + ":all",
    ]
    return client.eval(
        """
        if tonumber(redis.call('GET', KEYS[1]) or '0') >= 5 then return 0 end
        if tonumber(redis.call('GET', KEYS[2]) or '0') >= 30 then return 0 end
        for i=1,2 do
          redis.call('INCR', KEYS[i])
          redis.call('EXPIRE', KEYS[i], 1800)
        end
        return 1
        """,
        2,
        *keys,
    ) == 1


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _bearer() -> str:
    value = request.headers.get("Authorization", "")
    if not value.startswith("Bearer "):
        return ""
    token = value[7:].strip()
    return token if 32 <= len(token) <= 256 else ""


def _device(client):
    token = _bearer()
    if not token:
        return None
    raw = client.get(DEVICE_PREFIX + _token_digest(token))
    if not raw:
        return None
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) and value.get("device_id") else None
    except (TypeError, ValueError):
        return None


def _stable(event: dict[str, Any]) -> str:
    ordered = {
        "id": event["id"],
        "ts": event["ts"],
        "state": event["state"],
        "claim": event["claim"],
        "evidence": event["evidence"],
        "falsifier": event["falsifier"],
        "source": event["source"],
        "priority": event["priority"],
        "previous_hash": event["previous_hash"],
    }
    return json.dumps(ordered, ensure_ascii=False, separators=(",", ":"))


def _valid_record(event: Any) -> bool:
    if not isinstance(event, dict) or set(event) != set(FIELDS):
        return False
    for key in ("id", "ts", "state", "claim", "evidence", "falsifier", "source", "priority", "hash"):
        if not isinstance(event.get(key), str) or len(event[key]) > 50000:
            return False
    if not event["id"] or len(event["id"]) > 256 or not event["claim"].strip():
        return False
    if len(event["ts"]) > 64 or len(event["priority"]) > 128 or event["state"] not in STATES:
        return False
    try:
        datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    previous = event["previous_hash"]
    if previous is not None and (not isinstance(previous, str) or not HEX64.fullmatch(previous)):
        return False
    if not HEX64.fullmatch(event["hash"]):
        return False
    return hmac.compare_digest(hashlib.sha256(_stable(event).encode()).hexdigest(), event["hash"])


def _validate_ledger(events: Any) -> tuple[bool, str]:
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        return False, "schema_or_limit"
    ids: set[str] = set()
    hashes: set[str] = set()
    previous = None
    for index, event in enumerate(events):
        if not _valid_record(event):
            return False, "schema:" + str(index)
        if event["id"] in ids or event["hash"] in hashes:
            return False, "duplicate:" + str(index)
        if event["previous_hash"] != previous:
            return False, "chain:" + str(index)
        ids.add(event["id"])
        hashes.add(event["hash"])
        previous = event["hash"]
    return True, ""


def _empty_envelope() -> dict[str, Any]:
    return {"schema": "R3_SERVER_LEDGER_V1", "revision": 0, "updated_at": None, "head": None, "events": []}


def _decode(raw: Any) -> dict[str, Any]:
    if not raw:
        return _empty_envelope()
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema") != "R3_SERVER_LEDGER_V1":
        raise ValueError("server envelope invalid")
    ok, reason = _validate_ledger(value.get("events"))
    if not ok:
        raise ValueError("server ledger invalid: " + reason)
    if value.get("head") != (value["events"][-1]["hash"] if value["events"] else None):
        raise ValueError("server head invalid")
    if not isinstance(value.get("revision"), int) or value["revision"] < 0:
        raise ValueError("server revision invalid")
    return value


def _same_prefix(prefix: list[dict[str, Any]], full: list[dict[str, Any]]) -> bool:
    if len(prefix) > len(full):
        return False
    return all(prefix[i]["hash"] == full[i]["hash"] and _stable(prefix[i]) == _stable(full[i]) for i in range(len(prefix)))


def _json_size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode())


@app.after_request
def _headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers.pop("Access-Control-Allow-Origin", None)
    return response


@app.get("/api/r3-sync/health")
def health():
    client = _redis()
    configured = len(_secret()) >= 32 and _password_configured()
    if client is None:
        return jsonify(ok=False, storage="unavailable", auth_configured=configured), 503
    probe = "r3:sync:health:" + secrets.token_hex(8)
    try:
        client.set(probe, "1", ex=30)
        read_write = client.get(probe) == "1"
        client.delete(probe)
        return jsonify(ok=bool(read_write and configured), storage="redis", read_write=read_write, auth_configured=configured), (200 if read_write and configured else 503)
    except Exception:
        return jsonify(ok=False, storage="redis", read_write=False, auth_configured=configured), 503


@app.post("/api/r3-sync/enroll")
def enroll():
    client = _redis()
    if client is None or len(_secret()) < 32 or not _password_configured():
        return jsonify(ok=False, error="sync_not_configured"), 503
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(ok=False, error="invalid_request"), 400
    try:
        if not _allow_enroll(client):
            response = jsonify(ok=False, error="rate_limited")
            response.status_code = 429
            response.headers["Retry-After"] = "900"
            return response
    except Exception:
        return jsonify(ok=False, error="auth_storage_unavailable"), 503
    if not _password_matches(body.get("password")):
        return jsonify(ok=False, error="unauthorized"), 401
    label = body.get("device_name", "")
    if not isinstance(label, str):
        label = ""
    label = " ".join(label.strip().split())[:80]
    token = secrets.token_urlsafe(48)
    device = {"device_id": "R3D-" + secrets.token_hex(8), "label": label or "browser", "created_at": datetime.now(timezone.utc).isoformat()}
    client.set(DEVICE_PREFIX + _token_digest(token), json.dumps(device, separators=(",", ":")))
    return jsonify(ok=True, token=token, device=device)


def _authorized_store():
    client = _redis()
    if client is None:
        return None, None, (jsonify(ok=False, error="storage_unavailable"), 503)
    try:
        device = _device(client)
    except Exception:
        return None, None, (jsonify(ok=False, error="storage_unavailable"), 503)
    if not device:
        return None, None, (jsonify(ok=False, error="unauthorized"), 401)
    return client, device, None


@app.get("/api/r3-sync")
def get_ledger():
    client, device, error = _authorized_store()
    if error:
        return error
    try:
        envelope = _decode(client.get(DATA_KEY))
        return jsonify(ok=True, device=device, **envelope)
    except Exception:
        return jsonify(ok=False, error="server_ledger_invalid"), 503


@app.put("/api/r3-sync")
def put_ledger():
    client, device, error = _authorized_store()
    if error:
        return error
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or _json_size(body) > MAX_BYTES:
        return jsonify(ok=False, error="invalid_request"), 400
    events = body.get("events")
    base_revision = body.get("base_revision")
    base_head = body.get("base_head")
    if not isinstance(base_revision, int) or base_revision < 0:
        return jsonify(ok=False, error="invalid_base_revision"), 400
    if base_head is not None and (not isinstance(base_head, str) or not HEX64.fullmatch(base_head)):
        return jsonify(ok=False, error="invalid_base_head"), 400
    ok, reason = _validate_ledger(events)
    if not ok:
        return jsonify(ok=False, error="invalid_ledger", reason=reason), 400
    if _json_size(events) > MAX_BYTES:
        return jsonify(ok=False, error="ledger_too_large"), 413
    try:
        import redis
        for _ in range(4):
            pipe = client.pipeline()
            try:
                pipe.watch(DATA_KEY)
                current = _decode(pipe.get(DATA_KEY))
                if current["revision"] != base_revision or current["head"] != base_head:
                    pipe.unwatch()
                    return jsonify(ok=False, error="revision_conflict", revision=current["revision"], head=current["head"]), 409
                if not _same_prefix(current["events"], events):
                    pipe.unwatch()
                    return jsonify(ok=False, error="non_append_only", revision=current["revision"], head=current["head"]), 409
                if len(events) == len(current["events"]):
                    pipe.unwatch()
                    return jsonify(ok=True, unchanged=True, revision=current["revision"], head=current["head"])
                envelope = {
                    "schema": "R3_SERVER_LEDGER_V1",
                    "revision": current["revision"] + 1,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "head": events[-1]["hash"] if events else None,
                    "events": events,
                    "last_writer": device["device_id"],
                }
                pipe.multi()
                pipe.set(DATA_KEY, json.dumps(envelope, ensure_ascii=False, separators=(",", ":")))
                pipe.execute()
                return jsonify(ok=True, unchanged=False, revision=envelope["revision"], head=envelope["head"])
            except redis.WatchError:
                continue
            finally:
                try:
                    pipe.reset()
                except Exception:
                    pass
        return jsonify(ok=False, error="write_contention"), 409
    except Exception:
        return jsonify(ok=False, error="storage_unavailable"), 503


@app.post("/api/r3-sync/revoke")
def revoke():
    client, device, error = _authorized_store()
    if error:
        return error
    token = _bearer()
    client.delete(DEVICE_PREFIX + _token_digest(token))
    return jsonify(ok=True, revoked=device["device_id"])
