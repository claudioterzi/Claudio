"""Provider-routing contracts for the shared R3∞ System One layer.

No live model calls. CLM and Jev use the same canonical policy layer.
"""
import os
import unittest
from unittest.mock import patch

import httpx

from typesafe_sister.client import (
    SystemOneCapabilityUnavailable,
    backend_info,
    rank,
    system_one,
)


class TestSystemOneCLM(unittest.TestCase):
    def test_auto_prefers_deliberately_configured_clm(self):
        env = {
            "CLM_BASE_URL": "http://clm.internal:8700",
            "TYPESAFE_API_KEY": "LEGACY_JEV_KEY",
        }
        with patch.dict(os.environ, env, clear=True):
            info = backend_info()
        self.assertTrue(info["configured"])
        self.assertEqual(info["provider"], "clm")
        self.assertEqual(info["model"], "clm-latest")
        self.assertEqual(info["base_url"], "http://clm.internal:8700")

    def test_typesafe_can_be_forced_as_fallback(self):
        env = {
            "R3_SYSTEMONE_PROVIDER": "typesafe",
            "TYPESAFE_API_KEY": "TEST_ONLY",
            "CLM_BASE_URL": "http://clm.internal:8700",
        }
        with patch.dict(os.environ, env, clear=True):
            info = backend_info()
        self.assertEqual(info["provider"], "typesafe")
        self.assertEqual(info["model"], "jev-latest")

    def test_clm_systemone_can_run_without_bearer_key(self):
        answer = {
            "model": "clm-latest",
            "answers": {"x": {"type": "noul", "noul": 0.8}},
        }
        env = {"CLM_BASE_URL": "http://clm.internal:8700"}
        with patch.dict(os.environ, env, clear=True), patch("httpx.Client") as client:
            response = httpx.Response(
                200,
                json=answer,
                request=httpx.Request("POST", "http://clm.internal:8700/v1/systemone"),
            )
            client.return_value.__enter__.return_value.post.return_value = response
            result = system_one("state", {"x": {"type": "noul", "instructions": "Relevant?"}})
        sent = client.return_value.__enter__.return_value.post.call_args
        self.assertEqual(sent.args[0], "http://clm.internal:8700/v1/systemone")
        self.assertEqual(sent.kwargs["headers"], {})
        self.assertEqual(sent.kwargs["json"]["model"], "clm-latest")
        self.assertEqual(result["_r3_provider"], "clm")

    def test_clm_native_rank_is_exposed_without_emulating_it_on_jev(self):
        env = {"CLM_BASE_URL": "http://clm.internal:8700"}
        payload = {
            "model": "clm-latest",
            "ranked": [
                {"rank": 1, "candidate": "bank statement", "prob": 0.7},
                {"rank": 2, "candidate": "old email", "prob": 0.3},
            ],
        }
        with patch.dict(os.environ, env, clear=True), patch("httpx.Client") as client:
            response = httpx.Response(
                200,
                json=payload,
                request=httpx.Request("POST", "http://clm.internal:8700/v1/rank"),
            )
            client.return_value.__enter__.return_value.post.return_value = response
            result = rank(
                "Bitcoin Cannes 2009 recovery",
                "Which evidence path has highest information value?",
                ["bank statement", "old email"],
            )
        self.assertEqual(result["ranked"][0]["candidate"], "bank statement")

        with patch.dict(
            os.environ,
            {"R3_SYSTEMONE_PROVIDER": "typesafe", "TYPESAFE_API_KEY": "TEST_ONLY"},
            clear=True,
        ):
            with self.assertRaises(SystemOneCapabilityUnavailable):
                rank("x", "y", ["a", "b"])


if __name__ == "__main__":
    unittest.main()
