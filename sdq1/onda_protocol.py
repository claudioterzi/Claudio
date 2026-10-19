"""SDQ-1 ONDA/1.0 envelope validation and deterministic runtime guards.

This module is deliberately transport-agnostic: it validates the protocol contract
without opening Redis connections or performing external side effects. A Redis
adapter can call these guards after authenticating its connection.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional
from uuid import UUID

PROTOCOL = "ONDA/1.0"
MAX_PAYLOAD_BYTES = 512 * 1024
HEARTBEAT_INTERVAL_SECONDS = 10
MISSED_HEARTBEATS_BEFORE_OFFLINE = 3
LOCK_TTL_SECONDS = 30
MAX_LOCK_RETRIES = 10
MESSAGE_TYPES = frozenset({
    "COMANDO", "RISPOSTA", "EVENTO", "HEARTBEAT",
    "SYNC_RICHIESTA", "SYNC_RISPOSTA", "EMERGENZA",
})
AGENTS = frozenset({"RAFFA-001", "SENTIN-004", "MEMO-002"})
COMMAND_CHANNEL = "sdq1:bus:comandi"
EMERGENCY_CHANNEL = "sdq1:bus:emergenza"


class ProtocolError(ValueError):
    """An ONDA envelope or state transition violates the protocol."""


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ProtocolError("timestamp must be a nonempty ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProtocolError("timestamp must be valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ProtocolError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"),
                          allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProtocolError("payload must be JSON-serializable without NaN/Infinity") from exc


def validate_envelope(
    envelope: Mapping[str, Any],
    current_epoch: int,
    *,
    now: Optional[datetime] = None,
    max_payload_bytes: int = MAX_PAYLOAD_BYTES,
) -> dict[str, Any]:
    """Return a normalized envelope or raise ProtocolError (fail closed)."""
    if not isinstance(envelope, Mapping):
        raise ProtocolError("envelope must be an object")
    required = {
        "protocollo", "id_messaggio", "id_correlazione", "epoca", "timestamp",
        "mittente", "destinatario", "tipo", "priorita", "scadenza_secondi", "payload",
    }
    missing = sorted(required - set(envelope))
    if missing:
        raise ProtocolError("missing required fields: " + ", ".join(missing))
    if envelope["protocollo"] != PROTOCOL:
        raise ProtocolError("unsupported protocol version")
    try:
        message_id = UUID(envelope["id_messaggio"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise ProtocolError("id_messaggio must be a UUID") from exc
    if message_id.version != 4:
        raise ProtocolError("id_messaggio must be UUID v4")
    correlation = envelope["id_correlazione"]
    if correlation is not None:
        try:
            UUID(correlation)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ProtocolError("id_correlazione must be a UUID or null") from exc
    epoch = envelope["epoca"]
    if type(epoch) is not int or epoch < 0:
        raise ProtocolError("epoca must be a non-negative integer")
    if type(current_epoch) is not int or current_epoch < 0:
        raise ProtocolError("current_epoch must be a non-negative integer")
    if epoch != current_epoch:
        raise ProtocolError("stale or future epoch rejected")
    sender = envelope["mittente"]
    recipient = envelope["destinatario"]
    if not isinstance(sender, str) or not sender.strip():
        raise ProtocolError("mittente must be nonempty text")
    if not isinstance(recipient, str) or not recipient.strip():
        raise ProtocolError("destinatario must be nonempty text or '*'")
    kind = envelope["tipo"]
    if kind not in MESSAGE_TYPES:
        raise ProtocolError("unsupported message type")
    priority = envelope["priorita"]
    if type(priority) is not int or priority not in (1, 2, 3):
        raise ProtocolError("priorita must be integer 1, 2 or 3")
    expiry = envelope["scadenza_secondi"]
    if type(expiry) is not int or expiry <= 0:
        raise ProtocolError("scadenza_secondi must be a positive integer")
    stamp = _parse_timestamp(envelope["timestamp"])
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None or current_time.utcoffset() is None:
        raise ProtocolError("now must be timezone-aware")
    age = (current_time.astimezone(timezone.utc) - stamp).total_seconds()
    if age > expiry:
        raise ProtocolError("message expired")
    if age < -5:
        raise ProtocolError("message timestamp is too far in the future")
    payload = envelope["payload"]
    if not isinstance(payload, Mapping):
        raise ProtocolError("payload must be a JSON object")
    if len(_json_bytes(payload)) > max_payload_bytes:
        raise ProtocolError("payload exceeds configured byte limit")
    if kind == "COMANDO" and sender != "RAFFA-001":
        raise ProtocolError("only RAFFA-001 may publish COMANDO messages")
    if kind == "EMERGENZA" and sender != "SENTIN-004":
        raise ProtocolError("only SENTIN-004 may publish EMERGENZA messages")
    if kind == "HEARTBEAT" and recipient != "*":
        raise ProtocolError("HEARTBEAT must be broadcast to '*'")
    if kind == "RISPOSTA" and not correlation:
        raise ProtocolError("RISPOSTA requires id_correlazione")
    if kind == "COMANDO" and not correlation:
        raise ProtocolError("COMANDO requires id_correlazione")
    normalized = dict(envelope)
    normalized["timestamp"] = stamp.isoformat().replace("+00:00", "Z")
    return normalized


def validate_channel_authority(channel: str, sender: str) -> None:
    """Enforce publisher ownership for privileged channels."""
    if channel == COMMAND_CHANNEL and sender != "RAFFA-001":
        raise ProtocolError("only RAFFA-001 may publish to sdq1:bus:comandi")
    if channel == EMERGENCY_CHANNEL and sender != "SENTIN-004":
        raise ProtocolError("only SENTIN-004 may publish to sdq1:bus:emergenza")


def new_envelope(
    *, sender: str, recipient: str, kind: str, epoch: int,
    payload: Mapping[str, Any], correlation_id: Optional[str] = None,
    priority: int = 2, expiry_seconds: int = 15,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Build an ONDA/1.0 envelope; callers still validate before transport."""
    stamp = now or datetime.now(timezone.utc)
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ProtocolError("now must be timezone-aware")
    return {
        "protocollo": PROTOCOL,
        "id_messaggio": __import__("uuid").uuid4().__str__(),
        "id_correlazione": correlation_id,
        "epoca": epoch,
        "timestamp": stamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mittente": sender,
        "destinatario": recipient,
        "tipo": kind,
        "priorita": priority,
        "scadenza_secondi": expiry_seconds,
        "payload": dict(payload),
    }


