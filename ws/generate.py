"""Build sheets from the syllabus + plan, write their HTML and record them in the manifest."""

from __future__ import annotations

import json
import random
from pathlib import Path

from . import registry
from .content import tips, vocab
from .models import Level, Sheet
from .plan import LevelPlan, plan_new_words
from .render import write_html
from .syllabus import ROOT, page_seed, resolve_page, sheet_id

OUT_DIR = ROOT / "out"
MANIFEST = OUT_DIR / "manifest.jsonl"


def build_plan(level: Level, variant: int = 1) -> LevelPlan:
    if level.subject == "english":
        return plan_new_words(level, vocab("english"), variant)
    return LevelPlan(subject=level.subject, level=level.level, variant=variant)


def build_sheet(level: Level, page: int, plan: LevelPlan, variant: int = 1,
                seed: int | None = None, sheet_type: str | None = None) -> Sheet:
    spec = resolve_page(level, page)
    if sheet_type:
        spec = spec.model_copy(update={"sheet_type": sheet_type})
    section = level.section(spec.section)
    seed = page_seed(level.subject, level.level, spec.section, page, variant) if seed is None else seed
    ctx = registry.GenContext(spec=spec, rng=random.Random(seed), plan=plan,
                              banks={"tips": tips(level.subject)})
    content = registry.get(spec.sheet_type).generate(ctx)
    return Sheet(
        id=sheet_id(level, section, page, variant),
        subject=level.subject, level=level.level, section=spec.section, part=spec.part,
        sheet_type=spec.sheet_type, page_number=page, variant=variant, seed=seed,
        title=content.title, parent_tip=content.parent_tip, items=content.items,
        answer_key=content.answer_key, new_words=content.new_words, review_words=content.review_words,
    )


def sheet_dir(sheet: Sheet) -> Path:
    return OUT_DIR / sheet.subject / sheet.level / sheet.section


def generate_pages(level: Level, pages: list[int], variant: int = 1,
                   seed: int | None = None, sheet_type: str | None = None) -> list[tuple[Sheet, Path]]:
    plan = build_plan(level, variant)
    out = []
    for page in pages:
        sheet = build_sheet(level, page, plan, variant, seed, sheet_type)
        path = sheet_dir(sheet) / f"{sheet.id}.html"
        write_html(sheet, level, path)
        out.append((sheet, path))
    _record(s for s, _ in out)
    return out


def _record(sheets) -> None:
    """Append to the manifest; the latest line for an ID wins."""
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("a") as f:
        for s in sheets:
            f.write(json.dumps(s.model_dump(mode="json"), sort_keys=True) + "\n")


def load_manifest(subject: str | None = None, level: str | None = None) -> list[Sheet]:
    if not MANIFEST.exists():
        return []
    latest: dict[str, Sheet] = {}
    for line in MANIFEST.read_text().splitlines():
        if line.strip():
            s = Sheet.model_validate_json(line)
            latest[s.id] = s
    sheets = [s for s in latest.values()
              if (subject is None or s.subject == subject) and (level is None or s.level == level)]
    return sorted(sheets, key=lambda s: (s.subject, s.level, s.variant, s.page_number))
