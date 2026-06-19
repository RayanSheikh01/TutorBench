"""Grading gold set schema + loader (M6.2).

A gold item pairs a verified ``Question`` with a human-graded student answer:
the human total and the per-mark-point breakdown. The validators make a
malformed row fail loud (``ValidationError``) rather than silently skew QWK/MAE:
the per-point list must line up with the mark scheme, every point must sit in
``[0, point.marks]``, and the points must sum to the human total.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from ..models import Question


class GoldItem(BaseModel):
    """One human-graded question/answer used to score the grader."""

    question: Question
    student_answer: str = Field(min_length=1)
    human_total: int = Field(ge=0)
    human_per_point: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def _per_point_consistent(self) -> "GoldItem":
        scheme = self.question.mark_scheme
        if len(self.human_per_point) != len(scheme):
            raise ValueError(
                f"human_per_point has {len(self.human_per_point)} entries for "
                f"{len(scheme)} mark points"
            )
        for i, (awarded, mp) in enumerate(zip(self.human_per_point, scheme)):
            if not 0 <= awarded <= mp.marks:
                raise ValueError(
                    f"human_per_point[{i}]={awarded} outside [0, {mp.marks}]"
                )
        got = sum(self.human_per_point)
        if got != self.human_total:
            raise ValueError(
                f"human_total ({self.human_total}) must equal sum of "
                f"human_per_point ({got})"
            )
        return self


def load_gold(path) -> list[GoldItem]:
    """Load and validate the gold set; malformed rows raise ValidationError."""
    with open(Path(path), encoding="utf-8") as f:
        rows = json.load(f)
    return [GoldItem.model_validate(row) for row in rows]
