"""FastAPI app: POST /generate -> verified Question (M3, PLANV2 Step 4).

The LLM client and settings are injected via FastAPI dependencies so tests can
override them with a fake client (no network). Models come from config, never
hardcoded.
"""
from __future__ import annotations

from functools import lru_cache
from importlib.resources import files

import yaml
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel


from ..config import Settings, get_settings
from ..llm.client import LLMClient, OllamaClient
from ..models import Difficulty, QType, Question, Subject
from ..spec.loader import Objective, SpecDoc, all_codes
from ..verification.cs import build_cs_question
from ..grading.judge import grade as grd

app = FastAPI(title="TutorBench")


@lru_cache
def _cs_objectives() -> dict[str, Objective]:
    """Flat spec_code -> Objective map from the packaged OCR J277 taxonomy."""
    text = (
        files("tutorbench.spec.data")
        .joinpath("cs_ocr_j277.yaml")
        .read_text(encoding="utf-8")
    )
    doc = SpecDoc.model_validate(yaml.safe_load(text))
    return all_codes(doc)


def get_llm_client() -> LLMClient:
    """Production LLM client; overridden with a fake in tests."""
    return OllamaClient()


class GenerateRequest(BaseModel):
    subject: Subject
    spec_code: str
    difficulty: Difficulty
    marks: int
    type: QType
    
class GradeRequest(BaseModel):
    question: Question
    student_answer: str

@app.post("/grade")
def grade(
    req: GradeRequest,
    client: LLMClient = Depends(get_llm_client),
    settings: Settings = Depends(get_settings),
):
    if req.question.subject is not Subject.cs:
        raise HTTPException(status_code=400, detail="only cs grading is supported")
    return grd(
        req.question,
        req.student_answer,
        client=client,
        model=settings.ollama_grade_model,
    )
    
    


@app.post("/generate", response_model=Question)
def generate(
    req: GenerateRequest,
    client: LLMClient = Depends(get_llm_client),
    settings: Settings = Depends(get_settings),
) -> Question:
    if req.subject is not Subject.cs:
        raise HTTPException(status_code=400, detail="only cs generation is supported")
    objective = _cs_objectives().get(req.spec_code)
    if objective is None:
        raise HTTPException(status_code=404, detail=f"unknown spec_code: {req.spec_code}")
    return build_cs_question(
        objective,
        req.difficulty,
        req.type,
        client=client,
        model=settings.ollama_gen_model,
    )

