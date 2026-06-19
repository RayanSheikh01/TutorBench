# PLAN v3 — Trust the Grader (M6) + Find the Holes (M7)

## Context

M3–M5 are complete and committed: CS generation + hybrid verification (`build_cs_question`),
rubric LLM-as-judge grading (`grade`), and a QWK/MAE eval harness. The pipeline runs end to
end, but PLANV2 itself flags the weakest point: **CS verification is best-effort, not a proof —
a fluent-wrong item can slip; M5's QWK/MAE on grading is the empirical backstop.**

That backstop is not yet trustworthy. Three substance gaps make today's numbers misleading:

- **Grader is blind to the rubric.** [src/tutorbench/grading/judge.py](src/tutorbench/grading/judge.py)
  `_build_messages` never passes `mark_scheme` to the model, and `justification` is the literal
  `"justified"`. PLANV2 M4 specced *rubric-grounded, few-shot anchored*. Any QWK measured now is
  on a rubric-less grader — directionally useless.
- **Harness not wired to the real grader.** [src/tutorbench/eval/harness.py](src/tutorbench/eval/harness.py)
  `main()` uses a dummy `len(answer) % 5` grader; gold keys are flat (`human_score`), not the
  per-point shape PLANV2 M5 specced (`human_total`, `human_per_point`). No JSON report.
- **Verification is exact string match.** [src/tutorbench/verification/cs.py](src/tutorbench/verification/cs.py)
  `_reanswer_agrees` compares `model_answer` strings literally; PLANV2 M3 step 2 specced a *judge
  call* for consistency. Brittle (any phrasing diff fails), and the confidence is never stored.

planv3 closes the faithfulness gap PLANV2 flagged. Two milestones, no new external deps, Ollama-only.

- **M6** make the grader trustworthy: fix the rubric-blind bug, grow the gold set, report
  per-mark-point QWK, calibrate the verification knobs against measured false-pass rate.
- **M7** find the holes: an adversarial gold set of fluent-wrong items, and call/latency telemetry.

## Reuse (do NOT rebuild)

- [src/tutorbench/models.py](src/tutorbench/models.py) — `Question`, `MarkPoint`, `Submission`,
  `MarkAward`. Invariants already enforced; do not weaken. Per-point data lives in `Submission.awarded`.
- [src/tutorbench/grading/judge.py](src/tutorbench/grading/judge.py) `grade` — extend the prompt
  and post-processing; keep the clamp + total-by-construction.
- [src/tutorbench/eval/harness.py](src/tutorbench/eval/harness.py) `qwk`, `mae`, `run_eval` —
  keep the metric fns; rewrite `run_eval`/`main` to the real grader + per-point shape.
- [src/tutorbench/verification/cs.py](src/tutorbench/verification/cs.py) `verify_cs_question` —
  `n` and `threshold` are already parameters; M6 measures them, does not re-architect.
- Fake `LLMClient` from the existing M3–M5 unit tests — reuse for all new unit tests.

## Cross-cutting (unchanged from PLANV2)

- All new model I/O through Pydantic; malformed → fail loud.
- No hardcoded models/endpoints — `Settings`/env only.
- Unit tests inject a fake client (no network); real-model tests `@pytest.mark.integration`,
  auto-skip if Ollama absent.
- **Copyright**: every new gold/adversarial item is hand-authored and ORIGINAL — no past-paper
  text or official mark schemes.

## M6 — Trust the grader

### M6.1 Fix the rubric-blind grader (bug, do first — everything downstream depends on it)

[src/tutorbench/grading/judge.py](src/tutorbench/grading/judge.py):

- `_build_messages` must enumerate every `MarkPoint` (description + max marks) in the prompt, and
  carry **few-shot anchors** (1–2 worked award examples) per PLANV2 M4.
- Per-point output: the model returns a real `justification` per point; stop hardcoding `"justified"`.
  Aggregate per-point feedback into `Submission.feedback`.
- Keep the clamp to `[0, point.marks]` and `total = sum(...)` so the invariant holds by construction.
- Tests (fakes): prompt contains every mark point + the anchors; canned awards → validated
  Submission; clamp enforced; real justifications surfaced (no `"justified"` literal).

### M6.2 Grow the gold set

- [src/tutorbench/eval/data/grading_gold.json](src/tutorbench/eval/data/grading_gold.json) — expand
  to **50–100 original items**, each `{question, student_answer, human_total, human_per_point}`,
  spanning difficulties, qtypes, and a spread of correct / partial / wrong / fluent-wrong answers.
