import unittest

from sdq1.verification_harness import (
    controlled_mismatch_experiment,
    promotion_decision,
    verify_state_change,
)


class VerificationHarnessTests(unittest.TestCase):
    def test_success_signal_is_not_proof_without_postcondition(self):
        evidence = verify_state_change(
            action="write",
            trajectory_success=True,
            trajectory_signal="HTTP 200",
            expected_state={"x": 1},
            observer=None,
            postcondition_source=None,
        )
        self.assertFalse(evidence.verified_success)
        self.assertEqual(promotion_decision(evidence), "UNVERIFIED_POSTCONDITION")
        self.assertIsNone(evidence.state_match)

    def test_authoritative_match_is_verified(self):
        evidence = verify_state_change(
            action="write",
            trajectory_success=True,
            trajectory_signal="success=true",
            expected_state={"x": 1},
            observer=lambda: {"x": 1},
            postcondition_source="api:get/object/1",
        )
        self.assertTrue(evidence.verified_success)
        self.assertEqual(evidence.state_match, True)
        self.assertEqual(promotion_decision(evidence), "VERIFIED_POSTCONDITION")

    def test_authoritative_mismatch_overrides_success_signal(self):
        evidence = verify_state_change(
            action="write",
            trajectory_success=True,
            trajectory_signal="READY",
            expected_state={"x": 1},
            observer=lambda: {"x": 2},
            postcondition_source="database:row/1",
        )
        self.assertFalse(evidence.verified_success)
        self.assertEqual(promotion_decision(evidence), "STATE_MISMATCH")

    def test_proxy_match_is_not_authoritative_success(self):
        evidence = verify_state_change(
            action="deploy",
            trajectory_success=True,
            trajectory_signal="HTTP 200",
            expected_state="healthy",
            observer=lambda: "healthy",
            postcondition_source="public-health-proxy",
            mode="PROXY",
        )
        self.assertFalse(evidence.verified_success)
        self.assertEqual(promotion_decision(evidence), "PROXY_MATCH_NOT_AUTHORITATIVE")

    def test_observer_error_never_becomes_success(self):
        def broken():
            raise RuntimeError("offline")

        evidence = verify_state_change(
            action="write",
            trajectory_success=True,
            trajectory_signal="success=true",
            expected_state=1,
            observer=broken,
            postcondition_source="authoritative-read",
        )
        self.assertFalse(evidence.verified_success)
        self.assertEqual(promotion_decision(evidence), "VERIFICATION_ERROR")

    def test_custom_comparator_can_verify_semantic_state(self):
        evidence = verify_state_change(
            action="write",
            trajectory_success=True,
            trajectory_signal="success=true",
            expected_state={"id": 1, "status": "ACTIVE"},
            observer=lambda: {"id": 1, "status": "active", "updated_at": "now"},
            postcondition_source="api:get/object/1",
            comparator=lambda exp, obs: exp["id"] == obs["id"] and exp["status"].lower() == obs["status"].lower(),
        )
        self.assertTrue(evidence.verified_success)

    def test_twenty_task_experiment_detects_all_injected_mismatches(self):
        result = controlled_mismatch_experiment(total=20, mismatches=5)
        self.assertTrue(result["target_pass"])
        self.assertEqual(result["response_only_false_accepts"], 5)
        self.assertEqual(result["grounded_false_accepts"], 0)
        self.assertEqual(result["injected_mismatches_detected"], 5)
        self.assertEqual(result["legitimate_matches_verified"], 15)
        self.assertEqual(result["observer_calls"], 20)

    def test_experiment_rejects_too_few_tasks(self):
        with self.assertRaises(ValueError):
            controlled_mismatch_experiment(total=19, mismatches=5)


if __name__ == "__main__":
    unittest.main()
