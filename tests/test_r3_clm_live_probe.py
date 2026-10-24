import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import r3_clm_live_probe as probe


class LiveProbeEvidenceTests(unittest.TestCase):
    def test_failed_case_remains_in_accuracy_and_recall_denominators(self):
        rows = [
            {"result": {"status": "evaluated", "review_gate": {"lane": "VERIFY_FIRST"},
                        "focus": {"value": "evidence_gap"}},
             "expected_lane": "VERIFY_FIRST", "expected_focus": "evidence_gap",
             "must_detect_flags": ["unsupported_promotion"],
             "detected_required_flags": ["unsupported_promotion"], "wall_latency_ms": 10},
            {"result": {"status": "unavailable"}, "expected_lane": "VERIFY_FIRST",
             "expected_focus": "evidence_gap", "must_detect_flags": ["unsupported_promotion"],
             "detected_required_flags": [], "wall_latency_ms": 20},
        ]
        metrics = probe._metrics(rows)
        self.assertEqual(metrics["failed_count"], 1)
        self.assertEqual(metrics["lane_accuracy"], 0.5)
        self.assertEqual(metrics["focus_accuracy"], 0.5)
        self.assertEqual(metrics["required_flag_recall"], 0.5)

    def test_incomplete_and_empty_runs_do_not_report_completion(self):
        for cases in ([{"id": "failed"}], []):
            with self.subTest(cases=cases), tempfile.TemporaryDirectory() as tmp:
                src, out = Path(tmp) / "cases.json", Path(tmp) / "report.json"
                src.write_text(json.dumps({"cases": cases}), encoding="utf-8")
                failed = {"result": {"status": "unavailable"}, "must_detect_flags": [],
                          "detected_required_flags": [], "wall_latency_ms": 1}
                with patch("sys.argv", ["probe", "--cases", str(src), "--out", str(out)]), \
                     patch.object(probe, "_get_json", return_value={}), \
                     patch.object(probe, "_run_case", return_value=failed), \
                     patch("builtins.print"):
                    self.assertEqual(probe.main(), 1)
                report = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(report["status"], "LIVE_CLM_INFERENCE_INCOMPLETE")
                self.assertFalse(report["promotion_grade"])
