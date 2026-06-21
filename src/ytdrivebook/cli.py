"""Typer CLI entrypoint: `drivebook ...`.

Commands are wired as phases land. `info` works today and prints the configured
state so the install can be verified.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from ytdrivebook import __version__
from ytdrivebook.config import settings

app = typer.Typer(help="YouTube Drivebook — scrape, structure, and answer with LatticeRAG.")


@app.command()
def info() -> None:
    """Show version and resolved configuration."""
    typer.echo(f"ytdrivebook {__version__}")
    typer.echo(f"  model:       {settings.llm_model}")
    typer.echo(f"  data dir:    {settings.data_dir}")
    typer.echo(f"  groq key:    {'set' if settings.groq_api_key else 'MISSING'}")
    typer.echo(f"  ppr restart: {settings.ppr_restart}")


@app.command()
def ingest(ref: str, window: float = 90.0, out: str = "") -> None:
    """Extract raw segments from a YouTube video (transcript + metadata)."""
    from ytdrivebook.extract.youtube import YouTubeIngester

    segments = list(YouTubeIngester(window_seconds=window).extract(ref))
    title = segments[0].source.title or ref
    typer.echo(f"extracted {len(segments)} segments from: {title}")
    if out:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps([s.model_dump() for s in segments], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        typer.echo(f"saved -> {path}")


@app.command()
def export(fmt: str, out: str = "out.md") -> None:
    """Export ContentUnits to a format (markdown/jsonl/rag/csv). (Phase 3/5)"""
    raise typer.Exit(typer.echo(f"export {fmt} -> {out}: implemented in Phase 3/5"))


@app.command()
def ask(query: str) -> None:
    """Answer a question over the knowledge base with citations. (Phase 5)"""
    raise typer.Exit(typer.echo("ask: implemented in Phase 5"))


@app.command("serve-mcp")
def serve_mcp() -> None:
    """Serve the knowledge base over MCP. (Phase 6)"""
    raise typer.Exit(typer.echo("serve-mcp: implemented in Phase 6"))


if __name__ == "__main__":
    app()
