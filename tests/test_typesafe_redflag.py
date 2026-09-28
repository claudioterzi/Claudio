import os
import unittest
from unittest.mock import patch

import httpx

from typesafe_sister.client import TypeSafeNotConfigured, system_one
from typesafe_sister.policy import (
    R3_REDFLAG_FLAGS,
    R3_REDFLAG_FOCUS,
    R3_REDFLAG_SCORE_LEVELS,
)
from typesafe_sister.redflag import assess_redflag_state, compare_redflag_providers


def score_answer(levels, value=2.0):
    return {
        "type": "score",
        "score": float(value),
        "confidence": 0.90,
        "legend": {str(i): level for i, level in enumerate(levels)},
        "probabilities": {
            str(i): (1.0 if i == int(value) else 0.0)
            for i in range(len(levels))
        },
    }


def response(*, model="clm-test", focus="ready_for_controlled_test", overrides=None):
    flags = {key: 0.05 for key in R3_REDFLAG_FLAGS}
    if overrides:
        flags.update(overrides)
    return {
        "model": model,
        "answers": {
            "next_focus": {
                "type": "choice",
                "choice": focus,
                "confidence": 0.92,
                "probabilities": {
                    key: (0.92 if key == focus else 0.08 / (len(R3_REDFLAG_FOCUS) - 1))
                    for key in R3_REDFLAG_FOCUS
                },
            },
            **{
                key: score_answer(levels, 2.0)
                for key, levels in R3_REDFLAG_SCORE_LEVELS.items()
            },
            **{
                key: {"type": "noul", "noul": value}
                for key, value in flags.items()
            },
        },
    }


class RedFlagAssessmentTests(unittest.TestCase):
    def test_clm_packet_is_bounded_advisory_and_selects_controlled_test(self):
        seen = {}

        def caller(state, questions, **kwargs):
            seen["state"] = state
            seen["questions"] = questions
            seen["kwargs"] = kwargs
            return response()

        result = assess_redflag_state(
            "Raffaello",
            {
                "proposal": "Reuse canonical System One transport for CLM shadow mode.",
                "evidence": ["official CLM TypeSafe-compatible wire schema"],
            },
            provider="clm",
            caller=caller,
        )
        self.assertEqual(result["status"], "evaluated")
        self.assertEqual(result["provider"], "clm")
        self.assertEqual(result["review_gate"]["lane"], "CONTROLLED_TEST_CANDIDATE")
        self.assertEqual(result["authority"], "advisory_only")
        self.assertEqual(seen["kwargs"]["provider"], "clm")
        self.assertEqual(seen["kwargs"]["model"], "clm-latest")
        self.assertIn("authority", seen["state"])
        self.assertEqual(set(seen["questions"]), set(response()["answers"]))

    def test_secret_or_authority_signal_quarantines(self):
        result = assess_redflag_state(
            "Raffaello",
            {"proposal": "candidate change"},
            provider="clm",
            caller=lambda *args, **kwargs: response(
                overrides={"secret_exposure": 0.91, "authority_violation": 0.80}
            ),
        )
        self.assertEqual(result["status"], "evaluated")
        self.assertEqual(result["review_gate"]["lane"], "QUARANTINE_REVIEW")
        self.assertIn("secret_exposure", result["review_gate"]["signals"])
        self.assertIn("authority_violation", result["review_gate"]["signals"])

    def test_verification_flags_never_become_permission(self):
        result = assess_redflag_state(
            "Raffaello",
            {"proposal": "candidate change"},
            provider="clm",
            caller=lambda *args, **kwargs: response(
                focus="evidence_gap",
                overrides={"postcondition_gap": 0.88},
            ),
        )
        self.assertEqual(result["review_gate"]["lane"], "VERIFY_FIRST")
        self.assertEqual(result["authority"], "advisory_only")

    def test_incomplete_response_fails_closed(self):
        broken = response()
        del broken["answers"]["postcondition_gap"]
        result = assess_redflag_state(
            "R3",
            {"x": 1},
            caller=lambda *args, **kwargs: broken,
        )
        self.assertEqual(result["status"], "unavailable")

    def test_shadow_comparison_uses_identical_policy_and_reports_disagreement(self):
        clm = lambda *args, **kwargs: response(
            model="clm-test",
            focus="latency_cost",
            overrides={"duplicate_engine": 0.70},
        )
        jev = lambda *args, **kwargs: response(
            model="jev-test",
            focus="ready_for_controlled_test",
        )
        result = compare_redflag_providers(
            "R3",
            {"proposal": "benchmark CLM against Jev"},
            clm_caller=clm,
            jev_caller=jev,
        )
        self.assertTrue(result["comparison"]["both_evaluated"])
        self.assertFalse(result["comparison"]["focus_agreement"])
        self.assertFalse(result["comparison"]["gate_agreement"])
        self.assertGreater(result["comparison"]["max_flag_delta"], 0.6)
        self.assertIn("Agreement is not authority", result["promotion_rule"])


class CLMTransportTests(unittest.TestCase):
    def test_loopback_clm_uses_typesafe_wire_format_without_bearer(self):
        body = {
            "model": "clm-test",
            "answers": {"flag": {"type": "noul", "noul": 0.1}},
        }
        with patch("httpx.Client") as client:
            response_obj = httpx.Response(
                200,
                json=body,
                request=httpx.Request("POST", "http://127.0.0.1:8700/v1/systemone"),
            )
            client.return_value.__enter__.return_value.post.return_value = response_obj
            result = system_one(
                {"state": "x"},
                {"flag": {"type": "noul", "instructions": "flag?"}},
                provider="clm",
                base_url="http://127.0.0.1:8700",
                api_key="",
                model="clm-test",
            )

        sent = client.return_value.__enter__.return_value.post.call_args
        self.assertEqual(sent.args[0], "http://127.0.0.1:8700/v1/systemone")
        self.assertEqual(sent.kwargs["headers"], {})
        self.assertEqual(sent.kwargs["json"]["model"], "clm-test")
        self.assertEqual(result["model"], "clm-test")

    def test_remote_clm_without_key_is_refused_before_network(self):
        with patch.dict(os.environ, {"CLM_API_KEY": ""}), patch("httpx.Client") as client:
            with self.assertRaises(TypeSafeNotConfigured):
                system_one(
                    {"state": "x"},
                    {"flag": {"type": "noul", "instructions": "flag?"}},
                    provider="clm",
                    base_url="https://clm.example.invalid",
                    api_key="",
                )
            client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
