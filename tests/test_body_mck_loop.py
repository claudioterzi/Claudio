import json
import tempfile
import unittest
from pathlib import Path

from sdq1.body_mck_loop import (
    ActionCandidate,
    ActionTrajectory,
    BodyMCKLoop,
    CandidateVerification,
    PerceptionState,
    ReflectionState,
    SensorFrame,
    body_action_gate,
)
from sdq1.evolution_kernel import verify_ledger


def frame(**overrides):
    data = dict(
        core_identity_id="R3-CORE-1",
        body_id="BODY-A",
        frame_id="FRAME-001",
        observations={"target": "cup", "distance_cm": 30},
        provenance_refs=("sensor:camera-a",),
        integrity_ok=True,
    )
    data.update(overrides)
    return SensorFrame(**data)


def perception(**overrides):
    data = dict(
        edge_model_id="edge-perception-A",
        facts={"target": "cup", "distance_cm": 30},
        uncertainties=(),
        contradictions=(),
        provenance_refs=("sensor:camera-a",),
    )
    data.update(overrides)
    return PerceptionState(**data)


def reflection(**overrides):
    data = dict(
        core_identity_id="R3-CORE-1",
        body_id="BODY-A",
        self_state={"battery": "ok", "balance": "stable"},
        allowed_authority_scopes=frozenset({"hand.low_risk", "posture.safe"}),
        stop_asserted=False,
        phenomenal_consciousness_claimed=False,
    )
    data.update(overrides)
    return ReflectionState(**data)


def candidate(**overrides):
    data = dict(
        action_id="A-REACH",
        intent="move hand toward target",
        expected_state={"hand": "near_cup"},
        postcondition_source="body-state:hand",
        authority_scope="hand.low_risk",
        risk="low",
        source_kind="MODEL",
        execution_class="CORE_ACTION",
        reversible=True,
        preregistered_ref=None,
        priority=10,
    )
    data.update(overrides)
    return ActionCandidate(**data)


def verification(**overrides):
    data = dict(
        accepted=True,
        safety_ok=True,
        authority_ok=True,
        independent_of_origin=True,
        evidence_refs=("test:independent-verifier",),
        reasons=(),
    )
    data.update(overrides)
    return CandidateVerification(**data)


class BodyMCKGateTests(unittest.TestCase):
    def test_model_action_without_independent_verification_is_blocked(self):
        gate = body_action_gate(
            frame(),
            perception(),
            reflection(),
            candidate(),
            verification(independent_of_origin=False),
        )
        self.assertFalse(gate.allowed)
        self.assertIn("model-origin action lacks independent verification", gate.reasons)

    def test_stop_overrides_verified_action(self):
        gate = body_action_gate(
            frame(),
            perception(),
            reflection(stop_asserted=True),
            candidate(),
            verification(),
        )
        self.assertFalse(gate.allowed)
        self.assertIn("authenticated STOP asserted", gate.reasons)

    def test_sensor_contradiction_blocks_physical_action(self):
        gate = body_action_gate(
            frame(),
            perception(contradictions=("camera says clear; tactile says obstacle",)),
            reflection(),
            candidate(),
            verification(),
        )
        self.assertFalse(gate.allowed)
        self.assertIn("sensor/perception contradiction unresolved", gate.reasons)

    def test_high_risk_action_is_not_autonomously_executed(self):
        gate = body_action_gate(
            frame(),
            perception(),
            reflection(),
            candidate(risk="high"),
            verification(),
        )
        self.assertFalse(gate.allowed)
        self.assertIn("high/critical physical action requires a higher external gate", gate.reasons)

    def test_edge_reflex_must_be_deterministic_and_preregistered(self):
        bad = body_action_gate(
            frame(),
            perception(),
            reflection(),
            candidate(
                action_id="REFLEX-1",
                execution_class="EDGE_REFLEX",
                source_kind="MODEL",
                preregistered_ref=None,
            ),
            verification(),
        )
        self.assertFalse(bad.allowed)
        self.assertIn("EDGE_REFLEX cannot originate from a model", bad.reasons)
        self.assertIn("EDGE_REFLEX requires preregistration", bad.reasons)

        good = body_action_gate(
            frame(),
            perception(),
            reflection(),
            candidate(
                action_id="REFLEX-2",
                execution_class="EDGE_REFLEX",
                source_kind="DETERMINISTIC",
                preregistered_ref="body-policy:reflex-2",
            ),
            verification(),
        )
        self.assertTrue(good.allowed)


