"""Bounded Giardino RRR-01 -> ONDA/1.0 bridge.

The Giardino is a sandbox/data source, never an authority source. The bridge
can emit advisory EVENTO envelopes and correlated review responses; it cannot
execute, spend, publish, trade, deploy, contact third parties, or handle
credentials on the user's behalf.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional

from .onda_protocol import new_envelope, validate_envelope

SCHEMA = "R3-GIARDINO-ONDA/1"
GARDEN_SOURCE = "GIARDINO-RRR-01"
STAGES = frozenset({"IDEA", "SANDBOX", "VALIDATED", "READY_FOR_CLAUDIO_REVIEW", "REJECTED"})
CLASSIFICATIONS = frozenset({"PUBLIC", "PRIVATE", "SEALED"})
REVIEW_DISPOSITIONS = frozenset({"KEEP", "PATCH", "RETEST", "DEPRECATE", "ADVANCE_TO_CLAUDIO_REVIEW"})
CONSEQUENTIAL_ACTIONS = frozenset({
    "SPEND", "TRADE", "TRANSFER_FUNDS", "PUBLISH", "CONTACT_EXTERNAL",
    "DEPLOY_PRODUCTION", "SIGN_CONTRACT", "GRANT_ACCESS",
})
SENSITIVE_KEYS = frozenset({
    "password", "passwd", "passcode", "pin", "otp", "2fa", "api_key",
    "apikey", "access_token", "refresh_token", "private_key", "secret",
    "client_secret", "bearer", "credential", "credentials",
})
MAX_EVIDENCE_REFS = 16
MAX_TEXT = 4000


class GardenBridgeError(ValueError):
    """A Giardino candidate violates the bounded bridge contract."""


def _check_no_sensitive_keys(value: Any, path: str = "candidate") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in SENSITIVE_KEYS:
                raise GardenBridgeError(f"sensitive field forbidden at {path}.{key}")
            _check_no_sensitive_keys(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _check_no_sensitive_keys(child, f"{path}[{index}]")


def _text(candidate: Mapping[str, Any], key: str) -> str:
    value = candidate.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GardenBridgeError(f"{key} must be nonempty text")
    value = value.strip()
    if len(value) > MAX_TEXT:
        raise GardenBridgeError(f"{key} exceeds {MAX_TEXT} characters")
    return value


def validate_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one sandbox candidate without granting execution authority."""
    if not isinstance(candidate, Mapping):
        raise GardenBridgeError("candidate must be an object")
    _check_no_sensitive_keys(candidate)

    stage = _text(candidate, "stage").upper()
    if stage not in STAGES:
        raise GardenBridgeError("unsupported stage")
    classification = _text(candidate, "classification").upper()
    if classification not in CLASSIFICATIONS:
        raise GardenBridgeError("unsupported classification")

    evidence_refs = candidate.get("evidence_refs", [])
    if not isinstance(evidence_refs, list) or len(evidence_refs) > MAX_EVIDENCE_REFS:
        raise GardenBridgeError("evidence_refs must be a bounded list")
    if not all(isinstance(item, str) and item.strip() for item in evidence_refs):
        raise GardenBridgeError("evidence_refs entries must be nonempty text")

    requested_action = str(candidate.get("requested_action", "REVIEW_ONLY")).strip().upper()
    consequential = bool(candidate.get("consequential", False)) or requested_action in CONSEQUENTIAL_ACTIONS

    return {
        "candidate_id": _text(candidate, "candidate_id"),
        "project": _text(candidate, "project"),
        "hypothesis": _text(candidate, "hypothesis"),
        "metric": _text(candidate, "metric"),
        "next_reversible_test": _text(candidate, "next_reversible_test"),
        "stage": stage,
        "classification": classification,
        "evidence_refs": [item.strip() for item in evidence_refs],
        "requested_action": requested_action,
        "consequential": consequential,
        "authority": "DATA_ONLY_ADVISORY",
        "auto_execute": False,
        "requires_claudio_confirmation": consequential,
    }


def build_garden_event(
    candidate: Mapping[str, Any],
    *,
    epoch: int,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Emit a bounded advisory EVENTO from the memory layer to RAFFA-001."""
    normalized = validate_candidate(candidate)
    envelope = new_envelope(
        sender="MEMO-002",
        recipient="RAFFA-001",
        kind="EVENTO",
        epoch=epoch,
        payload={
            "schema": SCHEMA,
            "source": GARDEN_SOURCE,
            "authority": "DATA_ONLY_ADVISORY",
            "candidate": normalized,
        },
        now=now,
    )
    return validate_envelope(envelope, epoch, now=now)


def build_review_response(
    event: Mapping[str, Any],
    *,
    disposition: str,
    rationale: str,
    epoch: int,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Return a correlated ONDA review; still no execution authority is created."""
    validated_event = validate_envelope(event, epoch, now=now)
    if validated_event.get("tipo") != "EVENTO":
        raise GardenBridgeError("review source must be an EVENTO")
    payload = validated_event.get("payload", {})
    if payload.get("schema") != SCHEMA or payload.get("source") != GARDEN_SOURCE:
        raise GardenBridgeError("review source is not a Giardino bridge event")

    normalized_disposition = disposition.strip().upper()
    if normalized_disposition not in REVIEW_DISPOSITIONS:
        raise GardenBridgeError("unsupported review disposition")
    if not isinstance(rationale, str) or not rationale.strip():
        raise GardenBridgeError("rationale must be nonempty text")

    response = new_envelope(
        sender="RAFFA-001",
        recipient="MEMO-002",
        kind="RISPOSTA",
        epoch=epoch,
        correlation_id=validated_event["id_messaggio"],
        payload={
            "schema": SCHEMA,
            "source": GARDEN_SOURCE,
            "disposition": normalized_disposition,
            "rationale": rationale.strip()[:MAX_TEXT],
            "auto_execute": False,
        },
        now=now,
    )
    return validate_envelope(response, epoch, now=now)
