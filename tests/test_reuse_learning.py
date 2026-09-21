import unittest

from sdq1.reuse_learning import choose_route, rank_lessons


LESSONS = [
    {
        "id": "L-JEV",
        "capability": "canonical TypeSafe Jev live judgment",
        "status": "VERIFIED",
        "trigger": "typed semantic routing",
        "canonical_short_path": [
            "typesafe_sister/client.py",
            "POST /v1/systemone",
            "jev-latest",
        ],
        "failure_modes": ["do not create parallel engine"],
    },
    {
        "id": "L-PERFUME",
        "capability": "perfume bottle rendering",
        "status": "VERIFIED",
        "trigger": "image asset generation",
        "canonical_short_path": ["studio/parfums/genera_flaconi.cjs"],
        "failure_modes": [],
    },
]


class ReuseLearningTests(unittest.TestCase):
    def test_lexical_ranking_prefers_matching_existing_lesson(self):
        ranked = rank_lessons(
            "reuse TypeSafe Jev canonical typed judgment",
            LESSONS,
            encoder=None,
            learner=None,
        )
        self.assertEqual(ranked[0].lesson_id, "L-JEV")

    def test_ambiguous_route_asks_existing_jev_choice(self):
        calls = []

        def fake_jev(state, questions, **kwargs):
            calls.append((state, questions, kwargs))
            return {
                "model": "jev-test",
                "answers": {
                    "reuse_shortcut": {
                        "type": "choice",
                        "choice": "L-JEV",
                        "confidence": 0.7,
                        "probabilities": {"L-JEV": 0.7, "L-PERFUME": 0.3},
                    }
                },
            }

        decision, _ = choose_route(
            "need a reusable path",
            lessons=LESSONS,
            encoder=None,
            learner=None,
            jev_caller=fake_jev,
            min_score=1.0,  # force ambiguity
        )
        self.assertTrue(calls)
        self.assertEqual(decision.selected_lesson_id, "L-JEV")
        self.assertTrue(decision.jev_used)
        self.assertEqual(decision.route, "ml_shortlist+jev_choice")

    def test_jev_unavailable_never_fabricates_choice(self):
        def broken(*args, **kwargs):
            raise RuntimeError("unavailable")

        decision, ranked = choose_route(
            "need a reusable path",
            lessons=LESSONS,
            encoder=None,
            learner=None,
            jev_caller=broken,
            min_score=1.0,
        )
        self.assertFalse(decision.jev_used)
        self.assertFalse(decision.jev_available)
        self.assertEqual(decision.selected_lesson_id, ranked[0].lesson_id)


if __name__ == "__main__":
    unittest.main()
