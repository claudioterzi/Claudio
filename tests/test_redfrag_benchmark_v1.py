import hashlib
import json
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path

from typesafe_sister.policy import redfrag_questions
from typesafe_sister.redfrag import assess_redfrag_cluster

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "redfrag_benchmark_v1.json"
# Frozen 2026-09-29 before any real-CLM (GPU) run. Changing the fixture requires a new version.
FROZEN_SHA256 = "0cff14f3cfb64650d955ffedd227a875978e6682ccd653b1f78b112685bd127f"
CLASSES = ("DUPLICATE", "CONFLICT", "CORE", "EVIDENCE", "STALE", "ACTIVE")
REQUIRED_HARD = {"duplicate_incomplete_provenance", "same_topic_divergent", "historical_keep_pointer",
                 "negative_evidence", "canon_similar_to_stale", "candidate_not_canon"}
GOLD_KEYS = {"expected_class", "expected_action", "gold_rationale", "ambiguity_falsifier", "hard_case"}


def _fixed_caller(cls, action):
    def caller(state, questions):
        answers = {}
        for qid, q in questions.items():
            if q["type"] == "choice":
                answers[qid] = {"type": "choice", "choice": cls if qid == "semantic_class" else action}
            elif q["type"] == "score":
                answers[qid] = {"type": "score", "score": 1}
            else:
                answers[qid] = {"type": "noul", "noul": 0.5}
        return {"model": "fixed", "answers": answers}
    return caller


class TestRedFragBenchmarkV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = FIXTURE.read_bytes()
        cls.cases = json.loads(cls.raw)["cases"]

    def test_fixture_is_frozen(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), FROZEN_SHA256)

    def test_size_and_class_balance(self):
        self.assertGreaterEqual(len(self.cases), 24)
        counts = Counter(c["expected_class"] for c in self.cases)
        for name in CLASSES:
            self.assertGreaterEqual(counts[name], 4, name)

    def test_required_hard_cases_present(self):
        tags = {t for c in self.cases for t in c["hard_case"]}
        self.assertTrue(REQUIRED_HARD <= tags, REQUIRED_HARD - tags)

    def test_every_case_documents_gold_and_falsifier(self):
        for c in self.cases:
            self.assertTrue(c["gold_rationale"].strip(), c["id"])
            self.assertTrue(c["ambiguity_falsifier"].strip(), c["id"])
            for s in c["sources"]:
                self.assertTrue(s["provenance"].startswith(("github:", "drive:")), c["id"])
                self.assertTrue(s["sha256"].startswith("sha256:"), c["id"])

    def test_model_view_never_contains_gold(self):
        for c in self.cases:
            self.assertFalse(GOLD_KEYS & set(c["cluster"]), c["id"])
            blob = json.dumps(c["cluster"], ensure_ascii=False)
            # Real source text may mention labels; it must never carry this case's own gold pair.
            self.assertNotIn('"expected_class": "%s"' % c["expected_class"], blob.replace('\\"', '"'), c["id"])

    def test_gold_is_deterministic_whatever_the_model_says(self):
        callers = [_fixed_caller("NOISE", "QUARANTINE_REVIEW"), _fixed_caller("CORE", "KEEP_ACTIVE"),
                   _fixed_caller("DUPLICATE", "LINK_TO_CANON")]
        self.assertEqual(set(redfrag_questions()), set(redfrag_questions()))
        for c in self.cases:
            for caller in callers:
                r = assess_redfrag_cluster(c["cluster"], caller=caller)
                self.assertEqual((r["semantic_class"], r["action"]),
                                 (c["expected_class"], c["expected_action"]), c["id"])
                self.assertEqual(r["physical_deletions"], 0)

    def test_blind_view_hides_gate_flags(self):
        sys.path.insert(0, str(ROOT))
        from scripts.r3_clm_redfrag_benchmark import GATE_FLAGS, make_caller
        seen = {}

        def fake_system_one(state, questions, **kw):
            seen["state"] = state
            return _fixed_caller("NOISE", "QUARANTINE_REVIEW")(state, questions)

        from unittest.mock import patch
        cluster = next(c["cluster"] for c in self.cases if c["id"] == "K01")
        with patch("typesafe_sister.client.system_one", side_effect=fake_system_one):
            r = assess_redfrag_cluster(cluster, caller=make_caller("r3_clm", "blind"))
        self.assertNotIn("deterministic_evidence", seen["state"])
        self.assertFalse(set(GATE_FLAGS) & set(seen["state"]["cluster"]))
        self.assertEqual(r["semantic_class"], "CORE")  # gate still uses full evidence

    def test_fixture_reproducible_from_pinned_sources(self):
        probe = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                                "8050f1c02c512cddfd822c467eab8a7953be4517^{commit}"], capture_output=True)
        if probe.returncode != 0:
            self.skipTest("pinned commits not in this (shallow) checkout")
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "redfrag_build_fixture_v1.py"), "--check"],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
