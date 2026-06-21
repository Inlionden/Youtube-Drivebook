"""MCP server — exposes the knowledge base as an agent tool surface. Phase 6.

STUB. Planned tools (the 'adapter' that hands agents pre-aligned, cited context):
  search_concepts(query)        -> ranked concept nodes
  get_concept(id)               -> definition + relations + cited units
  related_concepts(id, hops)    -> graph neighborhood
  meet(a, b)                    -> shared prerequisite to teach first
  get_context(query, budget)    -> token-budgeted cited context block
  answer(query)                 -> full LatticeRAG pass with citations
"""

from __future__ import annotations

from ytdrivebook.index import ConceptHyperLattice


def build_server(lattice: ConceptHyperLattice):
    raise NotImplementedError("Phase 6: register MCP tools over the lattice")
