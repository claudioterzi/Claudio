import unittest

from typesafe_sister.redfrag import assess_redfrag_cluster


class TestRedFragCLM(unittest.TestCase):
    def test_verified_duplicate_collapses_active_payload_to_canon_pointer_only(self):
        cluster = {"id": "C01", "name": "Anima di Raffaello", "source_count": 2,
                   "content_hashes": ["sha256:same", "sha256:same"],
                   "provenance": ["drive:file-a", "github:file-b"],
                   "canonical_source": "drive:file-a", "same_topic": True}
        result = assess_redfrag_cluster(cluster)
        self.assertEqual(result["status"], "evaluated")
        self.assertEqual(result["semantic_class"], "DUPLICATE")
        self.assertEqual(result["action"], "LINK_TO_CANON")
        self.assertTrue(result["source_preserved"])
        self.assertEqual(result["physical_deletions"], 0)

    def test_divergent_versions_are_never_silently_merged(self):
        cluster = {"id": "C03", "name": "Il cerchio R3", "source_count": 3,
                   "content_hashes": ["sha256:a", "sha256:b", "sha256:c"],
                   "provenance": ["drive:a", "drive:b", "github:c"],
                   "same_topic": True, "semantic_divergence": True, "divergence_evidence": True}
        result = assess_redfrag_cluster(cluster)
        self.assertEqual(result["semantic_class"], "CONFLICT")
        self.assertEqual(result["action"], "KEEP_DISTINCT_POINTERS")
        self.assertEqual(result["physical_deletions"], 0)

    def test_duplicate_without_recoverable_provenance_is_quarantined(self):
        cluster = {"id": "C04", "name": "Incomplete duplicate", "source_count": 2,
                   "content_hashes": ["sha256:same", "sha256:same"],
                   "provenance": ["only-one-pointer"], "canonical_source": "only-one-pointer"}
        result = assess_redfrag_cluster(cluster)
        self.assertEqual(result["semantic_class"], "DUPLICATE")
        self.assertEqual(result["action"], "QUARANTINE_REVIEW")

    def test_canonical_invariant_stays_active(self):
        cluster = {"id": "C05", "name": "RRR invariant", "source_count": 1,
                   "content_hashes": ["sha256:x"], "provenance": ["github:canon"],
                   "canonical_source": "github:canon", "canonical_invariant": True}
        result = assess_redfrag_cluster(cluster)
        self.assertEqual(result["semantic_class"], "CORE")
        self.assertEqual(result["action"], "KEEP_ACTIVE")

    def test_closed_catalog_contains_no_delete_or_overwrite_action(self):
        cases = [
            {"id": "N1", "source_count": 1, "content_hashes": ["a"], "provenance": ["p"], "active_relevance": True},
            {"id": "N2", "source_count": 1, "content_hashes": ["b"], "provenance": ["q"], "superseded": True},
            {"id": "N3", "source_count": 1, "content_hashes": ["c"], "provenance": ["r"]},
        ]
        for case in cases:
            result = assess_redfrag_cluster(case)
            self.assertNotIn("DELETE", result["action"])
            self.assertNotIn("OVERWRITE", result["action"])
            self.assertEqual(result["physical_deletions"], 0)


if __name__ == "__main__":
    unittest.main()
