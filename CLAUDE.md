# Project Context

**YouTube Drivebook** — a data pipeline that scrapes YouTube channels (and later
websites, PDFs, podcasts) and turns them into a queryable knowledge base for a
**Perplexity-style answer engine**, plus exportable views (Markdown book, PDF,
fine-tune `.jsonl`, RAG chunks, flashcards, CSV).

The retrieval engine is a **custom RAG called LatticeRAG**, running on a new data
structure, the **Concept Hyper-Lattice**. See `ai/architecture.md` for the full design.

## Tech Stack
- Python 3.10+
- Pydantic v2 (schemas / validation — the keystone)
- Groq API (Stage 2 LLM structuring; OpenAI-compatible, JSON mode)
- youtube-transcript-api, yt-dlp (Stage 1 extraction)
- opencv-python (key-frame / scene-change sampling)
- NetworkX + NumPy/SciPy (the Concept Hyper-Lattice + PPR walk)
- FAISS or sqlite-vec (vector recall layer)
- Typer + Rich (CLI)
- `mcp` (serve the knowledge base as an MCP tool surface)
- pytest, ruff (test + lint)

## Architecture
Three-stage ETL with a graph layer on top, then a serve layer:
1. **Extract** — pluggable `Ingester`s (YouTube first) → `RawSegment`s.
2. **Transform** — Groq turns segments into `ContentUnit`s, then extracts +
   resolves `Concept`s into the global graph.
3. **Load** — exporters read `ContentUnit`s (Markdown/PDF/jsonl/RAG/CSV).
4. **Serve** — LatticeRAG + MCP server over the Concept Hyper-Lattice.

Patterns: feature-based / vertical slices, Clean Architecture, service layer,
strategy pattern for ingesters and exporters.

---

# Coding Standards

Always:
1. Think through multiple solutions.
2. Choose the simplest maintainable solution.
3. Explain reasoning.

Code requirements: SOLID, DRY, type hints everywhere, error handling, logging.

Never:
- Hardcode secrets (use `.env` / `config.py`).
- Duplicate code.
- Create unnecessary files.
- Break the `Ingester` / `Exporter` / schema contracts — they are the whole
  point of the extensible design.

---

# Before Writing Code
1. Read related files.
2. Understand the architecture (`ai/architecture.md`).
3. Explain the plan.
4. Implement.
5. Verify (run tests).

---

# Feature Development Process
1. Review PRD (`ai/prd.md`).
2. Review the development plan (`ai/plan.md`).
3. Implement the slice (extract → transform → load/serve).
4. Add tests.
5. Update documentation in `ai/docs/<feature>.md`.
6. Record any non-obvious choice in `ai/decisions.md`.

---

# Documentation Rules
After each feature, create/update `ai/docs/<feature-name>.md` with:
- Purpose
- Architecture
- Data Flow
- API / CLI surface
- Schema/graph changes
- Future Improvements

---

# Session Bootstrap
Start a session by reading, in order:
`ai/prd.md`, `ai/plan.md`, `ai/architecture.md`, `ai/decisions.md`,
then determine the next unfinished phase before writing code.
