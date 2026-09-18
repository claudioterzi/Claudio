import json
import tempfile
import unittest
from pathlib import Path

from sdq1.benchmark_integrity import (
    AmbiguousSnapshotError,
    compare_snapshots,
    generate_run_id,
    load_snapshot,
    prepare_snapshot,
    save_snapshot,
)


def _snapshot(*, error=False, total=2, run_id=None):
    data = {
        "meta": {
            "suite_versione": "v1",
            "modello": "stub-model",
            "timestamp_inizio": "2026-09-18T06:00:00+00:00",
            "timestamp_fine": "2026-09-18T06:00:01+00:00",
            "data": "2026-09-18",
        },
        "sommario": {
            "punteggio": 0.5,
            "superati": 1,
            "totale": total,
            "punteggi_categoria": {"stub": 0.5},
            "latenza_media_ms": 100,
            "latenza_mediana_ms": 100,
        },
        "risultati": [
            {
                "id": "T1",
                "categoria": "stub",
                "superato": True,
                "risposta": "ok",
                "latenza_ms": 100,
                "errore": None,
            },
            {
                "id": "T2",
                "categoria": "stub",
                "superato": False,
                "risposta": "" if error else "no",
                "latenza_ms": 100,
                "errore": "timeout" if error else None,
            },
        ],
    }
    return prepare_snapshot(data, run_id=run_id)


class BenchmarkIntegrityTests(unittest.TestCase):
    def test_complete_run_has_explicit_denominators(self):
        snap = _snapshot(run_id="run-complete")
        self.assertEqual(snap["meta"]["run_status"], "COMPLETE")
        self.assertEqual(snap["sommario"]["expected_total"], 2)
        self.assertEqual(snap["sommario"]["observed_total"], 2)
        self.assertEqual(snap["sommario"]["completed_count"], 2)
        self.assertEqual(snap["sommario"]["error_count"], 0)
        self.assertTrue(snap["sommario"]["promotion_grade_eligible"])

    def test_error_marks_run_incomplete(self):
        snap = _snapshot(error=True, run_id="run-incomplete")
        self.assertEqual(snap["meta"]["run_status"], "INCOMPLETE")
        self.assertEqual(snap["sommario"]["completed_count"], 1)
        self.assertEqual(snap["sommario"]["error_count"], 1)
        self.assertFalse(snap["sommario"]["promotion_grade_eligible"])

    def test_denominator_mismatch_marks_run_incomplete(self):
        snap = _snapshot(total=3, run_id="run-mismatch")
        self.assertEqual(snap["meta"]["run_status"], "INCOMPLETE")
        self.assertEqual(snap["sommario"]["expected_total"], 3)
        self.assertEqual(snap["sommario"]["observed_total"], 2)

    def test_missing_results_marks_run_invalid(self):
        snap = prepare_snapshot(
            {
                "meta": {
                    "modello": "stub-model",
                    "data": "2026-09-18",
                    "timestamp_inizio": "a",
                    "timestamp_fine": "b",
                },
                "sommario": {"totale": 2},
            },
            run_id="invalid",
        )
        self.assertEqual(snap["meta"]["run_status"], "INVALID")
        self.assertFalse(snap["sommario"]["promotion_grade_eligible"])

    def test_save_is_non_overwriting(self):
        snap = _snapshot(run_id="fixed-run-id")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            path = save_snapshot(snap, output_dir=out)
            self.assertTrue(path.exists())
            with self.assertRaises(FileExistsError):
                save_snapshot(snap, output_dir=out)

    def test_run_ids_are_unique(self):
        self.assertNotEqual(generate_run_id(), generate_run_id())

    def test_same_date_multiple_runs_requires_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            save_snapshot(_snapshot(run_id="run-a"), output_dir=out)
            save_snapshot(_snapshot(run_id="run-b"), output_dir=out)
            with self.assertRaises(AmbiguousSnapshotError):
                load_snapshot("stub-model", "2026-09-18", output_dir=out)
            chosen = load_snapshot("stub-model", "run-b", output_dir=out)
            self.assertEqual(chosen["meta"]["run_id"], "run-b")

    def test_comparison_refuses_incomplete_run(self):
        complete = _snapshot(run_id="run-complete")
        incomplete = _snapshot(error=True, run_id="run-incomplete")
        comparison = compare_snapshots(complete, incomplete)
        self.assertFalse(comparison["promotion_grade"])
        self.assertEqual(comparison["promotion_decision"], "REFUSE")

    def test_complete_comparison_only_advances_to_next_gates(self):
        first = _snapshot(run_id="run-1")
        second = _snapshot(run_id="run-2")
        second["sommario"]["punteggio"] = 0.6
        comparison = compare_snapshots(first, second)
        self.assertTrue(comparison["promotion_grade"])
        self.assertEqual(comparison["promotion_decision"], "ELIGIBLE_FOR_NEXT_GATES")
        self.assertAlmostEqual(comparison["delta_punteggio"], 0.1)


if __name__ == "__main__":
    unittest.main()
