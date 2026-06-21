# Architecture Decision Record

Newest first. Each: Context → Decision → Status → Consequences.

## ADR-0007 — Concept resolution strategy (cheapest-first cascade)
- **Context:** "Poynting vector" / "energy flux" / "S vector" across videos must
  become ONE node; wrong merges poison the graph. This is the project's core risk.
- **Decision:** cascade — (a) LLM proposes a canonical name + aliases per unit;
  (b) embed names, merge above a cosine threshold; (c) LLM adjudicates borderline
  pairs only. Keep a `merged_from` audit trail to allow un-merging.
- **Status:** Accepted (impl in Phase 4).
- **Consequences:** mostly cheap (embeddings); LLM only on borderline cases.

## ADR-0006 — Serve the knowledge base over MCP
- **Context:** Want any agent to fetch aligned, cited context easily ("adapter").
- **Decision:** expose an MCP server (search_concepts/get_concept/related/meet/
  get_context/answer). Concept node = the stable handle agents address.
- **Status:** Accepted (Phase 6).
- **Consequences:** agents avoid embedding plumbing; the server is the retrieval adapter.

## ADR-0005 — LatticeRAG: vector + PPR + prerequisite lattice
- **Context:** Plain vector RAG can't synthesize across videos or order pedagogically.
- **Decision:** custom engine = vector recall + Personalized PageRank walk + lattice
  ordering, on the Concept Hyper-Lattice. Graph-first, vector-as-fallback.
- **Status:** Accepted; PPR core implemented + tested in Phase 0.
- **Consequences:** more build than vector RAG; deterministic (Perron–Frobenius);
  the differentiator no YouTube summarizer has.

## ADR-0004 — New data structure: Concept Hyper-Lattice
- **Context:** A 2-min clip teaches several concepts at once; normal 2-node edges
  can't represent that, and teaching order matters.
- **Decision:** hypergraph (hyperedge = taught segment, carries timestamp/frame) +
  prerequisite partial order (lattice) + weighted similarity edges.
- **Status:** Accepted.
- **Consequences:** richer queries (meet, multi-hop, evidence-on-edge); more code.

## ADR-0003 — Groq for Stage 2 transform
- **Context:** Need fast, cheap structured output; user chose Groq.
- **Decision:** Groq (OpenAI-compatible, JSON mode) behind a thin swappable
  `llm_client`. Groq is text-only ⇒ no frame captioning via Groq.
- **Status:** Accepted.
- **Consequences:** fast/cheap; frame OCR/captioning deferred or via pytesseract.

## ADR-0002 — ContentUnit is the single intermediate schema
- **Context:** Want many outputs + many sources without re-architecting.
- **Decision:** one canonical Pydantic `ContentUnit`; ingesters and exporters are
  the only source/output-specific code.
- **Status:** Accepted.
- **Consequences:** new source = 1 ingester; new output = 1 exporter; Stages 2–4 stable.

## ADR-0001 — Local-first storage
- **Context:** v1 shouldn't need infra.
- **Decision:** JSON units + NetworkX graph + FAISS/sqlite-vec; graph DB only if needed.
- **Status:** Accepted.
- **Consequences:** zero-setup dev; revisit at scale.
