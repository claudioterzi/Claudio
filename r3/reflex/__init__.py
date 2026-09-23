"""R³∞ System One reflex candidate.

Candidate capability only: it does not write canonical memory and it does not
authorize external actions by itself.
"""
from .decider import Decision, ReflexDecider
from .runtime import Outcome, ReflexRuntime

__all__ = ["Decision", "ReflexDecider", "Outcome", "ReflexRuntime"]
