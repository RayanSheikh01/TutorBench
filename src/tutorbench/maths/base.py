"""Base class + build gate for deterministic Maths templates.

A template randomises params, renders a stem, and computes the model answer with
SymPy. `build_question` runs an independent SymPy re-derivation (`_verify`) and only
returns a Question marked verified=True. Mismatch raises — we never emit an
unverified Maths question (the faithfulness constraint).
"""
from abc import ABC, abstractmethod
from random import Random

from tutorbench.models import Question


class Template(ABC):
    spec_code: str
    topic: str
    subtopic: str

    @abstractmethod
    def generate(self, rng: Random) -> Question:
        """Produce a Question (verified=False) from a seeded RNG."""

    @abstractmethod
    def _verify(self, q: Question) -> bool:
        """Independently re-derive the answer in SymPy; True if it matches."""


def build_question(template: Template, rng: Random) -> Question:
    """Generate then verify; return a verified Question or raise."""
    q = template.generate(rng)
    if not template._verify(q):
        raise ValueError(
            f"verification failed for {type(template).__name__} (id={q.id})"
        )
    return q.model_copy(update={"verified": True})
