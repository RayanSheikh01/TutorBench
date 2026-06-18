

from tutorbench.generation.cs import CSDraft
from tutorbench.models import MarkAward, Submission


def grade(question, answer, *, client, model) -> Submission:
    """Grade the answer against the mark scheme; return a clamped Submission."""
    messages = _build_messages(question, answer)
    response = client.structured(model=model, messages=messages, schema=CSDraft)
    awards = _clamp_awards(response.mark_scheme, question.mark_scheme)
    total = sum(a.awarded_marks for a in awards)
    return Submission(
        question_id=question.id,
        student_answer=answer,
        awarded=awards,
        total=total,
        feedback=f"Awarded {total}/{question.marks} marks.",
    )


def _build_messages(question, answer) -> list[dict]:
    """Build messages for grading a question and answer."""
    return [
        {"role": "system", "content": "You are a helpful and precise assistant for grading student answers."},
        {"role": "user", "content": f"""Question (marks: {question.marks}): {question.stem}

Answer:
{answer}"""}
    ]
    
def _clamp_awards(raw_awards, mark_scheme) -> list[MarkAward]:
    """Clamp the raw awarded marks to the mark scheme and return MarkAward list."""
    awards = []
    for mp, raw in zip(mark_scheme, raw_awards):
        awarded = max(0, min(mp.marks, int(raw.marks)))
        awards.append(MarkAward(point=mp.description, awarded_marks=awarded, justification="justified"))
    return awards