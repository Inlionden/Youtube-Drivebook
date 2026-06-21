"""Concept extraction + resolution -> populates the Concept Hyper-Lattice. Phase 4.

STUB. Strategy (ADR-0007, cheapest-first cascade):
  1. LLM proposes a canonical concept name + aliases per ContentUnit.
  2. Embed names; merge pairs above a cosine threshold.
  3. LLM adjudicates only borderline pairs.
Then: add concepts, prerequisite/relation edges, and one hyperedge per unit
(carrying its timestamp + media) to the lattice.
"""

from __future__ import annotations

from ytdrivebook.index import ConceptHyperLattice
from ytdrivebook.schema import ContentUnit
from ytdrivebook.transform.llm_client import LLMClient


class ConceptResolver:
    def __init__(self, llm: LLMClient, merge_threshold: float = 0.86) -> None:
        self.llm = llm
        self.merge_threshold = merge_threshold

    def build(self, units: list[ContentUnit]) -> ConceptHyperLattice:
        raise NotImplementedError("Phase 4: extract + resolve concepts into the lattice")
