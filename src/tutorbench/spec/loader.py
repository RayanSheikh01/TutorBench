"""Load + validate the spec taxonomy from YAML.

Taxonomy shape: subject -> topics -> subtopics -> objectives.
Bad YAML or invalid structure fails loudly (FileNotFoundError / yaml error /
pydantic ValidationError) — we never silently accept a malformed spec.
"""
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator


class Objective(BaseModel):
    code: str = Field(min_length=1)
    description: str = Field(min_length=1)
    default_marks: int = Field(gt=0)


class Subtopic(BaseModel):
    name: str = Field(min_length=1)
    objectives: list[Objective] = Field(min_length=1)


class Topic(BaseModel):
    name: str = Field(min_length=1)
    subtopics: list[Subtopic] = Field(min_length=1)


class SpecDoc(BaseModel):
    subject: str = Field(min_length=1)
    topics: list[Topic] = Field(min_length=1)

    @model_validator(mode="after")
    def _codes_unique(self) -> "SpecDoc":
        seen: set[str] = set()
        for t in self.topics:
            for s in t.subtopics:
                for o in s.objectives:
                    if o.code in seen:
                        raise ValueError(f"duplicate spec_code: {o.code}")
                    seen.add(o.code)
        return self


def load_spec(path: str | Path) -> SpecDoc:
    """Parse and validate a spec YAML file into a SpecDoc."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SpecDoc.model_validate(raw)


def all_codes(doc: SpecDoc) -> dict[str, Objective]:
    """Flat map of spec_code -> Objective for fast lookup."""
    return {
        o.code: o
        for t in doc.topics
        for s in t.subtopics
        for o in s.objectives
    }
