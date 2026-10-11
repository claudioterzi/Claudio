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
        env = {"LETTA_API_KEY": "secret", "LETTA_AGENT_ID": "agent-123"}
        with patch.dict(os.environ, env, clear=False):
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


class _A1Client:
    """Stateful Letta mock. mode: exact | unknown | formatted | no_bind."""

    def __init__(self, mode, *args, **kwargs):
        self.mode = mode
        self.bound = set()
        self.block = None
        self.deleted = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def _agent(self, url):
        return url.split("/agents/", 1)[1].split("/", 1)[0]

    def get(self, url):
        if url.endswith("/v1/agents/"):
            return _Response(200, {"items": [{"id": "agent-a"}, {"id": "agent-b"}]})
        if "/core-memory/blocks/" in url:
            aid = self._agent(url)
            if aid in self.bound and self.block:
                return _Response(200, self.block)
            return _Response(404, {})
        if url.endswith("/core-memory/blocks"):
            aid = self._agent(url)
            items = [self.block] if aid in self.bound and self.block else []
            return _Response(200, items)
        if "/v1/blocks/" in url:
            return _Response(404 if self.deleted else 200, {})
        if "/v1/agents/" in url:
            return _Response(200, {"agent_type": "memgpt_v2_agent",
                                   "llm_config": {"model": "m-test", "model_endpoint_type": "x",
                                                  "context_window": 32000}})
        raise AssertionError(url)

    def post(self, url, json=None):
        if url.endswith("/v1/blocks/"):
            self.block = {"id": "block-1", "label": json["label"], "value": json["value"]}
            return _Response(200, {"id": "block-1"})
        if "/messages" in url:
            aid = self._agent(url)
            canary = self.block["value"].split("canary=", 1)[1].split("\n", 1)[0] if self.block else ""
            if aid in self.bound and self.mode == "exact":
                answer = canary
            elif aid in self.bound and self.mode == "formatted":
                answer = f"The canary is: {canary}."
            else:
                answer = "UNKNOWN"
            return _Response(200, {"messages": [
                {"message_type": "reasoning_message", "reasoning": "x"},
                {"message_type": "assistant_message", "content": answer}]})
        raise AssertionError(url)

    def patch(self, url):
        aid = self._agent(url)
        if "/attach/" in url:
            if self.mode != "no_bind":
                self.bound.add(aid)
            return _Response(200, {})
        if "/detach/" in url:
            self.bound.discard(aid)
            return _Response(200, {})
        raise AssertionError(url)

    def delete(self, url):
        self.deleted = True
        self.bound.clear()
        return _Response(200, {})


class LettaPhaseA1Tests(unittest.TestCase):
    def _run(self, mode):
        env = {"LETTA_API_KEY": "secret", "LETTA_AGENT_ID": "agent-a"}
        with patch.dict(os.environ, env, clear=False):
            with patch.object(app.secrets, "token_urlsafe", return_value="TESTCANARY"):
                with patch.object(app.secrets, "token_hex", return_value="abc123"):
                    with patch.object(app.httpx, "Client", side_effect=lambda *a, **kw: _A1Client(mode)):
                        return app.run_letta_phase_a1()

    def test_classifier(self):
        c = "R3A1-X"
        self.assertEqual(app.classify_letta_answer("R3A1-X", c), "EXACT_CANARY")
        self.assertEqual(app.classify_letta_answer(" unknown. ", c), "UNKNOWN")
        self.assertEqual(app.classify_letta_answer("It is R3A1-X", c), "CONTAINS_CANARY_NOT_EXACT")
        self.assertEqual(app.classify_letta_answer("no idea", c), "OTHER")

    def test_exact_mode_passes_with_verified_binding(self):
        r = self._run("exact")
        self.assertIsNone(r["error"])
        self.assertTrue(r["ab_diag_pass"])
        self.assertTrue(r["arm_a"]["binding"]["attach_visible"])
        self.assertEqual(r["arm_b"]["diagnosis"], "PASS")
        self.assertTrue(r["negative_after_detach_b"]["binding_after_detach"]["absent"])
        self.assertTrue(r["workers"]["A"]["is_configured_worker"])
        self.assertEqual(r["workers"]["A"]["model"], "m-test")
        self.assertTrue(r["cleanup"]["block_gone"])
        self.assertTrue(r["cleanup"]["a_absent_after"])
        self.assertIn("assistant_message", r["arm_a"]["answer"]["message_types"])
        self.assertNotIn("TESTCANARY", str(r))

    def test_unknown_mode_points_to_model_not_binding(self):
        r = self._run("unknown")
        self.assertFalse(r["ab_diag_pass"])
        self.assertEqual(r["arm_a"]["diagnosis"], "BLOCK_BOUND_BUT_NOT_USED_BY_MODEL")

    def test_formatted_mode_points_to_output_criterion(self):
        r = self._run("formatted")
        self.assertEqual(r["arm_a"]["diagnosis"], "MEMORY_WORKS_OUTPUT_FORMAT_FAILS")
        self.assertNotIn("TESTCANARY", str(r))

    def test_no_bind_mode_points_to_binding(self):
        r = self._run("no_bind")
        self.assertEqual(r["arm_a"]["diagnosis"], "BINDING_OR_API_PROBLEM")
        self.assertFalse(r["arm_a"]["binding"]["attach_visible"])


if __name__ == "__main__":
    unittest.main()
