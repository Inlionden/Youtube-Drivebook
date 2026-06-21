"""Concrete exporters — all views over the same ContentUnits.

`MarkdownBookExporter` is the Phase-3 reference implementation (real). The rest
are Phase-5 stubs with their shapes documented.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from ytdrivebook.load.base import Exporter
from ytdrivebook.schema import ContentUnit


def _timestamp_url(unit: ContentUnit) -> str:
    src = unit.source
    if src.video_id and src.start is not None:
        return f"https://youtube.com/watch?v={src.video_id}&t={int(src.start)}s"
    return src.url


class MarkdownBookExporter(Exporter):
    """A chaptered 'book' with key points and embedded key-frame images."""

    name = "markdown"

    def export(self, units: list[ContentUnit], out_path: Path) -> Path:
        lines: list[str] = []
        title = next((u.source.title for u in units if u.source.title), "Knowledge Book")
        lines.append(f"# {title}\n")
        for unit in units:
            heading = unit.chapter or unit.topic
            lines.append(f"## {heading}\n")
            lines.append(f"> {unit.summary}\n")
            lines.append(unit.content + "\n")
            for m in unit.media:
                cap = m.caption or "frame"
                lines.append(f"![{cap}]({m.path})\n")
            if unit.key_points:
                lines.append("**Key points**\n")
                lines.extend(f"- {kp}" for kp in unit.key_points)
                lines.append("")
            src = unit.source
            label = f"{src.channel or 'source'} — {src.title or ''}".strip(" —")
            lines.append(f"*Source: [{label}]({_timestamp_url(unit)})*\n")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path


class JsonlFinetuneExporter(Exporter):
    """One line per QA pair: {"messages": [user, assistant]}. Phase 5."""

    name = "jsonl"

    def export(self, units: list[ContentUnit], out_path: Path) -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fh:
            for unit in units:
                for qa in unit.qa_pairs:
                    row = {
                        "messages": [
                            {"role": "user", "content": qa.q},
                            {"role": "assistant", "content": qa.a},
                        ]
                    }
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return out_path


class RagChunksExporter(Exporter):
    """content split into chunks + retrieval metadata. Phase 5 (chunking TODO)."""

    name = "rag"

    def export(self, units: list[ContentUnit], out_path: Path) -> Path:
        chunks = [
            {
                "chunk_id": f"{u.id}#c0",
                "text": u.content,
                "metadata": {
                    "video_id": u.source.video_id,
                    "channel": u.source.channel,
                    "chapter": u.chapter,
                    "topic": u.topic,
                    "tags": u.tags,
                    "url": _timestamp_url(u),
                },
            }
            for u in units
        ]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), "utf-8")
        return out_path


class CsvRecordsExporter(Exporter):
    """Flat one-row-per-unit table. Phase 5."""

    name = "csv"

    def export(self, units: list[ContentUnit], out_path: Path) -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["id", "channel", "chapter", "topic", "summary", "tags", "url"])
            for u in units:
                w.writerow(
                    [
                        u.id,
                        u.source.channel or "",
                        u.chapter or "",
                        u.topic,
                        u.summary,
                        ";".join(u.tags),
                        _timestamp_url(u),
                    ]
                )
        return out_path


EXPORTERS: dict[str, type[Exporter]] = {
    e.name: e
    for e in (
        MarkdownBookExporter,
        JsonlFinetuneExporter,
        RagChunksExporter,
        CsvRecordsExporter,
    )
}
