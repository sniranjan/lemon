"""Public names: everything a buyer sees (sheets, booklets, previews, file names). CLAUDE.md §15.

Internal codes (7A, EN-7A-A-001) stay in the syllabus, manifest and work files; this module turns a
level into the names printed on paper and used for files people download.
"""

from __future__ import annotations

from .models import Level

# Subject names as parents see them (the site uses the same words).
SUBJECT_LABEL = {"english": "Reading", "math": "Math", "pencil": "Pencil skills"}
_SUBJECT_SLUG = {"english": "reading", "math": "math", "pencil": "pencil"}


def public_tag(level: Level, variant: int = 1) -> str:
    """File-name stem for one strand of a public level: `chicks-reading`, `chicks-math`, `chicks-pencil`."""
    tag = f"{level.slug}-{_SUBJECT_SLUG[level.subject]}"
    return f"{tag}-v{variant}" if variant > 1 else tag


def public_label(level: Level) -> str:
    """`Chicks · Reading`."""
    return f"{level.public_name} · {SUBJECT_LABEL[level.subject]}"
