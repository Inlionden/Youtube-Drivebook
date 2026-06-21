"""The Ingester contract. This ABC is half of the extensibility design."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from ytdrivebook.schema import RawSegment


class Ingester(ABC):
    """Turns a source reference (URL/path) into RawSegments.

    Implementations must NOT know anything about transform/load — they only
    produce RawSegments. That isolation is what lets new sources plug in.
    """

    @abstractmethod
    def supports(self, ref: str) -> bool:
        """Return True if this ingester can handle the given reference."""

    @abstractmethod
    def extract(self, ref: str) -> Iterable[RawSegment]:
        """Yield RawSegments for the given source reference."""
