# Architecture — YouTube Drivebook & LatticeRAG

## 1. Big picture

```
 SOURCES            STAGE 1            STAGE 2                 GRAPH              STAGE 3 / 4
 ───────            ───────            ───────                 ─────              ───────────
 YouTube  ─┐                                       ┌─ Concept Hyper-Lattice ─┐
 Web      ─┤  Ingester ─► RawSegment ─► Groq ─► ContentUnit ─► Concepts ─────┤  Exporters (Load)
 PDF      ─┤  (strategy)                (transform)     │      + edges        │  LatticeRAG (Serve)
 Podcast  ─┘                                            └─ vector index ──────┘    └─ MCP server
```

`ContentUnit` is the canonical intermediate schema. **Every output is a view on it.**
New source ⇒ new `Ingester` only. New output ⇒ new `Exporter` only. Stages 2–4 are
untouched by either. This is the core extensibility contract.

## 2. Package layout
```
src/ytdrivebook/
  config.py            # env-driven settings
  schema/              # Pydantic models — the keystone
    source.py          #   Source, MediaRef, RawSegment
    content_unit.py    #   QAPair, ContentUnit
    concept.py         #   RelationType, Relation, Concept, Hyperedge
  extract/             # Stage 1 — Ingester strategy
    base.py            #   Ingester ABC
    youtube.py
  transform/           # Stage 2 — Groq structuring
    llm_client.py      #   thin Groq wrapper (swappable)
    structurer.py      #   RawSegment -> ContentUnit
    concepts.py        #   concept extraction + resolution
  index/               # storage / engine
    hyperlattice.py    #   Concept Hyper-Lattice + PPR walk  ◄── core
    vectors.py         #   vector recall layer
  load/                # Stage 3 — exporters
    base.py            #   Exporter ABC
    exporters.py       #   markdown / pdf / jsonl / rag / csv / flashcards
  serve/               # Stage 4 — answer engine + MCP
    mcp_server.py
  pipeline.py          # orchestration
  cli.py               # Typer CLI
```

## 3. Schemas (data contracts)
- **Source**: `type, url, video_id?, channel?, title?, start?, end?`
- **MediaRef**: `path, timestamp?, caption?, kind(frame|ocr)`
- **RawSegment** (Stage 1 out): `source, text, start, end, media[]`
- **QAPair**: `q, a`
- **ContentUnit** (Stage 2 out): `id, source, chapter?, topic, summary, content,
  key_points[], qa_pairs[], tags[], media[], concepts[]`
- **RelationType**: `PREREQUISITE | EXPLAINS | CONTRADICTS | EXAMPLE_OF | SAME_AS | RELATED`
- **Relation**: `to(concept_id), type`
- **Concept**: `id, name, aliases[], definition?, relations[], unit_refs[]`
- **Hyperedge**: `id, concept_ids[], unit_ref, start, end, media[]` — one taught segment,
  the unit of *evidence* (carries timestamp + frame).

---

## 4. LatticeRAG — the custom retrieval engine

Combines three proven ideas and adds one new one:

| Borrowed from | Kept |
|---|---|
| Vector RAG | dense similarity → recall safety net |
| GraphRAG | ideas as a graph → structural reasoning |
| HippoRAG | random walk (Personalized PageRank) → multi-hop retrieval |
| **NEW** | a **prerequisite lattice** → pedagogical ordering (teach foundations first) |

### 4.1 The data structure: Concept Hyper-Lattice
Nodes = concepts. Three edge kinds:
- **Prerequisite** (directed) → a partial order / DAG (the "lattice").
- **Similarity** (weighted, symmetric) → semantic closeness (from embeddings/PMI).
- **Hyperedge** → a video segment teaching a *group* of concepts together; carries
  the timestamp, frame, and citation. A normal 2-node edge can't represent this.

### 4.2 Math