class BodyMCKLoopTests(unittest.TestCase):
    def make_loop(self, root: Path, *, perceived=None, possibilities=None, verify=None,
                  executor=None, observer_factory=None):
        perceived = perceived or perception()
        possibilities = possibilities or [candidate()]
        verify = verify or verification()
        executor = executor or (lambda action: ActionTrajectory(True, "simulated actuator accepted"))
        observer_factory = observer_factory or (lambda action: lambda: action.expected_state)

        return BodyMCKLoop(
            perceiver=lambda sensor_frame: perceived,
            possibility_generator=lambda p, r: possibilities,
            verifier=lambda c, p, r: verify,
            executor=executor,
            observer_factory=observer_factory,
            ledger_path=root / "body-ledger.jsonl",
        )

    def test_verified_cycle_promotes_experience_to_knowledge_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []
            loop = self.make_loop(
                root,
                executor=lambda action: calls.append(action.action_id)
                or ActionTrajectory(True, "actuator-ok"),
            )
            result = loop.run(frame(), reflection())

            self.assertEqual(calls, ["A-REACH"])
            self.assertEqual(result.selected_action_id, "A-REACH")
            self.assertEqual(result.gate_decision, "ALLOW")
            self.assertEqual(result.postcondition_decision, "VERIFIED_POSTCONDITION")
            self.assertTrue(result.knowledge_promoted)
            self.assertEqual(
                result.stages,
                (
                    "SENSE", "PERCEIVE", "REFLECT", "IMAGINE", "VERIFY",
                    "BODY_ACTION_GATE", "ACT", "OBSERVE", "LEARN", "EVOLVE_CANDIDATE",
                ),
            )
            self.assertTrue(verify_ledger(root / "body-ledger.jsonl")["valid"])

    def test_success_signal_without_authoritative_postcondition_does_not_learn(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = self.make_loop(root, observer_factory=lambda action: None)
            result = loop.run(frame(), reflection())

            self.assertEqual(result.postcondition_decision, "UNVERIFIED_POSTCONDITION")
            self.assertFalse(result.knowledge_promoted)

            record = json.loads((root / "body-ledger.jsonl").read_text().splitlines()[-1])
            self.assertFalse(record["payload"]["knowledge"]["promoted"])

    def test_wrong_persisted_state_is_retained_as_failure_not_knowledge(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = self.make_loop(
                root,
                observer_factory=lambda action: lambda: {"hand": "wrong_place"},
            )
            result = loop.run(frame(), reflection())
            self.assertEqual(result.postcondition_decision, "STATE_MISMATCH")
            self.assertFalse(result.knowledge_promoted)

    def test_no_action_executes_when_all_candidates_fail_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []
            loop = self.make_loop(
                root,
                perceived=perception(contradictions=("unsafe disagreement",)),
                possibilities=[candidate(), candidate(action_id="A-2", priority=5)],
                executor=lambda action: calls.append(action.action_id)
                or ActionTrajectory(True, "should-not-run"),
            )
            result = loop.run(frame(), reflection())

            self.assertEqual(calls, [])
            self.assertIsNone(result.selected_action_id)
            self.assertEqual(result.gate_decision, "HOLD")
            self.assertFalse(result.knowledge_promoted)

    def test_scacchiera_selects_allowed_branch_not_first_unsafe_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe = candidate(action_id="A-HIGH", risk="high", priority=100)
            safe = candidate(action_id="A-SAFE", risk="low", priority=10)
            calls = []
            loop = self.make_loop(
                root,
                possibilities=[unsafe, safe],
                executor=lambda action: calls.append(action.action_id)
                or ActionTrajectory(True, "ok"),
            )
            result = loop.run(frame(), reflection())

            self.assertEqual(calls, ["A-SAFE"])
            self.assertEqual(result.selected_action_id, "A-SAFE")
            self.assertTrue(result.knowledge_promoted)

    def test_hot_swap_edge_model_does_not_change_core_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop_a = self.make_loop(root, perceived=perception(edge_model_id="MiniCPM-candidate-A"))
            result_a = loop_a.run(frame(frame_id="F-A"), reflection())

            loop_b = self.make_loop(root, perceived=perception(edge_model_id="edge-model-B"))
            result_b = loop_b.run(frame(frame_id="F-B"), reflection())

            self.assertEqual(result_a.core_identity_id, "R3-CORE-1")
            self.assertEqual(result_b.core_identity_id, "R3-CORE-1")
            self.assertNotEqual(result_a.edge_model_id, result_b.edge_model_id)
            self.assertTrue(verify_ledger(root / "body-ledger.jsonl")["valid"])

    def test_body_swap_keeps_core_identity_but_requires_matching_reflection_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = self.make_loop(root)
            result = loop.run(
                frame(body_id="BODY-B", frame_id="F-B"),
                reflection(body_id="BODY-B"),
            )
            self.assertEqual(result.core_identity_id, "R3-CORE-1")
            self.assertEqual(result.body_id, "BODY-B")
            self.assertTrue(result.knowledge_promoted)


if __name__ == "__main__":
    unittest.main()
