# Grading gold set

`grading_gold.json` is the hand-authored reference set used to score the local
grader (QWK / MAE, per-mark-point in M6.3). Every row is validated by
`tutorbench.eval.gold.GoldItem` on load — malformed rows fail loud, they are
never silently dropped.

## Row schema

Each row is one `GoldItem`:

```json
{
  "question":        { ...a full Question, verified: true... },
  "student_answer":  "the answer a human graded",
  "human_total":     3,
  "human_per_point": [1, 1, 1, 0]
}
```

Invariants enforced by `GoldItem`:

- `human_per_point` has exactly one entry per mark point in
  `question.mark_scheme`.
- each entry sits in `[0, mark_point.marks]`.
- `sum(human_per_point) == human_total`.
- `question` itself must satisfy the `Question` model (so its `mark_scheme`
  marks already sum to `question.marks`).

## Authoring rubric

1. **Original only.** No past-paper stems, answers, or official mark schemes.
   Write fresh OCR J277-style items.
2. **Coverage.** Spread items across the spec topics, all three difficulties
   (`easy` / `medium` / `hard`) and the question types (`short_answer`,
   `calculation`, `structured`, `multiple_choice`).
3. **Score spread.** Include fully-correct (fraction 1.0), fully-wrong (0.0)
   and partial answers. Include **fluent-wrong** answers: well-written and
   confident but factually wrong — these should score low and are the items the
   grader is most likely to over-credit.
4. **Mark points are atomic.** Prefer 1-mark points so the human breakdown is
   unambiguous; each point tests one distinct thing.
5. **Grade as an examiner would.** `human_per_point` reflects what the
   `student_answer` actually demonstrates against each point, not what it
   gestures at. A vague answer that names the right area but gives no substance
   scores 0 on that point.
6. **Unique ids.** `question.id` is unique across the set (`gold-cs-<slug>`).

## Adding items

Append a row and run `pytest tests/eval/test_gold.py`. The tests assert the set
stays in the 50–100 range, keeps full difficulty/qtype coverage, keeps a score
spread, and keeps ids unique.
