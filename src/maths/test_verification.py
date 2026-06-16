"""Faithfulness harness (M2).

The guarantee: every emitted Maths question is independently re-derived in SymPy and
only returned verified. These tests exercise the whole gate across templates and
seeds, and — critically — prove the gate REJECTS a tampered answer (otherwise a
`_verify` that always returned True would pass everything silently).
"""
import re

import pytest

from tutorbench.maths.base import build_question
from tutorbench.maths.rng import make_rng
from tutorbench.maths.templates import TEMPLATES

SEEDS = range(60)


@pytest.mark.parametrize("template_cls", TEMPLATES.values(), ids=list(TEMPLATES))
def test_build_question_emits_only_verified(template_cls):
    t = template_cls()
    for seed in SEEDS:
        q = build_question(t, make_rng(seed))
        assert q.verified is True
        assert t._verify(q) is True


@pytest.mark.parametrize("template_cls", TEMPLATES.values(), ids=list(TEMPLATES))
def test_tampered_answer_fails_verification(template_cls):
    """Corrupt the model answer -> _verify must return False and build must raise."""
    t = template_cls()
    q = t.generate(make_rng(1))
    # bump the first integer in the model answer by 1 (a wrong but plausible answer)
    tampered_ans = re.sub(r"-?\d+", lambda m: str(int(m.group()) + 1), q.model_answer, count=1)
    assert tampered_ans != q.model_answer
    bad = q.model_copy(update={"model_answer": tampered_ans})
    assert t._verify(bad) is False


class _AlwaysWrong:
    """Stub template whose answer never matches; build_question must refuse it."""

    def generate(self, rng):
        good = TEMPLATES["quadratics"]().generate(rng)
        return good.model_copy(update={"model_answer": "x = 999 or x = 1000"})

    def _verify(self, q):
        return TEMPLATES["quadratics"]()._verify(q)


def test_build_question_raises_on_unverifiable():
    with pytest.raises(ValueError, match="verification failed"):
        build_question(_AlwaysWrong(), make_rng(0))
