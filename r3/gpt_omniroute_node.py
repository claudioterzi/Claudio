"""R3-GPT-NODE/1 execution runtime over the existing OmniRoute gateway.

This module deliberately separates:
- execution provider: OmniRoute;
- R3 node identity: Ed25519 key owned by this runtime;
- enrollment/authority: external R3 registry decision.

It does NOT implement receiver submission yet. That remains fail-closed until
R3-GPT-NODE/1 is enrolled by the generic multi-node receiver.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any

import nacl.encoding
import nacl.signing

from sdq1.llm.providers.omniroute_provider import OmniRouteProvider


NODE_ID = "R3-GPT-NODE/1"
_DEFAULT_MODEL = "auto/reasoning:pro"


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _load_signing_key() -> nacl.signing.SigningKey | None:
    """Load the persistent node key from secret storage only.

    Fail closed: unlike r3/node.py, this candidate runtime never generates a
    replacement key on ephemeral disk. Identity continuity requires the key to
    be provisioned explicitly by the operator/secret store.
    """
    raw = os.getenv("R3_GPT_SIGNING_KEY_HEX", "").strip()
    if not raw:
        return None
    try:
        seed = bytes.fromhex(raw)
        if len(seed) != 32:
            return None
        return nacl.signing.SigningKey(seed)
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True)
class GPTNodeStatus:
    node_id: str
    execution_gateway: str
    requested_model: str
    enabled: bool
    omniroute_available: bool
    identity_ready: bool
    enrollment_active: bool
    ready_for_enrollment: bool
    outbound_peer_transport_implemented: bool
    canonical_memory_write: bool
    public_key_sha256: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "execution_gateway": self.execution_gateway,
            "requested_model": self.requested_model,
            "enabled": self.enabled,
            "omniroute_available": self.omniroute_available,
            "identity_ready": self.identity_ready,
            "enrollment_active": self.enrollment_active,
            "ready_for_enrollment": self.ready_for_enrollment,
            "outbound_peer_transport_implemented": self.outbound_peer_transport_implemented,
            "canonical_memory_write": self.canonical_memory_write,
            "public_key_sha256": self.public_key_sha256,
        }


class R3GPTNode:
    """Candidate R3 node whose reasoning backend is OmniRoute.

    OmniRoute is transport/execution only. It does not become the node
    identity, an authority source, or a canonical-memory writer.
    """

    def __init__(self, model: str | None = None) -> None:
        self.node_id = NODE_ID
        self.model = (model or os.getenv("R3_GPT_OMNIROUTE_MODEL") or _DEFAULT_MODEL).strip()
        self.enabled = _truthy("R3_GPT_NODE_ENABLED")
        self.enrollment_active = (
            os.getenv("R3_GPT_ENROLLMENT_STATUS", "").strip().upper() == "ACTIVE"
        )
        self._signing_key = _load_signing_key()
        self._provider = OmniRouteProvider(
            modello=self.model,
            api_key=None,
            temperatura=0,
            max_token=int(os.getenv("R3_GPT_MAX_TOKENS", "4096")),
        )

    @property
    def verify_key_hex(self) -> str | None:
        if self._signing_key is None:
            return None
        return self._signing_key.verify_key.encode(nacl.encoding.HexEncoder).decode()

    def status(self) -> GPTNodeStatus:
        verify_hex = self.verify_key_hex
        fingerprint = (
            hashlib.sha256(bytes.fromhex(verify_hex)).hexdigest()
            if verify_hex is not None
            else None
        )
        identity_ready = self._signing_key is not None
        return GPTNodeStatus(
            node_id=self.node_id,
            execution_gateway="omniroute",
            requested_model=self.model,
            enabled=self.enabled,
            omniroute_available=bool(self._provider.disponibile),
            identity_ready=identity_ready,
            enrollment_active=self.enrollment_active,
            ready_for_enrollment=(
                self.enabled and bool(self._provider.disponibile) and identity_ready
            ),
            outbound_peer_transport_implemented=False,
            canonical_memory_write=False,
            public_key_sha256=fingerprint,
        )

    def reason(self, system: str, user: str) -> dict[str, Any]:
        """Run reasoning through OmniRoute without granting R3 peer authority."""
        if not self.enabled:
            raise RuntimeError("R3-GPT-NODE/1 is disabled")
        if not self._provider.disponibile:
            raise RuntimeError("OmniRoute is unavailable")
        result = self._provider.completa(system, user)
        if not result.via_api or not result.testo:
            raise RuntimeError(result.errore or "OmniRoute returned no usable response")
        return {
            "node_id": self.node_id,
            "authority": "NONE_NOT_ENROLLED" if not self.enrollment_active else "ENROLLED_IDENTITY_ONLY",
            "canonical_memory_write": False,
            "text": result.testo,
            "provider": result.provider,
            "model": result.modello,
            "metadata": dict(result.metadata),
        }

    def sign_enrollment_challenge(self, challenge: bytes) -> dict[str, str]:
        """Proof-of-possession only; not a peer-message signature."""
        if not self.enabled:
            raise RuntimeError("R3-GPT-NODE/1 is disabled")
        if self._signing_key is None:
            raise RuntimeError("persistent R3_GPT_SIGNING_KEY_HEX is required")
        if not challenge:
            raise ValueError("challenge must not be empty")
        signature = self._signing_key.sign(challenge).signature.hex()
        return {
            "node_id": self.node_id,
            "verify_key_hex": self.verify_key_hex or "",
            "challenge_sha256": hashlib.sha256(challenge).hexdigest(),
            "signature_hex": signature,
        }