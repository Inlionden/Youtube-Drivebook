"""Phase 3: exporters render ContentUnits into output files (end-to-end with
the Phase-2 structurer, all offline)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixtures import canned_llm_response, sample_segment  # noqa: E402

from ytdrivebook.load.exporters import (  # noqa: E402
    CsvRecordsExporter,
    JsonlFinetuneExporter,
    MarkdownBookExporter,
)
from ytdrivebook.transform.llm_client import FakeLLMClient  # noqa: E402
from ytdrivebook.transform.structurer import Structurer  # noqa: E402


def _units():
    structurer = Structurer(FakeLLMClient(canned_llm_response()))
    unit = structurer.structure(
        sample_segment(), unit_id="bHIhgxav9LY#0002", chapter="The Lightbulb Thought Experiment"
    )
    return [unit]


def test_markdown_book_has_chapter_image_and_citation():
    out = Path(tempfile.mkdtemp()) / "book.md"
    MarkdownBookExporter().export(_units(), out)
    text = out.read_text(encoding="utf-8")
    assert "## The Lightbulb Thought Experiment" in text  # chapter heading
    assert "![" in text and ".png" in text                # embedded key frame
    assert "youtube.com/watch?v=bHIhgxav9LY&t=95s" in text # timestamped citation
    assert "- Energy travels in the fields" in text        # key point


def test_jsonl_one_line_per_qa_pair():
    out = Path(tempfile.mkdtemp()) / "data.jsonl"
    JsonlFinetuneExporter().export(_units(), out)
    lines = [l for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["messages"][0]["role"] == "user"


def test_csv_has_header_and_row():
    out = Path(tempfile.mkdtemp()) / "records.csv"
    CsvRecordsExporter().export(_units(), out)
    rows = out.read_text(encoding="utf-8").splitlines()
    assert rows[0].startswith("id,channel,chapter")
    assert "Veritasium" in rows[1]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
