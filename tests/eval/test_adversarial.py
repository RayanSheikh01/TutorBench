import pytest
from pathlib import Path

ADVERSARIAL_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "tutorbench"
    / "eval"
    / "data"
    / "grading_adversarial.json"
)

def test_load_adversarial():
    from tutorbench.eval.harness import load_gold
    from tutorbench.eval.gold import GoldItem

    items = load_gold(ADVERSARIAL_PATH)
    assert len(items) == 3
    for item in items:
        assert isinstance(item, GoldItem)
        
def test_count_over_credit():
    from tutorbench.eval.harness import count_over_credit

    items = [
        {"human_total": 2, "grader_total": 2},
        {"human_total": 1, "grader_total": 2},  # over-credit
        {"human_total": 0, "grader_total": 0},
        {"human_total": 3, "grader_total": 4},  # over-credit
    ]
    assert count_over_credit(items) == 2
    
def test_harness_runs(tmp_path):
    from tutorbench.eval.harness import run_eval, format_report
    from tutorbench.eval.gold import GoldItem, MarkPoint, Question, Difficulty, QType, Subject

    # Create a fake gold item with a question and a student answer.
    question = Question(
        id="q1",
        subject=Subject.cs,
        spec_code="obj1",
        topic="Arithmetic",
        subtopic="Addition",
        difficulty=Difficulty.easy,
        marks=1,
        type=QType.short_answer,
        stem="What is 2 + 2?",
        model_answer="4",
        working="2 + 2 = 4",
        mark_scheme=[MarkPoint(description="Correct answer", marks=1)],
        verified=True,
    )
    gold_item = GoldItem(
        question=question,
        student_answer="4",
        human_per_point=[1],
        human_total=1,
    )

    # Run the evaluation harness with a fake grader that always awards full marks.
    from tutorbench.models import MarkAward, Submission

    def fake_grader(q, student_answer):
        awards = [
            MarkAward(point=mp.description, awarded_marks=mp.marks, justification="fake")
            for mp in q.mark_scheme
        ]
        return Submission(
            question_id=q.id,
            student_answer=student_answer,
            awarded=awards,
            total=sum(a.awarded_marks for a in awards),
            feedback="fake",
        )

    report = run_eval([gold_item], grader=fake_grader)
    assert report["n_items"] == 1
    assert report["total"]["n"] == 1

def test_format_report():
    from tutorbench.eval.harness import format_report

    report = {
        "n_items": 1,
        "n_points": 1,
        "total": {"n": 1, "qwk": 1.0, "mae": 0.0},
        "per_point": {"n": 1, "qwk": 1.0, "mae": 0.0},
        "by_type": {"short_answer": {"n": 1, "qwk": 1.0, "mae": 0.0}},
    }
    formatted = format_report(report)
    assert "Total Agreement" in formatted
    assert "Per-Point Agreement" in formatted
    assert "By Question Type" in formatted
    
