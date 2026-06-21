"""Tests for the Concept Hyper-Lattice — the core of LatticeRAG.

Reproduces the worked example from ai/architecture.md section 4.3 and checks the
properties that make the engine useful: convergence (Perron-Frobenius), mass
conservation, and multi-hop retrieval (an un-seeded concept surfacing).

Pure stdlib — runs with `pytest`, or directly: `python tests/test_hyperlattice.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ytdrivebook.index.hyperlattice import ConceptHyperLattice  # noqa: E402


def build_electricity_lattice() -> ConceptHyperLattice:
    """The 3-concept example: energy-flow, Poynting, drift-velocity."""
    g = ConceptHyperLattice()
    g.add_similarity("energy-flow", "poynting", 0.9)
    g.add_similarity("energy-flow", "drift", 0.5)
    g.add_similarity("poynting", "drift", 0.3)
    # prerequisite skeleton: both advanced ideas rest on "fields"
    g.add_prerequisite("poynting", "fields")
    g.add_prerequisite("drift", "fields")
    return g


def test_ppr_matches_worked_example():
    g = build_electricity_lattice()
    r = g.personalized_pagerank(
        seed={"energy-flow": 0.5, "poynting": 0.5}, restart=0.5
    )
    # converged values from ai/architecture.md (fields has 0 similarity weight)
    assert abs(r["energy-flow"] - 0.449) < 0.02
    assert abs(r["poynting"] - 0.419) < 0.02
    assert abs(r["drift"] - 0.133) < 0.02


def test_mass_is_conserved():
    g = build_electricity_lattice()
    r = g.personalized_pagerank(seed={"energy-flow": 1.0}, restart=0.5)
    assert abs(sum(r.values()) - 1.0) < 1e-9


def test_multihop_surfaces_unseeded_concept():
    """drift-velocity is never in the query, but the walk must surface it."""
    g = build_electricity_lattice()
    r = g.personalized_pagerank(
        seed={"energy-flow": 0.5, "poynting": 0.5}, restart=0.5
    )
    assert r["drift"] > 0.05  # found via graph links, not the query


def test_ranking_order():
    g = build_electricity_lattice()
    ranked = g.rank(seed={"energy-flow": 0.5, "poynting": 0.5}, restart=0.5)
    ids = [cid for cid, _ in ranked]
    assert ids[0] in {"energy-flow", "poynting"}
    assert ids[-1] in {"drift", "fields"}  # least relevant


def test_meet_finds_shared_foundation():
    g = build_electricity_lattice()
    assert g.meet("poynting", "drift") == "fields"


def test_hyperedge_adds_cooccurrence_and_evidence():
    g = ConceptHyperLattice()
    g.add_hyperedge("h1", ["poynting", "energy-flow", "drift"], unit_ref="vid#0002")
    # clique expansion created similarity edges between co-taught concepts
    assert g.sim["poynting"]["energy-flow"] > 0
    # the hyperedge is retrievable as evidence (timestamp/citation lives here)
    assert ("h1", "vid#0002") in g.evidence_for("poynting")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
