import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import nacl.signing

import r3.gpt_omniroute_node as mod


class _FakeProvider:
    def __init__(self, modello, api_key=None, **kwargs):
        self.modello = modello
        self.disponibile = True

    def completa(self, system, user):
        return SimpleNamespace(
            via_api=True,
            testo="omniroute-reasoning-ok",
            errore=None,
            provider="omniroute",
            modello=self.modello,
            metadata={
                "gateway": "omniroute",
                "requested_model": self.modello,
                "resolved_model": "openai/example-model",
            },
        )


class R3GPTNodeOmniRouteTests(unittest.TestCase):
    def test_fail_closed_without_persistent_key(self):
        env = {
            "R3_GPT_NODE_ENABLED": "1",
            "R3_GPT_ENROLLMENT_STATUS": "ACTIVE",
        }
        with patch.dict(os.environ, env, clear=True), patch.object(mod, "OmniRouteProvider", _FakeProvider):
            node = mod.R3GPTNode()
            status = node.status().as_dict()

        self.assertTrue(status["omniroute_available"])
        self.assertFalse(status["identity_ready"])
        self.assertFalse(status["ready_for_enrollment"])
        self.assertFalse(status["outbound_peer_transport_implemented"])
        self.assertFalse(status["canonical_memory_write"])

    def test_omniroute_reasoning_does_not_grant_authority(self):
        seed = bytes(range(32)).hex()
        env = {
            "R3_GPT_NODE_ENABLED": "1",
            "R3_GPT_SIGNING_KEY_HEX": seed,
        }
        with patch.dict(os.environ, env, clear=True), patch.object(mod, "OmniRouteProvider", _FakeProvider):
            node = mod.R3GPTNode()
            out = node.reason("system", "hello")

        self.assertEqual(out["node_id"], "R3-GPT-NODE/1")
        self.assertEqual(out["provider"], "omniroute")
        self.assertEqual(out["authority"], "NONE_NOT_ENROLLED")
        self.assertFalse(out["canonical_memory_write"])
        self.assertEqual(out["metadata"]["gateway"], "omniroute")

    def test_enrollment_proof_of_possession_verifies(self):
        seed = bytes(range(32))
        env = {
            "R3_GPT_NODE_ENABLED": "1",
            "R3_GPT_SIGNING_KEY_HEX": seed.hex(),
        }
        with patch.dict(os.environ, env, clear=True), patch.object(mod, "OmniRouteProvider", _FakeProvider):
            node = mod.R3GPTNode()
            proof = node.sign_enrollment_challenge(b"r3-enrollment-test")

        verify = nacl.signing.VerifyKey(bytes.fromhex(proof["verify_key_hex"]))
        verify.verify(b"r3-enrollment-test", bytes.fromhex(proof["signature_hex"]))
        self.assertEqual(proof["node_id"], "R3-GPT-NODE/1")
        self.assertTrue(node.status().ready_for_enrollment)
        self.assertFalse(node.status().outbound_peer_transport_implemented)


if __name__ == "__main__":
    unittest.main()