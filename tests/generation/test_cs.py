"""CS generation tests (M3, PLANV2 Step 2) — fake client only, no network."""
from tutorbench.generation.cs import (
    CSDraft,
    _build_messages,
    _stem_id,
    generate_cs_question,
)
from tutorbench.models import Difficulty, MarkPoint, QType, Subject
from tutorbench.spec.loader import Objective

OBJECTIVE = Objective(
    code="CS-1.2.1",
    description="Explain how data is represented in binary.",
    default_marks=4,
)

def test_stem_id_deterministic():
    stem = "Convert the denary number 13 to 8-bit binary."
    id1 = _stem_id(stem)
    id2 = _stem_id(stem)
    assert id1 == id2
    
def test_stem_id_different_for_different_stems():
    stem1 = "Convert the denary number 13 to 8-bit binary."
    stem2 = "Convert the denary number 14 to 8-bit binary."
    id1 = _stem_id(stem1)
    id2 = _stem_id(stem2)
    assert id1 != id2
    
def test_build_messages_contains_objective_and_copyright_guard():
    messages = _build_messages(OBJECTIVE, Difficulty.medium, QType.calculation)
    assert messages[0]["role"] == "system"
    assert "ORIGINAL" in messages[0]["content"]
    user = messages[1]["content"]
    assert OBJECTIVE.description in user
    assert OBJECTIVE.code in user
    
def test_generate_cs_question_returns_unverified_question(fake_llm): 
    client = fake_llm([CSDraft(
        topic="Data representation",
        subtopic="Binary",
        marks=4,
        stem="Convert the denary number 13 to 8-bit binary.",
        model_answer="00001101",
        working="13 = 8 + 4 + 1 -> 0000 1101.",
        mark_scheme=[
            MarkPoint(description="Correct method", marks=2),
            MarkPoint(description="Correct answer", marks=2),
        ],
    )])
    q = generate_cs_question(
        OBJECTIVE, Difficulty.medium, QType.calculation, client=client, model="m"
    )
    assert q.subject is Subject.cs
    assert q.spec_code == "CS-1.2.1"
    assert q.marks == 4
    assert q.verified is False

def _draft(**overrides) -> CSDraft:
    base = CSDraft(
        topic="Data representation",
        subtopic="Binary",
        marks=4,
        stem="Convert the denary number 13 to 8-bit binary.",
        model_answer="00001101",
        working="13 = 8 + 4 + 1 -> 0000 1101.",
        mark_scheme=[
            MarkPoint(description="Correct method", marks=2),
            MarkPoint(description="Correct answer", marks=2),
        ],
    )
    return base.model_copy(update=overrides)


def test_valid_draft_returns_unverified_question(fake_llm):
    client = fake_llm([_draft()])
    q = generate_cs_question(
        OBJECTIVE, Difficulty.medium, QType.calculation, client=client, model="m"
    )
    assert q.subject is Subject.cs
    assert q.spec_code == "CS-1.2.1"
    assert q.marks == 4
    assert q.verified is False


def test_prompt_has_objective_and_copyright_guard():
    messages = _build_messages(OBJECTIVE, Difficulty.medium, QType.calculation)
    assert messages[0]["role"] == "system"
    assert "ORIGINAL" in messages[0]["content"]
    user = messages[1]["content"]
    assert OBJECTIVE.description in user
    assert OBJECTIVE.code in user


def test_id_deterministic_from_stem(fake_llm):
    client = fake_llm([_draft(), _draft()])
    q1 = generate_cs_question(
        OBJECTIVE, Difficulty.medium, QType.calculation, client=client, model="m"
    )
    q2 = generate_cs_question(
        OBJECTIVE, Difficulty.medium, QType.calculation, client=client, model="m"
    )
    assert q1.id == q2.id == _stem_id(_draft().stem)


def test_model_name_passed_through(fake_llm):
    client = fake_llm([_draft()])
    generate_cs_question(
        OBJECTIVE, Difficulty.medium, QType.calculation, client=client, model="qwen2.5"
    )
    assert client.calls[0]["model"] == "qwen2.5"
    assert client.calls[0]["schema"] is CSDraft

