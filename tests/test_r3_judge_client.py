import os
import unittest
from unittest.mock import patch

from typesafe_sister.client import system_one


QUESTIONS = {
    "is_stub": {
        "type": "noul",
        "instructions": "Is it a stub?",
        "criteria": {"true": "stub", "false": "real"},
    }
}


class R3JudgeClientTests(unittest.TestCase):
    @patch.dict(os.environ, {"R3_JUDGE_MODE": "candidate"}, clear=False)
    @patch("typesafe_sister.client._post_system_one")
    def test_candidate_is_always_hypothesis_and_not_independent(self, post):
        post.return_value = {
            "model": "rizzo-spark-x2.5-4b-q8_0",
            "answers": {"is_stub": {"type": "noul", "noul": 0.9}},
        }
        result = system_one({"content": "TODO"}, QUESTIONS)
        meta = result["x_r3"]
        self.assertEqual(meta["epistemic_class"], "IPOTESI")
        self.assertFalse(meta["factual_authority"])
        self.assertFalse(meta["independent_confirmation"])
        self.assertIn("is_stub", meta["falsification"])
        self.assertEqual(meta["provider"], "r3_local_rizzo_candidate")

    @patch.dict(os.environ, {"R3_JUDGE_MODE": "active", "TYPESAFE_API_KEY": "hosted-key"}, clear=False)
    @patch("typesafe_sister.client.gate_allows", return_value=False)
    @patch("typesafe_sister.client._post_system_one")
    def test_active_rejected_local_falls_back_to_configured_hosted(self, post, gate):
        post.side_effect = [
            {"model": "rizzo-local", "answers": {"is_stub": {"type": "noul", "noul": 0.9}}},
            {"model": "jev-hosted", "answers": {"is_stub": {"type": "noul", "noul": 0.1}}},
        ]
        result = system_one({"content": "real"}, QUESTIONS)
        self.assertEqual(result["model"], "jev-hosted")
        self.assertEqual(result["x_r3"]["provider"], "typesafe_jev")
        self.assertEqual(post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
