"""TERZI — Token-Efficient Relevance & Zero-loss Inference.

Candidate context-purification layer for R³.  TERZI compresses evidence by
selection, never by silently rewriting source text.
"""

from .core import (
    ContextCapsule,
    DistillationPolicy,
    chunk_state,
    distill,
    decision_signature,
)

__all__ = [
    "ContextCapsule",
    "DistillationPolicy",
    "chunk_state",
    "distill",
    "decision_signature",
]

PROTOCOL = "TERZI/0.1"
ORIGIN = "Claudio Terzi [CT-LGAI-001]"
