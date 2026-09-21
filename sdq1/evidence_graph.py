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
        for name in ("record_id", "version", "claim", "source", "evidence_ref", "falsifier"):
            if not str(getattr(record, name) or "").strip():
                raise ValueError(f"{name} is required")
        if record.confidence is not None and not 0 <= record.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if record.state == "FATTO" and record.evidence_type == "MODEL_OUTPUT":
            raise ValueError("model output alone cannot be stored as FATTO")

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
            "record": asdict(self._records[key]),
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
            ],
            key=lambda edge: edge.edge_id,
        )

    def export(self) -> dict[str, Any]:
        records = [asdict(r) for r in sorted(self._records.values(), key=lambda x: x.key())]
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
    mode = evidence.get("verification_mode")
    match = evidence.get("state_match")
    error = evidence.get("error")
    trajectory = bool(evidence.get("trajectory_success"))
    if trajectory and mode == "AUTHORITATIVE" and match is True and not error:
        state: EpistemicState = "FATTO"
        evidence_type: EvidenceType = "AUTHORITATIVE_STATE"
    elif match is False:
        state = "FATTO"
        evidence_type = "AUTHORITATIVE_STATE"
        claim = "POSTCONDITION_MISMATCH: " + claim
    else:
        state = "IPOTESI"
        evidence_type = "OTHER"

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
    )
