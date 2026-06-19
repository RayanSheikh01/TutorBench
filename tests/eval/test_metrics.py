"""Harness metric + reporting tests (M6.3).

Metric correctness is checked on synthetic arrays; the eval run and report
shape are checked with a fake grader so the tests stay deterministic and
offline (no real client).
"""
import json

from tutorbench.eval.harness import (
    format_report,
    mae,
    qwk,
    run_eval,
)
from tutorbench.models import Difficulty, MarkAward, QType, Submission


def test_qwk_identical():
    assert qwk([0, 1, 2, 3, 4], [0, 1, 2, 3, 4]) == 1.0


def test_qwk_known():
    # 4 ratings over categories 1-4 with a single 3->2 disagreement.
    # Quadratic weights (i-j)^2/(N-1)^2 give QWK = 1 - (1/9)/(10/9) = 0.9.
    human = [1, 2, 3, 4]
    pred = [1, 2, 2, 4]
    assert abs(qwk(human, pred) - 0.9) < 1e-6


def test_mae():
    human = [0, 1, 2, 3, 4]
    pred = [0, 1, 1, 3, 5]
    expected_mae = (0 + 0 + 1 + 0 + 1) / 5
    assert abs(mae(human, pred) - expected_mae) < 1e-6


def _question(qid: str, qtype: QType, point_maxes: list[int]) -> dict:
    return {
        "id": qid,
        "subject": "cs",
        "spec_code": "CS-NUM-01",
        "topic": "Data representation",
        "subtopic": "Number bases",
        "difficulty": Difficulty.easy.value,
        "marks": sum(point_maxes),
        "type": qtype.value,
        "stem": "stem",
        "model_answer": "ans",
        "working": "work",
        "mark_scheme": [
            {"description": f"Point {i}", "marks": m}
            for i, m in enumerate(point_maxes)
        ],
        "verified": True,
    }


def _item(qid, qtype, point_maxes, per_point) -> dict:
    return {
        "question": _question(qid, qtype, point_maxes),
        "student_answer": "a student answer",
        "human_total": sum(per_point),
        "human_per_point": per_point,
    }


def _gold_file(tmp_path, rows) -> str:
    path = tmp_path / "gold.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    return str(path)


def _fake_grader(pred_by_id: dict[str, list[int]]):
    """Build a grader returning canned per-point awards keyed by question id."""
    def _grader(question, answer) -> Submission:
        awards = [
            MarkAward(
                point=mp.description,
                awarded_marks=p,
                justification="fake",
            )
            for mp, p in zip(question.mark_scheme, pred_by_id[question.id])
        ]
        total = sum(a.awarded_marks for a in awards)
        return Submission(
            question_id=question.id,
            student_answer=answer,
            awarded=awards,
            total=total,
            feedback="fake",
        )

    return _grader


def test_run_eval_aggregates_total_and_per_point(tmp_path):
    rows = [
        _item("q1", QType.short_answer, [1, 1], [1, 1]),
        _item("q2", QType.short_answer, [1, 1], [1, 0]),
        _item("q3", QType.structured, [1, 1, 1], [1, 1, 1]),
    ]
    gold_path = _gold_file(tmp_path, rows)
    # Grader gets one point wrong on q1 (point 0) and one on q3 (point 2).
    grader = _fake_grader({"q1": [0, 1], "q2": [1, 0], "q3": [1, 1, 0]})

    report = run_eval(gold_path, grader=grader)

    assert report["n_items"] == 3
    assert report["n_points"] == 7  # 2 + 2 + 3

    # Totals: human [2,1,3] vs pred [1,1,2] -> two off-by-one errors.
    assert report["total"]["n"] == 3
    assert abs(report["total"]["mae"] - (1 + 0 + 1) / 3) < 1e-6

    # Per-point: human [1,1,1,0,1,1,1] vs pred [0,1,1,0,1,1,0] -> 2/7 wrong.
    assert report["per_point"]["n"] == 7
    assert abs(report["per_point"]["mae"] - 2 / 7) < 1e-6


def test_run_eval_breaks_down_by_question_type(tmp_path):
    rows = [
        _item("q1", QType.short_answer, [1, 1], [1, 1]),
        _item("q2", QType.structured, [1, 1, 1], [1, 1, 1]),
    ]
    gold_path = _gold_file(tmp_path, rows)
    grader = _fake_grader({"q1": [1, 0], "q2": [1, 1, 1]})

    report = run_eval(gold_path, grader=grader)

    by_type = report["by_type"]
    assert set(by_type) == {"short_answer", "structured"}
    assert by_type["short_answer"]["n"] == 2
    assert by_type["structured"]["n"] == 3
    # structured points all correct -> zero error.
    assert by_type["structured"]["mae"] == 0.0


def test_report_is_json_serialisable_with_expected_shape(tmp_path):
    rows = [_item("q1", QType.short_answer, [1, 1], [1, 0])]
    gold_path = _gold_file(tmp_path, rows)
    grader = _fake_grader({"q1": [1, 0]})

    report = run_eval(gold_path, grader=grader)

    # Round-trips through JSON unchanged (no non-serialisable values).
    assert json.loads(json.dumps(report)) == report
    for section in ("total", "per_point"):
        assert set(report[section]) == {"n", "qwk", "mae"}
    assert {"n_items", "n_points", "total", "per_point", "by_type"} <= set(report)


def test_qwk_undefined_returns_none_not_nan(tmp_path):
    # A single item -> per-point arrays have no rating variation; QWK is
    # undefined and must surface as None, never NaN, so JSON stays valid.
    rows = [_item("q1", QType.short_answer, [1, 1], [1, 1])]
    gold_path = _gold_file(tmp_path, rows)
    grader = _fake_grader({"q1": [1, 1]})

    report = run_eval(gold_path, grader=grader)

    assert report["total"]["qwk"] is None
    assert report["per_point"]["qwk"] is None


def test_format_report_renders_sections(tmp_path):
    rows = [
        _item("q1", QType.short_answer, [1, 1], [1, 1]),
        _item("q2", QType.structured, [1, 1, 1], [1, 0, 1]),
    ]
    gold_path = _gold_file(tmp_path, rows)
    grader = _fake_grader({"q1": [1, 1], "q2": [1, 0, 0]})

    text = format_report(run_eval(gold_path, grader=grader))

    assert "Total:" in text
    assert "Per-point:" in text
    assert "short_answer" in text
    assert "structured" in text
