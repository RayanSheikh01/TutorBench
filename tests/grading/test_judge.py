import pytest

from tutorbench.generation.cs import CSDraft, _stem_id
from tutorbench.grading.judge import grade
from tutorbench.models import (
    Difficulty,
    MarkAward,
    MarkPoint,
    QType,
    Question,
    Subject,
)

STEM = "Convert the denary number 13 to 8-bit binary."
ANSWER = "00001101"

# Four mark points so we can exercise per-point clamping.
# Point maxes: [2, 2, 4, 2] (sum 10 == question.marks).
_POINT_MAXES = [2, 2, 4, 2]


def _question() -> Question:
    return Question(
        id=_stem_id(STEM),
        subject=Subject.cs,
        spec_code="CS-1.2.1",
        topic="Data representation",
        subtopic="Binary",
        difficulty=Difficulty.medium,
        marks=sum(_POINT_MAXES),
        type=QType.short_answer,
        stem=STEM,
        model_answer=ANSWER,
        working="13 = 8 + 4 + 1 -> 0000 1101.",
        mark_scheme=[
            MarkPoint(description=f"Point {i}", marks=m)
            for i, m in enumerate(_POINT_MAXES)
        ],
        verified=False,
    )


def _draft(raw_awards: list[int]) -> CSDraft:
    """A judge draft whose mark_scheme marks are the raw awards to clamp."""
    return CSDraft(
        topic="Data representation",
        subtopic="Binary",
        marks=sum(raw_awards) or 1,
        stem=STEM,
        model_answer=ANSWER,
        working="13 = 8 + 4 + 1 -> 0000 1101.",
        mark_scheme=[
            MarkPoint(description=f"Point {i}", marks=m)
            for i, m in enumerate(raw_awards)
        ],
    )


def test_grade_clamps_awards_and_sums_to_total(fake_llm):
    q = _question()
    # raw awards: 2x exact, 1x over-max (10 -> clamp to point max 4), 1x zero.
    # (Negative raws are unrepresentable: MarkPoint.marks is ge=0, so the
    # max(0, ...) lower guard in _clamp_awards is unreachable via the schema.)
    raw_awards = [2, 2, 10, 0]
    client = fake_llm([_draft(raw_awards)])

    submission = grade(q, "some answer", client=client, model="m")

    assert isinstance(submission, list)
    assert all(isinstance(a, MarkAward) for a in submission)
    assert submission[0].awarded_marks == 2
    assert submission[1].awarded_marks == 2
    assert submission[2].awarded_marks == 4  # clamped from 10 to point max 4
    assert submission[3].awarded_marks == 0
    total = sum(a.awarded_marks for a in submission)
    assert total == 8  # 2 + 2 + 4 + 0
