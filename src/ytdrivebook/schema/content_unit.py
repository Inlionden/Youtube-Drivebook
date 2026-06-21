"""Stage 2 contract: the canonical intermediate schema. Every output is a view on it."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ytdrivebook.schema.source import MediaRef, Source


class QAPair(BaseModel):
    q: str
    a: str


class ContentUnit(BaseModel):
    """The keystone. One unit ≈ one creator chapter or one detected topic.

    Exporters read ONLY this. Adding an output format means reading these fields
    differently — never re-processing the source or re-calling the LLM.
    """

    id: str
    source: Source
    chapter: str | None = None
    topic: str
    summary: str
    content: str
    key_points: list[str] = Field(default_factory=list)
    qa_pairs: list[QAPair] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    media: list[MediaRef] = Field(default_factory=list)
    concepts: list[str] = Field(
        default_factory=list, description="ids of Concepts this unit touches"
    )
