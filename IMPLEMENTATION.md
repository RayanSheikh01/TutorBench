# Implementation Guide (M1–M2) — you write the code

Ordered, TDD-style checklist. Skeletons/signatures only — fill in bodies yourself.
Each step: write the test first, watch it fail, then implement. Stop after M2.

---

## Step 0 — Scaffold

- [ ] `py -m venv .venv` then activate (`.venv\Scripts\Activate.ps1`).
- [ ] `pyproject.toml` — package `tutorbench`, src layout, deps:
      `pydantic>=2`, `pydantic-settings`, `sympy`, `pyyaml`, `python-dotenv`; dev: `pytest`.
      Add `[tool.pytest.ini_options] pythonpath = ["src"]` and `testpaths = ["tests"]`.
- [ ] `pip install -e ".[dev]"`.
- [ ] `.gitignore` (`.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `.env`).
- [ ] `.env.example`:
      ```
      OLLAMA_HOST=http://localhost:11434
      OLLAMA_GEN_MODEL=qwen2.5:7b-instruct
      OLLAMA_GRADE_MODEL=qwen2.5:7b-instruct
      ```
- [ ] `README.md` — what it is, setup, `pytest`, CLI usage.
- [ ] `git init`; commit `chore: scaffold M1` after Step 3.

---

## Step 1 — config.py (no test needed; config file)

```python
# src/tutorbench/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    ollama_host: str = "http://localhost:11434"
    ollama_gen_model: str = "qwen2.5:7b-instruct"
    ollama_grade_model: str = "qwen2.5:7b-instruct"

def get_settings() -> Settings: ...   # cache with functools.lru_cache
```

---

## Step 2 — Data model (TDD)

`tests/test_models.py` first. Cases:
- [ ] valid `Question` builds; `verified` defaults False.
- [ ] mark_scheme marks must sum to `marks` → else `ValidationError`.
- [ ] empty `stem` / `model_answer` rejected.
- [ ] bad `subject` / `difficulty` / `type` enum rejected.
- [ ] `Submission` total equals sum of `awarded[].awarded_marks`.

Then `src/tutorbench/models.py`:

```python
from enum import Enum
from pydantic import BaseModel, Field, model_validator

class Subject(str, Enum): MATHS="maths"; CS="cs"
class Difficulty(str, Enum): ...      # foundation/higher or easy/med/hard — pick
class QType(str, Enum): ...           # short, calculation, structured, ...

class MarkPoint(BaseModel):
    description: str = Field(min_length=1)
    marks: int = Field(ge=0)

class Question(BaseModel):
    id: str; subject: Subject; spec_code: str; topic: str; subtopic: str
    difficulty: Difficulty; marks: int = Field(gt=0); type: QType
    stem: str = Field(min_length=1); model_answer: str = Field(min_length=1)
    working: str; mark_scheme: list[MarkPoint]; verified: bool = False

    @model_validator(mode="after")
    def _marks_sum(self): ...   # assert sum == marks

class MarkAward(BaseModel): point: str; awarded_marks: int; justification: str
class Submission(BaseModel):
    question_id: str; student_answer: str
    awarded: list[MarkAward]; total: int; feedback: str
    @model_validator(mode="after")
    def _total(self): ...
```

---

## Step 3 — Spec taxonomy + loader (TDD)

`tests/test_spec_loader.py` first:
- [ ] loads seeded YAML, returns validated objects.
- [ ] every `spec_code` unique.
- [ ] malformed YAML / missing field raises.
- [ ] lookup by `spec_code` returns the objective.

YAML shape (`src/tutorbench/spec/data/maths.yaml`, `cs_ocr_j277.yaml`):
```yaml
subject: maths
topics:
  - name: Functions
    subtopics:
      - name: Composite functions
        objectives:
          - code: M-FUNC-COMP-01
            description: Evaluate and simplify composite functions
            default_marks: 3
```
Seed Maths topics for the 4 templates; seed a slice of OCR J277 for CS (1.x systems
architecture, 2.x algorithms/programming) — original wording, no past-paper text.

`loader.py`:
```python
class Objective(BaseModel): code: str; description: str; default_marks: int
# + Subtopic, Topic, SpecDoc models
def load_spec(path: Path) -> SpecDoc: ...
def all_codes(doc: SpecDoc) -> dict[str, Objective]: ...
```

**→ commit `chore: scaffold M1`.**

---

## Step 4 — Maths engine base (M2)

```python
# src/tutorbench/maths/rng.py
import random
def make_rng(seed: int) -> random.Random: ...   # seeded, reproducible
```

```python
# src/tutorbench/maths/base.py
from abc import ABC, abstractmethod
class Template(ABC):
    spec_code: str; topic: str; subtopic: str
    @abstractmethod
    def generate(self, rng) -> Question: ...
    def _verify(self, q: Question) -> bool: ...   # re-derive in SymPy, return match
```

Helpers worth sharing: deterministic `id` = hash of (template name, params); a
`build_question(...)` that runs `_verify` and only returns with `verified=True` (else raise).

Registry in `templates/__init__.py`: `TEMPLATES: dict[str, type[Template]]`.

---

## Step 5 — Four templates (TDD, one file + one test each)

For each: test asserts (a) generated answer matches an independent SymPy re-derivation,
(b) mark_scheme sums to marks, (c) same seed → identical question. Then implement.

- [ ] **composite_functions.py** — random f,g (linear/quadratic); compute fg(x)/gf(x) or
      fg(a) via `sympy.compose`/`subs` + `simplify`. Working = substitution steps.
- [ ] **vectors.py** — column vectors via `sympy.Matrix`; add/scale + magnitude/midpoint.
- [ ] **iteration.py** — `x_{n+1}=g(x_n)` to N d.p.; `sympy.N`. Working = iteration table.
      Guard rounding stability (see PLAN trade-off).
- [ ] **quadratics.py** — integer roots by construction → `factor`/`solve`. CTS variant.

---

## Step 6 — Verification harness test

`tests/maths/test_verification.py`:
- [ ] loop all templates × several seeds → `generate()` → assert `verified is True` and
      independently re-solve stem in SymPy == `model_answer`. This is the faithfulness gate.

---

## Step 7 — CLI

```python
# src/tutorbench/maths/cli.py  (argparse)
# args: --n, --seed, --topic, --difficulty, --json
# loop registry/topic -> generate -> print stem, model_answer, working, mark scheme
# --json: print [q.model_dump() ...]
```

---

## Step 8 — Verify + stop

- [ ] `pytest -q` all green.
- [ ] `python -m tutorbench.maths.cli --n 5 --seed 42` — eyeball output; re-run same seed →
      identical (reproducibility).
- [ ] commit `feat(maths): deterministic SymPy engine M2`.
- [ ] **STOP. Show generated questions for review before M3.**
```
