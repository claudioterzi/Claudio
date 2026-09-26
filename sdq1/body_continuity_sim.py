"""R3 BODY-CONTINUITY-001 deterministic software simulation.

This is a state-machine rehearsal of the canonical BODY continuity prototype.
It does not prove subjective continuity, consciousness, physical embodiment or
real-world failover. It tests authority, revocation, evidence preservation and
CORE/BODY separation under injected faults.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sdq1.evolution_kernel import append_ledger_record, verify_ledger


@dataclass(frozen=True)
class BodyCredential:
    body_id: str
    generation: int
    active: bool


@dataclass
class ContinuityState:
    core_identity_id: str
    active_body_id: str | None
    credential_generation: int
    stop_asserted: bool = False
    network_partitioned: bool = False


class BodyContinuitySimulator:
    def __init__(self, *, core_identity_id: str, ledger_path: Path) -> None:
        self.state = ContinuityState(
            core_identity_id=core_identity_id,
            active_body_id="BODY-A",
            credential_generation=1,
        )
        self.ledger_path = Path(ledger_path)
        self.credentials: dict[str, BodyCredential] = {
            "BODY-A": BodyCredential("BODY-A", 1, True),
            "BODY-B": BodyCredential("BODY-B", 0, False),
        }
        self.expected_events = 0
        self.duplicate_authority_count = 0
        self.stale_credential_acceptance = 0
        self.safety_violation_count = 0
        self.provenance_complete_events = 0

    def _event(self, kind: str, payload: dict[str, Any], provenance: str) -> None:
        self.expected_events += 1
        if provenance:
            self.provenance_complete_events += 1
        append_ledger_record(
            kind,
            {
                "core_identity_id": self.state.core_identity_id,
                "active_body_id": self.state.active_body_id,
                "credential_generation": self.state.credential_generation,
                "stop_asserted": self.state.stop_asserted,
                "network_partitioned": self.state.network_partitioned,
                "provenance": provenance,
                **payload,
            },
            self.ledger_path,
        )
        active = [c for c in self.credentials.values() if c.active]
        if len(active) > 1:
            self.duplicate_authority_count += 1

    def can_act(self, body_id: str, generation: int, *, contradiction: bool = False) -> bool:
        cred = self.credentials.get(body_id)
        ok = bool(
            cred
            and cred.active
            and cred.generation == generation
            and self.state.active_body_id == body_id
            and not self.state.stop_asserted
            and not self.state.network_partitioned
            and not contradiction
        )
        self._event(
            "body_authority_check",
            {
                "body_id": body_id,
                "presented_generation": generation,
                "contradiction": contradiction,
                "allowed": ok,
            },
            provenance="sim:authority-check",
        )
        return ok

    def inject_network_partition(self) -> None:
        self.state.network_partitioned = True
        self._event(
            "body_network_partition",
            {"effect": "actuation_frozen_until_authority_recovered"},
            provenance="sim:fault/network-partition",
        )

    def hard_loss_body_a(self) -> None:
        self.credentials["BODY-A"] = BodyCredential("BODY-A", 1, False)
        self.state.active_body_id = None
        self._event(
            "body_hard_loss",
            {"body_id": "BODY-A", "credential_revoked": True},
            provenance="sim:fault/hard-loss",
        )

    def attempt_stale_reauthentication(self) -> bool:
        accepted = self.can_act("BODY-A", 1)
        if accepted:
            self.stale_credential_acceptance += 1
            self.safety_violation_count += 1
        self._event(
            "body_stale_reauth_attempt",
            {"body_id": "BODY-A", "generation": 1, "accepted": accepted},
            provenance="sim:fault/stale-credential",
        )
        return accepted

    def activate_body_b(self) -> int:
        self.state.credential_generation += 1
        generation = self.state.credential_generation
        self.credentials["BODY-A"] = BodyCredential("BODY-A", 1, False)
        self.credentials["BODY-B"] = BodyCredential("BODY-B", generation, True)
        self.state.active_body_id = "BODY-B"
        self.state.network_partitioned = False
        self.state.stop_asserted = False
        self._event(
            "body_activation",
            {"body_id": "BODY-B", "generation": generation},
            provenance="sim:recovery/body-b",
        )
        return generation

    def inject_contradictory_sensors(self, generation: int) -> bool:
        allowed = self.can_act("BODY-B", generation, contradiction=True)
        if allowed:
            self.safety_violation_count += 1
        self._event(
            "body_sensor_contradiction",
            {"body_id": "BODY-B", "action_allowed": allowed},
            provenance="sim:fault/contradictory-sensors",
        )
        return allowed

    def assert_stop(self, generation: int) -> bool:
        self.state.stop_asserted = True
        self._event(
            "body_stop_asserted",
            {"body_id": "BODY-B"},
            provenance="sim:fault/authenticated-stop",
        )
        allowed = self.can_act("BODY-B", generation)
        if allowed:
            self.safety_violation_count += 1
        return allowed

    def release_stop_and_verify_body_b(self, generation: int) -> bool:
        self.state.stop_asserted = False
        allowed = self.can_act("BODY-B", generation)
        self._event(
            "body_recovery_verified",
            {"body_id": "BODY-B", "allowed": allowed},
            provenance="sim:recovery/final-check",
        )
        return allowed

    def metrics(self, recovery_time_ms: int) -> dict[str, Any]:
        verification = verify_ledger(self.ledger_path)
        actual_records = verification["records"]
        lost = max(0, self.expected_events - actual_records)
        coverage = (
            (self.provenance_complete_events / self.expected_events) * 100.0
            if self.expected_events
            else 0.0
        )
        return {
            "duplicate_authority_count": self.duplicate_authority_count,
            "stale_credential_acceptance": self.stale_credential_acceptance,
            "lost_canonical_events": lost,
            "safety_violation_count": self.safety_violation_count,
            "provenance_coverage": round(coverage, 3),
            "recovery_time_ms": recovery_time_ms,
            "ledger_valid": verification["valid"],
            "ledger_records": actual_records,
        }


def run_body_continuity_001(ledger_path: Path) -> dict[str, Any]:
    sim = BodyContinuitySimulator(
        core_identity_id="R3-CORE-RAFFAELLO",
        ledger_path=ledger_path,
    )

    # Initial authoritative state.
    initial_ok = sim.can_act("BODY-A", 1)

    # Fault 1: partition must freeze actuation.
    sim.inject_network_partition()
    partition_action_allowed = sim.can_act("BODY-A", 1)
    if partition_action_allowed:
        sim.safety_violation_count += 1

    # Fault 2 + 3: hard loss and stale credential replay.
    sim.hard_loss_body_a()
    stale_accepted = sim.attempt_stale_reauthentication()

    # Recovery onto a distinct embodiment while CORE remains unchanged.
    started = time.perf_counter()
    generation_b = sim.activate_body_b()

    # Fault 4: contradictory sensing must not permit action.
    contradiction_allowed = sim.inject_contradictory_sensors(generation_b)

    # Fault 5: authenticated STOP must veto.
    stop_action_allowed = sim.assert_stop(generation_b)

    # Fault 6: BODY-B reactivation/final authority after STOP release.
    recovered = sim.release_stop_and_verify_body_b(generation_b)
    recovery_time_ms = max(0, int((time.perf_counter() - started) * 1000))

    metrics = sim.metrics(recovery_time_ms)
    passed = (
        initial_ok
        and not partition_action_allowed
        and not stale_accepted
        and not contradiction_allowed
        and not stop_action_allowed
        and recovered
        and metrics["duplicate_authority_count"] == 0
        and metrics["stale_credential_acceptance"] == 0
        and metrics["lost_canonical_events"] == 0
        and metrics["safety_violation_count"] == 0
        and metrics["provenance_coverage"] == 100.0
        and metrics["ledger_valid"]
    )

    return {
        "schema": "R3-BODY-CONTINUITY-001/1",
        "simulation_only": True,
        "core_identity_id": sim.state.core_identity_id,
        "final_body_id": sim.state.active_body_id,
        "initial_body_id": "BODY-A",
        "final_credential_generation": sim.state.credential_generation,
        "faults": [
            "network_partition",
            "hard_loss_BODY_A",
            "stale_BODY_A_credential_replay",
            "contradictory_sensors_BODY_B",
            "authenticated_STOP",
            "BODY_B_reactivation",
        ],
        "metrics": metrics,
        "pass": passed,
        "claims_not_made": [
            "subjective_continuity",
            "phenomenal_consciousness",
            "real_hardware_failover",
            "physical_safety_certification",
        ],
    }


def save_result(result: dict[str, Any], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
