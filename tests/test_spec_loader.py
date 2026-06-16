"""Tests for the spec taxonomy loader (M1)."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from tutorbench import spec as spec_pkg
from tutorbench.spec.loader import Objective, SpecDoc, all_codes, load_spec

DATA_DIR = Path(spec_pkg.__file__).parent / "data"


@pytest.mark.parametrize("filename", ["maths.yaml", "cs_ocr_j277.yaml"])
def test_loads_seeded_yaml(filename):
    doc = load_spec(DATA_DIR / filename)
    assert isinstance(doc, SpecDoc)
    assert doc.topics, "expected at least one topic"
    # every objective is a validated Objective with a non-empty code
    codes = all_codes(doc)
    assert codes
    assert all(isinstance(o, Objective) and o.code for o in codes.values())


@pytest.mark.parametrize("filename", ["maths.yaml", "cs_ocr_j277.yaml"])
def test_spec_codes_unique(filename):
    doc = load_spec(DATA_DIR / filename)
    flat = [
        o.code
        for t in doc.topics
        for s in t.subtopics
        for o in s.objectives
    ]
    assert len(flat) == len(set(flat)), "duplicate spec_code in seeded data"


def test_lookup_by_code_returns_objective():
    doc = load_spec(DATA_DIR / "maths.yaml")
    codes = all_codes(doc)
    # composite functions objective seeded for the M2 template
    obj = codes["M-FUNC-COMP-01"]
    assert obj.default_marks > 0
    assert "composite" in obj.description.lower()


def test_missing_required_field_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "subject: maths\n"
        "topics:\n"
        "  - name: Functions\n"
        "    subtopics:\n"
        "      - name: Composite functions\n"
        "        objectives:\n"
        "          - code: M-X-01\n"
        "            description: missing default_marks\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_spec(bad)


def test_duplicate_code_raises(tmp_path):
    dup = tmp_path / "dup.yaml"
    dup.write_text(
        "subject: maths\n"
        "topics:\n"
        "  - name: Functions\n"
        "    subtopics:\n"
        "      - name: A\n"
        "        objectives:\n"
        "          - {code: DUP-1, description: a, default_marks: 1}\n"
        "      - name: B\n"
        "        objectives:\n"
        "          - {code: DUP-1, description: b, default_marks: 2}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_spec(dup)


def test_malformed_yaml_raises(tmp_path):
    broken = tmp_path / "broken.yaml"
    broken.write_text("subject: maths\n  topics: [oops\n", encoding="utf-8")
    with pytest.raises(Exception):
        load_spec(broken)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_spec(DATA_DIR / "does_not_exist.yaml")
