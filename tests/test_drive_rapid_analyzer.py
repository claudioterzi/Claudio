import unittest

from sdq1.drive_rapid_analyzer import build_drive_state, assess_drive_state, rapid_plan


class DriveRapidAnalyzerTests(unittest.TestCase):
    def test_build_state_preserves_drive_evidence_fields(self):
        state = build_drive_state(
            target="doc-1",
            metadata={"name": "Canon", "shared": False},
            revisions=[{"id": "2", "previousRevisionId": "1"}],
            git_alignment={"status": "aligned"},
        )
        self.assertEqual(state["target"], "doc-1")
        self.assertFalse(state["metadata"]["shared"])
        self.assertEqual(state["revisions"][0]["previousRevisionId"], "1")

    def test_real_typed_jev_shape_drives_focus(self):
        def fake_jev(state, questions, **kwargs):
            answers = {}
            for key, spec in questions.items():
                if spec["type"] == "choice":
                    choices = list(spec["criteria"])
                    choice = "git_drive_alignment"
                    answers[key] = {
                        "type": "choice",
                        "choice": choice,
                        "confidence": 0.8,
                        "probabilities": {name: (0.8 if name == choice else 0.2/(len(choices)-1)) for name in choices},
                    }
                elif spec["type"] == "score":
                    n = len(spec["criteria"])
                    answers[key] = {
                        "type": "score",
                        "score": 1.0,
                        "confidence": 0.8,
                        "probabilities": {str(i): (1.0 if i == 1 else 0.0) for i in range(n)},
                        "legend": {str(i): text for i, text in enumerate(spec["criteria"])},
                    }
                else:
                    answers[key] = {"type": "noul", "noul": 0.2}
            return {"model": "jev-test", "answers": answers}

        state = build_drive_state(target="doc-1", metadata={"name": "Canon"})
        advisory = assess_drive_state(state, caller=fake_jev)
        self.assertEqual(advisory["status"], "evaluated")
        plan = rapid_plan(state, advisory)
        self.assertEqual(plan["focus"], "git_drive_alignment")
        self.assertTrue(plan["jev_used"])

    def test_jev_unavailable_falls_back_without_fabrication(self):
        def broken(*args, **kwargs):
            raise RuntimeError("offline")

        state = build_drive_state(target="doc-1")
        advisory = assess_drive_state(state, caller=broken)
        self.assertEqual(advisory["status"], "unavailable")
        plan = rapid_plan(state, advisory)
        self.assertFalse(plan["jev_used"])
        self.assertEqual(plan["focus"], "deterministic_drive_review")


if __name__ == "__main__":
    unittest.main()
