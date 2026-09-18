"""Network Event v1 — twin Supereroe peer endpoints (no crisis/×3 side effects)."""

from __future__ import annotations

import os
import secrets
import time
import uuid
from collections import deque
from typing import Any

RECENT_MAX = 50
_recent: deque[dict[str, Any]] = deque(maxlen=RECENT_MAX)

EVENT_TYPES = frozenset(
    {
        "ping",
        "case.opened",
        "case.alert",
        "case.report_sealed",
        "case.nightwatch_miss",
        "scacchiera.house",
        "scacchiera.reflect",
        "epistemic.note",
        "handoff",
        "improve.proposal",
    }
)


def get_node_id() -> str:
    return (os.getenv("NODE_ID") or "protocollo-rosso").strip() or "protocollo-rosso"


def get_network_peers() -> list[str]:
    raw = os.getenv("NETWORK_PEERS") or ""
    return [p.strip().rstrip("/") for p in raw.split(",") if p.strip()]


def get_network_secret() -> str:
    return (os.getenv("NETWORK_SECRET") or "").strip()


def verify_network_secret(header: str | None) -> bool:
    """Match Supereroe: empty secret = open ingest (MVP); else constant-time compare."""
    secret = get_network_secret()
    if not secret:
        return True
    return secrets.compare_digest((header or "").encode(), secret.encode())


def is_network_event(x: Any) -> bool:
    if not isinstance(x, dict):
        return False
    return (
        x.get("v") == 1
        and isinstance(x.get("id"), str)
        and isinstance(x.get("type"), str)
        and isinstance(x.get("source"), str)
        and isinstance(x.get("at"), str)
        and isinstance(x.get("payload"), dict)
    )


def remember_network_event(ev: dict[str, Any]) -> None:
    _recent.appendleft(ev)


def get_recent_network_events() -> list[dict[str, Any]]:
    return list(_recent)


def create_network_event(
    type_: str,
    payload: dict[str, Any] | None = None,
    case_id: str | None = None,
) -> dict[str, Any]:
    ev: dict[str, Any] = {
        "v": 1,
        "id": f"evt_{int(time.time() * 1000):x}_{uuid.uuid4().hex[:8]}",
        "type": type_,
        "source": get_node_id(),
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "payload": payload or {},
    }
    if case_id:
        ev["caseId"] = case_id
    return ev


def nodes_payload() -> dict[str, Any]:
    return {
        "nodeId": get_node_id(),
        "peers": get_network_peers(),
        "recent": get_recent_network_events()[:20],
    }
