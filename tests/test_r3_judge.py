import json
import tempfile
import unittest
from pathlib import Path

from r3_judge.benchmark import summarize
from r3_judge.gate import gate_allows


def _ids(rows):
    for i, row in enumerate(rows):
        row.setdefault("id", f"case-{i}")
        row.setdefault("path", f"fixtures/case-{i}.txt")
    return rows


def _fixture(**overrides):
    rows = [{"expected": "stub" if i < 5 else "real", "correct": True,
             "model": "M", "backend_fingerprint": "F"} for i in range(10)]
    for row in rows:
        row.update(overrides)
    return _ids(rows)


class R3JudgeTests(unittest.TestCase):
    def test_strict_gate_adopts_eight_of_ten_when_balanced(self):
        rows = []
        for i in range(5):
            rows.append({"expected": "stub", "correct": i < 4, "model": "r3-model", "backend_fingerprint": "fp"})
        for i in range(5):
            rows.append({"expected": "real", "correct": i < 4, "model": "r3-model", "backend_fingerprint": "fp"})
        report = summarize(_ids(rows))
        self.assertTrue(report["beats_chance"])
        self.assertTrue(report["adopt"])
        self.assertEqual(report["correct"], 8)

    def test_six_of_ten_beats_chance_but_is_not_adopted_by_r3(self):
        rows = []
        for i in range(5):
            rows.append({"expected": "stub", "correct": i < 3, "model": "r3-model", "backend_fingerprint": "fp"})
        for i in range(5):
            rows.append({"expected": "real", "correct": i < 3, "model": "r3-model", "backend_fingerprint": "fp"})
        report = summarize(_ids(rows))
        self.assertTrue(report["beats_chance"])
        self.assertFalse(report["adopt"])

    def test_each_row_requires_backend_identity(self):
        rows = [{"expected": "stub" if i < 5 else "real", "correct": True,
                 "model": "rizzo-latest", "backend_fingerprint": "fp"} for i in range(10)]
        _ids(rows)
        for field in ("model", "backend_fingerprint"):
            for missing in ("", "   "):
                damaged = [dict(row) for row in rows]
                damaged[0][field] = missing
                self.assertFalse(summarize(damaged)["adopt"])
        for row in rows:
            row["model"] = ""
        self.assertFalse(summarize(rows)["adopt"])

    # --- regressions from the external review of 2026-10-05 (each reproduced first) ---
    def test_correct_must_be_a_real_boolean(self):
        for bad in ("false", "0", 1, [0], None):
            with self.assertRaises(ValueError):
                summarize(_fixture(correct=bad))

    def test_identity_must_be_strings(self):
        with self.assertRaises(ValueError):
            summarize(_fixture(model=123, backend_fingerprint=456))

    def test_padded_fingerprint_is_not_equated(self):
        rows = _fixture()
        rows[0]["backend_fingerprint"] = " F "
        self.assertFalse(summarize(rows)["adopt"])

    def test_duplicate_cases_are_rejected(self):
        rows = _fixture()
        rows[1]["id"] = rows[0]["id"]
        with self.assertRaises(ValueError):
            summarize(rows)
        rows = _fixture()
        rows[1]["path"] = rows[0]["path"]
        with self.assertRaises(ValueError):
            summarize(rows)

    def test_coherent_but_unrequested_model_is_not_adopted(self):
        self.assertTrue(summarize(_fixture(), expected_model="M")["adopt"])
        self.assertFalse(summarize(_fixture(model="wrong-model"), expected_model="M")["adopt"])
        self.assertFalse(summarize(_fixture(), expected_model="M", expected_fingerprint="G")["adopt"])

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
