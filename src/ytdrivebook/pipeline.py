"""Orchestration: extract -> transform -> (graph) -> load/serve.

STUB wiring — fills in as phases land. The shape shows how the pieces compose;
each call currently delegates to a stubbed stage.
"""

from __future__ import annotations

from pathlib import Path

from ytdrivebook.extract.youtube import YouTubeIngester
from ytdrivebook.index import ConceptHyperLattice
from ytdrivebook.load.exporters import EXPORTERS
from ytdrivebook.schema import ContentUnit
from ytdrivebook.transform.concepts import ConceptResolver
from ytdrivebook.transform.llm_client import LLMClient
from ytdrivebook.transform.structurer import Structurer


def ingest(ref: str, llm: LLMClient) -> list[ContentUnit]:
    """Extract raw segments and structure them into ContentUnits."""
    ingester = YouTubeIngester()
    structurer = Structurer(llm)
    units: list[ContentUnit] = []
    for i, segment in enumerate(ingester.extract(ref)):
        units.append(structurer.structure(segment, unit_id=f"{ref}#{i:04d}"))
    return units


def build_graph(units: list[ContentUnit], llm: LLMClient) -> ConceptHyperLattice:
    """Resolve concepts and assemble the Concept Hyper-Lattice."""
    return ConceptResolver(llm).build(units)


def export(units: list[ContentUnit], fmt: str, out_path: Path) -> Path:
    """Render ContentUnits via the chosen exporter."""
    if fmt not in EXPORTERS:
        raise ValueError(f"unknown format {fmt!r}; choose from {sorted(EXPORTERS)}")
    return EXPORTERS[fmt]().export(units, out_path)
