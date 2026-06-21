"""Shared offline fixtures: a sample RawSegment and a canned LLM response."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ytdrivebook.schema import MediaRef, RawSegment, Source, SourceType  # noqa: E402


def sample_segment() -> RawSegment:
    return RawSegment(
        source=Source(
            type=SourceType.YOUTUBE,
            url="https://youtube.com/watch?v=bHIhgxav9LY&t=95s",
            video_id="bHIhgxav9LY",
            channel="Veritasium",
            title="The Big Misconception About Electricity",
            start=95.0,
            end=240.0,
        ),
        text="Imagine a battery connected to a switch and two very long wires...",
        start=95.0,
        end=240.0,
        media=[
            MediaRef(
                path="data/output/frames/bHIhgxav9LY_0001m58s.png",
                timestamp=118.0,
                caption="Diagram of the battery, switch, and the two long wires",
            )
        ],
    )


def canned_llm_response() -> dict:
    return {
        "topic": "How long until a bulb lights when the wires are very long",
        "summary": "The bulb lights after about 1/c seconds, set by the small gap "
        "between the wires, because energy flows through the fields around them.",
        "content": "A battery and switch connect to a bulb via two long wires...",
        "key_points": [
            "Energy travels in the fields around wires, not through the electrons",
            "Timing is set by the wire gap, not the wire length",
        ],
        "qa_pairs": [
            {
                "q": "What determines how quickly the bulb lights up?",
                "a": "The small distance between the wires divided by the speed of light.",
            }
        ],
        "tags": ["physics", "electromagnetism", "poynting-vector"],
    }
