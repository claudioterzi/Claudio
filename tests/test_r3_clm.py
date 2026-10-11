import os
import unittest
from unittest.mock import patch

import httpx

from typesafe_sister import client
from typesafe_sister.r3_clm import compare_answer_sets, system_one_local
from typesafe_sister.redfrag import assess_redfrag_cluster


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
        self.assertEqual(result["answers"]["unsupported_noul"]["noul"], 0.5)
        self.assertIn("unsupported_noul", result["meta"]["abstained_questions"])

    def test_r3_clm_provider_is_explicit_and_network_free(self):
        questions = {"x": {"type": "choice", "instructions": "pick", "criteria": {"a": "alpha", "b": "beta"}}}
        with patch.dict(os.environ, {"R3_SYSTEMONE_PROVIDER": "r3_clm", "TYPESAFE_API_KEY": "", "CLM_BASE_URL": ""}), \
                patch("httpx.Client") as http:
            self.assertEqual(client.backend_info()["provider"], "r3_clm")
            result = client.system_one({"alpha": True}, questions)
            http.assert_not_called()
        self.assertEqual(result["_r3_provider"], "r3_clm")

    def test_auto_never_selects_local_baseline(self):
        env = {"R3_SYSTEMONE_PROVIDER": "auto", "TYPESAFE_API_KEY": "", "CLM_BASE_URL": "",
               "R3_SYSTEMONE_BASE_URL": "", "R3_SYSTEMONE_MODEL": ""}
        with patch.dict(os.environ, env):
            self.assertFalse(client.configured())

    def test_r3_clm_has_no_native_rank(self):
        with self.assertRaises(client.SystemOneCapabilityUnavailable):
            client.rank("ctx", "q", ["a", "b"], provider="r3_clm")

    def test_comparison_does_not_declare_a_winner(self):
        a = {"answers": {"q": {"type": "choice", "choice": "x"}}}
        b = {"answers": {"q": {"type": "choice", "choice": "y"}}}
        result = compare_answer_sets(a, b)
        self.assertEqual(result["agreement_rate"], 0.0)
        self.assertNotIn("winner", result)


class TestRedFragProviderSwap(unittest.TestCase):
    CLUSTER = {"id": "C01", "name": "dup", "source_count": 2,
               "content_hashes": ["sha256:same", "sha256:same"],
               "provenance": ["drive:a", "github:b"], "canonical_source": "drive:a", "same_topic": True}

    def test_default_redfrag_provider_is_local(self):
        with patch.dict(os.environ, {"R3_REDFRAG_PROVIDER": ""}), patch("httpx.Client") as http:
            result = assess_redfrag_cluster(self.CLUSTER)
            http.assert_not_called()
        self.assertEqual(result["provider"], "r3_clm")
        self.assertEqual(result["action"], "LINK_TO_CANON")

    def test_same_pipeline_runs_on_real_clm_endpoint(self):
        """Swapping to CLM changes only env: same questions, same gate, /v1/systemone wire."""
        from typesafe_sister.policy import redfrag_questions
        answers = {
            "semantic_class": {"type": "choice", "choice": "DUPLICATE"},
            "proposed_action": {"type": "choice", "choice": "LINK_TO_CANON"},
            "loss_risk": {"type": "score", "score": 0},
            "compression_value": {"type": "score", "score": 2},
            "exact_duplicate_supported": {"type": "noul", "noul": 0.9},
            "conflict_present": {"type": "noul", "noul": 0.1},
            "provenance_sufficient": {"type": "noul", "noul": 0.9},
        }
        self.assertEqual(set(answers), set(redfrag_questions()))
        env = {"R3_REDFRAG_PROVIDER": "clm", "CLM_BASE_URL": "http://127.0.0.1:8700", "CLM_API_KEY": ""}
        with patch.dict(os.environ, env), patch("httpx.Client") as http:
            post = http.return_value.__enter__.return_value.post
            post.return_value = httpx.Response(
                200, json={"model": "clm-latest", "answers": answers},
                request=httpx.Request("POST", "http://127.0.0.1:8700/v1/systemone"))
            result = assess_redfrag_cluster(self.CLUSTER)
        url = post.call_args.args[0]
        self.assertEqual(url, "http://127.0.0.1:8700/v1/systemone")
        self.assertEqual(result["provider"], "clm")
        self.assertEqual(result["action"], "LINK_TO_CANON")
        self.assertEqual(result["physical_deletions"], 0)


if __name__ == "__main__":
    unittest.main()
