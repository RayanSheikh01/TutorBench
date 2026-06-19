import pytest

from tutorbench.generation.cs import _stem_id
from tutorbench.grading.judge import GradeResult, PointAward, _build_messages, grade
from tutorbench.models import (
    Difficulty,
    MarkAward,
    MarkPoint,
    QType,
    Question,
    Subject,
    Submission,
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


def _result(awards: list[tuple[int, str]]) -> GradeResult:
    """A judge result: (awarded_marks, justification) per mark point."""
    return GradeResult(
        awards=[
            PointAward(awarded_marks=m, justification=j) for m, j in awards
        ]
    )


def test_grade_clamps_awards_and_sums_to_total(fake_llm):
    q = _question()
    # raw awards: 2x exact, 1x over-max (10 -> clamp to point max 4), 1x zero.
    raw = [
        (2, "Correct conversion of high nibble."),
        (2, "Correct conversion of low nibble."),
        (10, "Over-generous; clamped to the point maximum."),
        (0, "No working shown."),
    ]
    client = fake_llm([_result(raw)])

    submission = grade(q, "some answer", client=client, model="m")

    assert isinstance(submission, Submission)
    assert submission.question_id == q.id
    assert submission.student_answer == "some answer"
    awarded = submission.awarded
    assert all(isinstance(a, MarkAward) for a in awarded)
    assert awarded[0].awarded_marks == 2
    assert awarded[1].awarded_marks == 2
    assert awarded[2].awarded_marks == 4  # clamped from 10 to point max 4
    assert awarded[3].awarded_marks == 0
    assert submission.total == 8  # 2 + 2 + 4 + 0


def test_grade_surfaces_real_justifications(fake_llm):
    q = _question()
    raw = [
        (2, "High nibble 0000 is correct."),
        (2, "Low nibble 1101 is correct."),
        (4, "Method and place values fully shown."),
        (2, "Final answer matches the model answer."),
    ]
    client = fake_llm([_result(raw)])

    submission = grade(q, ANSWER, client=client, model="m")

    # Per-point justifications come from the model, not a hardcoded literal.
    justifications = [a.justification for a in submission.awarded]
    assert justifications == [j for _, j in raw]
    assert "justified" not in justifications
    # Per-point feedback is aggregated into the submission feedback.
    for _, j in raw:
        assert j in submission.feedback


def test_build_messages_enumerates_every_mark_point_and_anchors():
    q = _question()
    messages = _build_messages(q, ANSWER)
    prompt = "\n".join(m["content"] for m in messages)

    # Every mark point (description + its max marks) is in the prompt.
    for mp in q.mark_scheme:
        assert mp.description in prompt
        assert str(mp.marks) in prompt
    # The question stem and the answer being graded are present.
    assert q.stem in prompt
    assert ANSWER in prompt
    # Few-shot worked award anchors guide the grader (PLANV2 M4).
    assert prompt.lower().count("example") >= 1


def test_grade_raises_when_award_count_mismatches_mark_scheme(fake_llm):
    q = _question()
    # Only three awards for a four-point scheme: the grader must reject this,
    # not silently drop a mark point.
    raw = [(2, "a"), (2, "b"), (2, "c")]
    client = fake_llm([_result(raw)])

    with pytest.raises(ValueError):
        grade(q, ANSWER, client=client, model="m")
