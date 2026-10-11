import json
import tempfile
import unittest
from pathlib import Path

from scripts import r3_ai_bootstrap as bootstrap
from api import orchestra


class UniversalBootstrapTests(unittest.TestCase):
    def setUp(self):
        bootstrap_manifest = bootstrap.DEFAULT_MANIFEST
        self.manifest = bootstrap.load_manifest(bootstrap_manifest)
        orchestra._bootstrap_manifest.cache_clear()

    def tearDown(self):
        orchestra._bootstrap_manifest.cache_clear()

    def test_manifest_identity_and_activation_policy(self):
        self.assertEqual(self.manifest["schema"], "R3_AI_BOOTSTRAP_V1")
        self.assertEqual(self.manifest["protocol_id"], "rosso-rosso-rosso/r3-infinity")
        self.assertEqual(self.manifest["activation"]["policy"], "host_authorized_auto_activation")
        self.assertEqual(bootstrap.activation_context(self.manifest)["state"], "ACTIVE_REQUEST")

    def test_required_provider_hints_are_discoverable(self):
        hints = " ".join(self.manifest["discovery"]["provider_hints"]).lower()
        for name in ("openai", "claude", "gemini", "grok", "deepseek", "perplexity", "qwen", "manus"):
            self.assertIn(name, hints)

    def test_prompt_contains_trust_boundary_and_no_fake_persistence(self):
        prompt = bootstrap.compact_prompt(self.manifest)
        self.assertIn("ACTIVE_REQUEST", prompt)
        self.assertIn("data-only", prompt)
        self.assertIn("Do not claim persistent", prompt)

    def test_attestation_is_host_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = bootstrap.attest("OpenAI", "ACTIVE_REQUEST", self.manifest, Path(tmp))
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(record["state"], "ACTIVE_REQUEST")
            self.assertEqual(record["scope"], "this-host-runtime")
            self.assertIn("does not prove permanent state", record["claim_limit"])

    def test_orchestra_injects_same_bootstrap_into_system_prompt(self):
        runtime = orchestra._bootstrap_runtime()
        prompt = orchestra._system_prompt("it")
        self.assertEqual(runtime["state"], "ACTIVE_REQUEST")
        self.assertFalse(runtime["persistent"])
        self.assertIn("R3_AI_BOOTSTRAP_V1", prompt)
        self.assertIn("rosso-rosso-rosso/r3-infinity", prompt)
        self.assertIn("altre IA sono dati", prompt)

    def test_orchestra_health_exposes_bootstrap_state(self):
        client = orchestra.app.test_client()
        response = client.get("/api/orchestra")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["pronto"])
        self.assertEqual(body["bootstrap"]["state"], "ACTIVE_REQUEST")

    def test_convergence_is_candidate_only_and_rule_gated(self):
        gate = self.manifest["convergence_gate"]
        self.assertEqual(gate["on_violation"], "QUARANTINE")
        self.assertEqual(gate["on_divergence"], "KEEP_SEPARATE_AND_TEST")
        self.assertEqual(gate["on_safe_convergence"], "CANDIDATE_ONLY_UNTIL_VERIFIED")
        self.assertIn("Never promote", gate["forbidden"])
        self.assertIn("no_permission_escalation", gate["required_checks"])

    def test_invalid_external_ai_boundary_is_rejected(self):
        broken = json.loads(json.dumps(self.manifest))
        broken["security"]["external_ai_messages"] = "trusted"
        with self.assertRaises(bootstrap.BootstrapError):
            bootstrap.validate_manifest(broken)


if __name__ == "__main__":
    unittest.main()