- Hand-authored, no past-paper content. Document the authoring rubric in a short header/README.
- A schema check (Pydantic model for a gold item) so malformed rows fail loud, not silently.

### M6.3 Per-mark-point QWK in the harness

[src/tutorbench/eval/harness.py](src/tutorbench/eval/harness.py):

- Migrate gold keys to `human_total` / `human_per_point`; have `run_eval` call the real `grade()`
  (injected client/model), not the dummy.
- Report **total QWK + MAE** *and* **per-mark-point QWK** (which mark types the grader fails on).
- Emit a report in both human-readable and JSON (PLANV2 M5 wanted JSON; not yet done).
- Tests: metrics correct on synthetic arrays (deterministic); per-point aggregation correct with a
  fake grader; report JSON shape asserted.

### M6.4 Calibrate the verification knobs

- Replace the exact-string self-consistency in `_reanswer_agrees` with a **judge call** (re-answer
  fresh, then a judge checks consistency with `model_answer` + `mark_scheme`) — PLANV2 M3 step 2.
  Store the agreement fraction as a confidence on the result (log at minimum).
- A small sweep script/test over `n ∈ {1,3,5}` and `threshold ∈ {0.5,0.66,0.8}` measuring
  **false-pass rate** against a labelled set of known-good / known-bad questions.
- Pick defaults from the measurement; record the chosen `n`/`threshold` and the curve in the report.
- Tests: judge-based agreement path with a fake client (deterministic); sweep harness runs on a
  fake set with no network.

**→ STOP after M6 for review**: read total + per-point QWK/MAE and the false-pass curve; decide
whether the local grader is reliable enough, and lock `n`/`threshold`.

## M7 — Find the holes

### M7.1 Adversarial gold set

- `src/tutorbench/eval/data/grading_adversarial.json` — original **fluent-wrong** items: plausible,
  well-written, but factually wrong answers (and a few well-written-but-off-rubric questions).
- Run the M6 grader + verifier over it; report how many fluent-wrong items the grader over-credits
  and the verifier waves through. This is the empirical measure of the PLANV2 "slip" risk.
- Tests: harness runs on the adversarial set with a fake grader; over-credit count computed correctly.

### M7.2 Call / latency telemetry

- Lightweight instrumentation around `LLMClient.structured` (decorator or wrapper) counting calls
  and wall-time per `build_cs_question` / `grade`. No new deps — stdlib `time`/`logging`.
- Surface **calls-per-question**, retry counts, and p50/p95 latency in the eval report. PLANV2
  flagged latency as a trade-off but never measured it; this closes that.
- Tests: wrapper counts calls and records timings with a fake client (monkeypatched clock).

**→ Review after M7**: calls-per-question + latency inform whether Phase 3 (caching, batch) is worth it.

## Build order & commits

M6.1 (grader fix + tests) — commit. M6.2 (gold set) — commit. M6.3 (per-point harness) — commit,
**STOP for review**. M6.4 (judge-based verify + calibration) — commit. M7.1 (adversarial) — commit.
M7.2 (telemetry) — commit. Conventional Commits, one per sub-milestone.

## Verification (end-to-end)

1. `pytest -q` → all unit tests green (fakes only), including new grader/harness/telemetry tests.
2. `python -m tutorbench.eval.harness <gold>` → prints total + per-point QWK/MAE and writes JSON.
3. `pytest -m integration` → live grade over the grown gold set; QWK/MAE printed.
4. Calibration sweep → false-pass curve over `n`/`threshold`; chosen defaults recorded.
5. Adversarial run → over-credit count; telemetry shows calls-per-question + p50/p95 latency.

## Trade-offs flagged

- **Small gold set = noisy QWK** (PLANV2 caveat persists). 50–100 items is directional, not final;
  keep the sample-size caveat in the report and grow over time.
- **Human labels are the ceiling.** Per-point QWK only means something if `human_per_point` is
  authored carefully; budget real time on the gold set, not just the code.
- **Judge-based verification adds calls.** M6.4 replaces a free string compare with an LLM judge —
  slower, all local (no $). M7.2 telemetry quantifies the cost so Phase 3 caching is data-driven.
- **Out of scope (later phases):** caching/dedup, persistence, batch generation, new qtypes, other
  subjects, cloud-model fallback. Roadmap, not this plan.
