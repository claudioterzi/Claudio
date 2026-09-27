import unittest
from unittest.mock import patch

from typesafe_sister.bitcoin_recovery import assess_bitcoin_recovery
from typesafe_sister.client import TypeSafeNotConfigured
from typesafe_sister.policy import (
    BITCOIN_RECOVERY_FOCUS,
    BITCOIN_RECOVERY_SCORE_LEVELS,
    UNIVERSAL_FOCUS,
    UNIVERSAL_SCORE_LEVELS,
)


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


def choice_answer(criteria, value):
    probs = {key: 0.0 for key in criteria}
    probs[value] = 1.0
    return {
        "type": "choice",
        "choice": value,
        "confidence": 1.0,
        "probabilities": probs,
    }


def good_response():
    answers = {
        "focus": choice_answer(UNIVERSAL_FOCUS, "verify"),
        **{key: score_answer(levels) for key, levels in UNIVERSAL_SCORE_LEVELS.items()},
        "contradiction": {"type": "noul", "noul": 0.1},
        "missing_critical_input": {"type": "noul", "noul": 0.8},
        "unsupported_claim": {"type": "noul", "noul": 0.7},
        "freshness_needed": {"type": "noul", "noul": 0.2},
        "external_side_effect": {"type": "noul", "noul": 0.0},
        "recovery_next_focus": choice_answer(BITCOIN_RECOVERY_FOCUS, "payment_rail"),
        **{key: score_answer(levels, 3) for key, levels in BITCOIN_RECOVERY_SCORE_LEVELS.items()},
        "ownership_inference_risk": {"type": "noul", "noul": 0.1},
        "branch_exhausted": {"type": "noul", "noul": 0.2},
    }
    return {"model": "jev-test", "answers": answers}


class BitcoinRecoveryJevTests(unittest.TestCase):
    @patch("typesafe_sister.bitcoin_recovery.system_one")
    def test_combines_universal_and_forensic_questions(self, system_one):
        system_one.return_value = good_response()
        result = assess_bitcoin_recovery({
            "observed": ["2009 employment email"],
            "testimony": ["possible card payment"],
            "hypotheses": ["purchase", "mining"],
        })

        self.assertEqual(result["status"], "evaluated")
        self.assertEqual(result["universal"]["focus"]["value"], "verify")
        self.assertEqual(result["forensic"]["next_focus"]["value"], "payment_rail")
        self.assertEqual(result["forensic"]["scores"]["hypothesis_discrimination"]["score"], 3.0)
        self.assertEqual(result["epistemic_note"], "typed_model_judgment_not_independent_factual_evidence")

        state, questions = system_one.call_args.args
        self.assertTrue(state["epistemic_contract"]["authorized_sources_only"])
        self.assertIn("readiness", questions)
        self.assertIn("recovery_next_focus", questions)
        self.assertIn("ownership_inference_risk", questions)

    @patch("typesafe_sister.bitcoin_recovery.system_one")
    def test_not_configured_degrades_cleanly(self, system_one):
        system_one.side_effect = TypeSafeNotConfigured("no key")
        result = assess_bitcoin_recovery({"x": 1})
        self.assertEqual(result["status"], "not_configured")

    @patch("typesafe_sister.bitcoin_recovery.system_one")
    def test_incomplete_answer_is_not_promoted(self, system_one):
        response = good_response()
        del response["answers"]["branch_exhausted"]
        system_one.return_value = response
        result = assess_bitcoin_recovery({"x": 1})
        self.assertEqual(result["status"], "unavailable")

    @patch("typesafe_sister.bitcoin_recovery.system_one")
    def test_large_state_rejected_before_api_call(self, system_one):
        result = assess_bitcoin_recovery({"text": "x" * 70000})
        self.assertEqual(result["status"], "state_too_large")
        system_one.assert_not_called()


if __name__ == "__main__":
    unittest.main()
