import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("evidence_review", Path(__file__).resolve().parents[1] / "sdq1/sar/evidence_review.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    return {
        "objective": "Reject unsupported claims", "revision": "fixture-v1",
        "model": "offline-test", "acceptance_criterion": "No evidence means blocked",
        "candidates": [{
            "id": "a", "proposal": "Use a fail-closed gate", "falsifier": "An unsupported claim passes",
            "impact": 8, "speed": 6, "risk": 2,
            "evidence": [{"id": "e1", "source": "fixture://test", "observation": "Synthetic test record", "kind": "test"}],
            "checks": [{"name": role, "role": role, "status": "pass", "evidence_ids": ["e1"]}
                       for role in ("acceptance", "countercheck", "regression")],
        }],
    }


class ReviewTests(unittest.TestCase):
    def test_deterministic_and_no_promotion(self):
        record = fixture()
        result = module.review(record)
        self.assertEqual(result, module.review(record))
        self.assertEqual(result["selected_for_review"], "a")
        self.assertFalse(result["automatic_promotion"])
        self.assertEqual(result["candidates"][0]["priority"], 24)

    def test_high_score_cannot_override_failed_check(self):
        record = fixture()
        bad = copy.deepcopy(record["candidates"][0])
        bad.update(id="b", impact=10, speed=10, risk=1)
        bad["checks"][1]["status"] = "fail"
        record["candidates"].append(bad)
        self.assertEqual(module.review(record)["selected_for_review"], "a")

    def test_unknown_missing_and_simulated_evidence_block(self):
        for change in ("unknown", "missing", "simulation", "missing-role"):
            with self.subTest(change=change):
                record = fixture(); c = record["candidates"][0]
                if change == "unknown": c["checks"][0]["status"] = "unknown"
                if change == "missing": c["evidence"] = []
                if change == "simulation": c["evidence"][0]["kind"] = "simulation"
                if change == "missing-role": c["checks"].pop()
                self.assertIsNone(module.review(record)["selected_for_review"])

    def test_invalid_ratings(self):
        for value in (0, 11, float("nan"), float("inf"), True, "9"):
            with self.subTest(value=value):
                record = fixture(); record["candidates"][0]["risk"] = value
                with self.assertRaises(ValueError): module.review(record)

    def test_duplicate_ids_and_unresolved_references(self):
        record = fixture(); record["candidates"].append(copy.deepcopy(record["candidates"][0]))
        with self.assertRaises(ValueError): module.review(record)
        record = fixture(); record["candidates"][0]["checks"][0]["evidence_ids"] = ["missing"]
        self.assertIsNone(module.review(record)["selected_for_review"])

    def test_empty_input_rejected(self):
        for value in ({}, [], {**fixture(), "candidates": []}):
            with self.assertRaises(ValueError): module.review(value)


if __name__ == "__main__":
    unittest.main()
