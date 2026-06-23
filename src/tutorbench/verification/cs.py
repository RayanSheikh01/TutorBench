"""CS question verification — hybrid gate (M3, PLANV2 Step 3).

A generated Question is never trusted on its face. It must pass:
  1. cheap constraint checks (no LLM), then
  2. self-consistency: re-answer the stem ``n`` times and require the agreement
     fraction to clear ``threshold``.

``build_cs_question`` wraps generate + verify with a capped, logged retry loop;
it returns a Question with ``verified=True`` or raises — never emits an
unverified item.
"""
from __future__ import annotations

import logging

from ..generation.cs import CSDraft, generate_cs_question
from ..models import Difficulty, QType, Question, Subject
from ..spec.loader import Objective

log = logging.getLogger(__name__)


def _constraints_ok(q: Question, objective: Objective) -> bool:
    """Cheap, LLM-free sanity checks (Pydantic already enforces marks-sum)."""
    return (
        q.subject is Subject.cs
        and bool(q.stem.strip())
        and len(q.mark_scheme) >= 1
        and q.spec_code == objective.code
        and 0 < q.marks <= objective.default_marks
    )


def _reanswer_agrees(q: Question, *, client, model: str, n: int) -> float:
    """Independently re-answer the stem ``n`` times; fraction matching model_answer.

    The re-answer is generated fresh from the stem only (never shown the stored
    ``model_answer``); agreement is the self-consistency confidence.
    """
    matches = 0
    for _ in range(n):
        messages = [
            {"role": "system", "content": "You are an expert OCR GCSE Computer Science student."},
            {"role": "user", "content": f"Answer this question:\n\n{q.stem}"},
        ]
        answer = client.structured(model=model, messages=messages, schema=CSDraft)
        if answer.model_answer.strip() == q.model_answer.strip():
            matches += 1
    return matches / n




def verify_cs_question(
    q: Question,
    objective: Objective,
    *,
    client,
    model: str,
    n: int = 3,
    threshold: float = 0.66,
) -> bool:
    """True iff the question passes constraints and clears the agreement threshold."""
    if not _constraints_ok(q, objective):
        return False
    return _reanswer_agrees(q, client=client, model=model, n=n) >= threshold


def build_cs_question(
    objective: Objective,
    difficulty: Difficulty,
    qtype: QType,
    *,
    client,
    model: str,
    max_retries: int = 3,
    n: int = 3,
    threshold: float = 0.66,
) -> Question:
    """Generate + verify with capped retries; return verified Question or raise."""
    for attempt in range(1, max_retries + 1):
        q = generate_cs_question(objective, difficulty, qtype, client=client, model=model)
        if verify_cs_question(
            q, objective, client=client, model=model, n=n, threshold=threshold
        ):
            return q.model_copy(update={"verified": True})
        log.warning(
            "CS question verification failed (attempt %d/%d) for %s",
            attempt,
            max_retries,
            objective.code,
        )
    raise ValueError(
        f"Generated question failed verification after {max_retries} attempts"
    )