**(a) Edge weights — PMI (statistics).** Co-teaching strength of concepts A,B:
```
PMI(A,B) = log( P(A,B) / (P(A)·P(B)) )
```
`P(A)` = fraction of segments mentioning A; `P(A,B)` = fraction mentioning both.
Positive PMI → similarity/hyperedge weight.

**(b) Concept embeddings — SVD (linear algebra).** Co-occurrence matrix `M`
(concepts×concepts, PMI-filled) factored `M ≈ U Σ Vᵀ`; top-k columns of `U` =
dense concept vectors (LSA-style; denoises the graph, no neural net required).

**(c) Retrieval = random walk = linear system.** Column-stochastic transition `P`,
query seed distribution `q`, restart `c`:
```
r = c·q + (1−c)·P·r        ⇒    r = c·(I − (1−c)P)⁻¹ q
```
- The inverse is the **Neumann (geometric) series** Σ ((1−c)P)ᵏ — term k = k-hop walks
  (calculus / series convergence, valid since spectral radius (1−c)ρ(P) < 1).
- **Perron–Frobenius theorem** guarantees a unique positive stationary solution ⇒
  retrieval is deterministic and convergent.
- Solved by **power iteration** (no inverse): `r ← c·q + (1−c)·P·r` until ‖Δ‖<ε.

**(d) Scoring — softmax with temperature (probability).**
```
sᵢ = λ₁·simᵢ + λ₂·rᵢ + λ₃·depthᵢ
pᵢ = exp(sᵢ/T) / Σⱼ exp(sⱼ/T)
```
Temperature `T`: low = sharp/precise ("explain simply"), high = broad/exploratory
("explain deeply").

**(e) Lattice "meet" (order theory).** `meet(A,B)` = greatest common prerequisite =
the shared foundation to teach before combining two ideas. Unique to this engine.

### 4.3 Worked example (the test target)
Concepts: ①energy-flow ②Poynting ③drift-velocity. Similarity weights
E–P=0.9, E–D=0.5, P–D=0.3. Restart c=0.5, seed q=[0.5,0.5,0].
Power iteration converges to ≈ **[0.449, 0.419, 0.133]**.
Key result: **drift-velocity (~0.13) surfaces though it was never seeded** — the walk
found the relevant *contrasting* concept. That is multi-hop retrieval; plain vector
RAG would miss it. Reproduced in `tests/test_hyperlattice.py`.

### 4.4 Query pipeline
```
query → ① embed → similarity to concept SVD vectors → seed q   (recall)
      → ② PPR power-iteration on Hyper-Lattice → relevance r    (multi-hop precision)
      → ③ lattice/topological ordering of survivors            (pedagogy)
      → ④ softmax(λ·[sim,r,depth]/T), pick within token budget
      → ⑤ gather each concept's hyperedges (text+timestamp+frame)
      → LLM writes the answer FROM hyperedges, each claim cited
```
Graph-first, vector-as-fallback: graph gives precision/synthesis, vectors give recall.

## 5. How features map onto the engine
| Feature | Mechanism |
|---|---|
| pic + timestamp | stored on the hyperedge (evidence unit) |
| combine 4–5 videos on one idea | a concept node aggregates hyperedges across videos |
| how one video treats an idea | filter that node's hyperedges by `video_id` |
| Markdown/PDF/flashcards/jsonl/csv | exporters over the same `ContentUnit`s |
| the "idea map" | **is** the Concept Hyper-Lattice |
| MCP "adapter" | server exposing get_concept/walk/meet/get_context |
| simple vs deep | softmax temperature `T` |

## 6. Storage & infra
Local-first: `ContentUnit`s as JSON; lattice as serialized NetworkX; vectors in
FAISS or sqlite-vec. Graph DB only if it outgrows memory. No services required for v1.

## 7. Key risks
- **Concept resolution** (merging aliases across videos) is the make-or-break step —
  see `ai/decisions.md`. A wrong merge poisons the graph.
- Frame captioning needs a vision model (Groq is text-only) → defer / use OCR.
