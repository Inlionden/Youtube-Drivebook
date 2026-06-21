"""RawSegment -> ContentUnit via the LLM. Phase 2.

STUB. Builds the prompt, calls the LLM in JSON mode, validates against the
ContentUnit schema (retry on validation failure), and stamps source provenance.
"""

from __future__ import annotations

from ytdrivebook.schema import ContentUnit, RawSegment
from ytdrivebook.transform.llm_client import LLMClient


class Structurer:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def structure(self, segment: RawSegment, unit_id: str) -> ContentUnit:
        raise NotImplementedError("Phase 2: prompt Groq, validate into ContentUnit")
