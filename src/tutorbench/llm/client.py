"""LLM client Protocol + Ollama implementation (M3).

All model I/O goes through a Pydantic schema. Unit tests inject a fake client
(see ``tests/conftest.py``); the production ``OllamaClient`` wraps Ollama via
``instructor`` so the schema is the enforced structured-output format.
"""
from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

from ..config import Settings, get_settings

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMClient(Protocol):
    """Anything that turns a chat prompt into a validated Pydantic object."""

    def structured(
        self, *, model: str, messages: list[dict], schema: type[T]
    ) -> T: ...


class OllamaClient:
    """``instructor``-wrapped Ollama client, built from :class:`Settings`.

    The instructor client is created lazily so importing this module (and
    running the fake-client unit tests) never touches the network.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None

    def _instructor(self):
        if self._client is None:
            import instructor
            from openai import OpenAI

            self._client = instructor.from_openai(
                OpenAI(
                    base_url=f"{self._settings.ollama_host}/v1",
                    api_key="ollama",  # required by the SDK, ignored by Ollama
                ),
                mode=instructor.Mode.JSON,
            )
        return self._client

    def structured(
        self, *, model: str, messages: list[dict], schema: type[T]
    ) -> T:
        # instructor enforces `schema` as the response format and retries on
        # schema-invalid output, then raises if it never validates.
        return self._instructor().chat.completions.create(
            model=model,
            messages=messages,
            response_model=schema,
        )
