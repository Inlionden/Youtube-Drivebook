"""Phase 1: YouTube ingester — URL parsing and windowed segmentation, offline.

Uses injected fake fetchers so no network is touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from ytdrivebook.extract.youtube import YouTubeIngester, parse_video_id  # noqa: E402


def test_parse_video_id_forms():
    assert parse_video_id("https://www.youtube.com/watch?v=bHIhgxav9LY") == "bHIhgxav9LY"
    assert parse_video_id("https://youtu.be/bHIhgxav9LY?t=10") == "bHIhgxav9LY"
    assert parse_video_id("https://youtube.com/shorts/bHIhgxav9LY") == "bHIhgxav9LY"
    assert parse_video_id("bHIhgxav9LY") == "bHIhgxav9LY"
    with pytest.raises(ValueError):
        parse_video_id("not a url")


def _fake_transcript(_video_id):
    # 5 snippets, 60s apart -> with a 90s window this yields 2 segments
    return [{"text": f"line {i}", "start": i * 60.0, "duration": 5.0} for i in range(5)]


def _fake_meta(_video_id):
    return {"title": "Test Video", "channel": "TestChannel"}


def _ingester():
    return YouTubeIngester(
        window_seconds=90.0, transcript_fetcher=_fake_transcript, meta_fetcher=_fake_meta
    )


def test_segmentation_windows():
    segments = list(_ingester().extract("bHIhgxav9LY"))
    # starts at 0,60,120,180,240; 90s windows -> [0,60],[120,180],[240]
    assert len(segments) == 3
    assert segments[0].start == 0.0
    assert "line 0" in segments[0].text and "line 1" in segments[0].text


def test_segment_provenance():
    seg = next(iter(_ingester().extract("bHIhgxav9LY")))
    assert seg.source.video_id == "bHIhgxav9LY"
    assert seg.source.channel == "TestChannel"
    assert seg.source.url.endswith("&t=0s")


def test_playlist_rejected():
    with pytest.raises(NotImplementedError):
        list(_ingester().extract("https://youtube.com/watch?v=bHIhgxav9LY&list=PLxyz"))


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        try:
            fn()
            print(f"ok  {fn.__name__}")
        except Exception as e:
            print(f"FAIL {fn.__name__}: {e}")
            raise
    print(f"\n{len(fns)} passed")
