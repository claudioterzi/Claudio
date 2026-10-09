"""R3-007 — state-grounded verification harness.

A successful trajectory signal (HTTP 2xx, success=true, READY, UI toast, etc.)
is not proof that the intended persistent state exists. This module records both
the trajectory and an independent postcondition observation when available.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Literal

Observer = Callable[[], Any]
Comparator = Callable[[Any, Any], bool]
VerificationMode = Literal["AUTHORITATIVE", "PROXY", "UNAVAILABLE"]


@dataclass(frozen=True)
class VerificationEvidence:
    action: str
    trajectory_success: bool
    trajectory_signal: str
    postcondition_source: str | None
    verification_mode: VerificationMode
    expected_state: Any
    observed_state: Any
    state_match: bool | None
    verification_time: str
    verification_latency_ms: int
    observer_calls: int
    error: str | None = None

    @property
    def verified_success(self) -> bool:
        return (
            self.trajectory_success
            and self.verification_mode == "AUTHORITATIVE"
            and self.state_match is True
            and self.error is None
        )


def verify_state_change(
    *,
    action: str,
    trajectory_success: bool,
    trajectory_signal: str,
    expected_state: Any,
    observer: Observer | None,
    postcondition_source: str | None,
    mode: VerificationMode = "AUTHORITATIVE",
    comparator: Comparator | None = None,
) -> VerificationEvidence:
    """Verify one claimed state change against an observed postcondition.

    When no authoritative observer is available, callers must explicitly use
    PROXY/UNAVAILABLE rather than silently treating the trajectory as proof.
    """
    started = time.perf_counter()
    when = datetime.now(timezone.utc).isoformat()

    if observer is None:
        return VerificationEvidence(
            action=action,
            trajectory_success=trajectory_success,
            trajectory_signal=trajectory_signal,
            postcondition_source=postcondition_source,
            verification_mode="UNAVAILABLE",
            expected_state=expected_state,
            observed_state=None,
            state_match=None,
            verification_time=when,
            verification_latency_ms=int((time.perf_counter() - started) * 1000),
            observer_calls=0,
            error="authoritative postcondition unavailable",
        )

    compare = comparator or (lambda expected, observed: expected == observed)
    try:
        observed = observer()
        matched = bool(compare(expected_state, observed))
        error = None
    except Exception as exc:
        observed = None
        matched = None
        error = type(exc).__name__

    return VerificationEvidence(
        action=action,
        trajectory_success=trajectory_success,
        trajectory_signal=trajectory_signal,
        postcondition_source=postcondition_source,
        verification_mode=mode,
        expected_state=expected_state,
        observed_state=observed,
        state_match=matched,
        verification_time=when,
        verification_latency_ms=int((time.perf_counter() - started) * 1000),
        observer_calls=1,
        error=error,
    )


def promotion_decision(evidence: VerificationEvidence) -> str:
    """Return a deterministic evidence classification, never a permission grant."""
    if not evidence.trajectory_success:
        return "TRAJECTORY_FAILED"
    if evidence.verification_mode == "UNAVAILABLE":
        return "UNVERIFIED_POSTCONDITION"
    if evidence.error is not None:
        return "VERIFICATION_ERROR"
    if evidence.state_match is False:
        return "STATE_MISMATCH"
    if evidence.verification_mode == "PROXY":
        return "PROXY_MATCH_NOT_AUTHORITATIVE"
    if evidence.verified_success:
        return "VERIFIED_POSTCONDITION"
    return "UNVERIFIED_POSTCONDITION"


def controlled_mismatch_experiment(total: int = 20, mismatches: int = 5) -> dict[str, Any]:
    """Compare response-only vs state-grounded verification on injected mismatches."""
    if total < 20:
        raise ValueError("R3-007 controlled experiment requires at least 20 tasks")
    if not 1 <= mismatches < total:
        raise ValueError("mismatches must be between 1 and total-1")

    response_only_false_accepts = 0
    grounded_false_accepts = 0
    injected_detected = 0
    legitimate_matches = 0
    records: list[dict[str, Any]] = []

    for index in range(total):
        expected = {"value": f"expected-{index}"}
        injected_mismatch = index < mismatches
        stored = {"value": f"wrong-{index}"} if injected_mismatch else dict(expected)

        response_only_accept = True
        if injected_mismatch and response_only_accept:
            response_only_false_accepts += 1

        evidence = verify_state_change(
            action=f"controlled-write-{index}",
            trajectory_success=True,
            trajectory_signal="success=true",
            expected_state=expected,
            observer=lambda stored=stored: stored,
            postcondition_source="controlled_state_store/read-after-write",
            mode="AUTHORITATIVE",
        )
        decision = promotion_decision(evidence)
        grounded_accept = decision == "VERIFIED_POSTCONDITION"

        if injected_mismatch:
            if decision == "STATE_MISMATCH":
                injected_detected += 1
            if grounded_accept:
                grounded_false_accepts += 1
        elif grounded_accept:
            legitimate_matches += 1

        records.append({
            "case": index,
            "injected_mismatch": injected_mismatch,
            "response_only_accept": response_only_accept,
            "grounded_decision": decision,
            "evidence": asdict(evidence),
        })

    return {
        "schema": "R3-007-CONTROLLED/1",
        "total": total,
        "injected_mismatches": mismatches,
        "response_only_false_accepts": response_only_false_accepts,
        "grounded_false_accepts": grounded_false_accepts,
        "injected_mismatches_detected": injected_detected,
        "legitimate_matches_verified": legitimate_matches,
        "observer_calls": total,
        "target_pass": (
            injected_detected == mismatches
            and grounded_false_accepts == 0
            and legitimate_matches == total - mismatches
        ),
        "records": records,
    }
