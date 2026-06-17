"""LLM client layer tests (M3, PLANV2 Step 1).

Only the fake client is exercised here — no network. The real ``OllamaClient``
is covered by ``@pytest.mark.integration`` tests elsewhere.
"""
import pytest
from pydantic import BaseModel

from tutorbench.llm.client import LLMClient, OllamaClient


class _Schema(BaseModel):
    x: int


def test_ollama_client_satisfies_protocol():
    assert isinstance(OllamaClient(), LLMClient)


def test_fake_returns_queued_object(fake_llm):
    client = fake_llm([_Schema(x=1)])
    out = client.structured(model="m", messages=[], schema=_Schema)
    assert out == _Schema(x=1)
    assert client.calls[0]["model"] == "m"


def test_fake_raises_when_queue_empty(fake_llm):
    client = fake_llm([])
    with pytest.raises(RuntimeError):
        client.structured(model="m", messages=[], schema=_Schema)


def test_fake_raises_on_schema_mismatch(fake_llm):
    class _Other(BaseModel):
        y: int

    client = fake_llm([_Other(y=1)])
    with pytest.raises(TypeError):
        client.structured(model="m", messages=[], schema=_Schema)
