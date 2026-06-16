import pytest


def test_question_validation():
    from src.tutorbench.models import Question, Subject, Difficulty, QType, MarkPoint
    from pydantic import ValidationError
    
    # Valid Question
    q = Question(
        subject=Subject.math,
        difficulty=Difficulty.easy,
        qtype=QType.mcq,
        question="What is 2+2?",
        options=["3", "4", "5"],
        answer="4",
        mark_points=[MarkPoint(description="Correct answer", points=1)]
    )
    assert q.subject == Subject.math
    assert q.difficulty == Difficulty.easy
    assert q.qtype == QType.mcq
    
    # Invalid subject
    with pytest.raises(ValidationError):
        Question(
            subject="history",
            difficulty=Difficulty.easy,
            qtype=QType.mcq,
            question="What is 2+2?",
            options=["3", "4", "5"],
            answer="4",
            mark_points=[MarkPoint(description="Correct answer", points=1)]
        )

    # Invalid difficulty
    with pytest.raises(ValidationError):
        Question(
            subject=Subject.math,
            difficulty="very hard",
            qtype=QType.mcq,
            question="What is 2+2?",
            options=["3", "4", "5"],
            answer="4",
            mark_points=[MarkPoint(description="Correct answer", points=1)]
        )
        
    # Invalid qtype
    with pytest.raises(ValidationError):
        Question(
            subject=Subject.math,
            difficulty=Difficulty.easy,
            qtype="essay",
            question="What is 2+2?",
            options=["3", "4", "5"],
            answer="4",
            mark_points=[MarkPoint(description="Correct answer", points=1)]
        )
    
    # Empty question stem
    with pytest.raises(ValidationError):
        Question(
            subject=Subject.math,
            difficulty=Difficulty.easy,
            qtype=QType.mcq,
            question="",
            options=["3", "4", "5"],
            answer="4",
            mark_points=[MarkPoint(description="Correct answer", points=1)]
        )
    
    # Empty answer
    with pytest.raises(ValidationError):
        Question(
            subject=Subject.math,
            difficulty=Difficulty.easy,
            qtype=QType.mcq,
            question="What is 2+2?",
            options=["3", "4", "5"],
            answer="",
            mark_points=[MarkPoint(description="Correct answer", points=1)]
        )
    
    # Mark points sum ≠ total marks (not enforced by model, but could be a logical check)
    q = Question(
        subject=Subject.math,
        difficulty=Difficulty.easy,
        qtype=QType.mcq,
        question="What is 2+2?",
        options=["3", "4", "5"],
        answer="4",
        mark_points=[MarkPoint(description="Correct answer", points=1)]
    )
    
    total_marks = sum(mp.points for mp in q.mark_points)
    assert total_marks == 1  # In this case, it matches, but if we had a different scheme, it could be a logical error to check for
    
    
    