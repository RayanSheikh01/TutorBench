"""CS question generation (M3, PLANV2 Step 2).

The LLM fills a draft (content only); this module stamps the trusted fields it
controls — deterministic ``id`` from the stem, ``subject=cs``, ``spec_code`` from
the objective, and ``verified=False`` (a Question is never trusted until the
verification gate runs).
"""
from __future__ import annotations

import hashlib

from pydantic import BaseModel, Field

from ..models import Difficulty, MarkPoint, QType, Question, Subject
from ..spec.loader import Objective

# Copyright/originality guard — keep generated items original, never past-paper text.
_SYSTEM = (
    "You are an expert OCR GCSE (J277) Computer Science examiner. Produce an "
    "ORIGINAL exam item in the style of OCR J277. Do NOT reproduce past-paper "
    "text or official mark schemes. Marks in the mark scheme must sum to the "
    "total marks."
)


class CSDraft(BaseModel):
    """LLM-authored content for a CS question; trusted fields are stamped later."""

    topic: str = Field(min_length=1)
    subtopic: str = Field(min_length=1)
    marks: int = Field(gt=0)
    stem: str = Field(min_length=1)
    model_answer: str = Field(min_length=1)
    working: str = Field(min_length=1)
    mark_scheme: list[MarkPoint] = Field(min_length=1)


def _stem_id(stem: str) -> str:
    """Deterministic id from the stem: same stem -> same id."""
    digest = hashlib.sha1(stem.strip().encode("utf-8")).hexdigest()[:12]
    return f"cs-{digest}"


def _build_messages(
    objective: Objective, difficulty: Difficulty, qtype: QType
) -> list[dict]:
    """Chat messages: system originality guard first, then the task spec."""
    difficulty = Difficulty(difficulty)
    qtype = QType(qtype)
    user = (
        f"Write one {difficulty.value} {qtype.value} question for OCR J277 "
        f"objective {objective.code}: {objective.description}\n"
        f"Target total marks: {objective.default_marks}."
    )
    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user},
    ]


def generate_cs_question(
    objective: Objective,
    difficulty: Difficulty,
    qtype: QType,
    *,
    client,
    model: str,
) -> Question:
    """Generate an unverified CS Question for a spec objective."""
    messages = _build_messages(objective, difficulty, qtype)
    draft = client.structured(model=model, messages=messages, schema=CSDraft)
    return Question(
        id=_stem_id(draft.stem),
        subject=Subject.cs,
        spec_code=objective.code,
        topic=draft.topic,
        subtopic=draft.subtopic,
        difficulty=Difficulty(difficulty),
        marks=draft.marks,
        type=QType(qtype),
        stem=draft.stem,
        model_answer=draft.model_answer,
        working=draft.working,
        mark_scheme=draft.mark_scheme,
        verified=False,
    )
