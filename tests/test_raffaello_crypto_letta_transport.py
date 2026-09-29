import os
import unittest
from unittest.mock import patch

from raffaello_crypto_scout import app


class _Response:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload


class _Client:
    def __init__(self, response, *args, **kwargs):
        self.response = response
        self.headers = kwargs.get("headers", {})
        self.last_url = None
        self.last_json = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url):
        self.last_url = url
        return self.response

    def post(self, url, json=None):
        self.last_url = url
        self.last_json = json
        return self.response




class _PhaseClient:
    def __init__(self, *args, **kwargs):
        self.attached = set()
        self.canary = "R3A-TESTCANARY"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url):
        if url.endswith("/v1/agents/"):
            return _Response(200, {"items": [{"id": "agent-a"}, {"id": "agent-b"}]})
        raise AssertionError(url)

    def post(self, url, json=None):
        if url.endswith("/v1/blocks/"):
            value = json["value"]
            self.canary = value.split("canary=", 1)[1].split("\n", 1)[0]
            return _Response(200, {"id": "block-1"})
        if "/messages" in url:
            agent_id = url.split("/agents/", 1)[1].split("/", 1)[0]
            answer = self.canary if agent_id in self.attached else "UNKNOWN"
            return _Response(
                200,
                {"messages": [{"message_type": "assistant_message", "content": answer}]},
            )
        raise AssertionError(url)

    def patch(self, url):
        agent_id = url.split("/agents/", 1)[1].split("/", 1)[0]
        if "/attach/" in url:
            self.attached.add(agent_id)
            return _Response(200, {})
        if "/detach/" in url:
            self.attached.discard(agent_id)
            return _Response(200, {})
        raise AssertionError(url)

    def delete(self, url):
        self.attached.clear()
        return _Response(200, {})


class LettaTransportTests(unittest.TestCase):
    def test_diagnose_uses_httpx_and_returns_agent_metadata(self):
        response = _Response(
            200,
            {"items": [{"id": "agent-123", "name": "Raffaello"}]},
        )
        with patch.dict(os.environ, {"LETTA_API_KEY": "secret"}, clear=False):
            with patch.object(app.httpx, "Client", side_effect=lambda *a, **kw: _Client(response, *a, **kw)):
                result = app.diagnose_letta_api()
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], 200)
        self.assertEqual(result["agents"], [{"id": "agent-123", "name": "Raffaello"}])

    def test_diagnose_preserves_http_error_body_without_secret(self):
        response = _Response(403, {}, "blocked")
        with patch.dict(os.environ, {"LETTA_API_KEY": "secret"}, clear=False):
            with patch.object(app.httpx, "Client", side_effect=lambda *a, **kw: _Client(response, *a, **kw)):
                result = app.diagnose_letta_api()
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], 403)
        self.assertEqual(result["body"], "blocked")
        self.assertNotIn("secret", str(result))

    def test_blind_probe_extracts_assistant_message(self):
        response = _Response(
            200,
            {
                "messages": [
                    {
                        "message_type": "assistant_message",
                        "content": "CANARY-OK",
                    }
                ]
            },
        )
        env = {"LETTA_API_KEY": "secret", "LETTA_AGENT_ID": "agent-123"}
        with patch.dict(os.environ, env, clear=False):
            with patch.object(app.httpx, "Client", side_effect=lambda *a, **kw: _Client(response, *a, **kw)):
                result = app.blind_letta_probe()
        self.assertEqual(result["status"], 200)
        self.assertEqual(result["answer"], "CANARY-OK")

    def test_generic_cooperation_message_is_bounded(self):
        with self.assertRaises(ValueError):
            app.letta_message("")
        with self.assertRaises(ValueError):
            app.letta_message("x" * 8001)

    def test_generic_cooperation_message_uses_configured_agent(self):
        response = _Response(
            200,
            {
                "messages": [
                    {
                        "message_type": "assistant_message",
                        "content": "COOP-OK",
                    }
                ]
            },
        )
        env = {"LETTA_API_KEY": "secret", "LETTA_AGENT_ID": "agent-123"}
        with patch.dict(os.environ, env, clear=False):
            with patch.object(app.httpx, "Client", side_effect=lambda *a, **kw: _Client(response, *a, **kw)):
                result = app.letta_message("Conferma cooperazione")
        self.assertEqual(result["status"], 200)
        self.assertEqual(result["agent_id"], "agent-123")
        self.assertEqual(result["answer"], "COOP-OK")


    def test_phase_a_ab_variant_passes_and_does_not_return_canary(self):
        env = {"LETTA_API_KEY": "secret"}
        with patch.dict(os.environ, env, clear=False):
            with patch.object(app.secrets, "token_urlsafe", return_value="TESTCANARY"):
                with patch.object(app.secrets, "token_hex", return_value="abc123"):
                    with patch.object(app.httpx, "Client", side_effect=lambda *a, **kw: _PhaseClient(*a, **kw)):
                        result = app.run_letta_phase_a()
        self.assertTrue(result["ab_variant_pass"])
        self.assertFalse(result["full_phase_a_with_independent_c"])
        self.assertTrue(result["worker_a_exact"])
        self.assertTrue(result["worker_b_exact"])
        self.assertFalse(result["negative_before_contains_canary"])
        self.assertFalse(result["negative_after_detach_contains_canary"])
        self.assertTrue(all(result["cleanup"].values()))
        self.assertNotIn("R3A-TESTCANARY", str(result))


if __name__ == "__main__":
    unittest.main()
