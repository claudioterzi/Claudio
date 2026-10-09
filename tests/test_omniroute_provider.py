import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

from sdq1.llm.providers import omniroute_provider as omni
from sdq1.llm.router import LLMRouter, PROVIDER_REGISTRY, RegolaRouter


class _FakeCompletions:
    def __init__(self, owner):
        self.owner = owner

    def create(self, **kwargs):
        self.owner.last_request = kwargs
        return SimpleNamespace(
            model="resolved/provider-model",
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="omniroute-ok"),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
        )


class _FakeOpenAI:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.last_request = None
        self.chat = SimpleNamespace(completions=_FakeCompletions(self))
        self.__class__.instances.append(self)


class OmniRouteProviderTests(unittest.TestCase):
    def setUp(self):
        _FakeOpenAI.instances.clear()

    def test_remote_endpoint_without_key_is_unavailable(self):
        env = {
            "OMNIROUTE_BASE_URL": "https://router.example/v1",
            "OMNIROUTE_LOCAL_NO_AUTH": "1",
        }
        with patch.dict(os.environ, env, clear=True), patch.object(omni, "_OK", True), patch.object(omni, "OpenAI", _FakeOpenAI):
            provider = omni.OmniRouteProvider(modello="auto", api_key=None)
        self.assertFalse(provider.disponibile)
        self.assertEqual(_FakeOpenAI.instances, [])

    def test_loopback_no_auth_requires_explicit_opt_in(self):
        with patch.dict(os.environ, {"OMNIROUTE_BASE_URL": "http://127.0.0.1:20128/v1"}, clear=True), patch.object(omni, "_OK", True), patch.object(omni, "OpenAI", _FakeOpenAI):
            provider = omni.OmniRouteProvider(modello="auto", api_key=None)
        self.assertFalse(provider.disponibile)

        env = {
            "OMNIROUTE_BASE_URL": "http://127.0.0.1:20128/v1",
            "OMNIROUTE_LOCAL_NO_AUTH": "1",
        }
        with patch.dict(os.environ, env, clear=True), patch.object(omni, "_OK", True), patch.object(omni, "OpenAI", _FakeOpenAI):
            provider = omni.OmniRouteProvider(modello="auto", api_key=None)
        self.assertTrue(provider.disponibile)
        self.assertEqual(_FakeOpenAI.instances[-1].kwargs["base_url"], "http://127.0.0.1:20128/v1")
        self.assertEqual(_FakeOpenAI.instances[-1].kwargs["api_key"], "omniroute-local-no-auth")

    def test_remote_key_enables_gateway_and_preserves_route_metadata(self):
        env = {
            "OMNIROUTE_BASE_URL": "https://router.example/v1",
            "OMNIROUTE_API_KEY": "test-only",
        }
        with patch.dict(os.environ, env, clear=True), patch.object(omni, "_OK", True), patch.object(omni, "OpenAI", _FakeOpenAI):
            provider = omni.OmniRouteProvider(
                modello="auto/reasoning:pro",
                api_key=None,
                temperatura=0,
                max_token=512,
            )
            response = provider.completa("system", "user")

        self.assertTrue(response.via_api)
        self.assertEqual(response.testo, "omniroute-ok")
        self.assertEqual(response.provider, "omniroute")
        self.assertEqual(response.metadata["requested_model"], "auto/reasoning:pro")
        self.assertEqual(response.metadata["resolved_model"], "resolved/provider-model")
        self.assertEqual(response.metadata["input_tokens"], 11)
        self.assertEqual(response.metadata["output_tokens"], 7)
        request = _FakeOpenAI.instances[-1].last_request
        self.assertEqual(request["model"], "auto/reasoning:pro")
        self.assertEqual(request["temperature"], 0)

    def test_router_falls_back_when_omniroute_is_not_configured(self):
        rules = [RegolaRouter(profilo="default", cascata=["omniroute", "stub"])]
        with patch.dict(os.environ, {}, clear=True):
            router = LLMRouter(opts_globali={}, regole=rules)
            result = router.chiama("system", "hello", cache=False)
        self.assertEqual(result.risposta.provider, "stub")
        self.assertEqual(result.provider_usati, ["omniroute", "stub"])

    def test_registry_and_profiles_use_omniroute_without_clouding_local_profile(self):
        self.assertIn("omniroute", PROVIDER_REGISTRY)
        data = yaml.safe_load(Path("sdq1/config/sdq1.yaml").read_text(encoding="utf-8"))
        profiles = {item["profilo"]: item for item in data["router"]["regole"]}

        self.assertEqual(profiles["default"]["cascata"][0], "omniroute")
        self.assertEqual(profiles["veloce"]["modelli"]["omniroute"], "auto/fast")
        self.assertEqual(profiles["economia"]["modelli"]["omniroute"], "auto/cheap")
        self.assertEqual(profiles["ragionamento"]["modelli"]["omniroute"], "auto/reasoning:pro")
        self.assertNotIn("omniroute", profiles["locale"]["cascata"])


if __name__ == "__main__":
    unittest.main()
