"""Tests for the core Pydantic data model (M1, PLAN-aligned)."""
import pytest
from pydantic import ValidationError

from tutorbench.models import (
    Difficulty,
    MarkAward,
    MarkPoint,
    QType,
    Question,
    Subject,
    Submission,
)


def _valid_question(**overrides):
    base = dict(
        id="q-1",
        subject=Subject.maths,
        spec_code="M-FUNC-COMP-01",
        topic="Functions",
        subtopic="Composite functions",
        difficulty=Difficulty.medium,
        marks=3,
        type=QType.calculation,
        stem="Find fg(x).",
        model_answer="fg(x) = 2x + 1",
        working="Substitute g into f.",
        mark_scheme=[
            MarkPoint(description="Correct substitution", marks=2),
            MarkPoint(description="Correct simplification", marks=1),
        ],
    )
    base.update(overrides)
    return Question(**base)


def test_valid_question_builds_and_defaults_unverified():
    q = _valid_question()
    assert q.subject is Subject.maths
    assert q.verified is False  # never trusted until the engine verifies


def test_mark_scheme_must_sum_to_marks():
    with pytest.raises(ValidationError):
        _valid_question(
            marks=5,
            mark_scheme=[MarkPoint(description="only two", marks=2)],
        )


def test_empty_stem_rejected():
    with pytest.raises(ValidationError):
        _valid_question(stem="")


def test_empty_model_answer_rejected():
    with pytest.raises(ValidationError):
        _valid_question(model_answer="")


def test_bad_subject_rejected():
    with pytest.raises(ValidationError):
        _valid_question(subject="history")


def test_bad_difficulty_rejected():
    with pytest.raises(ValidationError):
        _valid_question(difficulty="impossible")


def test_bad_type_rejected():
    with pytest.raises(ValidationError):
        _valid_question(type="essay")


def test_marks_must_be_positive():
    with pytest.raises(ValidationError):
        _valid_question(marks=0, mark_scheme=[MarkPoint(description="x", marks=0)])


def test_submission_total_must_equal_sum_of_awards():
    awarded = [
        MarkAward(point="Correct substitution", awarded_marks=2, justification="ok"),
        MarkAward(point="Correct simplification", awarded_marks=1, justification="ok"),
    ]
    Submission(
        question_id="q-1",
        student_answer="fg(x)=2x+1",
        awarded=awarded,
        total=3,
        feedback="Well done.",
    )
    with pytest.raises(ValidationError):
        Submission(
            question_id="q-1",
            student_answer="fg(x)=2x+1",
            awarded=awarded,
            total=99,
            feedback="mismatch",
        )
