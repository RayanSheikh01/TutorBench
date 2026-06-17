"""CS verification gate tests (M3, PLANV2 Step 3) — fake client only, no network.

The fake client speaks one schema (CSDraft): generation pops one draft, then each
re-answer pops one more. Agreement is decided by whether a re-answer's
``model_answer`` matches the generated question's.
"""
import pytest

from tutorbench.generation.cs import CSDraft, _stem_id
from tutorbench.models import (
    Difficulty,
    MarkPoint,
    QType,
    Question,
    Subject,
)
from tutorbench.spec.loader import Objective
from tutorbench.verification.cs import (
    _constraints_ok,
    build_cs_question,
    verify_cs_question,
)

OBJECTIVE = Objective(
    code="CS-1.2.1",
    description="Explain how data is represented in binary.",
    default_marks=4,
)
ANSWER = "00001101"
STEM = "Convert the denary number 13 to 8-bit binary."


def _draft(**overrides) -> CSDraft:
    base = CSDraft(
        topic="Data representation",
        subtopic="Binary",
        marks=4,
        stem=STEM,
        model_answer=ANSWER,
        working="13 = 8 + 4 + 1 -> 0000 1101.",
        mark_scheme=[
            MarkPoint(description="Correct method", marks=2),
            MarkPoint(description="Correct answer", marks=2),
        ],
    )
    return base.model_copy(update=overrides)


def _question(**overrides) -> Question:
    base = Question(
        id=_stem_id(STEM),
        subject=Subject.cs,
        spec_code=OBJECTIVE.code,
        topic="Data representation",
        subtopic="Binary",
        difficulty=Difficulty.medium,
        marks=4,
        type=QType.short_answer,
        stem=STEM,
        model_answer=ANSWER,
        working="13 = 8 + 4 + 1 -> 0000 1101.",
        mark_scheme=[
            MarkPoint(description="Correct method", marks=2),
            MarkPoint(description="Correct answer", marks=2),
        ],
        verified=False,
    )
    return base.model_copy(update=overrides)


def test_constraints_reject_invalid_and_accept_valid():
    assert _constraints_ok(_question(), OBJECTIVE)
    # wrong subject
    assert not _constraints_ok(_question(subject=Subject.maths), OBJECTIVE)
    # spec_code mismatch
    assert not _constraints_ok(_question(spec_code="CS-9.9.9"), OBJECTIVE)
    # marks out of bounds (> objective.default_marks); keep mark_scheme summing to it
    oob = _question(
        marks=10, mark_scheme=[MarkPoint(description="all", marks=10)]
    )
    assert not _constraints_ok(oob, OBJECTIVE)


def test_agreement_above_threshold_verifies(fake_llm):
    q = _question()
    # n=3: two agree, one disagrees -> 0.66 >= 0.66
    client = fake_llm(
        [_draft(), _draft(), _draft(model_answer="WRONG")]
    )
    assert verify_cs_question(q, OBJECTIVE, client=client, model="m", n=3, threshold=0.66)


def test_disagreement_below_threshold_fails_verify(fake_llm):
    q = _question()
    client = fake_llm([_draft(model_answer="WRONG")])
    assert not verify_cs_question(q, OBJECTIVE, client=client, model="m", n=1, threshold=1.0)


def test_build_retries_then_returns_verified(fake_llm):
    # attempt 1: re-answer disagrees -> fail; attempt 2: agrees -> verified
    client = fake_llm(
        [
            _draft(), _draft(model_answer="WRONG"),  # attempt 1 (gen, re-answer)
            _draft(), _draft(),                       # attempt 2 (gen, re-answer)
        ]
    )
    q = build_cs_question(
        OBJECTIVE,
        Difficulty.medium,
        QType.short_answer,
        client=client,
        model="m",
        n=1,
        threshold=1.0,
    )
    assert q.verified is True


def test_build_raises_when_never_verified(fake_llm):
    client = fake_llm(
        [
            _draft(), _draft(model_answer="WRONG"),
            _draft(), _draft(model_answer="WRONG"),
            _draft(), _draft(model_answer="WRONG"),
        ]
    )
    with pytest.raises(ValueError, match="failed verification"):
        build_cs_question(
            OBJECTIVE,
            Difficulty.medium,
            QType.short_answer,
            client=client,
            model="m",
            max_retries=3,
            n=1,
            threshold=1.0,
        )
