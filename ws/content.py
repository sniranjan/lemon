"""Load the content banks: vocabulary, parent tips, picture licences."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from .models import VocabEntry
from .syllabus import ROOT

CONTENT_DIR = ROOT / "content"
PICTURES_DIR = ROOT / "assets" / "pictures"


@lru_cache(maxsize=None)
def vocab(subject: str = "english") -> tuple[VocabEntry, ...]:
    entries = yaml.safe_load((CONTENT_DIR / "vocab" / f"{subject}.yaml").read_text()) or []
    words = tuple(VocabEntry.model_validate(e) for e in entries)
    seen: set[str] = set()
    for w in words:
        if w.word in seen:
            raise ValueError(f"word {w.word!r} appears twice in the {subject} word bank")
        seen.add(w.word)
    return words


def vocab_by_word(subject: str = "english") -> dict[str, VocabEntry]:
    return {w.word: w for w in vocab(subject)}


@lru_cache(maxsize=None)
def tips(subject: str) -> dict[str, list[str]]:
    path = CONTENT_DIR / "tips" / f"{subject}.yaml"
    return yaml.safe_load(path.read_text()) if path.exists() else {}


@lru_cache(maxsize=None)
def licenses() -> dict[str, dict]:
    return yaml.safe_load((PICTURES_DIR / "LICENSES.yaml").read_text()) or {}


def picture_path(slug: str) -> Path:
    return PICTURES_DIR / f"{slug}.svg"


@lru_cache(maxsize=None)
def stories(subject: str = "english") -> dict:
    return yaml.safe_load((CONTENT_DIR / "stories" / f"{subject}.yaml").read_text())


@lru_cache(maxsize=None)
def math_objects() -> tuple[dict, ...]:
    return tuple(yaml.safe_load((CONTENT_DIR / "math" / "objects.yaml").read_text()))


@lru_cache(maxsize=None)
def line_targets() -> tuple[str, ...]:
    return tuple(yaml.safe_load((CONTENT_DIR / "pencil" / "line_targets.yaml").read_text()))


@lru_cache(maxsize=None)
def line_stories() -> tuple[tuple[str, str], ...]:
    """(start picture, end picture) pairs that make a little story: the bee goes to the flower."""
    data = yaml.safe_load((CONTENT_DIR / "pencil" / "line_stories.yaml").read_text())
    return tuple((d["from"], d["to"]) for d in data)


def clear_caches() -> None:
    for f in (vocab, tips, licenses, stories, math_objects, line_targets, line_stories):
        f.cache_clear()
