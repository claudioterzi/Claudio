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


def verification_evidence(
    *,
    mode="AUTHORITATIVE",
    expected=None,
    observed=None,
    match=True,
    error=None,
    source="filesystem:test/state.bin#read_bytes",
    observer_calls=1,
    trajectory=True,
):
    expected = {"value": "expected"} if expected is None else expected
    if observed is None and error is None:
        observed = dict(expected) if match else {"value": "different"}
    return {
        "trajectory_success": trajectory,
        "verification_mode": mode,
        "postcondition_source": source,
        "expected_state": expected,
        "observed_state": observed,
        "state_match": match,
        "verification_time": "2026-10-08T00:00:00+00:00",
        "observer_calls": observer_calls,
        "error": error,
    }


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
        evidence = verification_evidence()
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
        self.assertEqual(
            item.postcondition_source,
            "filesystem:test/state.bin#read_bytes",
        )

    def test_proxy_r3_007_match_remains_hypothesis(self):
        evidence = verification_evidence(mode="PROXY")
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
        self.assertEqual(
            item.postcondition_source,
            "filesystem:test/state.bin#read_bytes",
        )

    def test_authoritative_r3_007_mismatch_becomes_negative_fact(self):
        item = record_from_state_verification(
            record_id="STATE-3",
            version="1",
            claim="requested state exists",
            evidence=verification_evidence(match=False),
            source="R3-007",
            evidence_ref="run://3",
            falsifier="authoritative reread matches",
        )
        self.assertEqual(item.state, "FATTO")
        self.assertEqual(item.evidence_type, "AUTHORITATIVE_STATE")
        self.assertTrue(item.claim.startswith("POSTCONDITION_MISMATCH:"))
        self.assertEqual(
            item.postcondition_source,
            "filesystem:test/state.bin#read_bytes",
        )

    def test_proxy_mismatch_never_becomes_authoritative_fact(self):
        item = record_from_state_verification(
            record_id="STATE-4",
            version="1",
            claim="requested state differs",
            evidence=verification_evidence(mode="PROXY", match=False),
            source="R3-007",
            evidence_ref="run://4",
            falsifier="authoritative reread differs",
        )
        self.assertEqual(item.state, "IPOTESI")
        self.assertEqual(item.evidence_type, "OTHER")
        self.assertEqual(
            item.postcondition_source,
            "filesystem:test/state.bin#read_bytes",
        )

    def test_r3_007_evidence_requires_bound_source_and_observer(self):
        for evidence in (
            verification_evidence(source=None),
            verification_evidence(source="   "),
            verification_evidence(observer_calls=0),
        ):
            with self.subTest(evidence=evidence):
                with self.assertRaises(ValueError):
                    record_from_state_verification(
                        record_id="STATE-INVALID",
                        version="1",
                        claim="requested state exists",
                        evidence=evidence,
                        source="R3-007",
                        evidence_ref="run://invalid",
                        falsifier="authoritative reread differs",
                    )

    def test_r3_007_evidence_rejects_inconsistent_match(self):
        evidence = verification_evidence(match=True, observed={"value": "different"})
        with self.assertRaises(ValueError):
            record_from_state_verification(
                record_id="STATE-INCONSISTENT",
                version="1",
                claim="requested state exists",
                evidence=evidence,
                source="R3-007",
                evidence_ref="run://inconsistent",
                falsifier="authoritative reread differs",
            )

    def test_verification_error_remains_nonfactual(self):
        item = record_from_state_verification(
            record_id="STATE-ERROR",
            version="1",
            claim="requested state exists",
            evidence=verification_evidence(
                observed=None, match=None, error="FileNotFoundError"
            ),
            source="R3-007",
            evidence_ref="run://error",
            falsifier="authoritative reread succeeds",
        )
        self.assertEqual(item.state, "IPOTESI")
        self.assertEqual(item.evidence_type, "OTHER")
        self.assertEqual(
            item.postcondition_source,
            "filesystem:test/state.bin#read_bytes",
        )

    def test_direct_authoritative_state_requires_postcondition_source(self):
        graph = EvidenceGraph()
        with self.assertRaises(ValueError):
            graph.add_record(record(
                "STATE-DIRECT",
                "1",
                "state exists",
                state="FATTO",
                evidence_type="AUTHORITATIVE_STATE",
            ))

    def test_invalid_non_authoritative_source_metadata_is_rejected(self):
        graph = EvidenceGraph()
        invalid = [
            type(item)(**{
                **item.__dict__,
                "postcondition_source": source,
            })
            for item, source in (
                (
                    record("DOC", "1", "documented claim", state="IPOTESI"),
                    "filesystem:test/state.bin#read_bytes",
                ),
                (
                    record(
                        "FACT-OTHER",
                        "1",
                        "factual other claim",
                        state="FATTO",
                        evidence_type="OTHER",
                    ),
                    "filesystem:test/state.bin#read_bytes",
                ),
                (
                    record(
                        "BLANK-OTHER",
                        "1",
                        "blank observation source",
                        state="IPOTESI",
                        evidence_type="OTHER",
                    ),
                    "   ",
                ),
            )
        ]
        for item in invalid:
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    graph.add_record(item)

    def test_nonfactual_observation_source_is_metadata_not_authority(self):
        graph = EvidenceGraph()
        source_record = record(
            "OBSERVATION-ERROR",
            "1",
            "observer could not read state",
            state="IPOTESI",
            evidence_type="OTHER",
        )
        source_record = type(source_record)(**{
            **source_record.__dict__,
            "postcondition_source": "filesystem:temporary/missing.bin#read_bytes",
        })
        source_key = graph.add_record(source_record)
        target_key = graph.add_record(record("TARGET", "1", "candidate claim"))
        graph.add_edge(EvidenceEdge(
            edge_id="edge-observation-error",
            source_key=source_key,
            target_key=target_key,
            relation="TESTS",
            basis="EXPLICIT",
            rationale="failed observation preserves its attempted source",
            created_at="2026-10-09T00:00:00+00:00",
        ))

        self.assertEqual(
            graph.export()["records"][0]["postcondition_source"],
            "filesystem:temporary/missing.bin#read_bytes",
        )
        self.assertEqual(graph.promotion_support(target_key), [])

    def test_preexisting_filesystem_fixture_preserves_all_observation_sources(self):
        cases = [
            verification_evidence(
                source="filesystem:temporary/state.bin#read_bytes",
            ),
            verification_evidence(
                source="filesystem:temporary/state.bin#read_bytes",
                match=False,
            ),
            verification_evidence(
                source="filesystem:temporary/missing.bin#read_bytes",
                observed=None,
                match=None,
                error="FileNotFoundError",
            ),
        ]
        records = [
            record_from_state_verification(
                record_id=f"FS-{index}",
                version="1",
                claim=f"filesystem case {index}",
                evidence=evidence,
                source="R3-007",
                evidence_ref=f"receipt://108f3c20/{index}",
                falsifier="independent readback differs",
            )
            for index, evidence in enumerate(cases, start=1)
        ]

        self.assertEqual(
            [item.postcondition_source for item in records],
            [case["postcondition_source"] for case in cases],
        )
        self.assertEqual(
            [(item.state, item.evidence_type) for item in records],
            [
                ("FATTO", "AUTHORITATIVE_STATE"),
                ("FATTO", "AUTHORITATIVE_STATE"),
                ("IPOTESI", "OTHER"),
            ],
        )

    def test_distinct_authoritative_sources_survive_export(self):
        sources = [
            "filesystem:store-a/state.bin#read_bytes",
            "filesystem:store-b/state.bin#read_bytes",
        ]
        exports = []
        for index, source in enumerate(sources, start=1):
            graph = EvidenceGraph()
            item = record_from_state_verification(
                record_id="STATE-SOURCE",
                version="1",
                claim="requested state exists",
                evidence=verification_evidence(source=source),
                source="R3-007",
                evidence_ref="run://source",
                falsifier="authoritative reread differs",
            )
            graph.add_record(item)
            exports.append(graph.export())
        self.assertEqual(
            [item["records"][0]["postcondition_source"] for item in exports],
            sources,
        )
        self.assertNotEqual(exports[0]["graph_sha256"], exports[1]["graph_sha256"])

    def test_absent_source_preserves_legacy_schema_v1_hash(self):
        graph = EvidenceGraph()
        source_key = graph.add_record(record("A", "1", "alpha"))
        target_key = graph.add_record(record("B", "1", "beta"))
        graph.add_edge(EvidenceEdge(
            edge_id="related",
            source_key=source_key,
            target_key=target_key,
            relation="RELATED",
            basis="INFERRED",
            rationale="structural sensor",
            created_at="2026-09-21T00:00:00+00:00",
        ))

        exported = graph.export()
        self.assertEqual(
            exported["graph_sha256"],
            "e1b20336f3288dfe247803c7bd8b7856cc6d06213074a03c11aa0835bf108757",
        )
        self.assertTrue(all("postcondition_source" not in item for item in exported["records"]))
        self.assertNotIn("postcondition_source", graph.provenance_chain(target_key)["record"])

    def test_nonfactual_explicit_source_is_not_promotion_support(self):
        graph = EvidenceGraph()
        source_key = graph.add_record(
            record("E1", "1", "unverified test", state="IPOTESI", evidence_type="OTHER")
        )
        target_key = graph.add_record(record("C1", "1", "candidate claim"))
        graph.add_edge(EvidenceEdge(
            edge_id="edge-unverified-test",
            source_key=source_key,
            target_key=target_key,
            relation="TESTS",
            basis="EXPLICIT",
            rationale="explicitly linked but not factual",
            created_at="2026-10-08T00:00:00+00:00",
        ))
        self.assertEqual(graph.promotion_support(target_key), [])

    def test_unknown_record_enums_are_rejected(self):
        graph = EvidenceGraph()
        with self.assertRaises(ValueError):
            graph.add_record(record("C1", "1", "claim", state="UNKNOWN"))
        with self.assertRaises(ValueError):
            graph.add_record(record("C2", "1", "claim", evidence_type="UNKNOWN"))

    def test_unknown_edge_enums_are_rejected(self):
        graph = EvidenceGraph()
        source_key = graph.add_record(record("S", "1", "source"))
        target_key = graph.add_record(record("T", "1", "target"))
        with self.assertRaises(ValueError):
            graph.add_edge(EvidenceEdge(
                "bad-relation", source_key, target_key, "UNKNOWN", "EXPLICIT", "bad", "2026-10-08T00:00:00+00:00"
            ))
        with self.assertRaises(ValueError):
            graph.add_edge(EvidenceEdge(
                "bad-basis", source_key, target_key, "RELATED", "UNKNOWN", "bad", "2026-10-08T00:00:00+00:00"
            ))

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
