"""/generate API tests (M3, PLANV2 Step 4) — TestClient + injected fake client."""
import pytest
from fastapi.testclient import TestClient

from tutorbench.api.app import app, get_llm_client
from tutorbench.generation.cs import CSDraft
from tutorbench.models import MarkPoint

# Real packaged spec_code (CS-J277-1.1-01, default_marks=2).
SPEC_CODE = "CS-J277-1.1-01"


def _draft() -> CSDraft:
    return CSDraft(
        topic="Systems architecture",
        subtopic="The CPU",
        marks=2,
        stem="State the three stages of the fetch-decode-execute cycle.",
        model_answer="Fetch, decode, execute.",
        working="The CPU repeats fetch, decode, then execute each cycle.",
        mark_scheme=[MarkPoint(description="All three stages named", marks=2)],
    )


@pytest.fixture
def client(fake_llm):
    # Queue: 1 generation draft + 3 agreeing re-answers (default n=3, threshold=0.66).
    fake = fake_llm([_draft(), _draft(), _draft(), _draft()])
    app.dependency_overrides[get_llm_client] = lambda: fake
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_generate_returns_verified_question(client):
    resp = client.post(
        "/generate",
        json={
            "subject": "cs",
            "spec_code": SPEC_CODE,
            "difficulty": "easy",
            "marks": 2,
            "type": "short_answer",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["subject"] == "cs"
    assert body["spec_code"] == SPEC_CODE
    assert body["verified"] is True


def test_unknown_spec_code_returns_404(client):
    resp = client.post(
        "/generate",
        json={
            "subject": "cs",
            "spec_code": "CS-DOES-NOT-EXIST",
            "difficulty": "easy",
            "marks": 2,
            "type": "short_answer",
        },
    )
    assert resp.status_code == 404
