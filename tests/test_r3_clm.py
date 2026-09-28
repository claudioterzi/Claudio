import os
import unittest
from unittest.mock import patch

import httpx

from typesafe_sister.client import configured, system_one
from typesafe_sister.r3_clm import compare_answer_sets, system_one_local


class TestR3CLM(unittest.TestCase):
    def test_typed_schema_is_complete_and_bounded(self):
        questions = {
            "focus": {"type": "choice", "instructions": "Choose the dominant focus.",
                      "criteria": {"duplicate": "exact duplicate content", "conflict": "divergent incompatible content"}},
            "risk": {"type": "score", "instructions": "Rank semantic loss risk.",
                     "criteria": ["negligible", "low", "material", "high"]},
            "dupe": {"type": "noul", "instructions": "Is exact duplicate evidence present?",
                     "criteria": {"true": "matching fingerprints prove duplicate", "false": "fingerprints diverge"}},
            "unsupported_noul": {"type": "noul", "instructions": "An uncalibrated generic flag?"},
        }
        result = system_one_local({"matching_fingerprints": True, "exact_duplicate": True}, questions)
        self.assertEqual(set(result["answers"]), set(questions))
        self.assertEqual(result["provider"], "r3_internal")
        self.assertAlmostEqual(sum(result["answers"]["focus"]["probabilities"].values()), 1.0, places=8)
        self.assertTrue(0 <= result["answers"]["risk"]["score"] <= 3)
        self.assertAlmostEqual(sum(result["answers"]["risk"]["probabilities"].values()), 1.0, places=8)
        self.assertEqual(result["answers"]["unsupported_noul"]["noul"], 0.5)
        self.assertIn("unsupported_noul", result["meta"]["abstained_questions"])

    def test_internal_backend_is_opt_in_and_network_free(self):
        questions = {"x": {"type": "choice", "instructions": "pick", "criteria": {"a": "alpha", "b": "beta"}}}
        with patch.dict(os.environ, {"R3_SYSTEM_ONE_BACKEND": "r3_clm", "TYPESAFE_API_KEY": ""}), patch("httpx.Client") as client:
            self.assertTrue(configured())
            result = system_one({"alpha": True}, questions)
            client.assert_not_called()
        self.assertEqual(result["provider"], "r3_internal")

    def test_explicit_typesafe_connection_preserves_historical_transport(self):
        payload = {"model": "jev-test", "answers": {"x": {"type": "noul", "noul": 0.7}}}
        with patch("httpx.Client") as client:
            response = httpx.Response(200, json=payload, request=httpx.Request("POST", "https://api.typesafe.ai/v1/systemone"))
            client.return_value.__enter__.return_value.post.return_value = response
            result = system_one({"x": 1}, {"x": {"type": "noul", "instructions": "x?"}},
                                api_key="TEST_ONLY", model="jev-test", base_url="https://api.typesafe.ai")
        self.assertEqual(result["model"], "jev-test")
        client.return_value.__enter__.return_value.post.assert_called_once()

    def test_shadow_keeps_jev_primary_and_records_candidate(self):
        primary = {"model": "jev-test", "answers": {"x": {"type": "choice", "choice": "a", "confidence": 0.9,
                                                           "probabilities": {"a": 0.9, "b": 0.1}}}}
        questions = {"x": {"type": "choice", "instructions": "pick alpha", "criteria": {"a": "alpha", "b": "beta"}}}
        with patch.dict(os.environ, {"R3_SYSTEM_ONE_BACKEND": "shadow", "TYPESAFE_API_KEY": "KEY"}),              patch("typesafe_sister.client._system_one_typesafe", return_value=primary):
            result = system_one({"alpha": True}, questions)
        self.assertEqual(result["model"], "jev-test")
        self.assertIn("shadow", result)
        self.assertEqual(result["shadow"]["authority"], "observation_only")

    def test_comparison_does_not_declare_a_winner(self):
        a = {"answers": {"q": {"type": "choice", "choice": "x"}}}
        b = {"answers": {"q": {"type": "choice", "choice": "y"}}}
        result = compare_answer_sets(a, b)
        self.assertEqual(result["status"], "compared")
        self.assertEqual(result["agreement_rate"], 0.0)
        self.assertNotIn("winner", result)


if __name__ == "__main__":
    unittest.main()
