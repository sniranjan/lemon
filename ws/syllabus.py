"""Load syllabus YAML and resolve pages to sections, parts, sheet types and rules."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .models import SUBJECT_PREFIX, LadderLevel, Level, PageSpec, Section

ROOT = Path(__file__).resolve().parent.parent
SYLLABUS_DIR = ROOT / "syllabus"


# Levels in teaching order (earliest first). "≤ current level" means "not later in this list".
LEVEL_ORDER = ["7A", "6A", "5A", "4A", "3A", "2A", "R3"]
LEVEL_ORDER += ["R5"]   # Otters Reading (kept on its own line: other R levels are added beside it)


def level_rank(level: str) -> int:
    try:
        return LEVEL_ORDER.index(level)
    except ValueError:
        raise ValueError(f"unknown level {level!r}; add it to LEVEL_ORDER") from None


def level_path(subject: str, level: str) -> Path:
    return SYLLABUS_DIR / subject / f"{level}.yaml"


# Strand order inside a public level (covers, previews).
STRAND_ORDER = ["english", "math", "pencil"]
_PUBLIC_KEYS = ("public_name", "public_title", "slug")


@lru_cache(maxsize=None)
def load_ladder() -> tuple[LadderLevel, ...]:
    """The public level ladder (CLAUDE.md §15). Each internal level belongs to exactly one public level."""
    rungs = tuple(LadderLevel.model_validate(d) for d in yaml.safe_load((SYLLABUS_DIR / "ladder.yaml").read_text()))
    seen_slugs: set[str] = set()
    seen_strands: dict[tuple[str, str], str] = {}
    for r in rungs:
        if r.slug in seen_slugs:
            raise ValueError(f"ladder: duplicate slug {r.slug!r}")
        seen_slugs.add(r.slug)
        for subject, code in r.strands.items():
            if (subject, code) in seen_strands:
                raise ValueError(f"ladder: {subject} {code} is in both {seen_strands[(subject, code)]} and {r.slug}")
            seen_strands[(subject, code)] = r.slug
    return rungs


def ladder_level(slug: str) -> LadderLevel:
    for r in load_ladder():
        if r.slug == slug:
            return r
    raise KeyError(f"no public level {slug!r} in syllabus/ladder.yaml")


def rung_for(subject: str, level: str) -> LadderLevel:
    for r in load_ladder():
        if r.strands.get(subject) == level:
            return r
    raise ValueError(f"{subject} {level} is not in syllabus/ladder.yaml; give it a public level first")


@lru_cache(maxsize=None)
def load_level(subject: str, level: str) -> Level:
    path = level_path(subject, level)
    if not path.exists():
        raise FileNotFoundError(f"no syllabus for {subject} {level} (expected {path})")
    data = yaml.safe_load(path.read_text())
    if set(_PUBLIC_KEYS) & set(data):
        raise ValueError(f"{path}: public names belong in syllabus/ladder.yaml, not the level file")
    lvl = Level.model_validate(data)
    if (lvl.subject, lvl.level) != (subject, level):
        raise ValueError(f"{path} declares {lvl.subject} {lvl.level}, expected {subject} {level}")
    rung = rung_for(subject, level)
    return lvl.model_copy(update={"public_name": rung.public_name, "public_title": rung.public_title,
                                  "slug": rung.slug})


def all_levels() -> list[Level]:
    return [load_level(p.parent.name, p.stem) for p in sorted(SYLLABUS_DIR.glob("*/*.yaml"))]


def merge_rules(*layers: dict[str, Any]) -> dict[str, Any]:
    """Merge rule dicts left to right; later layers win. Nested dicts merge key by key."""
    out: dict[str, Any] = {}
    for layer in layers:
        for key, value in layer.items():
            if isinstance(value, dict) and isinstance(out.get(key), dict):
                out[key] = merge_rules(out[key], value)
            else:
                out[key] = value
    return out


def resolve_page(level: Level, page: int) -> PageSpec:
    section = level.section_for_page(page)
    part = section.part_for_page(page)
    types = (part.sheet_types if part and part.sheet_types else None) or section.sheet_types
    # Pages cycle through the type list, counted from the start of the part (or section).
    first, last = part.pages if part else section.pages
    sheet_type = types[(page - first) % len(types)]
    rules = merge_rules(level.rules, section.rules, part.rules if part else {})
    return PageSpec(
        subject=level.subject,
        level=level.level,
        section=section.code,
        part=part.part if part else None,
        page=page,
        sheet_type=sheet_type,
        rules=rules,
        progress=(page - first) / (last - first) if last > first else 0.0,
    )


def sheet_id(level: Level, section: Section, page: int, variant: int = 1) -> str:
    """`EN-7A-B-001` numbers pages within the section; pencil drops the subject prefix."""
    n = page - section.pages[0] + 1
    prefix = SUBJECT_PREFIX[level.subject]
    parts = [prefix, level.level, section.code, f"{n:03d}"] if prefix else [level.level, section.code, f"{n:03d}"]
    sid = "-".join(parts)
    return f"{sid}-v{variant}" if variant > 1 else sid


def page_seed(subject: str, level: str, section: str, page: int, variant: int = 1, attempt: int = 0) -> int:
    """`attempt` > 0 gives the follow-up seeds used when a page would repeat an earlier one."""
    key = f"{subject}|{level}|{section}|{page}|{variant}" + (f"|{attempt}" if attempt else "")
    digest = hashlib.sha256(key.encode()).digest()
    return int.from_bytes(digest[:8], "big")


def parse_pages(spec: str) -> list[int]:
    """'1-50' or '7' or '1-5,9' → sorted page numbers."""
    pages: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if "-" in chunk:
            lo, hi = (int(x) for x in chunk.split("-", 1))
            if hi < lo:
                raise ValueError(f"bad page range {chunk!r}")
            pages.update(range(lo, hi + 1))
        elif chunk:
            pages.add(int(chunk))
    return sorted(pages)
