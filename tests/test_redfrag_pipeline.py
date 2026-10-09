import unittest
import hashlib
from unittest.mock import patch

from typesafe_sister import redfrag_pipeline
from typesafe_sister.redfrag_pipeline import MAX_CONTENT_CHARS, build_clusters, plan_context


class TestRedFragPipeline(unittest.TestCase):
    def test_context_planning_fingerprints_each_source_once(self):
        records = [{"id": str(i), "content": "context", "provenance": f"test:{i}"}
                   for i in range(10)]
        with patch.object(redfrag_pipeline, "_fingerprint", wraps=redfrag_pipeline._fingerprint) as digest:
            plan_context(records)
        self.assertEqual(digest.call_count, len(records))

    def test_supplied_hash_must_match_source(self):
        record = {"id": "a", "content": "actual", "provenance": "test:a",
                  "content_hash": "sha256:" + "0" * 64}
        for operation in (build_clusters, plan_context):
            with self.assertRaises(ValueError):
                operation([record])

    def test_distinct_tails_cannot_be_exact_duplicates(self):
        prefix = "x" * MAX_CONTENT_CHARS
        records = [{"id": tail, "logical_id": "same", "content": prefix + tail,
                    "provenance": "test:" + tail, "canonical": True}
                   for tail in ("a", "b")]
        cluster = build_clusters(records)[0]
        self.assertEqual(len(set(cluster["content_hashes"])), 2)
        result = plan_context(records)
        self.assertFalse(result["plans"][0]["evidence"]["exact_duplicate"])
        self.assertEqual(records[0]["content"], prefix + "a")

    def test_full_hash_preserved_and_truncated_core_is_not_activated(self):
        content = "x" * (MAX_CONTENT_CHARS + 1)
        expected = "sha256:" + hashlib.sha256(content.encode()).hexdigest()
        record = {"id": "a", "content": content, "provenance": "test:a",
                  "content_hash": expected, "canonical_invariant": True}
        result = plan_context([record])
        self.assertEqual(result["active_records"], [])
        self.assertEqual(result["quarantined"][0]["sha256"], expected)
        self.assertEqual(build_clusters([record])[0]["content_hashes"], [expected])

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
