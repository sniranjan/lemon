"""Load syllabus YAML and resolve pages to sections, parts, sheet types and rules."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .models import SUBJECT_PREFIX, Level, PageSpec, Section

ROOT = Path(__file__).resolve().parent.parent
SYLLABUS_DIR = ROOT / "syllabus"


# Levels in teaching order (earliest first). "≤ current level" means "not later in this list".
LEVEL_ORDER = ["7A", "6A", "5A", "4A", "3A", "2A"]


def level_rank(level: str) -> int:
    try:
        return LEVEL_ORDER.index(level)
    except ValueError:
        raise ValueError(f"unknown level {level!r}; add it to LEVEL_ORDER") from None


def level_path(subject: str, level: str) -> Path:
    return SYLLABUS_DIR / subject / f"{level}.yaml"


@lru_cache(maxsize=None)
def load_level(subject: str, level: str) -> Level:
    path = level_path(subject, level)
    if not path.exists():
        raise FileNotFoundError(f"no syllabus for {subject} {level} (expected {path})")
    data = yaml.safe_load(path.read_text())
    lvl = Level.model_validate(data)
    if (lvl.subject, lvl.level) != (subject, level):
        raise ValueError(f"{path} declares {lvl.subject} {lvl.level}, expected {subject} {level}")
    return lvl


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