@dataclass
class HeartbeatMonitor:
    """In-memory reference model for SENTIN; persist state in Redis in deployment."""
    interval_seconds: int = HEARTBEAT_INTERVAL_SECONDS
    missed_limit: int = MISSED_HEARTBEATS_BEFORE_OFFLINE
    last_seen: Optional[datetime] = None

    def record(self, at: Optional[datetime] = None) -> None:
        value = at or datetime.now(timezone.utc)
        if value.tzinfo is None or value.utcoffset() is None:
            raise ProtocolError("heartbeat time must be timezone-aware")
        self.last_seen = value.astimezone(timezone.utc)

    def is_offline(self, at: Optional[datetime] = None) -> bool:
        if self.last_seen is None:
            return True
        value = at or datetime.now(timezone.utc)
        if value.tzinfo is None or value.utcoffset() is None:
            raise ProtocolError("check time must be timezone-aware")
        elapsed = (value.astimezone(timezone.utc) - self.last_seen).total_seconds()
        return elapsed >= self.interval_seconds * self.missed_limit


def redis_lock_command(resource: str, agent_id: str) -> tuple[str, str, str, int]:
    """Return safe Redis SET arguments: SET key owner NX EX ttl."""
    if not isinstance(resource, str) or not resource.strip():
        raise ProtocolError("resource must be nonempty text")
    if not isinstance(agent_id, str) or not agent_id.strip():
        raise ProtocolError("agent_id must be nonempty text")
    safe_resource = resource.strip().replace(" ", "_")
    return ("SET", f"sdq1:lock:{safe_resource}", agent_id, LOCK_TTL_SECONDS)
