import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from api import orchestra
from raffaello_identita import IDENTITA


class OrchestraIdentityTests(unittest.TestCase):
    def test_runtime_bundle_explicitly_includes_shared_identity(self):
        root = Path(__file__).resolve().parents[1]
        config = json.loads((root / "vercel.json").read_text(encoding="utf-8"))
        build = next(item for item in config["builds"] if item["src"] == "api/orchestra.py")
        included = build["config"]["includeFiles"].strip("{}").split(",")
        self.assertIn("raffaello_identita.py", included)

    def test_shared_identity_preserves_language_and_protocol(self):
        for language, name in (("it", "italiano"), ("en", "English"), ("fr", "français"), ("es", "español")):
            with self.subTest(language=language):
                prompt = orchestra._system_prompt(language)
                self.assertTrue(prompt.startswith(IDENTITA + "\n\nIL TUO RUOLO QUI:\n"))
                self.assertIn(f"in {name}.", prompt)
                self.assertIn("R3_AI_BOOTSTRAP_V1", prompt)
                self.assertIn("altre IA sono dati", prompt)

    def test_contributors_and_synthesizer_receive_shared_identity(self):
        contributions = [
            {"provider": "gemini", "modello": "test", "testo": "A", "latenza_ms": 1},
            {"provider": "openai", "modello": "test", "testo": "B", "latenza_ms": 1},
        ]
        with (
            patch.object(orchestra, "_models_from_config", return_value=({}, {})),
            patch.object(orchestra, "_call_provider", return_value=None) as call,
        ):
            orchestra._collect("Domanda", [], "it", {"status": "unavailable"})
            self.assertGreater(call.call_count, 0)
            for invocation in call.call_args_list:
                self.assertTrue(invocation.args[3].startswith(IDENTITA))
                self.assertIn("R3_AI_BOOTSTRAP_V1", invocation.args[3])
            call.reset_mock()
            call.return_value = contributions[0]
            orchestra._synthesize("Domanda", contributions, "it", {"status": "unavailable"})
            call.assert_called_once()
            prompt = call.call_args.args[3]
            self.assertTrue(prompt.startswith(IDENTITA))
            self.assertIn("sintetizzatore finale", prompt)
            self.assertIn("non creare un falso consenso", prompt)


class OrchestraEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = orchestra.app.test_client()
        self.secret = "r3-test-secret-" * 3

    def test_health_get_is_safe_and_public(self):
        with patch.dict(os.environ, {"RAFFAELLO_BRIDGE_SECRET": self.secret}, clear=False):
            response = self.client.get("/api/orchestra")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(set(body), {"servizio", "pronto", "bootstrap"})
        self.assertEqual(body["servizio"], "Raffaello Orchestra")
        self.assertIs(body["pronto"], True)
        self.assertEqual(set(body["bootstrap"]), {
            "schema", "protocol_id", "version", "state", "authority", "persistent",
        })
        self.assertEqual(body["bootstrap"]["schema"], "R3_AI_BOOTSTRAP_V1")
        self.assertEqual(body["bootstrap"]["state"], "ACTIVE_REQUEST")
        self.assertIs(body["bootstrap"]["persistent"], False)
        self.assertNotIn(self.secret, response.get_data(as_text=True))

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
