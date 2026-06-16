"""Core Pydantic v2 data model for TutorBench.

A Question is never trusted until verified: `verified` defaults False and is only
set True by the engine (SymPy for Maths, the verification loop for CS).
"""
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Subject(str, Enum):
    maths = "maths"
    cs = "cs"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QType(str, Enum):
    short_answer = "short_answer"
    calculation = "calculation"
    structured = "structured"
    multiple_choice = "multiple_choice"


class MarkPoint(BaseModel):
    description: str = Field(min_length=1)
    marks: int = Field(ge=0)


class Question(BaseModel):
    id: str = Field(min_length=1)
    subject: Subject
    spec_code: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    subtopic: str = Field(min_length=1)
    difficulty: Difficulty
    marks: int = Field(gt=0)
    type: QType
    stem: str = Field(min_length=1)
    model_answer: str = Field(min_length=1)
    working: str = Field(min_length=1)
    mark_scheme: list[MarkPoint] = Field(min_length=1)
    verified: bool = False

    @model_validator(mode="after")
    def _mark_scheme_sums_to_marks(self) -> "Question":
        total = sum(mp.marks for mp in self.mark_scheme)
        if total != self.marks:
            raise ValueError(
                f"mark_scheme marks ({total}) must sum to marks ({self.marks})"
            )
        return self


class MarkAward(BaseModel):
    point: str = Field(min_length=1)
    awarded_marks: int = Field(ge=0)
    justification: str = Field(min_length=1)


class Submission(BaseModel):
    question_id: str = Field(min_length=1)
    student_answer: str
    awarded: list[MarkAward]
    total: int = Field(ge=0)
    feedback: str

    @model_validator(mode="after")
    def _total_equals_awards(self) -> "Submission":
        got = sum(a.awarded_marks for a in self.awarded)
        if got != self.total:
            raise ValueError(
                f"total ({self.total}) must equal sum of awarded_marks ({got})"
            )
        return self
