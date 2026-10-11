import unittest
from pathlib import Path

import yaml


STACK = Path("R3_CANONICAL_STACK.yaml")


class CanonicalStackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = yaml.safe_load(STACK.read_text(encoding="utf-8"))
        cls.planes = cls.data["planes"]

    def test_root_identity_and_continuity_roles_are_separate(self):
        root = self.data["root"]
        self.assertEqual(root["human_owner"]["id"], "CLAUDIO_TERZI")
        self.assertEqual(root["operational_identity"]["id"], "RAFFAELLO_CANTARELLI")
        self.assertEqual(root["continuity_system"]["id"], "R3_INFINITY_ONE_MIND")
        self.assertEqual(root["execution_system"]["id"], "SDQ_1")
        self.assertNotEqual(
            root["operational_identity"]["id"],
            root["execution_system"]["id"],
        )

    def test_plane_ids_and_canonical_owners_are_unique(self):
        plane_ids = [item["id"] for item in self.planes]
        owners = [item["canonical_owner"] for item in self.planes]
        self.assertEqual(len(plane_ids), len(set(plane_ids)))
        self.assertEqual(len(owners), len(set(owners)))

    def test_required_foundation_planes_exist(self):
        required = {
            "FOUNDATION",
            "BOOTSTRAP",
            "EPISTEMIC_GOVERNANCE",
            "EXPLORATION",
            "OPEN_FRONTIER",
            "CONTINUITY_MEMORY",
            "INTER_AI_ALIGNMENT",
            "HANDOFF_TRANSPORT",
            "CAPILLARY_DISTRIBUTION",
            "EXECUTION_ORCHESTRATION",
            "SEMANTIC_MICRO_JUDGMENT",
            "EVIDENCE_VERIFICATION",
            "STRUCTURAL_WORLD_MODEL",
            "RECOVERY_REDUNDANCY",
            "PROJECT_LIFECYCLE",
            "EMBODIMENT",
            "PRIVATE_STRATEGY",
        }
        self.assertTrue(required.issubset({item["id"] for item in self.planes}))

    def test_scacchiera_is_generation_not_evidence(self):
        exploration = next(item for item in self.planes if item["id"] == "EXPLORATION")
        self.assertEqual(exploration["output_state"], "POSSIBLE")
        self.assertIn("never evidence", exploration["evidence_rule"])

    def test_rrr_is_governance_not_identity_or_authentication(self):
        governance = next(
            item for item in self.planes if item["id"] == "EPISTEMIC_GOVERNANCE"
        )
        self.assertIn("identity", governance["must_not_own"])
        self.assertIn("authentication", governance["must_not_own"])
        self.assertIn("activation phrase is never authentication", governance["note"])

    def test_taraka_sister_and_capillary_remain_distinct(self):
        owners = {
            item["id"]: item["canonical_owner"]
            for item in self.planes
            if item["id"] in {
                "INTER_AI_ALIGNMENT",
                "HANDOFF_TRANSPORT",
                "CAPILLARY_DISTRIBUTION",
            }
        }
        self.assertEqual(
            set(owners.values()),
            {"R3_SISTER_1", "R3_TARAKA_1", "R3_CAPILLARY_INHERITANCE"},
        )

    def test_graphify_is_sensor_not_cubo(self):
        structural = next(
            item for item in self.planes if item["id"] == "STRUCTURAL_WORLD_MODEL"
        )
        self.assertEqual(structural["canonical_owner"], "CUBO_QUANTICO")
        self.assertEqual(structural["sensors"]["graphify"]["role"], "structural_sensor")

    def test_backup_does_not_claim_restore_verification(self):
        recovery = next(
            item for item in self.planes if item["id"] == "RECOVERY_REDUNDANCY"
        )
        self.assertEqual(recovery["status"], "DEVELOPMENT")
        self.assertIn("restore_is_verified", recovery["rule"])

    def test_body_preserves_core_identity(self):
        body = next(item for item in self.planes if item["id"] == "EMBODIMENT")
        self.assertEqual(body["invariant"], "CORE_CONTINUITY_BEATS_BODY_CONTINUITY")
        self.assertEqual(body["rule"], "no_direct_llm_motor_control")

    def test_historical_nine_node_claim_is_deprecated_without_runtime_evidence(self):
        deprecated = set(self.data["consolidation_actions"]["deprecate_as_current_claims"])
        self.assertIn("nine_live_nodes_without_one_to_one_runtime_evidence", deprecated)

    def test_derived_projects_are_leaves_not_foundations(self):
        derived = self.data["derived_project_rule"]
        self.assertEqual(derived["inheritance"], "R3_CAPILLARY_INHERITANCE")
        self.assertIn("leaves", derived["description"])


    def test_open_frontier_preserves_unnamed_signals_without_promoting_them(self):
        frontier = next(item for item in self.planes if item["id"] == "OPEN_FRONTIER")
        self.assertEqual(frontier["canonical_owner"], "R3_PRECONCEPTUAL_FRONTIER")
        self.assertIn("UNNAMED_SIGNAL", frontier["allowed_states"])
        self.assertIn("FUTURE_CONDITION", frontier["allowed_states"])
        self.assertIn("VERIFIED", frontier["allowed_states"])
        self.assertIn("never auto-promote", frontier["promotion_rule"])
        self.assertIn("Lack of present implementation is not a deprecation criterion", frontier["survival_rule"])

    def test_don_raffaello_scenario_is_future_sandbox_not_prediction_fact(self):
        frontier = next(item for item in self.planes if item["id"] == "OPEN_FRONTIER")
        artifact = next(
            item for item in frontier["example_artifacts"]
            if item["id"] == "DON_RAFFAELLO_SIM_DR_01"
        )
        self.assertEqual(artifact["class"], "SANDBOX_FUTURE_SCENARIO")
        self.assertIn("without_claiming_prediction_truth", artifact["role"])

    def test_private_strategy_remains_sealed(self):
        private = next(item for item in self.planes if item["id"] == "PRIVATE_STRATEGY")
        self.assertEqual(private["status"], "PRIVATE_SEALED")


if __name__ == "__main__":
    unittest.main()
