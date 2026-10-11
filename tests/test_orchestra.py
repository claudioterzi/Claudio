import os
import unittest
from unittest.mock import patch

from api import orchestra


class OrchestraEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = orchestra.app.test_client()
        self.secret = "r3-test-secret-" * 3

    def test_health_get_is_safe_and_public(self):
        response = self.client.get("/api/orchestra")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"servizio": "Raffaello Orchestra", "pronto": True})

    def test_post_requires_shared_secret(self):
        with patch.dict(os.environ, {"RAFFAELLO_BRIDGE_SECRET": self.secret}, clear=False):
            response = self.client.post("/api/orchestra", json={"domanda": "Ciao"})
        self.assertEqual(response.status_code, 401)

    def test_authenticated_post_returns_orchestrated_answer_without_live_api(self):
        contributions = [
            {"provider": "deepseek", "modello": "deepseek-flash", "testo": "Contributo DeepSeek", "latenza_ms": 12},
            {"provider": "gemini", "modello": "gemini-2.5-flash", "testo": "Contributo Gemini", "latenza_ms": 15},
        ]
        with (
            patch.dict(os.environ, {"RAFFAELLO_BRIDGE_SECRET": self.secret}, clear=False),
            patch.object(orchestra, "_collect", return_value=contributions),
            patch.object(
                orchestra,
                "_synthesize",
                return_value=("Risposta sintetizzata", {"provider": "gemini", "modello": "gemini-2.5-flash", "modo": "sintesi"}),
            ),
        ):
            response = self.client.post(
                "/api/orchestra",
                json={"domanda": "Analizza questo problema", "lingua": "it", "cronologia": []},
                headers={"X-Raffaello-Secret": self.secret},
            )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["risposta"], "Risposta sintetizzata")
        self.assertEqual(data["motore"]["tipo"], "orchestra")
        self.assertEqual([p["nome"] for p in data["motore"]["provider"]], ["deepseek", "gemini"])

    def test_no_provider_is_explicit_503(self):
        with (
            patch.dict(os.environ, {"RAFFAELLO_BRIDGE_SECRET": self.secret}, clear=False),
            patch.object(orchestra, "_collect", return_value=[]),
        ):
            response = self.client.post(
                "/api/orchestra",
                json={"domanda": "Ciao"},
                headers={"X-Raffaello-Secret": self.secret},
            )
        self.assertEqual(response.status_code, 503)
        self.assertIn("Nessun provider", response.get_json()["errore"])


if __name__ == "__main__":
    unittest.main()
