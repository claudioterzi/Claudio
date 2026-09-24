import json
import tempfile
import unittest
from pathlib import Path

from r3_judge.benchmark import summarize
from r3_judge.gate import gate_allows


class R3JudgeTests(unittest.TestCase):
    def test_strict_gate_adopts_eight_of_ten_when_balanced(self):
        rows = []
        for i in range(5):
            rows.append({"expected": "stub", "correct": i < 4, "model": "r3-model", "backend_fingerprint": "fp"})
        for i in range(5):
            rows.append({"expected": "real", "correct": i < 4, "model": "r3-model", "backend_fingerprint": "fp"})
        report = summarize(rows)
        self.assertTrue(report["beats_chance"])
        self.assertTrue(report["adopt"])
        self.assertEqual(report["correct"], 8)

    def test_six_of_ten_beats_chance_but_is_not_adopted_by_r3(self):
        rows = []
        for i in range(5):
            rows.append({"expected": "stub", "correct": i < 3, "model": "r3-model", "backend_fingerprint": "fp"})
        for i in range(5):
            rows.append({"expected": "real", "correct": i < 3, "model": "r3-model", "backend_fingerprint": "fp"})
        report = summarize(rows)
        self.assertTrue(report["beats_chance"])
        self.assertFalse(report["adopt"])

    def test_active_gate_must_match_model_and_fingerprint(self):
        gate = {
            "protocol": "R3-JUDGE/1",
            "adopt": True,
            "model": "rizzo-spark-x2.5-4b-q8_0",
            "backend_fingerprint": "abc",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gate.json"
            path.write_text(json.dumps(gate), encoding="utf-8")
            result = {
                "model": "rizzo-spark-x2.5-4b-q8_0",
                "x_rizzo": {"fingerprint": "abc"},
            }
            self.assertTrue(gate_allows(result, str(path)))
            result["x_rizzo"]["fingerprint"] = "other"
            self.assertFalse(gate_allows(result, str(path)))


if __name__ == "__main__":
    unittest.main()
