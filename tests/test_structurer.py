"""Phase 2: RawSegment -> ContentUnit, tested offline with a fake LLM."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixtures import canned_llm_response, sample_segment  # noqa: E402

from ytdrivebook.schema import ContentUnit  # noqa: E402
from ytdrivebook.transform.llm_client import FakeLLMClient  # noqa: E402
from ytdrivebook.transform.structurer import Structurer  # noqa: E402


def _make_unit() -> ContentUnit:
    structurer = Structurer(FakeLLMClient(canned_llm_response()))
    return structurer.structure(sample_segment(), unit_id="bHIhgxav9LY#0002")


def test_builds_valid_content_unit():
    unit = _make_unit()
    assert isinstance(unit, ContentUnit)
    assert unit.id == "bHIhgxav9LY#0002"
    assert unit.topic.startswith("How long")
    assert len(unit.qa_pairs) == 1


def test_provenance_and_media_carry_over():
    unit = _make_unit()
    # source provenance comes from the segment, not the LLM
    assert unit.source.video_id == "bHIhgxav9LY"
    assert unit.source.channel == "Veritasium"
    # media (key frame) is preserved from the raw segment
    assert unit.media and unit.media[0].timestamp == 118.0


def test_retry_recovers_from_bad_first_response():
    """First call returns junk; the strict retry returns a valid object."""

    class FlakyLLM:
        def __init__(self) -> None:
            self.calls = 0

        def complete_json(self, system, user, schema=None):
            self.calls += 1
            return {} if self.calls == 1 else canned_llm_response()

    structurer = Structurer(FlakyLLM())
    unit = structurer.structure(sample_segment(), unit_id="x#1")
    assert unit.topic.startswith("How long")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
