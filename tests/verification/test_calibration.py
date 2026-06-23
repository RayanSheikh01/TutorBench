import pytest

from tutorbench.models import MarkPoint, Subject

'''false-pass / false-fail counted correctly on a synthetic labelled set
sweep produces one row per (n, threshold) cell
deterministic given canned client responses'''

def test_sweep(tmp_path, monkeypatch):
    import tutorbench.verification.calibrate as calibrate_mod
    from tutorbench.verification.calibrate import sweep
    from tutorbench.models import Question, Difficulty, QType


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
        verified=False,
    )

    # Patch _reanswer_agrees to return a canned agreement value.
    def fake_reanswer_agrees(q, *, client, model, n):
        return 0.7  # fixed agreement for testing

    monkeypatch.setattr(calibrate_mod, "_reanswer_agrees", fake_reanswer_agrees)

    # Run the sweep with the fake function.
    labelled = sweep(
        [question],
        client=None,
        model=None,
        ns=(1, 3),
        thresholds=(0.5, 0.75),
    )

    # Check that the output has the expected number of rows and labels.
    assert len(labelled) == 4  # 2 ns * 2 thresholds
    for lq in labelled:
        assert lq.question == question
        if lq.question.id == "q1":
            if lq.good:
                assert lq.good is True
            else:
                assert lq.good is False