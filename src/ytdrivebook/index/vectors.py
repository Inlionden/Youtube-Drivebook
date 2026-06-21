"""Vector recall layer (the safety net under the graph walk).

STUB — Phase 4/5. Wrap FAISS or sqlite-vec behind this interface so LatticeRAG
can do graph-first retrieval with a vector fallback for recall.
"""

from __future__ import annotations

from typing import Protocol


class VectorIndex(Protocol):
    def add(self, key: str, vector: list[float], payload: dict) -> None: ...
    def search(self, vector: list[float], top_k: int = 10) -> list[tuple[str, float]]: ...


class InMemoryVectorIndex:
    """Trivial brute-force cosine index for tests/small corpora."""

    def __init__(self) -> None:
        self._items: list[tuple[str, list[float], dict]] = []

    def add(self, key: str, vector: list[float], payload: dict) -> None:
        self._items.append((key, vector, payload))

    def search(self, vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        def cos(u: list[float], v: list[float]) -> float:
            dot = sum(a * b for a, b in zip(u, v))
            nu = sum(a * a for a in u) ** 0.5
            nv = sum(b * b for b in v) ** 0.5
            return dot / (nu * nv) if nu and nv else 0.0

        scored = [(k, cos(vector, vec)) for k, vec, _ in self._items]
        scored.sort(key=lambda kv: kv[1], reverse=True)
        return scored[:top_k]
