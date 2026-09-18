"""Private browser proxy and shared engine tests. No external requests."""
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from api import raffaello, tarot_alpha


class RaffaelloBridgeTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"RAFFAELLO_BRIDGE_SECRET": "test-secret-" * 4,
                                         "RAFFAELLO_BOT_URL": "https://bot.example.invalid"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = raffaello.app.test_client()

    def test_engine_is_private_and_browser_cannot_call_it(self):
        with patch.object(raffaello, "_engine") as engine:
            for headers in ({}, {"X-Raffaello": "1"}, {"X-Raffaello-Secret": "wrong"}):
                response = self.client.post("/api/raffaello/engine", json={"domanda": "x"}, headers=headers)
                self.assertEqual(response.status_code, 401)
            engine.assert_not_called()

    def test_unlinked_request_never_reaches_private_bot(self):
        with patch.object(raffaello, "_bridge") as bridge:
            response = self.client.get("/api/raffaello/readings")
            self.assertEqual(response.status_code, 401)
            bridge.assert_not_called()

    def test_pairing_token_is_http_only_and_not_returned_in_json(self):
        with patch.object(raffaello, "_bridge", return_value={"token": "test-session-token"}):
            response = self.client.post("/api/raffaello/link", json={"code": "test"}, headers={"X-Raffaello": "1"})
        self.assertEqual(response.get_json(), {"linked": True})
        cookie = response.headers["Set-Cookie"]
        for value in ("HttpOnly", "Secure", "SameSite=Strict", "Path=/"):
            self.assertIn(value, cookie)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)

    def test_csrf_and_arbitrary_proxy_paths_are_rejected(self):
        self.client.set_cookie(raffaello.COOKIE, "test-session-token")
        with patch.object(raffaello, "_bridge") as bridge:
            self.assertEqual(self.client.post("/api/raffaello/link", json={"code": "x"}).status_code, 403)
            self.assertEqual(self.client.post("/api/raffaello/link", json={"code": "x"}, headers={"X-Raffaello": "1", "Origin": "https://hostile.invalid"}).status_code, 403)
            self.assertEqual(self.client.get("/api/raffaello/anything").status_code, 404)
            bridge.assert_not_called()

    def test_authenticated_request_forwards_session_not_client_owner(self):
        self.client.set_cookie(raffaello.COOKIE, "test-session-token")
        with patch.object(raffaello, "_bridge", return_value={"letture": []}) as bridge:
            self.assertEqual(self.client.get("/api/raffaello/readings").status_code, 200)
        bridge.assert_called_once_with("GET", "/readings", None, "test-session-token")

    def test_alpha_engine_uses_the_canon_and_prior_context(self):
        card = json.loads((Path(__file__).parents[1] / "tarocchi_quantici_alpha.json").read_text())["carte"][0]
        snapshot = {"domanda": "Originale", "contesto": "Contesto", "carte": [{"carta": card["nome"], "asse": "ovest", "polarita": "ombra", "significato_canonico": "FORGED"}], "lettura": {"messaggio": "Precedente"}}
        with patch.object(tarot_alpha, "_ai_follow_up", return_value=({"risposta": "Answer", "carte_richiamate": [card["nome"]]}, {"provider": "test"})) as ai:
            response = self.client.post("/api/raffaello/engine", json={"domanda": "E poi?", "lettura": snapshot}, headers={"X-Raffaello-Secret": "test-secret-" * 4})
        self.assertEqual(response.status_code, 200)
        args = ai.call_args.args
        self.assertEqual(args[0][0]["significato_canonico"], card["ombra"]["ovest"])
        self.assertEqual(args[1], "E poi?")
        self.assertEqual(args[2], "Originale")
        self.assertEqual(args[4]["messaggio"], "Precedente")

    def test_missing_reading_or_polarity_never_draws_random_cards(self):
        for snapshot in ({"carte": []}, {"carte": [{"carta": "X", "asse": "nord"}]}):
            with patch.object(tarot_alpha, "_normalize_items") as normalizer:
                response = self.client.post("/api/raffaello/engine", json={"domanda": "E poi?", "lettura": snapshot}, headers={"X-Raffaello-Secret": "test-secret-" * 4})
                self.assertEqual(response.status_code, 400)
                normalizer.assert_not_called()

    def test_missing_provider_is_an_error_not_a_fake_interpretation(self):
        card = tarot_alpha._deck()[0]
        with patch.object(tarot_alpha, "_ai_follow_up", return_value=(None, None)):
            response = self.client.post("/api/raffaello/engine", json={"domanda": "E poi?", "lettura": {"carte": [{"carta": card["nome"], "asse": "est", "polarita": "luce"}]}}, headers={"X-Raffaello-Secret": "test-secret-" * 4})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("risposta", response.get_json())

    def test_oversize_and_unconfigured_status(self):
        response = self.client.post("/api/raffaello/link", json={"code": "x" * 300000})
        self.assertEqual(response.status_code, 413)
        with patch.dict(os.environ, {"RAFFAELLO_BRIDGE_SECRET": ""}):
            self.assertFalse(self.client.get("/api/raffaello/status").get_json()["configured"])


if __name__ == "__main__":
    unittest.main()
