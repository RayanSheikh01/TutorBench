# Implementation Guide (M1–M2) — you write the code

Ordered TDD checklist. Test first → watch fail → implement. Minimal stubs only. Stop after M2.

---

## Step 0 — Scaffold ✅ done

venv, `pyproject.toml`, `.gitignore`, `.env.example`, `README.md`, `src/tutorbench/__init__.py`,
`pip install -e ".[dev]"`, `git init` + commit.

---

## Step 1 — config.py

```python
# src/tutorbench/config.py
class Settings(BaseSettings):
    ollama_host: str = ...
    ollama_gen_model: str = ...
    ollama_grade_model: str = ...

def get_settings() -> Settings: ...   # lru_cache
```

---

## Step 2 — Data model (TDD)

Tests (`tests/test_models.py`) — write first:

- valid Question builds; `verified` defaults False
- mark_scheme marks sum ≠ marks → ValidationError
- empty stem / model_answer rejected
- bad subject / difficulty / type enum rejected
- Submission total ≠ sum(awarded) → error

```python
# src/tutorbench/models.py
class Subject(str, Enum): ...
class Difficulty(str, Enum): ...
class QType(str, Enum): ...

class MarkPoint(BaseModel): description: str; marks: int

class Question(BaseModel):
    id; subject; spec_code; topic; subtopic
    difficulty; marks; type; stem; model_answer
    working; mark_scheme: list[MarkPoint]; verified: bool = False
    # @model_validator: sum(mark_scheme marks) == marks

class MarkAward(BaseModel): point: str; awarded_marks: int; justification: str
class Submission(BaseModel): ...   # @model_validator: total == sum(awarded)
```

---

## Step 3 — Spec taxonomy + loader (TDD)

Tests (`tests/test_spec_loader.py`):

- loads seeded YAML → validated objects
- spec_codes unique
- malformed / missing field raises
- lookup by code returns objective

YAML (`spec/data/maths.yaml`, `cs_ocr_j277.yaml`) — subject → topics → subtopics → objectives
`{code, description, default_marks}`. Original wording, no past-paper text.

```python
# src/tutorbench/spec/loader.py
class Objective(BaseModel): ...
class Subtopic / Topic / SpecDoc(BaseModel): ...
def load_spec(path) -> SpecDoc: ...
def all_codes(doc) -> dict[str, Objective]: ...
```

**→ commit `chore: scaffold M1`.**

---

## Step 4 — Maths engine base

```python
# maths/rng.py
def make_rng(seed: int) -> random.Random: ...

# maths/base.py
class Template(ABC):
    spec_code; topic; subtopic
    @abstractmethod
    def generate(self, rng) -> Question: ...
    def _verify(self, q) -> bool: ...        # re-derive in SymPy == model_answer

# build_question(...) -> sets verified, raises if mismatch (never emit unverified)
# templates/__init__.py: TEMPLATES: dict[str, type[Template]]
```

---

## Step 5 — Four templates (TDD: one test + one file each)

Each test: (a) answer == independent SymPy re-derive, (b) mark_scheme sums to marks,
(c) same seed → identical question.

```python
# composite_functions.py  random f,g -> fg(x)/gf(x)/fg(a); sympy compose/subs/simplify
# vectors.py              column vecs (sympy.Matrix); add/scale, magnitude/midpoint
# iteration.py            x_{n+1}=g(x_n) to N dp; sympy.N; guard rounding stable
# quadratics.py           integer roots by construction; factor/solve; CTS variant
```

---

## Step 6 — Verification harness test

```python
# tests/maths/test_verification.py
# all templates x several seeds -> generate() -> assert verified and SymPy re-solve == answer
```

---

## Step 7 — CLI

```python
# maths/cli.py  argparse: --n --seed --topic --difficulty --json
# loop -> generate -> print stem, model_answer, working, mark scheme  (--json: model_dump)
def main(): ...
```

---

## Step 8 — Verify + stop

- `pytest -q` green
- `python -m tutorbench.maths.cli --n 5 --seed 42` (re-run same seed → identical)
- commit `feat(maths): deterministic SymPy engine M2`
- **STOP. Show questions for review before M3.**
