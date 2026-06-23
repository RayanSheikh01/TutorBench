"""Grading-eval harness (M6.3).

Runs the real rubric grader over the human-labelled gold set and reports how
closely it agrees with the human marks at two granularities:

* **total** — QWK + MAE over the per-question total mark.
* **per-point** — QWK + MAE over every individual mark point (flattened),
  which surfaces point-level disagreements that cancel out in the total.

The per-point agreement is also broken down by question type, so you can see
which kinds of mark the grader fails on. ``run_eval`` returns a plain
JSON-serialisable dict; ``format_report`` renders it human-readable.
"""
from __future__ import annotations

import json
import math
import warnings
from collections import defaultdict
from importlib.resources import files

from tutorbench.eval.gold import load_gold
from tutorbench.grading.judge import grade


def qwk(human, pred) -> float:
    """Quadratic Weighted Kappa (QWK) over integer ratings."""
    from sklearn.metrics import cohen_kappa_score
    return cohen_kappa_score(human, pred, weights="quadratic")


def mae(human, pred) -> float:
    """Mean Absolute Error (MAE)."""
    return sum(abs(h - p) for h, p in zip(human, pred)) / len(human)


def _safe_qwk(human, pred) -> float | None:
    """QWK, or ``None`` when undefined (fewer than two ratings, or no variation
    so Cohen's kappa is NaN)."""
    if len(human) < 2:
        return None
    with warnings.catch_warnings():
        # No rating variation makes Cohen's kappa undefined; sklearn warns and
        # returns NaN, which we collapse to None below.
        warnings.simplefilter("ignore")
        score = qwk(human, pred)
    return None if math.isnan(score) else float(score)


def _metrics(human, pred) -> dict:
    """QWK + MAE + sample size for one pair of aligned rating arrays."""
    return {
        "n": len(human),
        "qwk": _safe_qwk(human, pred),
        "mae": mae(human, pred) if human else None,
    }


def make_grader(*, client, model):
    """Adapt the real rubric grader to the ``(question, answer) -> Submission``
    callable that :func:`run_eval` expects, with the client/model injected."""
    def _grader(question, answer):
        return grade(question, answer, client=client, model=model)
    return _grader


def run_eval(gold_path, *, grader) -> dict:
    """Grade every gold item and report total + per-point agreement.

    ``grader`` maps ``(question, student_answer) -> Submission``. Production
    passes :func:`make_grader` (the real judge with an injected client/model);
    tests pass a fake grader so the run is deterministic and offline.
    """
    items = load_gold(gold_path)

    total_human: list[int] = []
    total_pred: list[int] = []
    point_human: list[int] = []
    point_pred: list[int] = []
    by_type_human: dict[str, list[int]] = defaultdict(list)
    by_type_pred: dict[str, list[int]] = defaultdict(list)

    for item in items:
        submission = grader(item.question, item.student_answer)
        pred_points = [a.awarded_marks for a in submission.awarded]
        if len(pred_points) != len(item.human_per_point):
            raise ValueError(
                f"{item.question.id}: grader returned {len(pred_points)} awards "
                f"for {len(item.human_per_point)} mark points"
            )
        total_human.append(item.human_total)
        total_pred.append(submission.total)
        qtype = item.question.type.value
        for h, p in zip(item.human_per_point, pred_points):
            point_human.append(h)
            point_pred.append(p)
            by_type_human[qtype].append(h)
            by_type_pred[qtype].append(p)

    return {
        "n_items": len(items),
        "n_points": len(point_human),
        "total": _metrics(total_human, total_pred),
        "per_point": _metrics(point_human, point_pred),
        "by_type": {
            t: _metrics(by_type_human[t], by_type_pred[t])
            for t in sorted(by_type_human)
        },
    }


def format_report(report) -> str:
    """Render a :func:`run_eval` report as a human-readable block."""
    def fmt(m: dict) -> str:
        qwk_s = "n/a" if m["qwk"] is None else f"{m['qwk']:.4f}"
        mae_s = "n/a" if m["mae"] is None else f"{m['mae']:.4f}"
        return f"QWK={qwk_s}  MAE={mae_s}  (n={m['n']})"

    lines = [
        f"Gold items: {report['n_items']}  mark points: {report['n_points']}",
        f"Total:     {fmt(report['total'])}",
        f"Per-point: {fmt(report['per_point'])}",
        "By question type:",
    ]
    for qtype, m in report["by_type"].items():
        lines.append(f"  {qtype:<16} {fmt(m)}")
    return "\n".join(lines)


def _default_gold_path() -> str:
    """Path to the packaged gold set."""
    return str(files("tutorbench.eval.data").joinpath("grading_gold.json"))


def main() -> None:
    import argparse

    from tutorbench.config import get_settings
    from tutorbench.llm.client import OllamaClient

    parser = argparse.ArgumentParser(
        description="Evaluate the rubric grader against the gold set."
    )
    parser.add_argument(
        "gold_path",
        nargs="?",
        default=_default_gold_path(),
        help="Path to the gold data JSON file (defaults to the packaged set).",
    )
    parser.add_argument(
        "--json",
        dest="json_out",
        help="Write the report as JSON to this path.",
    )
    args = parser.parse_args()

    settings = get_settings()
    grader = make_grader(
        client=OllamaClient(), model=settings.ollama_grade_model
    )
    report = run_eval(args.gold_path, grader=grader)

    print(format_report(report))
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nJSON report written to {args.json_out}")


if __name__ == "__main__":
    main()