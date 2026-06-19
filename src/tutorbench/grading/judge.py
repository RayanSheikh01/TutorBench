"""Rubric-aware grading judge (M6.1).

The grader sees every mark point (description + max marks) and a couple of
worked award anchors, then returns a per-point award with a real justification.
Trusted invariants — clamping to ``[0, point.marks]`` and ``total = sum(...)`` —
are enforced here, not trusted to the model.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from tutorbench.models import MarkAward, Submission

# Few-shot worked award anchors (PLANV2 M4): short, subject-agnostic examples
# that show the model how to reason about partial credit and justify each award.
_ANCHORS = """Example 1 — mark point "State the time complexity" (max 1):
  answer "O(n log n)" → awarded 1, justification "Correct complexity stated."
Example 2 — mark point "Explain why a stack is used" (max 2):
  answer "It stores the return address" → awarded 1, justification "Names one
  correct use but does not explain the LIFO ordering, so 1 of 2."
"""

_SYSTEM = (
    "You are a precise GCSE examiner. Grade the student's answer against the "
    "mark scheme one mark point at a time. For each mark point award between 0 "
    "and its maximum marks and give a one-sentence justification. Be strict: "
    "award marks only for what the answer actually demonstrates."
)


class PointAward(BaseModel):
    """A single mark point's award as returned by the model."""

    awarded_marks: int = Field(ge=0)
    justification: str = Field(min_length=1)


class GradeResult(BaseModel):
    """The model's per-point grading output (one entry per mark point)."""

    awards: list[PointAward] = Field(min_length=1)


def grade(question, answer, *, client, model) -> Submission:
    """Grade the answer against the mark scheme; return a clamped Submission."""
    messages = _build_messages(question, answer)
    result = client.structured(model=model, messages=messages, schema=GradeResult)
    if len(result.awards) != len(question.mark_scheme):
        raise ValueError(
            f"grader returned {len(result.awards)} awards for "
            f"{len(question.mark_scheme)} mark points"
        )
    awards = _clamp_awards(result.awards, question.mark_scheme)
    total = sum(a.awarded_marks for a in awards)
    feedback = _build_feedback(awards, total, question.marks)
    return Submission(
        question_id=question.id,
        student_answer=answer,
        awarded=awards,
        total=total,
        feedback=feedback,
    )


def _build_messages(question, answer) -> list[dict]:
    """Build grading messages enumerating every mark point + worked anchors."""
    scheme_lines = "\n".join(
        f"  {i + 1}. ({mp.marks} mark{'s' if mp.marks != 1 else ''}) {mp.description}"
        for i, mp in enumerate(question.mark_scheme)
    )
    user = (
        f"Question (total {question.marks} marks): {question.stem}\n\n"
        f"Mark scheme — award each point independently:\n{scheme_lines}\n\n"
        f"Worked examples of awarding marks:\n{_ANCHORS}\n"
        f"Student answer:\n{answer}\n\n"
        f"Return one award per mark point, in order."
    )
    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user},
    ]


def _clamp_awards(raw_awards, mark_scheme) -> list[MarkAward]:
    """Clamp each award to ``[0, point.marks]``; keep the model's justification."""
    awards = []
    for mp, raw in zip(mark_scheme, raw_awards):
        awarded = max(0, min(mp.marks, int(raw.awarded_marks)))
        awards.append(
            MarkAward(
                point=mp.description,
                awarded_marks=awarded,
                justification=raw.justification,
            )
        )
    return awards


def _build_feedback(awards, total, marks) -> str:
    """Aggregate per-point justifications into the submission feedback."""
    lines = [f"Awarded {total}/{marks} marks."]
    for a in awards:
        lines.append(f"- {a.point}: {a.awarded_marks} — {a.justification}")
    return "\n".join(lines)
