"""Schema checks for the grading gold set (M6.2).

A gold item is a human-graded question + answer. Malformed rows must fail loud
(ValidationError), never silently skew the metrics.
"""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tutorbench.eval.gold import GoldItem, load_gold

GOLD_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "tutorbench"
    / "eval"
    / "data"
    / "grading_gold.json"
)


def _question_dict() -> dict:
    return {
        "id": "gold-test-1",
        "subject": "cs",
        "spec_code": "CS-NUM-01",
        "topic": "Data representation",
        "subtopic": "Number bases",
        "difficulty": "easy",
        "marks": 2,
        "type": "short_answer",
        "stem": "Convert denary 5 to binary.",
        "model_answer": "101",
        "working": "4 + 1 = 5 -> 101.",
        "mark_scheme": [
            {"description": "Correct method", "marks": 1},
            {"description": "Correct answer 101", "marks": 1},
        ],
        "verified": True,
    }


def _item_dict(per_point, total) -> dict:
    return {
        "question": _question_dict(),
        "student_answer": "101",
        "human_total": total,
        "human_per_point": per_point,
    }


def test_valid_item_parses():
    item = GoldItem.model_validate(_item_dict([1, 1], 2))
    assert item.human_total == 2
    assert item.human_per_point == [1, 1]


def test_per_point_must_match_mark_scheme_length():
    with pytest.raises(ValidationError):
        GoldItem.model_validate(_item_dict([1], 1))


def test_per_point_total_must_equal_human_total():
    with pytest.raises(ValidationError):
        GoldItem.model_validate(_item_dict([1, 1], 1))


def test_per_point_cannot_exceed_mark_point_max():
    with pytest.raises(ValidationError):
        GoldItem.model_validate(_item_dict([2, 0], 2))  # point 0 max is 1


def test_per_point_cannot_be_negative():
    with pytest.raises(ValidationError):
        GoldItem.model_validate(_item_dict([-1, 1], 0))


def test_gold_file_loads_and_validates():
    items = load_gold(GOLD_PATH)
    assert all(isinstance(i, GoldItem) for i in items)
    # M6.2 target: 50-100 hand-authored items.
    assert 50 <= len(items) <= 100


def test_gold_file_covers_difficulties_and_qtypes():
    items = load_gold(GOLD_PATH)
    difficulties = {i.question.difficulty.value for i in items}
    qtypes = {i.question.type.value for i in items}
    assert {"easy", "medium", "hard"} <= difficulties
    # At least three distinct question types represented.
    assert len(qtypes) >= 3


def test_gold_file_spans_score_spread():
    items = load_gold(GOLD_PATH)
    # A spread of correct / partial / wrong answers (full, zero, and partial).
    fractions = [i.human_total / i.question.marks for i in items]
    assert any(f == 1.0 for f in fractions)  # fully correct
    assert any(f == 0.0 for f in fractions)  # fully wrong
    assert any(0.0 < f < 1.0 for f in fractions)  # partial


def test_gold_ids_unique():
    items = load_gold(GOLD_PATH)
    ids = [i.question.id for i in items]
    assert len(ids) == len(set(ids))
