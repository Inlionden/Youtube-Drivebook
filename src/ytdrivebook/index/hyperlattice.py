"""The Concept Hyper-Lattice — the core data structure behind LatticeRAG.

A graph of *concepts* with three kinds of edges:

  * **similarity** (weighted, symmetric)  -> semantic closeness; drives the walk
  * **prerequisite** (directed)           -> a partial order = the "lattice"
  * **hyperedge**   (a taught segment)    -> connects several concepts at once and
                                             carries the evidence (timestamp/frame)

Retrieval is a Personalized PageRank / Random-Walk-with-Restart over the
similarity graph:

    r = c·q + (1−c)·P·r           (P column-stochastic, q = query seed)

solved by power iteration. It converges to a unique ranking by the
Perron–Frobenius theorem. The walk surfaces concepts the query never named but
that are graph-linked (multi-hop) — the property plain vector RAG lacks.

This module is intentionally pure-stdlib (dicts, no numpy) so the engine and its
tests run with zero installs. A numpy/scipy fast path can be added later behind
the same interface.
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class ConceptHyperLattice:
    """Concepts + similarity edges + prerequisite DAG + hyperedges."""

    # concept id -> human-readable name
    names: dict[str, str] = field(default_factory=dict)
    # symmetric similarity weights: sim[a][b] == sim[b][a]
    sim: dict[str, dict[str, float]] = field(default_factory=lambda: defaultdict(dict))
    # directed prerequisite edges: child -> set(parents it depends on)
    prereq: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    # hyperedges: each is (id, frozenset(concept_ids), unit_ref)
    hyperedges: list[tuple[str, frozenset[str], str]] = field(default_factory=list)

    # ---- construction ----------------------------------------------------

    def add_concept(self, concept_id: str, name: str | None = None) -> None:
        self.names.setdefault(concept_id, name or concept_id)
        _ = self.sim[concept_id]  # touch so isolated nodes still exist

    def add_similarity(self, a: str, b: str, weight: float) -> None:
        """Add/strengthen an undirected similarity edge."""
        if a == b or weight <= 0:
            return
        self.add_concept(a)
        self.add_concept(b)
        self.sim[a][b] = self.sim[a].get(b, 0.0) + weight
        self.sim[b][a] = self.sim[b].get(a, 0.0) + weight

    def add_prerequisite(self, concept: str, requires: str) -> None:
        """`concept` requires `requires` first (directed lattice edge)."""
        self.add_concept(concept)
        self.add_concept(requires)
        self.prereq[concept].add(requires)

    def add_hyperedge(self, edge_id: str, concept_ids: list[str], unit_ref: str) -> None:
        """A segment that teaches several concepts together. Also lays down
        similarity edges between co-taught concepts (clique expansion)."""
        ids = [c for c in concept_ids if c]
        for c in ids:
            self.add_concept(c)
        self.hyperedges.append((edge_id, frozenset(ids), unit_ref))
        for i, a in enumerate(ids):
            for b in ids[i + 1 :]:
                self.add_similarity(a, b, 1.0)

    # ---- retrieval: Personalized PageRank --------------------------------

    def personalized_pagerank(
        self,
        seed: dict[str, float],
        restart: float = 0.5,
        max_iter: int = 200,
        tol: float = 1e-12,
    ) -> dict[str, float]:
        """Random-walk-with-restart relevance scores over the similarity graph.

        Args:
            seed: query distribution over concept ids (need not be normalized).
            restart: probability c of teleporting back to the seed each step.
            max_iter / tol: power-iteration stopping criteria.

        Returns:
            concept id -> relevance, summing to 1.0.
        """
        nodes = list(self.names)
        if not nodes:
            return {}

        seed_total = sum(v for v in seed.values() if v > 0) or 1.0
        q = {n: max(seed.get(n, 0.0), 0.0) / seed_total for n in nodes}

        # weighted out-degree of each node (column sum of the transition matrix)
        deg = {n: sum(self.sim[n].values()) for n in nodes}

        r = dict(q)
        for _ in range(max_iter):
            nxt = {n: restart * q[n] for n in nodes}
            # redistribute mass that lands on dangling (degree-0) nodes back to q
            dangling = 0.0
            for j in nodes:
                if r[j] == 0.0:
                    continue
                if deg[j] == 0.0:
                    dangling += r[j]
                    continue
                share = (1.0 - restart) * r[j] / deg[j]
                for i, w in self.sim[j].items():
                    nxt[i] += share * w
            if dangling:
                add = (1.0 - restart) * dangling
                for n in nodes:
                    nxt[n] += add * q[n]
            diff = sum(abs(nxt[n] - r[n]) for n in nodes)
            r = nxt
            if diff < tol:
                break
        return r

    def rank(self, seed: dict[str, float], top_k: int | None = None, **kw):
        """PPR, returned as a sorted (concept_id, score) list."""
        scores = self.personalized_pagerank(seed, **kw)
        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return ordered[:top_k] if top_k else ordered

    # ---- lattice operations ----------------------------------------------

    def ancestors(self, concept: str) -> set[str]:
        """All prerequisites reachable from `concept` (its foundations)."""
        seen: set[str] = set()
        dq = deque(self.prereq.get(concept, ()))
        while dq:
            cur = dq.popleft()
            if cur in seen:
                continue
            seen.add(cur)
            dq.extend(self.prereq.get(cur, ()))
        return seen

    def depth(self, concept: str) -> int:
        """Longest prerequisite chain below `concept` (0 = foundational)."""
        best = 0
        for parent in self.prereq.get(concept, ()):
            best = max(best, 1 + self.depth(parent))
        return best

    def meet(self, a: str, b: str) -> str | None:
        """Greatest common prerequisite of two concepts — the shared foundation
        to teach before combining them (order-theory 'meet')."""
        common = self.ancestors(a) & self.ancestors(b)
        if not common:
            return None
        return max(common, key=self.depth)

    # ---- statistics ------------------------------------------------------

    def pmi(self, a: str, b: str) -> float:
        """Pointwise mutual information of co-teaching, from hyperedge counts.

        PMI(a,b) = log( P(a,b) / (P(a)·P(b)) ). Positive => taught together more
        than chance. Useful for weighting/pruning similarity edges (Phase 4).
        """
        total = len(self.hyperedges)
        if total == 0:
            return 0.0
        c_a = sum(1 for _, cs, _ in self.hyperedges if a in cs)
        c_b = sum(1 for _, cs, _ in self.hyperedges if b in cs)
        c_ab = sum(1 for _, cs, _ in self.hyperedges if a in cs and b in cs)
        if c_a == 0 or c_b == 0 or c_ab == 0:
            return 0.0
        p_a, p_b, p_ab = c_a / total, c_b / total, c_ab / total
        return math.log(p_ab / (p_a * p_b))

    def evidence_for(self, concept: str) -> list[tuple[str, str]]:
        """(hyperedge_id, unit_ref) pairs that teach `concept` — its citations."""
        return [(eid, ref) for eid, cs, ref in self.hyperedges if concept in cs]
