"""Loads content/math/algebra_stories.yaml (Whales math situations), from whichever content folder
is active (tests swap ws.content.CONTENT_DIR), cached per folder."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml


@lru_cache(maxsize=None)
def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    for group in ("linear", "area"):
        ids = [f["id"] for f in data[group]]
        if len(set(ids)) != len(ids):
            raise ValueError(f"{path}: {group} ids must be unique")
    return data


def algebra_stories() -> dict:
    from .. import content
    return _load(content.CONTENT_DIR / "math" / "algebra_stories.yaml")


def frame(group: str, frame_id: str) -> dict:
    for f in algebra_stories()[group]:
        if f["id"] == frame_id:
            return f
    raise KeyError(f"no {group} story {frame_id!r} in content/math/algebra_stories.yaml")
