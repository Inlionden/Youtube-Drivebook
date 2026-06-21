"""YouTube ingester — Phase 1.

STUB. Implementation plan:
  * expand playlist/channel URLs via yt-dlp
  * transcript + timestamps via youtube-transcript-api
  * metadata / chapters / description / top comments via yt-dlp
  * sampled key frames via opencv scene-change detection
  * cache raw pulls under settings.raw_dir to avoid re-scraping
Segment boundaries: creator chapters when present, else fixed transcript windows
(LLM topic boundaries are refined in Stage 2).
"""

from __future__ import annotations

from collections.abc import Iterable

from ytdrivebook.extract.base import Ingester
from ytdrivebook.schema import RawSegment


class YouTubeIngester(Ingester):
    def supports(self, ref: str) -> bool:
        return "youtube.com" in ref or "youtu.be" in ref

    def extract(self, ref: str) -> Iterable[RawSegment]:
        raise NotImplementedError("Phase 1: implement YouTube extraction")
