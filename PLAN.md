# GCSE Exam-Prep Generator + Auto-Grader — Plan

## Context

Greenfield build (empty dir, no git). Goal: a fully-local AI system that (1) generates
original, spec-aligned GCSE questions and (2) auto-grades free-text answers — no paid/hosted
APIs. Two paths: **Maths** is deterministic (parameterised templates + SymPy, no LLM),
**Computer Science** uses a local Ollama model with a generate→verify→grade loop.

This plan covers the full milestone roadmap but **scopes execution to M1–M2 only**. Per the
user's instruction we **STOP after M2** for review — M2 proves the deterministic Maths path
works end-to-end with zero model calls. M3–M6 are described for context but not built yet.

Environment verified: Python 3.13.11 (`py`), Ollama 0.30.6 installed (not needed until M3).

## Decisions locked
- **Maths templates (M2):** all four chosen — composite functions, 2D vectors,
  iteration (fixed-point), quadratics (solve/factorise). Each: randomise params → render
  stem → SymPy computes model answer + working → build itemised mark scheme.
- No LLM, no Ollama calls, no network in M1–M2.
- Config-driven: nothing hardcoded; env via `.env` / pydantic-settings.

## Tech stack
Python 3.11+ (venv) · Pydantic v2 · SymPy · pytest · (later: Ollama client, instructor,
FastAPI, ReportLab). Add only M1–M2 deps now (pydantic, pydantic-settings, sympy, pytest,
pyyaml, python-dotenv). Heavier deps deferred to their milestone.

## File tree (created in M1–M2)

```
TutorBench/
├─ .env.example
├─ .gitignore
├─ README.md
├─ pyproject.toml              # deps + pytest config (ruff optional)
├─ src/
│  └─ tutorbench/
│     ├─ __init__.py
│     ├─ config.py             # pydantic-settings: OLLAMA_* etc (read now, used later)
│     ├─ models.py             # M1: Pydantic v2 data model (Question, MarkPoint, ...)
│     ├─ spec/
│     │  ├─ __init__.py
│     │  ├─ loader.py          # load + validate YAML taxonomy
│     │  └─ data/
│     │     ├─ cs_ocr_j277.yaml
│     │     └─ maths.yaml
│     └─ maths/
│        ├─ __init__.py
│        ├─ base.py            # Template ABC: generate(seed) -> Question
│        ├─ rng.py             # seeded RNG helper (reproducible questions)
│        ├─ templates/
│        │  ├─ __init__.py     # registry of templates
│        │  ├─ composite_functions.py
│        │  ├─ vectors.py
│        │  ├─ iteration.py
│        │  └─ quadratics.py
│        └─ cli.py             # `tutorbench-maths --n 5 --seed 42 [--topic ...]`
└─ tests/
   ├─ test_models.py           # M1
   ├─ test_spec_loader.py      # M1
   └─ maths/
      ├─ test_composite_functions.py
      ├─ test_vectors.py
      ├─ test_iteration.py
      ├─ test_quadratics.py
      └─ test_verification.py  # every generated Q: model_answer re-derives via SymPy
```

## Data model (M1) — Pydantic v2

Exactly as specified, with v2 idioms (`model_config`, `Field`, validators):
- `Question { id, subject, spec_code, topic, subtopic, difficulty, marks, type, stem,
  model_answer, working, mark_scheme: list[MarkPoint], verified: bool }`
- `MarkPoint { description, marks }`
- `Submission { question_id, student_answer, awarded: list[MarkAward], total, feedback }`
- `MarkAward { point, awarded_marks, justification }`

Validators enforce invariants: `sum(mark_scheme[].marks) == marks`; `subject ∈ {maths, cs}`;
`difficulty` and `type` as enums; non-empty stem/model_answer. Malformed → raises (fail loud).

## Spec taxonomy (M1)
`spec/data/*.yaml`: subject → topic → subtopic → objective → marks. Seed **OCR J277** (CS)
and the Maths topics matching the four templates. `loader.py` parses + validates against a
Pydantic schema; bad YAML fails loudly. Templates reference real `spec_code`s from this file.

## Maths engine (M2) — the deliverable to review

`base.Template` ABC: `generate(rng) -> Question`. Each template:
1. **Randomise** params within sane ranges (seeded RNG → reproducible).
2. **Render** stem string from params.
3. **Solve with SymPy** — this IS the engine, not a check: compute model answer + step working.
4. **Build mark scheme** — itemised `MarkPoint`s (method marks + answer mark) summing to `marks`.
5. Set `verified=True` only after the independent re-derivation in step 6 passes.
6. **Verify** (`test_verification.py` + inline guard): re-solve the rendered stem from scratch
   in SymPy and assert it equals the stored `model_answer`. Mismatch → drop/raise, never emit.

Template specifics:
- **Composite functions:** random linear/quadratic f,g; ask fg(x)/gf(x) or fg(a). SymPy
  `compose`/`subs` + `simplify`.
- **2D vectors:** column vectors; add/scale, magnitude, midpoint/collinearity. SymPy `Matrix`.
- **Iteration (fixed-point):** `x_{n+1}=g(x_n)` to N d.p.; emit iteration table as working.
  SymPy numeric eval (`nsimplify`/`N`), rounding asserted stable.
- **Quadratics:** integer-roots-by-construction so factorise/solve is clean; SymPy
  `factor`/`solve`, complete-the-square variant.

**CLI** (`maths/cli.py`): `--n`, `--seed`, optional `--topic`, `--difficulty`, `--json`.
Prints N generated questions with stem, model answer, working, and mark scheme. Default human
-readable; `--json` dumps validated Pydantic. This is what you run to review M2.

## Out of scope now (roadmap only)
- **M3** CS generation + verification via Ollama → `/generate`.
- **M4** Grading engine (rubric-grounded local LLM-as-judge) → `/grade`.
- **M5** Eval harness: gold set → QWK + MAE report.
- **M6** ReportLab PDF export; (stretch) adaptive selection + spaced repetition.

## Commits
Conventional Commits, one clean commit per milestone (`git init` first since not a repo):
`chore: scaffold M1` then `feat(maths): deterministic SymPy engine M2`.

## Verification (M1–M2)
1. `py -m venv .venv` + install deps; `pytest -q` → all green.
2. `pytest tests/maths/test_verification.py` — every generated question's stored answer
   re-derives independently in SymPy (the faithfulness guarantee).
3. Run CLI: `python -m tutorbench.maths.cli --n 5 --seed 42` → eyeball stems, answers,
   working, mark schemes across all four templates. Re-run same seed → identical output
   (reproducibility). **Then STOP for review.**

## Design trade-offs flagged
- **Iteration rounding:** floating round-to-N-dp can be brittle near .5 boundaries. Mitigation:
  construct g(x) with a comfortable margin from rounding edges; verify rounding is stable across
  one extra iteration before emitting.
- **Mark-scheme granularity:** GCSE method/accuracy mark conventions are a judgement call for
  original items. I'll keep marks summing to total and method-before-answer ordering; will want
  your eye on whether the split matches OCR expectations during M2 review.
- **Question `id`:** deterministic hash of (template, seed, params) for reproducibility +
  dedup, rather than random UUID.
