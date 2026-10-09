"""Capability registry for Raffaello Creative Studio.

External systems are described here before integration so the Studio can track
what is discovered, what is only a candidate, and what has actually been
verified/adopted.
"""

from .openmontage import OPENMONTAGE_CAPABILITY, CapabilityRecord

__all__ = ["CapabilityRecord", "OPENMONTAGE_CAPABILITY"]
