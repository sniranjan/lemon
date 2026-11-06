"""Build sheets from the syllabus + plan, write their HTML and record them in the manifest."""

from __future__ import annotations

import json
import random
from pathlib import Path

from . import registry
from .content import grammar, passages, phonics, phrases, sounds, tips, vocab
from .models import Level, Sheet
from .phonics import plan_phonics
from .plan import LevelPlan, plan_letters, plan_new_words, plan_phrases, plan_review, plan_spelling
from .reading import plan_reading
from .render import write_html
from .syllabus import ROOT, page_seed, resolve_page, sheet_id

OUT_DIR = ROOT / "out"
MANIFEST = OUT_DIR / "manifest.jsonl"


def build_plan(level: Level, variant: int = 1) -> LevelPlan:
    if level.subject == "english" and level.rules.get("planner") == "letters":
        return plan_letters(level, vocab("english"), sounds("english"), variant)
    if level.subject == "english":
        bank = vocab("english")
        plan = plan_review(level, plan_new_words(level, bank, variant), bank)
        plan = plan_phonics(level, bank, plan, phonics("english"))
        plan = plan_phrases(level, bank, plan, phrases("english"))
        plan = plan_reading(level, bank, plan, grammar("english"), passages("english"))   # Cubs Reading (2A)
        return plan_spelling(level, bank, plan, phonics("english"))   # Puppies Reading (3A)
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


MAX_ATTEMPTS = 100


def _same_content(a: Sheet, b: Sheet) -> bool:
    return a.sheet_type == b.sheet_type and a.items == b.items


def build_section(level: Level, section_code: str, up_to: int, plan: LevelPlan,
                  variant: int = 1) -> dict[int, Sheet]:
    """Build the section's pages in order up to `up_to`, with no repeated sheet.

    A page whose items match an earlier page of the section is rebuilt with the next seed
    in a fixed sequence. Every page depends only on the syllabus, the plan and the pages
    before it in the section, never on which pages were generated before, so any page range
    gives the same sheets as a full run.
    """
    section = level.section(section_code)
    built: dict[int, Sheet] = {}
    for page in range(section.pages[0], up_to + 1):
        if page < up_to and level.subject == "english" and page not in plan.pages:
            continue   # the word bank can't plan this page yet (6A-C part 5 before part 10)
        for attempt in range(MAX_ATTEMPTS):
            seed = page_seed(level.subject, level.level, section_code, page, variant, attempt)
            sheet = build_sheet(level, page, plan, variant, seed)
            if not any(_same_content(sheet, other) for other in built.values()):
                break
        # if every attempt repeats, keep the last one: verify reports the duplicate
        built[page] = sheet
    return built


def sheet_dir(sheet: Sheet) -> Path:
    return OUT_DIR / sheet.subject / sheet.level / sheet.section


def generate_pages(level: Level, pages: list[int], variant: int = 1,
                   seed: int | None = None, sheet_type: str | None = None,
                   skip_waiting: bool = False) -> list[tuple[Sheet, Path]]:
    """Write the requested pages. A forced `seed` or `sheet_type` (previews, one-offs) builds
    each page on its own; otherwise pages come from `build_section`, free of repeats.
    `skip_waiting` leaves out pages the plan says still wait for new words (`--all`)."""
    plan = build_plan(level, variant)
    if skip_waiting:
        pages = [p for p in pages if p not in plan.waiting]
    sheets: dict[int, Sheet] = {}
    if seed is not None or sheet_type:
        for page in pages:
            sheets[page] = build_sheet(level, page, plan, variant, seed, sheet_type)
    else:
        by_section: dict[str, list[int]] = {}
        for page in pages:
            by_section.setdefault(level.section_for_page(page).code, []).append(page)
        for code, wanted in by_section.items():
            built = build_section(level, code, max(wanted), plan, variant)
            sheets.update({p: built[p] for p in wanted})
    out = []
    for page in pages:
        sheet = sheets[page]
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


def select_pages(level: Level, *, section: str | None = None, part: int | None = None,
                 count: int | None = None, pages: list[int] | None = None, all_pages: bool = False,
                 variant: int = 1) -> list[int]:
    """Turn the CLI's page selection into page numbers.

    `--count N` takes the next N pages of the section (or part) that the manifest doesn't
    have yet for this variant, and errors clearly once the range is complete.
    """
    if all_pages:
        return list(range(1, level.pages + 1))
    if pages:
        return pages
    if not section:
        raise ValueError("choose --section (with --count or --part), --pages or --all")
    sec = level.section(section)
    lo, hi = sec.pages
    label = f"{level.level}-{section}"
    if part is not None:
        p = next((p for p in sec.parts if p.part == part), None)
        if p is None:
            raise ValueError(f"{label} has no part {part}")
        lo, hi = p.pages
        label += f" part {part}"
    candidates = list(range(lo, hi + 1))
    if count is None:
        return candidates
    done = {s.page_number for s in load_manifest(level.subject, level.level)
            if s.section == section and s.variant == variant}
    todo = [p for p in candidates if p not in done]
    if not todo:
        raise ValueError(f"{label} is complete: pages {lo}–{hi}")
    return todo[:count]
