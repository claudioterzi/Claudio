import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("r3_live_systemone", ROOT / "r3" / "typesafe_sister.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


class LiveSystemOneGatewayTests(unittest.TestCase):
    def setUp(self):
        self.old_token = mod.R3_API_TOKEN
        mod.R3_API_TOKEN = "TEST_R3_TOKEN"
        self.client = TestClient(mod.app)

    def tearDown(self):
        mod.R3_API_TOKEN = self.old_token

    def test_health_reports_provider_neutral_backend_metadata(self):
        with patch.object(mod, "backend_info", return_value={
            "configured": True,
            "provider": "typesafe",
            "model": "jev-latest",
            "base_url": "https://api.typesafe.ai",
        }):
            body = self.client.get("/health").json()
        self.assertEqual(body["service"], "r3-typesafe-sister")
        self.assertEqual(body["provider"], "typesafe")
        self.assertFalse(body["native_rank"])

    def test_judge_preserves_backend_provider(self):
        answer = {"model": "jev-latest", "answers": {"x": {"type": "noul", "noul": 0.8}}, "_r3_provider": "typesafe"}
        with patch.object(mod, "system_one", return_value=answer):
            resp = self.client.post(
                "/judge",
                headers={"Authorization": "Bearer TEST_R3_TOKEN"},
                json={"state": {"x": 1}, "questions": {"x": {"type": "noul", "instructions": "test"}}},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["provider"], "typesafe")

    def test_rank_is_explicitly_unavailable_on_jev(self):
        with patch.object(mod, "rank", side_effect=mod.SystemOneCapabilityUnavailable("no rank")):
            resp = self.client.post(
                "/rank",
                headers={"Authorization": "Bearer TEST_R3_TOKEN"},
                json={"context": "c", "question": "q", "answers": ["a", "b"]},
            )
        self.assertEqual(resp.status_code, 501)

    def test_rank_returns_clm_provider_when_available(self):
        answer = {"model": "clm-latest", "ranked": [{"answer": "b"}], "_r3_provider": "clm"}
        with patch.object(mod, "rank", return_value=answer):
            resp = self.client.post(
                "/rank",
                headers={"Authorization": "Bearer TEST_R3_TOKEN"},
                json={"context": "c", "question": "q", "answers": ["a", "b"]},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["provider"], "clm")


if __name__ == "__main__":
    unittest.main()
