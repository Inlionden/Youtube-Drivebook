"""Thin, swappable LLM client. Groq today (OpenAI-compatible, JSON mode); the
interface stays stable if the provider changes (see ADR-0003)."""

from __future__ import annotations

import json
import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    def complete_json(self, system: str, user: str, schema: dict | None = None) -> dict:
        """Return a parsed JSON object adhering to `schema` if given."""
        ...


class GroqClient:
    """Wraps the Groq SDK and forces JSON output.

    The SDK is imported lazily so the rest of the package (and its tests) load
    even when `groq` isn't installed.
    """

    def __init__(self, api_key: str, model: str, temperature: float = 0.2) -> None:
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing; set it in .env")
        self.model = model
        self.temperature = temperature
        try:
            from groq import Groq
        except ImportError as exc:  # pragma: no cover - depends on env
            raise ImportError("install the 'groq' package to use GroqClient") from exc
        self._client = Groq(api_key=api_key)

    def complete_json(self, system: str, user: str, schema: dict | None = None) -> dict:
        resp = self._client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = resp.choices[0].message.content or "{}"
        logger.debug("groq returned %d chars", len(content))
        return json.loads(content)


class FakeLLMClient:
    """Deterministic stub for offline tests — returns a canned object."""

    def __init__(self, response: dict) -> None:
        self._response = response

    def complete_json(self, system: str, user: str, schema: dict | None = None) -> dict:
        return dict(self._response)
