"""YouTube ingester — Phase 1.

This first slice uses only lightweight, already-installed pieces:
  * transcript + timestamps via youtube-transcript-api (v1.x instance API)
  * title / channel via YouTube's oEmbed endpoint (plain urllib, no extra dep)
  * segmentation into fixed time windows

Deferred to a follow-up (needs yt-dlp / a video download):
  * creator chapter boundaries, playlist/channel expansion, key-frame sampling

The transcript and metadata fetchers are injectable so the segmentation logic
is unit-testable offline (no network).
"""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable

from ytdrivebook.extract.base import Ingester
from ytdrivebook.schema import RawSegment, Source, SourceType

logger = logging.getLogger(__name__)

# text, start, duration  (matches youtube_transcript_api .to_raw_data())
Snippet = dict
TranscriptFetcher = Callable[[str], list[Snippet]]
MetaFetcher = Callable[[str], dict]

_ID_PATTERNS = (
    re.compile(r"[?&]v=([A-Za-z0-9_-]{11})"),
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})"),
    re.compile(r"/(?:embed|shorts)/([A-Za-z0-9_-]{11})"),
)


def parse_video_id(ref: str) -> str:
    """Pull the 11-char video id out of any common YouTube URL form."""
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", ref):
        return ref
    for pat in _ID_PATTERNS:
        m = pat.search(ref)
        if m:
            return m.group(1)
    raise ValueError(f"could not find a video id in {ref!r}")


def _default_transcript_fetcher(video_id: str, languages: tuple[str, ...] = ("en",)) -> list[Snippet]:
    from youtube_transcript_api import YouTubeTranscriptApi

    fetched = YouTubeTranscriptApi().fetch(video_id, languages=list(languages))
    return fetched.to_raw_data()


def _default_meta_fetcher(video_id: str) -> dict:
    params = urllib.parse.urlencode(
        {"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"}
    )
    try:
        with urllib.request.urlopen(f"https://www.youtube.com/oembed?{params}", timeout=10) as r:
            data = json.load(r)
        return {"title": data.get("title"), "channel": data.get("author_name")}
    except Exception as exc:  # metadata is best-effort; transcript still works
        logger.warning("oembed metadata fetch failed for %s: %s", video_id, exc)
        return {"title": None, "channel": None}


class YouTubeIngester(Ingester):
    def __init__(
        self,
        window_seconds: float = 90.0,
        transcript_fetcher: TranscriptFetcher | None = None,
        meta_fetcher: MetaFetcher | None = None,
    ) -> None:
        self.window_seconds = window_seconds
        self._fetch_transcript = transcript_fetcher or _default_transcript_fetcher
        self._fetch_meta = meta_fetcher or _default_meta_fetcher

    def supports(self, ref: str) -> bool:
        return "youtube.com" in ref or "youtu.be" in ref or bool(
            re.fullmatch(r"[A-Za-z0-9_-]{11}", ref)
        )

    def extract(self, ref: str) -> Iterable[RawSegment]:
        if "list=" in ref:
            raise NotImplementedError(
                "playlist/channel expansion needs yt-dlp (follow-up); pass a single video"
            )
        video_id = parse_video_id(ref)
        meta = self._fetch_meta(video_id)
        snippets = self._fetch_transcript(video_id)
        if not snippets:
            raise ValueError(f"no transcript available for {video_id}")
        yield from self._segment(video_id, meta, snippets)

    def _segment(self, video_id: str, meta: dict, snippets: list[Snippet]) -> Iterable[RawSegment]:
        """Group snippets into ~window_seconds chunks, each a RawSegment."""
        bucket: list[Snippet] = []
        bucket_start = float(snippets[0]["start"])

        def flush(items: list[Snippet]) -> RawSegment:
            start = float(items[0]["start"])
            last = items[-1]
            end = float(last["start"]) + float(last.get("duration", 0.0))
            text = " ".join(s["text"].strip() for s in items if s["text"].strip())
            return RawSegment(
                source=Source(
                    type=SourceType.YOUTUBE,
                    url=f"https://youtube.com/watch?v={video_id}&t={int(start)}s",
                    video_id=video_id,
                    channel=meta.get("channel"),
                    title=meta.get("title"),
                    start=start,
                    end=end,
                ),
                text=text,
                start=start,
                end=end,
            )

        for snip in snippets:
            start = float(snip["start"])
            if bucket and start - bucket_start >= self.window_seconds:
                yield flush(bucket)
                bucket = []
                bucket_start = start
            bucket.append(snip)
        if bucket:
            yield flush(bucket)
