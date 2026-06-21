"""The Exporter contract. The other half of the extensibility design."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ytdrivebook.schema import ContentUnit


class Exporter(ABC):
    """Renders ContentUnits into an output file. Reads ONLY ContentUnit — never
    re-processes the source and never calls the LLM again."""

    name: str = "exporter"

    @abstractmethod
    def export(self, units: list[ContentUnit], out_path: Path) -> Path:
        """Write the output and return the path written."""
