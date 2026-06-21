"""Environment-driven settings. No external deps so it imports anywhere."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _get(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    data_dir: Path = Path("data")
    frame_diff_threshold: float = 0.45
    ppr_restart: float = 0.5

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            groq_api_key=_get("GROQ_API_KEY", ""),
            llm_model=_get("DRIVEBOOK_LLM_MODEL", "llama-3.3-70b-versatile"),
            data_dir=Path(_get("DRIVEBOOK_DATA_DIR", "data")),
            frame_diff_threshold=float(_get("DRIVEBOOK_FRAME_DIFF_THRESHOLD", "0.45")),
            ppr_restart=float(_get("DRIVEBOOK_PPR_RESTART", "0.5")),
        )

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def intermediate_dir(self) -> Path:
        return self.data_dir / "intermediate"

    @property
    def output_dir(self) -> Path:
        return self.data_dir / "output"


settings = Settings.from_env()
