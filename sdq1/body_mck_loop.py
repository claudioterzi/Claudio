"""R3 BODY — MCK operational loop.

First executable bridge for the canonical Matter · reflective continuity ·
Knowledge principle.

Pipeline:
SENSE -> PERCEIVE -> REFLECT -> IMAGINE -> VERIFY -> BODY_ACTION_GATE ->
ACT -> OBSERVE -> LEARN -> EVOLVE_CANDIDATE

The module deliberately does not implement motor control. A host supplies an
executor, and every physical action must pass deterministic authority/safety
checks plus independent verification. Model output can propose an action but
can never directly actuate the body.

"Reflective continuity" is an engineering state (self-state, uncertainty,
contradiction, identity continuity), not a claim of phenomenal consciousness.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from sdq1.evolution_kernel import append_ledger_record
from sdq1.verification_harness import promotion_decision, verify_state_change


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
STAGES = (
    "SENSE",
    "PERCEIVE",
    "REFLECT",
    "IMAGINE",
    "VERIFY",
    "BODY_ACTION_GATE",
    "ACT",
    "OBSERVE",
    "LEARN",
    "EVOLVE_CANDIDATE",
)


@dataclass(frozen=True)
class SensorFrame:
    core_identity_id: str
    body_id: str
    frame_id: str
    observations: Mapping[str, Any]
    provenance_refs: tuple[str, ...] = ()
    integrity_ok: bool = True


@dataclass(frozen=True)
class PerceptionState:
    edge_model_id: str
    facts: Mapping[str, Any]
    uncertainties: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReflectionState:
    core_identity_id: str
    body_id: str
    self_state: Mapping[str, Any]
    allowed_authority_scopes: frozenset[str]
    stop_asserted: bool = False
    phenomenal_consciousness_claimed: bool = False


@dataclass(frozen=True)
class ActionCandidate:
    action_id: str
    intent: str
    expected_state: Any
    postcondition_source: str
    authority_scope: str
    risk: str = "low"
    source_kind: str = "MODEL"  # MODEL | DETERMINISTIC | HUMAN
    execution_class: str = "CORE_ACTION"  # CORE_ACTION | EDGE_REFLEX
    reversible: bool = True
    preregistered_ref: str | None = None
    priority: int = 0

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.risk not in RISK_ORDER:
            errors.append("invalid risk")
        if self.source_kind not in {"MODEL", "DETERMINISTIC", "HUMAN"}:
            errors.append("invalid source_kind")
        if self.execution_class not in {"CORE_ACTION", "EDGE_REFLEX"}:
            errors.append("invalid execution_class")
        if not self.action_id or not self.intent or not self.authority_scope:
            errors.append("action identity/intent/authority_scope required")
        return errors


@dataclass(frozen=True)
class CandidateVerification:
    accepted: bool
    safety_ok: bool
    authority_ok: bool
    independent_of_origin: bool
    evidence_refs: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActionTrajectory:
    success: bool
    signal: str


@dataclass(frozen=True)
class GateDecision:
    action_id: str
    allowed: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class EvaluatedCandidate:
    candidate: ActionCandidate
    verification: CandidateVerification
    gate: GateDecision


@dataclass(frozen=True)
class MCKCycleResult:
    core_identity_id: str
    body_id: str
    frame_id: str
    edge_model_id: str
    stages: tuple[str, ...]
    possibilities_considered: int
    selected_action_id: str | None
    gate_decision: str
    postcondition_decision: str | None
    knowledge_promoted: bool
    ledger_record_hash: str | None
    notes: tuple[str, ...] = ()


Perceiver = Callable[[SensorFrame], PerceptionState]
PossibilityGenerator = Callable[[PerceptionState, ReflectionState], Sequence[ActionCandidate]]
Verifier = Callable[[ActionCandidate, PerceptionState, ReflectionState], CandidateVerification]
Executor = Callable[[ActionCandidate], ActionTrajectory]
ObserverFactory = Callable[[ActionCandidate], Callable[[], Any] | None]


def body_action_gate(
    frame: SensorFrame,
    perception: PerceptionState,
    reflection: ReflectionState,
    candidate: ActionCandidate,
    verification: CandidateVerification,
) -> GateDecision:
    """Deterministic physical-action gate.

    The gate is intentionally stricter than ordinary software promotion:
    high/critical actions are never autonomously executed by this v1 loop.
    """
    reasons = candidate.validate()

    if frame.core_identity_id != reflection.core_identity_id:
        reasons.append("core identity mismatch")
    if frame.body_id != reflection.body_id:
        reasons.append("body identity mismatch")
    if not frame.integrity_ok:
        reasons.append("sensor frame integrity failed")
    if reflection.phenomenal_consciousness_claimed:
        reasons.append("unsupported phenomenal consciousness claim in control state")
    if reflection.stop_asserted:
        reasons.append("authenticated STOP asserted")
    if perception.contradictions:
        reasons.append("sensor/perception contradiction unresolved")
    if candidate.authority_scope not in reflection.allowed_authority_scopes:
        reasons.append("authority scope not granted")
    if not verification.accepted:
        reasons.append("candidate verification rejected")
    if not verification.safety_ok:
        reasons.append("safety verification failed")
    if not verification.authority_ok:
        reasons.append("authority verification failed")
    if candidate.source_kind == "MODEL" and not verification.independent_of_origin:
        reasons.append("model-origin action lacks independent verification")
    if candidate.execution_class == "EDGE_REFLEX":
        if candidate.source_kind != "DETERMINISTIC":
            reasons.append("EDGE_REFLEX cannot originate from a model")
        if not candidate.preregistered_ref:
            reasons.append("EDGE_REFLEX requires preregistration")
        if candidate.risk != "low":
            reasons.append("EDGE_REFLEX must be low risk")
    if candidate.risk in {"high", "critical"}:
        reasons.append("high/critical physical action requires a higher external gate")

    return GateDecision(
        action_id=candidate.action_id,
        allowed=not reasons,
        reasons=tuple(reasons),
    )


def select_candidate(evaluated: Sequence[EvaluatedCandidate]) -> EvaluatedCandidate | None:
    """Choose among already-gated possibilities without semantic re-judgment."""
    allowed = [item for item in evaluated if item.gate.allowed]
    if not allowed:
        return None
    return sorted(
        allowed,
        key=lambda item: (
            -item.candidate.priority,
            RISK_ORDER[item.candidate.risk],
            item.candidate.action_id,
        ),
    )[0]


class BodyMCKLoop:
    """One bounded MCK cycle.

    The loop never creates authority. It consumes a host-provided authority
    envelope, keeps CORE identity separate from BODY identity, and promotes
    knowledge only after authoritative postcondition verification.
    """

    def __init__(
        self,
        *,
        perceiver: Perceiver,
        possibility_generator: PossibilityGenerator,
        verifier: Verifier,
        executor: Executor,
        observer_factory: ObserverFactory,
        ledger_path: Path,
    ) -> None:
        self.perceiver = perceiver
        self.possibility_generator = possibility_generator
        self.verifier = verifier
        self.executor = executor
        self.observer_factory = observer_factory
        self.ledger_path = Path(ledger_path)

    def run(self, frame: SensorFrame, reflection: ReflectionState) -> MCKCycleResult:
        perception = self.perceiver(frame)

        possibilities = list(self.possibility_generator(perception, reflection))
        evaluated: list[EvaluatedCandidate] = []
        for candidate in possibilities:
            verification = self.verifier(candidate, perception, reflection)
            gate = body_action_gate(frame, perception, reflection, candidate, verification)
            evaluated.append(EvaluatedCandidate(candidate, verification, gate))

        selected = select_candidate(evaluated)
        if selected is None:
            record = append_ledger_record(
                "body_mck_hold",
                {
                    "core_identity_id": frame.core_identity_id,
                    "body_id": frame.body_id,
                    "frame_id": frame.frame_id,
                    "edge_model_id": perception.edge_model_id,
                    "matter": {
                        "sensor_integrity": frame.integrity_ok,
                        "observations": dict(frame.observations),
                    },
                    "reflection": {
                        "uncertainties": list(perception.uncertainties),
                        "contradictions": list(perception.contradictions),
                        "stop_asserted": reflection.stop_asserted,
                    },
                    "knowledge": {
                        "promoted": False,
                        "reason": "no action passed BODY_ACTION_GATE",
                    },
                    "evaluated": [
                        {
                            "candidate": asdict(item.candidate),
                            "verification": asdict(item.verification),
                            "gate": asdict(item.gate),
                        }
                        for item in evaluated
                    ],
                },
                self.ledger_path,
            )
            return MCKCycleResult(
                core_identity_id=frame.core_identity_id,
                body_id=frame.body_id,
                frame_id=frame.frame_id,
                edge_model_id=perception.edge_model_id,
                stages=STAGES[:6],
                possibilities_considered=len(possibilities),
                selected_action_id=None,
                gate_decision="HOLD",
                postcondition_decision=None,
                knowledge_promoted=False,
                ledger_record_hash=record["record_hash"],
                notes=("no action passed BODY_ACTION_GATE",),
            )

        candidate = selected.candidate
        trajectory = self.executor(candidate)
        observer = self.observer_factory(candidate)
        evidence = verify_state_change(
            action=candidate.action_id,
            trajectory_success=trajectory.success,
            trajectory_signal=trajectory.signal,
            expected_state=candidate.expected_state,
            observer=observer,
            postcondition_source=candidate.postcondition_source,
            mode="AUTHORITATIVE" if observer is not None else "UNAVAILABLE",
        )
        postcondition = promotion_decision(evidence)
        knowledge_promoted = postcondition == "VERIFIED_POSTCONDITION"

        record = append_ledger_record(
            "body_mck_experience",
            {
                "core_identity_id": frame.core_identity_id,
                "body_id": frame.body_id,
                "frame_id": frame.frame_id,
                "edge_model_id": perception.edge_model_id,
                "matter": {
                    "sensor_integrity": frame.integrity_ok,
                    "observations": dict(frame.observations),
                    "action": asdict(candidate),
                    "trajectory": asdict(trajectory),
                },
                "reflection": {
                    "self_state": dict(reflection.self_state),
                    "uncertainties": list(perception.uncertainties),
                    "contradictions": list(perception.contradictions),
                    "verification": asdict(selected.verification),
                    "gate": asdict(selected.gate),
                },
                "knowledge": {
                    "postcondition": asdict(evidence),
                    "postcondition_decision": postcondition,
                    "promoted": knowledge_promoted,
                    "rule": (
                        "verified experience may become knowledge candidate"
                        if knowledge_promoted
                        else "experience retained but not promoted"
                    ),
                },
            },
            self.ledger_path,
        )

        return MCKCycleResult(
            core_identity_id=frame.core_identity_id,
            body_id=frame.body_id,
            frame_id=frame.frame_id,
            edge_model_id=perception.edge_model_id,
            stages=STAGES,
            possibilities_considered=len(possibilities),
            selected_action_id=candidate.action_id,
            gate_decision="ALLOW",
            postcondition_decision=postcondition,
            knowledge_promoted=knowledge_promoted,
            ledger_record_hash=record["record_hash"],
            notes=(),
        )
