"""R3-011 — append-only Evidence Graph contract.

This graph stores claims, provenance, tests and explicit relations. Structural
sensors such as Graphify and heuristic relations from R3_COLLATE_ALL may feed
candidate edges, but inferred edges never become factual support automatically.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal

EpistemicState = Literal[
    "FATTO", "INTERPRETAZIONE", "INFERENZA", "IPOTESI", "SIMULAZIONE", "POSSIBLE"
]
EvidenceType = Literal[
    "AUTHORITATIVE_STATE", "TEST", "DOCUMENT", "CODE", "MODEL_OUTPUT",
    "USER_DECLARATION", "STRUCTURAL_SENSOR", "OTHER"
]
RelationType = Literal[
    "SUPPORTS", "CONTRADICTS", "TESTS", "DERIVED_FROM", "SUPERSEDES", "RELATED"
]
RelationBasis = Literal["EXPLICIT", "INFERRED"]

EPISTEMIC_STATES = frozenset({
    "FATTO", "INTERPRETAZIONE", "INFERENZA", "IPOTESI", "SIMULAZIONE", "POSSIBLE"
})
EVIDENCE_TYPES = frozenset({
    "AUTHORITATIVE_STATE", "TEST", "DOCUMENT", "CODE", "MODEL_OUTPUT",
    "USER_DECLARATION", "STRUCTURAL_SENSOR", "OTHER",
})
RELATION_TYPES = frozenset({
    "SUPPORTS", "CONTRADICTS", "TESTS", "DERIVED_FROM", "SUPERSEDES", "RELATED"
})
RELATION_BASES = frozenset({"EXPLICIT", "INFERRED"})
PROMOTION_EVIDENCE_TYPES = frozenset({
    "AUTHORITATIVE_STATE", "TEST", "DOCUMENT", "CODE", "USER_DECLARATION"
})


@dataclass(frozen=True)
class EvidenceRecord:
    record_id: str
    version: str
    claim: str
    state: EpistemicState
    source: str
    source_version: str | None
    evidence_type: EvidenceType
    evidence_ref: str
    falsifier: str
    created_at: str
    priority: str | None = None
    independence_group: str | None = None
    confidence: float | None = None
    payload_sha256: str | None = None
    postcondition_source: str | None = None

    def key(self) -> str:
        return f"{self.record_id}@{self.version}"


@dataclass(frozen=True)
class EvidenceEdge:
    edge_id: str
    source_key: str
    target_key: str
    relation: RelationType
    basis: RelationBasis
    rationale: str
    created_at: str


class EvidenceGraph:
    def __init__(self) -> None:
        self._records: dict[str, EvidenceRecord] = {}
        self._edges: dict[str, EvidenceEdge] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _validate_record(record: EvidenceRecord) -> None:
        for name in (
            "record_id", "version", "claim", "source", "evidence_ref", "falsifier", "created_at"
        ):
            if not str(getattr(record, name) or "").strip():
                raise ValueError(f"{name} is required")
        if record.state not in EPISTEMIC_STATES:
            raise ValueError(f"unsupported epistemic state: {record.state}")
        if record.evidence_type not in EVIDENCE_TYPES:
            raise ValueError(f"unsupported evidence type: {record.evidence_type}")
        if record.confidence is not None and not 0 <= record.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if record.payload_sha256 is not None:
            digest = record.payload_sha256.lower()
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("payload_sha256 must be a 64-character hexadecimal digest")
        if record.state == "FATTO" and record.evidence_type == "MODEL_OUTPUT":
            raise ValueError("model output alone cannot be stored as FATTO")
        if record.evidence_type == "AUTHORITATIVE_STATE":
            if not isinstance(record.postcondition_source, str) or not record.postcondition_source.strip():
                raise ValueError("AUTHORITATIVE_STATE requires a nonempty postcondition_source")
        elif record.postcondition_source is not None:
            if not isinstance(record.postcondition_source, str) or not record.postcondition_source.strip():
                raise ValueError("postcondition_source must be null or a nonempty string")
            if record.evidence_type != "OTHER" or record.state == "FATTO":
                raise ValueError(
                    "non-authoritative postcondition_source requires non-factual OTHER evidence"
                )

    @staticmethod
    def _validate_edge(edge: EvidenceEdge) -> None:
        for name in ("edge_id", "source_key", "target_key", "rationale", "created_at"):
            if not str(getattr(edge, name) or "").strip():
                raise ValueError(f"{name} is required")
        if edge.relation not in RELATION_TYPES:
            raise ValueError(f"unsupported relation: {edge.relation}")
        if edge.basis not in RELATION_BASES:
            raise ValueError(f"unsupported relation basis: {edge.basis}")

    @staticmethod
    def _serialize_record(record: EvidenceRecord) -> dict[str, Any]:
        """Keep schema-v1 output stable when the additive source field is absent."""
        serialized = asdict(record)
        if serialized["postcondition_source"] is None:
            del serialized["postcondition_source"]
        return serialized

    def add_record(self, record: EvidenceRecord) -> str:
        self._validate_record(record)
        key = record.key()
        current = self._records.get(key)
        if current is not None:
            if current != record:
                raise ValueError("immutable evidence record collision")
            return key
        self._records[key] = record
        return key

    def add_edge(self, edge: EvidenceEdge) -> str:
        self._validate_edge(edge)
        if edge.source_key not in self._records or edge.target_key not in self._records:
            raise ValueError("edge endpoints must already exist")
        if edge.source_key == edge.target_key:
            raise ValueError("self edge not allowed")
        if edge.basis == "INFERRED" and edge.relation in {"SUPPORTS", "CONTRADICTS"}:
            # Inference may flag a candidate relation, but it is not explicit evidence.
            pass
        current = self._edges.get(edge.edge_id)
        if current is not None:
            if current != edge:
                raise ValueError("immutable edge collision")
            return edge.edge_id
        self._edges[edge.edge_id] = edge
        return edge.edge_id

    def record(self, key: str) -> EvidenceRecord:
        return self._records[key]

    def provenance_chain(self, key: str) -> dict[str, Any]:
        if key not in self._records:
            raise KeyError(key)
        incoming = [
            edge for edge in self._edges.values()
            if edge.target_key == key and edge.relation in {"DERIVED_FROM", "TESTS", "SUPPORTS"}
        ]
        return {
            "record": self._serialize_record(self._records[key]),
            "incoming": [asdict(edge) for edge in sorted(incoming, key=lambda x: x.edge_id)],
        }

    def claim_history(self, record_id: str) -> list[EvidenceRecord]:
        values = [r for r in self._records.values() if r.record_id == record_id]
        return sorted(values, key=lambda r: (r.created_at, r.version))

    def conflicts(self) -> list[EvidenceEdge]:
        return sorted(
            [e for e in self._edges.values() if e.relation == "CONTRADICTS"],
            key=lambda e: e.edge_id,
        )

    def promotion_support(self, key: str) -> list[EvidenceEdge]:
        """Return only explicit evidence edges eligible for promotion review."""
        if key not in self._records:
            raise KeyError(key)
        return sorted(
            [
                edge for edge in self._edges.values()
                if edge.target_key == key
                and edge.basis == "EXPLICIT"
                and edge.relation in {"SUPPORTS", "TESTS"}
                and self._records[edge.source_key].state == "FATTO"
                and self._records[edge.source_key].evidence_type in PROMOTION_EVIDENCE_TYPES
            ],
            key=lambda edge: edge.edge_id,
        )

    def export(self) -> dict[str, Any]:
        records = [
            self._serialize_record(record)
            for record in sorted(self._records.values(), key=lambda item: item.key())
        ]
        edges = [asdict(e) for e in sorted(self._edges.values(), key=lambda x: x.edge_id)]
        body = {
            "schema": "R3-EVIDENCE-GRAPH/1",
            "records": records,
            "edges": edges,
            "rules": {
                "append_only": True,
                "model_output_alone_cannot_be_fact": True,
                "inferred_edges_are_not_authority": True,
            },
        }
        canonical = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        body["graph_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return body


def record_from_state_verification(
    *,
    record_id: str,
    version: str,
    claim: str,
    evidence: dict[str, Any],
    source: str,
    evidence_ref: str,
    falsifier: str,
    priority: str | None = None,
) -> EvidenceRecord:
    """Convert R3-007-shaped state verification evidence without hard dependency."""
    _validate_state_verification_evidence(evidence)
    mode = evidence.get("verification_mode")
    match = evidence.get("state_match")
    error = evidence.get("error")
    trajectory = bool(evidence.get("trajectory_success"))
    if trajectory and mode == "AUTHORITATIVE" and match is True and not error:
        state: EpistemicState = "FATTO"
        evidence_type: EvidenceType = "AUTHORITATIVE_STATE"
    elif trajectory and mode == "AUTHORITATIVE" and match is False and not error:
        state = "FATTO"
        evidence_type = "AUTHORITATIVE_STATE"
        claim = "POSTCONDITION_MISMATCH: " + claim
    else:
        state = "IPOTESI"
        evidence_type = "OTHER"

    postcondition_source = None
    if mode in {"AUTHORITATIVE", "PROXY"}:
        postcondition_source = str(evidence["postcondition_source"]).strip()

    payload = json.dumps(evidence, sort_keys=True, ensure_ascii=False, default=str)
    return EvidenceRecord(
        record_id=record_id,
        version=version,
        claim=claim,
        state=state,
        source=source,
        source_version=None,
        evidence_type=evidence_type,
        evidence_ref=evidence_ref,
        falsifier=falsifier,
        created_at=str(evidence.get("verification_time") or datetime.now(timezone.utc).isoformat()),
        priority=priority,
        payload_sha256=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        postcondition_source=postcondition_source,
    )


def _validate_state_verification_evidence(evidence: dict[str, Any]) -> None:
    required = {
        "trajectory_success", "verification_mode", "postcondition_source",
        "expected_state", "observed_state", "state_match", "verification_time",
        "observer_calls", "error",
    }
    missing = sorted(required.difference(evidence))
    if missing:
        raise ValueError("R3-007 evidence missing fields: " + ", ".join(missing))

    trajectory = evidence["trajectory_success"]
    if not isinstance(trajectory, bool):
        raise ValueError("trajectory_success must be boolean")
    mode = evidence["verification_mode"]
    if mode not in {"AUTHORITATIVE", "PROXY", "UNAVAILABLE"}:
        raise ValueError(f"unsupported verification mode: {mode}")
    match = evidence["state_match"]
    if match is not None and not isinstance(match, bool):
        raise ValueError("state_match must be boolean or null")
    calls = evidence["observer_calls"]
    if isinstance(calls, bool) or not isinstance(calls, int) or calls < 0:
        raise ValueError("observer_calls must be a non-negative integer")
    error = evidence["error"]
    if error is not None and (not isinstance(error, str) or not error.strip()):
        raise ValueError("error must be null or a nonempty string")

    timestamp = evidence["verification_time"]
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("verification_time must be a nonempty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("verification_time must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("verification_time must be timezone-aware")

    if mode in {"AUTHORITATIVE", "PROXY"}:
        source = evidence["postcondition_source"]
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"{mode} evidence requires a nonempty postcondition_source")
        if calls < 1:
            raise ValueError(f"{mode} evidence requires at least one observer call")
        if error is not None:
            if match is not None or evidence["observed_state"] is not None:
                raise ValueError("errored observation requires null state_match and observed_state")
            return
        if match is None:
            raise ValueError("successful observation requires a boolean state_match")
        states_equal = evidence["expected_state"] == evidence["observed_state"]
        if match is not states_equal:
            raise ValueError("state_match contradicts expected_state and observed_state")
        return

    if calls != 0:
        raise ValueError("UNAVAILABLE evidence requires observer_calls=0")
    if match is not None or evidence["observed_state"] is not None:
        raise ValueError("UNAVAILABLE evidence cannot contain an observed match or state")
