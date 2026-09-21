import json
import unittest
from pathlib import Path


MANIFEST = Path("R3_NODE_REALITY.json")


class NodeRealityManifestTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_schema_and_work_item(self):
        self.assertEqual(self.data["schema"], "R3_NODE_REALITY_V1")
        self.assertEqual(self.data["work_item"], "R3-006")

    def test_historical_nine_node_claim_is_not_promoted(self):
        claim = self.data["historical_nine_node_claim"]
        self.assertEqual(claim["state"], "UNRESOLVED_MAPPING")
        self.assertFalse(claim["current_one_to_one_runtime_mapping"])

    def test_adapters_are_separate_from_runtime_services(self):
        adapters = set(self.data["provider_registry"]["adapters"])
        service_ids = {item["id"] for item in self.data["observed_services"]}
        self.assertNotIn("gemini", service_ids)
        self.assertNotIn("grok", service_ids)
        self.assertIn("gemini", adapters)
        self.assertIn("grok", adapters)

    def test_discovery_hints_do_not_become_adapters(self):
        missing = set(self.data["discovery_hints"]["not_in_current_provider_registry"])
        adapters = set(self.data["provider_registry"]["adapters"])
        self.assertTrue({"Qwen", "Manus"}.issubset(missing))
        self.assertNotIn("qwen", adapters)
        self.assertNotIn("manus", adapters)

    def test_observed_storage_nodes_are_same_provider_and_not_durable(self):
        nodes = [
            item for item in self.data["observed_services"]
            if item["class"] == "R3_STORAGE_SERVICE"
        ]
        self.assertEqual(len(nodes), 2)
        self.assertEqual({item["provider"] for item in nodes}, {"Railway"})
        for node in nodes:
            self.assertEqual(node["state"], "OBSERVED_SERVICE_PROCESS")
            self.assertGreater(node["evidence"]["metrics_samples"], 0)
            self.assertGreater(node["evidence"]["current_memory_gb"], 0)
            self.assertFalse(node["evidence"]["durable_volume_observed"])

    def test_failed_runner_is_not_counted_as_node(self):
        runner = next(
            item for item in self.data["observed_services"]
            if item["id"] == "railway:r3-external-property-runner"
        )
        self.assertFalse(runner["counts_as_canonical_node"])
        self.assertEqual(runner["state"], "NOT_CURRENTLY_RUNNING")


if __name__ == "__main__":
    unittest.main()
