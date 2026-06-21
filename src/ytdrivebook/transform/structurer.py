"""RawSegment -> ContentUnit via the LLM (Stage 2).

Builds the prompt, calls the LLM in JSON mode, validates the result into the
ContentUnit schema (with one retry), and stamps source provenance + media from
the original segment. Concept extraction happens separately in Phase 4.
"""

from __future__ import annotations

import logging

from pydantic import ValidationError

from ytdrivebook.schema import ContentUnit, QAPair, RawSegment
from ytdrivebook.transform.llm_client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You structure raw video transcript into a clean study unit. "
    "Be faithful to the transcript; do not invent facts. "
    "Respond with a single JSON object only."
)

_FIELDS_SPEC = (
    "Return JSON with these keys:\n"
    '  "topic": short title of what this segment is about\n'
    '  "summary": 1-2 sentence abstract\n'
    '  "content": cleaned, readable prose of the segment\n'
    '  "key_points": array of short takeaway strings\n'
    '  "qa_pairs": array of {"q": question, "a": answer}\n'
    '  "tags": array of lowercase topic tags\n'
)


class Structurer:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def _user_prompt(self, segment: RawSegment, strict: bool = False) -> str:
        extra = "\nAll listed keys are REQUIRED." if strict else ""
        return f"{_FIELDS_SPEC}{extra}\n\nTRANSCRIPT:\n{segment.text}"

    def _to_unit(
        self, data: dict, segment: RawSegment, unit_id: str, chapter: str | None
    ) -> ContentUnit:
        return ContentUnit(
            id=unit_id,
            source=segment.source,
            chapter=chapter or data.get("chapter"),
            topic=data["topic"],
            summary=data["summary"],
            content=data.get("content") or segment.text,
            key_points=list(data.get("key_points", [])),
            qa_pairs=[QAPair(**qa) for qa in data.get("qa_pairs", [])],
            tags=list(data.get("tags", [])),
            media=segment.media,
        )

    def structure(
        self, segment: RawSegment, unit_id: str, chapter: str | None = None
    ) -> ContentUnit:
        data = self.llm.complete_json(SYSTEM_PROMPT, self._user_prompt(segment))
        try:
            return self._to_unit(data, segment, unit_id, chapter)
        except (KeyError, ValidationError, TypeError) as exc:
            logger.warning("structurer first pass failed (%s); retrying strictly", exc)
            data = self.llm.complete_json(
                SYSTEM_PROMPT, self._user_prompt(segment, strict=True)
            )
            return self._to_unit(data, segment, unit_id, chapter)
