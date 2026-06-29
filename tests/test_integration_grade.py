"""Live-Ollama integration tests for the real grade path (PLANV3 M6).

These hit a real Ollama server and are marked ``integration`` so the default
``pytest -q`` run (fakes only) deselects them. They auto-skip when Ollama is
unreachable or the configured grade model is not pulled, so the suite stays
green on a machine without the model.

Run explicitly with ``pytest -m integration``.
"""
from __future__ import annotations

import json
import urllib.request

import pytest

from tutorbench.config import get_settings

pytestmark = pytest.mark.integration

_SETTINGS = get_settings()


def _ollama_has_model(host: str, model: str) -> bool:
    """True when the Ollama server at ``host`` lists ``model`` (exact name or
    same family before the ``:`` tag)."""
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=2) as resp:
            tags = json.load(resp)
    except Exception:
        return False
    names = {m.get("name", "") for m in tags.get("models", [])}
    family = model.split(":")[0]
    return model in names or any(n.split(":")[0] == family for n in names)


_MODEL_READY = _ollama_has_model(_SETTINGS.ollama_host, _SETTINGS.ollama_grade_model)
_skip = pytest.mark.skipif(
    not _MODEL_READY,
    reason=f"Ollama grade model {_SETTINGS.ollama_grade_model!r} not available",
)


@_skip
def test_real_grade_returns_schema_valid_submission():
    """A real grade over a gold item yields one award per mark point, each
    clamped into range, with ``total == sum`` — the invariants the harness
    relies on, regardless of grading accuracy."""
    from tutorbench.eval.harness import _default_gold_path
    from tutorbench.eval.gold import load_gold
    from tutorbench.grading.judge import grade
    from tutorbench.llm.client import OllamaClient

    item = load_gold(_default_gold_path())[0]
    q = item.question

    sub = grade(
        q,
        item.student_answer,
        client=OllamaClient(),
        model=_SETTINGS.ollama_grade_model,
    )

    assert sub.question_id == q.id
    assert len(sub.awarded) == len(q.mark_scheme)
    for award, mp in zip(sub.awarded, q.mark_scheme):
        assert 0 <= award.awarded_marks <= mp.marks
    assert sub.total == sum(a.awarded_marks for a in sub.awarded)
    assert 0 <= sub.total <= q.marks
