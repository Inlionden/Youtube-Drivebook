"""Stage 1 — pluggable ingesters. New source = new Ingester, nothing else changes."""

from ytdrivebook.extract.base import Ingester

__all__ = ["Ingester"]
