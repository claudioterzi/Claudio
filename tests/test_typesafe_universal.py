import unittest
from unittest.mock import patch

from typesafe_sister.client import TypeSafeNotConfigured
from typesafe_sister.policy import UNIVERSAL_SCORE_LEVELS
from typesafe_sister.universal import assess_project_state


def score_answer(levels, index=2):
    probabilities = {str(i): 0.0 for i in range(len(levels))}
    probabilities[str(index)] = 1.0
    return {
        "type": "score",
        "score": float(index),
        "confidence": 1.0,
        "legend": {str(i): level for i, level in enumerate(levels)},
        "probabilities": probabilities,
    }


def good_response():
    return {
        "model": "jev-test",
        "answers": {
            "focus": {
                "type": "choice",
                "choice": "verify",
                "confidence": 0.8,
                "probabilities": {
                    "develop": 0.1,
                    "clarify": 0.05,
                    "verify": 0.8,
                    "review": 0.05,
                },
            },
            **{
                key: score_answer(levels)
                for key, levels in UNIVERSAL_SCORE_LEVELS.items()
            },
            "contradiction": {"type": "noul", "noul": 0.1},
            "missing_critical_input": {"type": "noul", "noul": 0.2},
            "unsupported_claim": {"type": "noul", "noul": 0.9},
            "freshness_needed": {"type": "noul", "noul": 0.85},
            "external_side_effect": {"type": "noul", "noul": 0.05},
        },
    }


class UniversalTypeSafeTests(unittest.TestCase):
    @patch("typesafe_sister.universal.system_one")
    def test_returns_typed_advisory_without_authorization(self, system_one):
        system_one.return_value = good_response()

        result = assess_project_state("R3", {"proposal": "Verify a current deployment claim"})

        self.assertEqual(result["status"], "evaluated")
        self.assertEqual(result["project"], "R3")
        self.assertEqual(result["focus"]["value"], "verify")
        self.assertEqual(result["flags"]["unsupported_claim"], 0.9)
        self.assertIn("risk", result["scores"])
        self.assertIn("input_sha256", result)

        state, questions = system_one.call_args.args
        self.assertEqual(state["project"], "R3")
        self.assertEqual(questions["focus"]["type"], "choice")
        self.assertEqual(questions["readiness"]["type"], "score")
        self.assertEqual(questions["contradiction"]["type"], "noul")

    @patch("typesafe_sister.universal.system_one")
    def test_not_configured_degrades_cleanly(self, system_one):
        system_one.side_effect = TypeSafeNotConfigured("no key")
        result = assess_project_state("general", {"x": 1})
        self.assertEqual(result["status"], "not_configured")

    @patch("typesafe_sister.universal.system_one")
    def test_invalid_answer_never_becomes_a_judgment(self, system_one):
        response = good_response()
        del response["answers"]["freshness_needed"]
        system_one.return_value = response
        result = assess_project_state("general", {"x": 1})
        self.assertEqual(result["status"], "unavailable")

    @patch("typesafe_sister.universal.system_one")
    def test_large_state_is_rejected_before_api_call(self, system_one):
        result = assess_project_state("general", {"text": "x" * 70000})
        self.assertEqual(result["status"], "state_too_large")
        system_one.assert_not_called()


if __name__ == "__main__":
    unittest.main()
