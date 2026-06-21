"""Thin, swappable LLM client. Groq today (OpenAI-compatible, JSON mode); the
interface stays stable if the provider changes (see ADR-0003).

STUB — Phase 2. `FakeLLMClient` lets transform/structurer be tested offline.
"""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def complete_json(self, system: str, user: str, schema: dict | None = None) -> dict:
        """Return a parsed JSON object adhering to `schema` if given."""
        ...


class GroqClient:
    """Wraps the Groq SDK. Implemented in Phase 2."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def complete_json(self, system: str, user: str, schema: dict | None = None) -> dict:
        raise NotImplementedError("Phase 2: call Groq chat completions with JSON mode")


class FakeLLMClient:
    """Deterministic stub for offline tests — returns a canned object."""

    def __init__(self, response: dict) -> None:
        self._response = response

    def complete_json(self, system: str, user: str, schema: dict | None = None) -> dict:
        return dict(self._response)
