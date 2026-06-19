"""/grade API tests (M3) — TestClient + injected fake client.

The endpoint runs ``grading.judge.grade``, which asks the LLM for a
``GradeResult`` (a per-point award + justification), then clamps each award to
the question's mark-point max. So the queued fake response is a GradeResult, and
the endpoint returns the clamped ``list[MarkAward]``.
"""
import pytest
from fastapi.testclient import TestClient

from tutorbench.api.app import app, get_llm_client
from tutorbench.grading.judge import GradeResult, PointAward
from tutorbench.models import (
    Difficulty,
    MarkPoint,
    QType,
    Question,
    Subject,
)


def _question() -> Question:
    return Question(
        id="q1",
        subject=Subject.cs,
        spec_code="CS-J277-1.1-01",
        topic="functions",
        subtopic="defining and calling functions",
        difficulty=Difficulty.easy,
        marks=2,
        type=QType.short_answer,
        stem="Define a function f that returns 42.",
        model_answer="def f(): return 42",
        working="A function returning the literal 42.",
        mark_scheme=[
            MarkPoint(description="defines a function", marks=1),
            MarkPoint(description="returns 42", marks=1),
        ],
    )


def _result(raw_awards: list[int]) -> GradeResult:
    """Judge result whose awards are the raw per-point awards to clamp."""
    return GradeResult(
        awards=[
            PointAward(awarded_marks=m, justification=f"award {i}")
            for i, m in enumerate(raw_awards)
        ]
    )


@pytest.fixture
def client(fake_llm):
    fake = fake_llm([_result([1, 5])])  # second raw award clamps 5 -> point max 1
    app.dependency_overrides[get_llm_client] = lambda: fake
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_grade_returns_clamped_awards(client):
    question = _question()
    resp = client.post(
        "/grade",
        json={"question": question.model_dump(), "student_answer": "def f(): return 42"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["question_id"] == question.id
    assert body["student_answer"] == "def f(): return 42"
    assert [a["awarded_marks"] for a in body["awarded"]] == [1, 1]
    assert [a["point"] for a in body["awarded"]] == ["defines a function", "returns 42"]
    assert body["total"] == 2
    # Invariant: clamped total never exceeds the question's marks.
    assert body["total"] <= question.marks


def test_non_cs_question_returns_400(client):
    question = _question().model_copy(update={"subject": Subject.maths})
    resp = client.post(
        "/grade",
        json={"question": question.model_dump(), "student_answer": "x"},
    )
    assert resp.status_code == 400
