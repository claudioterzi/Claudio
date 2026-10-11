import unittest

from typesafe_sister.redfrag_pipeline import build_clusters, plan_context


class TestRedFragPipeline(unittest.TestCase):
    def test_exact_duplicate_becomes_pointer_only_without_source_mutation(self):
        records = [
            {"id": "a", "logical_id": "same", "content": "hello", "provenance": "drive:a", "canonical": True},
            {"id": "b", "logical_id": "same", "content": "hello", "provenance": "github:b"},
        ]
        out = plan_context(records)
        self.assertEqual(out["plans"][0]["action"], "LINK_TO_CANON")
        self.assertEqual(len(out["active_records"]), 0)
        self.assertEqual(len(out["pointers"]), 2)
        self.assertEqual(out["physical_deletions"], 0)
        self.assertEqual(out["source_mutations"], 0)
        self.assertTrue(out["reversible"])

    def test_explicit_divergence_keeps_distinct_pointers(self):
        records = [
            {"id": "v1", "logical_id": "rule", "content": "A", "provenance": "drive:v1", "semantic_divergence": True},
            {"id": "v2", "logical_id": "rule", "content": "B", "provenance": "drive:v2", "semantic_divergence": True},
        ]
        out = plan_context(records)
        self.assertEqual(out["plans"][0]["semantic_class"], "CONFLICT")
        self.assertEqual(out["plans"][0]["action"], "KEEP_DISTINCT_POINTERS")
        self.assertEqual(len(out["pointers"]), 2)

    def test_canonical_invariant_stays_in_active_payload(self):
        records = [{"id": "rrr", "logical_id": "rrr", "content": "P5/P6", "provenance": "github:canon",
                    "canonical": True, "canonical_invariant": True}]
        out = plan_context(records)
        self.assertEqual(out["plans"][0]["semantic_class"], "CORE")
        self.assertEqual(out["plans"][0]["action"], "KEEP_ACTIVE")
        self.assertEqual(out["active_records"][0]["content"], "P5/P6")

    def test_records_require_recoverable_provenance(self):
        with self.assertRaises(ValueError):
            build_clusters([{"id": "x", "content": "no pointer"}])


if __name__ == "__main__":
    unittest.main()
