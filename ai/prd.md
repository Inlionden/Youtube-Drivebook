# Product Requirements Document — YouTube Drivebook

## 1. Project Overview
YouTube Drivebook ingests YouTube content (a video, playlist, or whole channel),
structures it into a canonical schema with an LLM, and builds a **concept-centric
knowledge base**. Over that base it offers (a) exportable study/training artifacts
and (b) a **source-cited answer engine** (LatticeRAG) usable directly or via MCP.

It is designed source-agnostic: YouTube is the first ingester; websites, PDFs,
and podcasts plug in later without touching transform, storage, or serving.

## 2. Goals
- G1. Turn a playlist/channel into a clean, chaptered, image-rich knowledge base.
- G2. Answer natural-language questions over that base with citations to the exact
  video + timestamp (Perplexity-style, but scoped to chosen sources).
- G3. **Synthesize across videos** — combine 4–5 videos on one idea into a single
  explanation, and conversely show how *one* video treats an idea.
- G4. Emit multiple outputs from one ingest: Markdown book, PDF, fine-tune `.jsonl`,
  RAG chunks, flashcards, CSV.
- G5. Expose the base as an MCP tool surface so any agent can pull aligned context.

## 3. User Personas
- **Self-learner** — wants a readable book + flashcards from a course playlist.
- **Builder / researcher** — wants a cited Q&A engine and RAG chunks over a channel.
- **ML practitioner** — wants `.jsonl` instruction data distilled from videos.
- **Agent / LLM (non-human)** — calls the MCP tools to fetch grounded context.

## 4. User Stories
- As a learner, I paste a playlist URL and get a Markdown/PDF "book" with chapters,
  key points, and embedded slide frames.
- As a builder, I ask "how does energy reach a bulb?" and get an answer citing the
  exact videos and timestamps it came from.
- As a learner, I ask to "combine all videos on the Poynting vector" and get one
  consolidated, cited explanation.
- As a learner, I ask "how does *this* video explain X" and get only that video's take.
- As an agent, I call `get_context(query)` over MCP and receive a token-budgeted,
  cited context block.
- As a practitioner, I export `dataset.jsonl` of instruction/response pairs.

## 5. Functional Requirements
- FR1. Expand a playlist/channel URL into a list of videos (yt-dlp).
- FR2. Extract per video: transcript+timestamps, chapters, description+links,
  top comments, sampled key frames (scene-change detection).
- FR3. Segment each video into `ContentUnit`s (default: creator chapters, else
  LLM-detected topic boundaries).
- FR4. For each unit, Groq fills: topic, summary, content, key_points, qa_pairs,
  tags, media refs.
- FR5. Extract `Concept`s per unit and **resolve/merge** them into a global graph
  (dedup aliases across videos).
- FR6. Build the Concept Hyper-Lattice: concept nodes, prerequisite/similarity edges,
  and hyperedges (one per segment, carrying timestamp + frame evidence).
- FR7. LatticeRAG retrieval: vector recall → PPR walk → lattice ordering → cited answer.
- FR8. Exporters: markdown_book, pdf, jsonl_finetune, rag_chunks, flashcards, csv.
- FR9. Cross-video synthesis and single-video views, selectable by the user.
- FR10. MCP server exposing search_concepts, get_concept, walk, meet, get_context, answer.

## 6. Non-Functional Requirements
- NFR1. Incremental: adding videos updates the graph without a full rebuild.
- NFR2. Offline-testable: cached transcript fixtures so tests need no network/LLM.
- NFR3. Local-first infra (NetworkX + FAISS/sqlite) before any external DB.
- NFR4. Deterministic core retrieval (PPR converges — Perron–Frobenius).
- NFR5. Cost-aware: one LLM pass per segment; exporters never call the LLM again.
- NFR6. Typed (Pydantic v2) and validated at every stage boundary.

## 7. Data Design
Core entities (see `ai/architecture.md` for full schema):
`Source`, `MediaRef`, `RawSegment` (Stage 1) → `ContentUnit`, `QAPair` (Stage 2) →
`Concept`, `Relation`, `Hyperedge` (graph). Storage: JSON for units, NetworkX graph
(serialized) for the lattice, FAISS/sqlite-vec for vectors.

## 8. API / Interface Requirements
- CLI (`drivebook`): `ingest`, `build-graph`, `export`, `ask`, `serve-mcp`.
- MCP tools: `search_concepts`, `get_concept`, `related_concepts`, `meet`,
  `get_context`, `answer`.

## 9. Security Requirements
- Secrets only via `.env` / environment; never committed.
- Respect source ToS and rate limits; cache to avoid re-scraping.
- No PII collection beyond public video metadata/comments.

## 10. Future Features
Speaker diarization, OCR on slide/code frames, code-only extractor, quiz/flashcard
generation, channel-wide RAG Q&A, learned concept-resolution, graph DB backend.

## Open Questions
- Segmentation granularity when a video has no creator chapters (topic-window size)?
- Comment mining for FAQ: include in v1 or defer? (flagged as differentiated)
- Frame captioning needs a vision model — Groq is text-only; OCR via pytesseract?
