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
def phrases(subject: str = "english") -> dict:
    """Phrase and sentence frames for 6A-B/C (see the file's header)."""
    path = CONTENT_DIR / "phrases" / f"{subject}.yaml"
    return yaml.safe_load(path.read_text()) if path.exists() else {}


@lru_cache(maxsize=None)
def phonics(subject: str = "english") -> dict:
    """Hand-checked letter teams and rhyme groups (Kittens Reading) and spelling patterns, endings, syllables, sight words (Puppies Reading)."""
    path = CONTENT_DIR / "phonics" / f"{subject}.yaml"
    return yaml.safe_load(path.read_text()) if path.exists() else {}


@lru_cache(maxsize=None)
def grammar(subject: str = "english") -> dict:
    """Word kinds, fill-in sentences and puzzle words for Cubs Reading (content/grammar/<subject>.yaml)."""
    path = CONTENT_DIR / "grammar" / f"{subject}.yaml"
    return yaml.safe_load(path.read_text()) if path.exists() else {}


@lru_cache(maxsize=None)
def passages(subject: str = "english") -> dict:
    """Read-aloud passages with questions (content/passages/<subject>.yaml)."""
    path = CONTENT_DIR / "passages" / f"{subject}.yaml"
    return yaml.safe_load(path.read_text()) if path.exists() else {"passages": []}


@lru_cache(maxsize=None)
def sounds(subject: str = "english") -> dict:
    """Letter words and onset + rime splits for letters-and-sounds levels (5A)."""
    path = CONTENT_DIR / "sounds" / f"{subject}.yaml"
    return yaml.safe_load(path.read_text()) if path.exists() else {}


@lru_cache(maxsize=None)
def math_objects() -> tuple[dict, ...]:
    return tuple(yaml.safe_load((CONTENT_DIR / "math" / "objects.yaml").read_text()))


@lru_cache(maxsize=None)
def math_stories() -> dict:
    """Story-problem frames for Cubs math (content/math/stories.yaml)."""
    return yaml.safe_load((CONTENT_DIR / "math" / "stories.yaml").read_text())


@lru_cache(maxsize=None)
def line_targets() -> tuple[str, ...]:
    return tuple(yaml.safe_load((CONTENT_DIR / "pencil" / "line_targets.yaml").read_text()))


@lru_cache(maxsize=None)
def line_stories() -> tuple[tuple[str, str], ...]:
    """(start picture, end picture) pairs that make a little story: the bee goes to the flower."""
    data = yaml.safe_load((CONTENT_DIR / "pencil" / "line_stories.yaml").read_text())
    return tuple((d["from"], d["to"]) for d in data)


@lru_cache(maxsize=None)
def level_passages(level: str, section: str) -> tuple[dict, ...]:
    """Reading passages for one section of a passage level: content/passages/<level>/<section>.yaml."""
    path = CONTENT_DIR / "passages" / level / f"{section}.yaml"
    return tuple(yaml.safe_load(path.read_text()) or []) if path.exists() else ()


@lru_cache(maxsize=None)
def wordparts(level: str) -> dict:
    """Prefixes, suffixes and compound words to build: content/wordparts/<level>.yaml."""
    path = CONTENT_DIR / "wordparts" / f"{level}.yaml"
    return yaml.safe_load(path.read_text()) if path.exists() else {}


@lru_cache(maxsize=None)
def figurative(level: str) -> tuple[dict, ...]:
    """Hand-checked similes, metaphors, idioms, adages and proverbs: content/figurative/<level>.yaml."""
    path = CONTENT_DIR / "figurative" / f"{level}.yaml"
    return tuple(yaml.safe_load(path.read_text()) or []) if path.exists() else ()


@lru_cache(maxsize=None)
def story_problems() -> tuple[dict, ...]:
    """Story problem frames for math word problems (see the file's header)."""
    frames = tuple(yaml.safe_load((CONTENT_DIR / "math" / "story_problems.yaml").read_text()))
    ids = [f["id"] for f in frames]
    if len(set(ids)) != len(ids):
        raise ValueError("story_problems.yaml: frame ids must be unique")
    return frames


@lru_cache(maxsize=None)
def math_frames(name: str) -> tuple[dict, ...]:
    """Frames and contexts for Pandas math: content/math/<name>.yaml (ratios, rational_stories)."""
    frames = tuple(yaml.safe_load((CONTENT_DIR / "math" / f"{name}.yaml").read_text()))
    ids = [f["id"] for f in frames]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{name}.yaml: ids must be unique")
    return frames


def clear_caches() -> None:
    for f in (vocab, tips, licenses, stories, phrases, phonics, sounds, math_objects, math_stories, line_targets,
              line_stories, story_problems, grammar, passages, level_passages, wordparts, math_frames,
              figurative):
        f.cache_clear()
