import unittest

from sdq1.evidence_graph import (
    EvidenceEdge,
    EvidenceGraph,
    EvidenceRecord,
    record_from_state_verification,
)


def record(
    record_id,
    version,
    claim,
    *,
    state="IPOTESI",
    evidence_type="DOCUMENT",
    source="test",
    evidence_ref="test://evidence",
    created_at="2026-09-21T00:00:00+00:00",
):
    return EvidenceRecord(
        record_id=record_id,
        version=version,
        claim=claim,
        state=state,
        source=source,
        source_version=None,
        evidence_type=evidence_type,
        evidence_ref=evidence_ref,
        falsifier="find contrary authoritative evidence",
        created_at=created_at,
    )


class EvidenceGraphTests(unittest.TestCase):
    def test_model_output_alone_cannot_be_fact(self):
        graph = EvidenceGraph()
        with self.assertRaises(ValueError):
            graph.add_record(
                record("C1", "1", "claim", state="FATTO", evidence_type="MODEL_OUTPUT")
            )

    def test_append_only_collision_is_rejected(self):
        graph = EvidenceGraph()
        graph.add_record(record("C1", "1", "first"))
        with self.assertRaises(ValueError):
            graph.add_record(record("C1", "1", "silently rewritten"))

    def test_distinct_versions_are_preserved(self):
        graph = EvidenceGraph()
        graph.add_record(record("C1", "1", "first"))
        graph.add_record(record("C1", "2", "second", created_at="2026-09-21T01:00:00+00:00"))
        history = graph.claim_history("C1")
        self.assertEqual([item.version for item in history], ["1", "2"])
        self.assertEqual([item.claim for item in history], ["first", "second"])

    def test_inferred_support_never_enters_promotion_support(self):
        graph = EvidenceGraph()
        source_key = graph.add_record(record("E1", "1", "heuristic similarity"))
        target_key = graph.add_record(record("C1", "1", "candidate claim"))
        graph.add_edge(EvidenceEdge(
            edge_id="edge-inferred",
            source_key=source_key,
            target_key=target_key,
            relation="SUPPORTS",
            basis="INFERRED",
            rationale="R3_COLLATE_ALL lexical relation",
            created_at="2026-09-21T00:00:00+00:00",
        ))
        self.assertEqual(graph.promotion_support(target_key), [])

    def test_explicit_test_can_enter_promotion_support(self):
        graph = EvidenceGraph()
        source_key = graph.add_record(
            record("T1", "1", "test passed", state="FATTO", evidence_type="TEST")
        )
        target_key = graph.add_record(record("C1", "1", "candidate claim"))
        edge = EvidenceEdge(
            edge_id="edge-test",
            source_key=source_key,
            target_key=target_key,
            relation="TESTS",
            basis="EXPLICIT",
            rationale="controlled falsifier",
            created_at="2026-09-21T00:00:00+00:00",
        )
        graph.add_edge(edge)
        self.assertEqual(graph.promotion_support(target_key), [edge])

    def test_conflicting_claims_are_preserved_not_overwritten(self):
        graph = EvidenceGraph()
        a = graph.add_record(record("C1", "1", "service is active"))
        b = graph.add_record(record("C2", "1", "service is not active"))
        edge = EvidenceEdge(
            edge_id="conflict-1",
            source_key=a,
            target_key=b,
            relation="CONTRADICTS",
            basis="EXPLICIT",
            rationale="same service, incompatible authoritative observations",
            created_at="2026-09-21T00:00:00+00:00",
        )
        graph.add_edge(edge)
        self.assertEqual(graph.conflicts(), [edge])
        self.assertEqual(len(graph.export()["records"]), 2)

    def test_authoritative_r3_007_match_becomes_fact(self):
        evidence = {
            "trajectory_success": True,
            "verification_mode": "AUTHORITATIVE",
            "state_match": True,
            "error": None,
            "verification_time": "2026-09-21T00:00:00+00:00",
        }
        item = record_from_state_verification(
            record_id="STATE-1",
            version="1",
            claim="requested state exists",
            evidence=evidence,
            source="R3-007",
            evidence_ref="run://1",
            falsifier="authoritative reread differs",
        )
        self.assertEqual(item.state, "FATTO")
        self.assertEqual(item.evidence_type, "AUTHORITATIVE_STATE")

    def test_proxy_r3_007_match_remains_hypothesis(self):
        evidence = {
            "trajectory_success": True,
            "verification_mode": "PROXY",
            "state_match": True,
            "error": None,
            "verification_time": "2026-09-21T00:00:00+00:00",
        }
        item = record_from_state_verification(
            record_id="STATE-2",
            version="1",
            claim="requested state exists",
            evidence=evidence,
            source="R3-007",
            evidence_ref="run://2",
            falsifier="authoritative reread differs",
        )
        self.assertEqual(item.state, "IPOTESI")
        self.assertNotEqual(item.evidence_type, "AUTHORITATIVE_STATE")

    def test_export_hash_is_deterministic_for_same_graph(self):
        def build():
            graph = EvidenceGraph()
            a = graph.add_record(record("A", "1", "alpha"))
            b = graph.add_record(record("B", "1", "beta"))
            graph.add_edge(EvidenceEdge(
                edge_id="related",
                source_key=a,
                target_key=b,
                relation="RELATED",
                basis="INFERRED",
                rationale="structural sensor",
                created_at="2026-09-21T00:00:00+00:00",
            ))
            return graph.export()

        one = build()
        two = build()
        self.assertEqual(one["graph_sha256"], two["graph_sha256"])


if __name__ == "__main__":
    unittest.main()
