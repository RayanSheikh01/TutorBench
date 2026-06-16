"""Per-template tests (M2): correctness, mark-scheme integrity, reproducibility."""
import pytest

from tutorbench.maths.base import build_question
from tutorbench.maths.rng import make_rng
from tutorbench.maths.templates import TEMPLATES

ALL = list(TEMPLATES.values())


@pytest.mark.parametrize("template_cls", ALL, ids=list(TEMPLATES))
def test_answer_passes_independent_verification(template_cls):
    t = template_cls()
    for seed in range(25):
        q = t.generate(make_rng(seed))
        assert t._verify(q), f"{template_cls.__name__} seed={seed} failed verify"


@pytest.mark.parametrize("template_cls", ALL, ids=list(TEMPLATES))
def test_mark_scheme_sums_to_marks(template_cls):
    t = template_cls()
    for seed in range(25):
        q = t.generate(make_rng(seed))
        assert sum(mp.marks for mp in q.mark_scheme) == q.marks


@pytest.mark.parametrize("template_cls", ALL, ids=list(TEMPLATES))
def test_same_seed_reproducible(template_cls):
    t = template_cls()
    q1 = t.generate(make_rng(7))
    q2 = t.generate(make_rng(7))
    assert q1 == q2


@pytest.mark.parametrize("template_cls", ALL, ids=list(TEMPLATES))
def test_build_question_marks_verified(template_cls):
    q = build_question(template_cls(), make_rng(3))
    assert q.verified is True
