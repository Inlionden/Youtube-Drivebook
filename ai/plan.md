# Development Plan — Vertical Slice Architecture

Build thin end-to-end slices, smallest risk first. Each phase: Goal, Deliverables,
Tasks, Dependencies, Acceptance Criteria.

---

## Phase 0 — Foundations  ✅ (this scaffold)
- **Goal:** Project skeleton, docs, schemas, and the graph engine's core.
- **Deliverables:** `ai/` docs, `CLAUDE.md`, package layout, Pydantic schemas,
  Concept Hyper-Lattice + PPR walk **with a passing test**.
- **Tasks:** scaffold packages; define `Source/RawSegment/ContentUnit/Concept/Hyperedge`;
  implement `ConceptHyperLattice.personalized_pagerank`; unit-test it.
- **Dependencies:** none.
- **Acceptance:** `pytest tests/test_hyperlattice.py` passes; PPR reproduces the
  worked numeric example (multi-hop surfaces an unseeded concept).

## Phase 1 — YouTube Extract (single video)  ◐ core done
- **Goal:** Real transcript + metadata + key frames into `RawSegment`s.
- **Deliverables:** `extract/youtube.py` implementing `Ingester`; `drivebook ingest` CLI.
- **Done:** transcript+timestamps (youtube-transcript-api v1.x), title/channel via
  oEmbed, windowed segmentation, CLI that saves RawSegments to JSON. Verified live
  on a real video (16 tests pass; offline via injected fetchers).
- **Deferred (needs yt-dlp / video download):** creator chapters, playlist/channel
  expansion, key-frame sampling (opencv), comments.
- **Dependencies:** Phase 0 schemas.
- **Acceptance:** one video → list of `RawSegment`s with timestamps. ✅ (frames pending)

## Phase 2 — Transform to ContentUnits  ✅
- **Goal:** Groq turns segments into validated `ContentUnit`s.
- **Deliverables:** `transform/llm_client.py` (Groq, JSON mode), `transform/structurer.py`.
- **Tasks:** prompt + schema-constrained output; segment→unit mapping; retry/validate.
- **Dependencies:** Phase 1, schemas.
- **Acceptance:** segments → `ContentUnit`s passing Pydantic validation; offline test
  with a stubbed LLM client.

## Phase 3 — First Exporter (Markdown book)  ✅
- **Goal:** Visible artifact end to end for one video.
- **Deliverables:** `load/exporters.py:MarkdownBookExporter`.
- **Tasks:** render chapters, key points, embedded frames, source citations.
- **Dependencies:** Phase 2.
- **Acceptance:** `drivebook export markdown` produces a readable `.md` with images.

## Phase 4 — Concept extraction + resolution → the Lattice
- **Goal:** Build the idea map across videos.
- **Deliverables:** `transform/concepts.py`, graph build in `index/hyperlattice.py`.
- **Tasks:** per-unit concept extraction; alias/embedding-based merge; PMI edge weights;
  hyperedges from segments; SVD concept embeddings.
- **Dependencies:** Phase 2.
- **Acceptance:** playlist → single graph where a shared concept aggregates units from
  multiple videos; dedup verified on a fixture.

## Phase 5 — LatticeRAG retrieval + remaining exporters
- **Goal:** Cited answers + all output views.
- **Deliverables:** retrieval pipeline; `jsonl_finetune`, `rag_chunks`, `csv`,
  `flashcards`, `pdf` exporters; cross-video + single-video synthesis.
- **Dependencies:** Phases 2–4.
- **Acceptance:** `drivebook ask "..."` returns an answer citing video+timestamp;
  exporters emit valid files.

## Phase 6 — MCP serve
- **Goal:** Expose the base as an agent tool surface.
- **Deliverables:** `serve/mcp_server.py` with the documented tools.
- **Dependencies:** Phase 5.
- **Acceptance:** an MCP client can call `get_context`/`answer` and receive cited context.

## Phase 7 — Second source (website ingester)
- **Goal:** Prove extensibility.
- **Deliverables:** `extract/web.py` implementing `Ingester` only.
- **Acceptance:** a webpage flows through transform→graph→serve with **zero** changes
  to Stages 2–4.

---

### Tracking
Keep `ai/decisions.md` updated per phase. Mark phases done here as they land.
