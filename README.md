# TutorBench — GCSE Exam-Prep Generator + Auto-Grader

Fully local AI system that generates original, spec-aligned GCSE questions and auto-grades
free-text answers. No paid/hosted APIs.

- **Maths** — deterministic: parameterised templates + SymPy. No LLM. Guaranteed-correct.
- **Computer Science** — local Ollama model with a generate → verify → grade loop.

See [PLAN.md](PLAN.md) for architecture and [IMPLEMENTATION.md](IMPLEMENTATION.md) for the build checklist.

## Setup

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env   # edit if your Ollama host/models differ (needed from M3)
```

## Test

```powershell
pytest -q
```

## Generate Maths questions (M2)

```powershell
python -m tutorbench.maths.cli --n 5 --seed 42
python -m tutorbench.maths.cli --n 3 --seed 42 --json
```

Same `--seed` → identical questions (reproducible).

## Config

All runtime config via environment (`.env`), never hardcoded:

| Var | Default | Used by |
|-----|---------|---------|
| `OLLAMA_HOST` | `http://localhost:11434` | CS generation/grading (M3+) |
| `OLLAMA_GEN_MODEL` | `qwen2.5:7b-instruct` | generation (M3) |
| `OLLAMA_GRADE_MODEL` | `qwen2.5:7b-instruct` | grading (M4) |

## Status

- **M1** scaffold + Pydantic data model + spec taxonomy
- **M2** deterministic Maths engine (SymPy) + CLI

M3–M6 (CS generation, grading, eval harness, PDF export) are planned, not yet built.

## Copyright

All items are generated **original** in the style of the spec. No past-paper questions or
official mark schemes are ingested, stored, or reproduced.
