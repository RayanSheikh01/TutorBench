"""Shared test fixtures. The fake LLM client keeps unit tests deterministic
and offline (PLANV2: all unit tests inject a fake client, no network)."""
import pytest
from pydantic import BaseModel


class FakeLLM:
    """In-memory ``LLMClient``: pops canned objects from a queue, records calls.

    Each queued response must be an instance of the ``schema`` requested at the
    matching call (mirrors instructor validating real model output). Raises when
    the queue is empty or the type does not match.
    """

    def __init__(self, responses: list[BaseModel] | None = None) -> None:
        self.responses: list[BaseModel] = list(responses or [])
        self.calls: list[dict] = []

    def structured(self, *, model: str, messages: list[dict], schema: type[BaseModel]) -> BaseModel:
        self.calls.append({"model": model, "messages": messages, "schema": schema})
        if not self.responses:
            raise RuntimeError("FakeLLM queue empty: no canned response left")
        obj = self.responses.pop(0)
        if not isinstance(obj, schema):
            raise TypeError(
                f"FakeLLM response {type(obj).__name__} does not match schema {schema.__name__}"
            )
        return obj


@pytest.fixture
def fake_llm():
    """Factory: build a :class:`FakeLLM` from a list of canned responses."""
    def _make(responses=None):
        return FakeLLM(responses)

    return _make
