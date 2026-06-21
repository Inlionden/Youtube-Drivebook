# YouTube Drivebook

Scrape YouTube channels (and later websites, PDFs, podcasts) into a structured
knowledge base, and answer questions over it like a focused, source-cited
**Perplexity** — powered by a custom RAG engine, **LatticeRAG**.

## What it does

```
YouTube playlist / channel
        │  Stage 1: Extract   (transcript, chapters, comments, key frames)
        ▼
   RawSegments
        │  Stage 2: Transform (Groq → ContentUnits, then Concepts)
        ▼
  ContentUnits ──► Concept Hyper-Lattice (the "idea map")
        │                        │
        │ Stage 3: Load          │ Stage 4: Serve
        ▼                        ▼
  Markdown book / PDF      LatticeRAG answer engine
  fine-tune .jsonl         exposed over MCP
  RAG chunks / CSV         (get_concept, walk, meet, get_context)
```

The middle schema (`ContentUnit`) is the source of truth — every output is a
different *view* on it, so adding a new source = writing one `Ingester`, and
adding a new output = writing one `Exporter`.

## The engine: LatticeRAG

A custom RAG combining **vector recall + graph random-walk (Personalized
PageRank) + a prerequisite lattice**, running on the **Concept Hyper-Lattice**.
Full design and the math (PMI weighting, SVD embeddings, PPR / Perron–Frobenius,
softmax temperature) are in [`ai/architecture.md`](ai/architecture.md).

## Status
Scaffolding + core graph engine. The Concept Hyper-Lattice PPR walk is
implemented and tested (`tests/test_hyperlattice.py`); ingesters, transform,
exporters and the MCP server are stubbed with their interfaces defined.

## Quickstart (planned CLI)
```bash
pip install -e .
cp .env.example .env          # add GROQ_API_KEY
drivebook ingest "https://youtube.com/playlist?list=..."
drivebook export markdown --out book.md
drivebook serve-mcp           # expose the knowledge base to an agent
```

## Layout
See [`ai/architecture.md`](ai/architecture.md). Project docs live in `ai/`,
code in `src/ytdrivebook/`, tests in `tests/`.
