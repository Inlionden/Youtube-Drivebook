"""Stage 1 contracts: where content comes from and the raw segments pulled out."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    YOUTUBE = "youtube"
    WEB = "web"
    PDF = "pdf"
    PODCAST = "podcast"


class Source(BaseModel):
    """Provenance for a piece of content. Source-agnostic by design."""

    type: SourceType
    url: str
    video_id: str | None = None
    channel: str | None = None
    title: str | None = None
    start: float | None = Field(default=None, description="segment start, seconds")
    end: float | None = Field(default=None, description="segment end, seconds")


class MediaRef(BaseModel):
    """A reference to extracted media (a key frame, or OCR'd text region)."""

    path: str
    timestamp: float | None = None
    caption: str | None = None
    kind: str = "frame"  # "frame" | "ocr"


class RawSegment(BaseModel):
    """Stage 1 output: a chunk of raw transcript + any media, with timing.

    This is what every `Ingester` must yield, regardless of source.
    """

    source: Source
    text: str
    start: float
    end: float
    media: list[MediaRef] = Field(default_factory=list)
