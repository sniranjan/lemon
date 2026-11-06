"""Public names: everything a buyer sees (sheets, booklets, previews, file names). CLAUDE.md §15.

Internal codes (7A, EN-7A-A-001) stay in the syllabus, manifest and work files; this module turns a
level into the names printed on paper and used for files people download.
"""

from __future__ import annotations

from .models import Level

# Subject names as parents see them (the site uses the same words).
SUBJECT_LABEL = {"english": "Reading", "math": "Numbers", "pencil": "Pencil skills"}
_SUBJECT_SLUG = {"english": "reading", "math": "numbers", "pencil": "pencil"}


def public_tag(level: Level, variant: int = 1) -> str:
    """File-name stem for a level: `chicks-reading`, `ducklings-numbers`; pencil levels are just `tadpoles`."""
    tag = level.slug if level.subject == "pencil" else f"{level.slug}-{_SUBJECT_SLUG[level.subject]}"
    return f"{tag}-v{variant}" if variant > 1 else tag


def public_label(level: Level) -> str:
    """`Chicks · Reading`."""
    return f"{level.public_name} · {SUBJECT_LABEL[level.subject]}"
