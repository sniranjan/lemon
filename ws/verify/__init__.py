"""`ws verify` (CLAUDE.md §8): content checks on every sheet, group checks per level and
variant, then layout checks on the rendered pages.

Exposure rules ("every word seen ≥ 3 times", strip windows) are checked on the level plan,
which always covers the whole level, so verify passes on a partly generated level. Each
generated sheet is also rebuilt from its seed and compared, which catches sheets made by
older code or content ("stale").
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import yaml

from .. import registry
from ..content import licenses, picture_path, vocab_by_word
from ..models import Issue, Level, Sheet
from ..pictures import check_svg_source
from ..plan import LevelPlan
from ..syllabus import ROOT, level_rank, load_level, resolve_page, sheet_id

TIP_MAX = 220


def _err(sheet_id: str, msg: str) -> Issue:
    return Issue(sheet_id=sheet_id, severity="error", message=msg)


def _warn(sheet_id: str, msg: str) -> Issue:
    return Issue(sheet_id=sheet_id, severity="warning", message=msg)


# --- banned words ------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _banned_pattern() -> re.Pattern:
    # policy, not test content: always the repo's own list
    data = yaml.safe_load((ROOT / "content" / "banned.yaml").read_text())
    words = sorted({w.lower() for group in data.values() for w in group}, key=len, reverse=True)
    return re.compile(r"(?<!\w)(" + "|".join(re.escape(w) for w in words) + r")(?!\w)", re.IGNORECASE)


def banned_words(text: str) -> list[str]:
    return sorted({m.group(1).lower() for m in _banned_pattern().finditer(text)})


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


# --- pictures ----------------------------------------------------------------------------

def _picture_slugs(sheet: Sheet) -> set[str]:
    return {item[k] for item in sheet.items for k in ("picture", "target") if k in item} \
        | {p for item in sheet.items for p in item.get("pictures", [])}


@lru_cache(maxsize=None)
def check_picture(slug: str) -> tuple[str, ...]:
    path = picture_path(slug)
    if not path.exists():
        return (f"picture {slug}.svg does not exist",)
    problems = []
    try:
        root = ET.parse(path).getroot()
        if not root.tag.endswith("svg"):
            problems.append(f"{slug}.svg is not an SVG document")
    except ET.ParseError as e:
        problems.append(f"{slug}.svg is not valid XML: {e}")
    problems += [f"{slug}.svg: {p}" for p in check_svg_source(path)]
    if slug not in licenses():
        problems.append(f"{slug}.svg has no LICENSES.yaml entry")
    return tuple(problems)


# --- per-sheet checks --------------------------------------------------------------------

def _words_on(sheet: Sheet) -> set[str]:
    return {i["word"] for i in sheet.items if "word" in i and isinstance(i["word"], str)} \
        | set(sheet.new_words) | set(sheet.review_words)


def check_sheet(sheet: Sheet, level: Level, plan: LevelPlan) -> list[Issue]:
    from ..generate import build_sheet

    sid = sheet.id
    issues: list[Issue] = []
    try:
        section = level.section_for_page(sheet.page_number)
    except KeyError as e:
        return [_err(sid, e.args[0])]
    if sheet.section != section.code:
        issues.append(_err(sid, f"page {sheet.page_number} belongs to section {section.code}, not {sheet.section}"))
    expected_id = sheet_id(level, section, sheet.page_number, sheet.variant)
    if sid != expected_id:
        issues.append(_err(sid, f"ID should be {expected_id}"))
    spec = resolve_page(level, sheet.page_number)
    if sheet.part != spec.part:
        issues.append(_err(sid, f"page {sheet.page_number} is in part {spec.part}, sheet says {sheet.part}"))
    forced = sheet.sheet_type != spec.sheet_type
    if forced:
        issues.append(_warn(sid, f"sheet type {sheet.sheet_type} was forced; the syllabus uses "
                                 f"{spec.sheet_type} on page {sheet.page_number}"))
    rules = spec.rules

    # rebuild from the recorded seed: catches nondeterminism and content/code changes
    try:
        again = build_sheet(level, sheet.page_number, plan, sheet.variant, sheet.seed, sheet.sheet_type)
        fields = ("items", "title", "parent_tip", "new_words", "review_words", "answer_key")
        changed = [f for f in fields if getattr(again, f) != getattr(sheet, f)]
        if changed:
            issues.append(_err(sid, f"stale: content or code changed since it was generated ({', '.join(changed)}); "
                                    f"regenerate it"))
    except KeyError as e:
        issues.append(_err(sid, f"stale: can't rebuild it any more ({e.args[0]}); regenerate it"))

    # parent tip
    if not sheet.parent_tip.strip():
        issues.append(_err(sid, "parent tip is missing"))
    elif len(sheet.parent_tip) > TIP_MAX:
        issues.append(_err(sid, f"parent tip is {len(sheet.parent_tip)} characters (max {TIP_MAX})"))

    # pictures
    for slug in sorted(_picture_slugs(sheet)):
        issues += [_err(sid, p) for p in check_picture(slug)]

    # vocabulary (English)
    if sheet.subject == "english":
        bank = vocab_by_word()
        for w in sorted(_words_on(sheet)):
            entry = bank.get(w)
            if entry is None:
                issues.append(_err(sid, f"word {w!r} is not in the word bank"))
            elif level_rank(entry.level) > level_rank(level.level):
                issues.append(_err(sid, f"word {w!r} belongs to level {entry.level}, after {level.level}"))
            if "max_word_length" in rules and len(w) > rules["max_word_length"]:
                issues.append(_err(sid, f"word {w!r} is longer than {rules['max_word_length']} letters"))
        allowed_new = rules.get("new_words_per_sheet", 0)
        if len(sheet.new_words) > allowed_new:
            issues.append(_err(sid, f"{len(sheet.new_words)} new words; this section allows {allowed_new}"))
        if not forced and sheet.page_number in plan.pages:
            entry = plan.pages[sheet.page_number]
            if sheet.new_words != entry.new_words or sorted(sheet.review_words) != sorted(entry.review_words):
                issues.append(_err(sid, "words don't match the level plan; regenerate it"))

    # banned content anywhere in the sheet's text
    text = " ".join([sheet.title, sheet.parent_tip, *_strings(sheet.items)])
    for w in banned_words(text):
        issues.append(_err(sid, f"banned word {w!r}"))

    # the sheet type's own checks
    try:
        issues += registry.get(sheet.sheet_type).verify(sheet)
    except Exception as e:   # a crashing check is a failed check, not a crashed verify
        issues.append(_err(sid, f"{sheet.sheet_type} check crashed: {e!r}"))
    return issues


# --- color words ---------------------------------------------------------------------------

def color_word_pages(sheets: Iterable[Sheet]) -> list[int]:
    """Pages showing a word that only makes sense in color (`needs_color` in the word bank)."""
    bank = vocab_by_word()
    return sorted({s.page_number for s in sheets
                   if s.subject == "english" and any(bank[w].needs_color for w in _words_on(s) if w in bank)})


def _ranges(pages: list[int]) -> str:
    """[31, 32, 34, 35, 36] -> '31–32, 34–36'"""
    out, start = [], None
    for i, p in enumerate(pages):
        if start is None:
            start = p
        if i + 1 == len(pages) or pages[i + 1] != p + 1:
            out.append(f"{start}" if start == p else f"{start}–{p}")
            start = None
    return ", ".join(out)


# --- group checks (one level, one variant) -----------------------------------------------

def _word_sections(level: Level) -> list:
    return [s for s in level.sections if s.rules.get("new_words_per_sheet", 0)
            or any(p.rules.get("new_words_per_sheet", 0) for p in s.parts)]


def check_group(level: Level, variant: int, sheets: list[Sheet], plan: LevelPlan) -> list[Issue]:
    tag = f"{level.level}" + (f" v{variant}" if variant > 1 else "")
    issues: list[Issue] = []

    # no duplicate sheets
    seen: dict[tuple, str] = {}
    for s in sheets:
        key = (s.sheet_type, repr(s.items))
        if key in seen:
            issues.append(_err(s.id, f"same items as {seen[key]}"))
        else:
            seen[key] = s.id

    # words are new exactly once
    new_on: dict[str, str] = {}
    for s in sheets:
        for w in s.new_words:
            if w in new_on:
                issues.append(_err(s.id, f"{w!r} was already new on {new_on[w]}"))
            new_on[w] = s.id

    if level.subject != "english" or not _word_sections(level):
        return issues

    color_pages = color_word_pages(sheets)
    if color_pages:
        issues.append(_warn(tag, f"pages {_ranges(color_pages)} use color words; print them in color if you can"))

    # earlier levels this one reviews (6A-A reviews 7A): warn while their word bank is short
    bank = vocab_by_word()
    from_levels = sorted({lv for p in range(1, level.pages + 1)
                          for lv in resolve_page(level, p).rules.get("review_from_levels", [])})
    for lv in from_levels:
        target = load_level(level.subject, lv).vocab_target or 0
        have = sum(1 for e in bank.values() if e.level == lv)
        if have < target:
            issues.append(_warn(tag, f"this level reviews {lv} words: the word bank has {have} of {lv}'s {target}; "
                                     f"sheets that review or reuse them will change as words are added"))

    # exposure rules, on the plan (always the whole level)
    word_pages = [p for p in range(1, level.pages + 1)
                  if resolve_page(level, p).rules.get("new_words_per_sheet", 0)]
    missing = [p for p in word_pages if p not in plan.pages]
    if missing:
        later = [s for s in sheets if s.page_number > missing[0] and s.page_number not in word_pages]
        issues.append(_warn(tag, f"the word bank covers {len(word_pages) - len(missing)} of {len(word_pages)} "
                                 f"new-word pages (next: page {missing[0]}); exposure rules are checked once it's "
                                 f"complete" + (f", and the {len(later)} review/story sheets already generated "
                                                f"will change as words are added" if later else "")))
    else:
        min_seen = level.rules.get("min_exposures_per_word", 0)
        new_here = {w for p in plan.pages.values() for w in p.new_words}
        counts = Counter(w for p in plan.pages.values() for w in p.new_words + p.review_words)
        for w, n in sorted(counts.items()):
            if w in new_here and n < min_seen:
                issues.append(_err(tag, f"plan shows {w!r} only {n} times (needs {min_seen})"))
    # strip words must be 3–10 sheets old
    intro = {w: page for page, p in plan.pages.items() for w in p.new_words}
    for page, p in sorted(plan.pages.items()):
        strip = resolve_page(level, page).rules.get("say_it_again")
        if strip and p.new_words:
            lo, hi = strip["sheets_back"]
            for w in p.review_words:
                if not lo <= page - intro.get(w, -999) <= hi:
                    issues.append(_err(tag, f"page {page}: strip word {w!r} is not {lo}–{hi} sheets old"))

    # once every page of the level is generated, count real exposures too
    if {s.page_number for s in sheets} >= set(range(1, level.pages + 1)):
        counts = Counter(w for s in sheets for w in set(s.new_words) | set(s.review_words))
        for w in intro:
            if counts[w] < level.rules.get("min_exposures_per_word", 0):
                issues.append(_err(tag, f"{w!r} appears on only {counts[w]} sheets"))
    return issues


# --- entry point -------------------------------------------------------------------------

def verify_sheets(sheets: list[Sheet]) -> list[Issue]:
    from ..generate import build_plan

    issues: list[Issue] = []
    groups: dict[tuple, list[Sheet]] = defaultdict(list)
    for s in sheets:
        groups[(s.subject, s.level, s.variant)].append(s)
    for (subject, lvl_code, variant), group in sorted(groups.items()):
        level = load_level(subject, lvl_code)
        plan = build_plan(level, variant)
        group.sort(key=lambda s: s.page_number)
        for s in group:
            issues += check_sheet(s, level, plan)
        issues += check_group(level, variant, group, plan)
    return issues


def verify_layout(sheets: list[Sheet]) -> tuple[list[Issue], dict]:
    """Render each sheet to PNG with the layout checks; returns issues and {(subject, level): [png]}."""
    from ..generate import sheet_dir
    from ..render import min_child_px, render_pngs

    issues: list[Issue] = []
    pngs: dict[tuple, list[Path]] = defaultdict(list)
    by_level: dict[tuple, list[Sheet]] = defaultdict(list)
    for s in sheets:
        by_level[(s.subject, s.level)].append(s)
    for (subject, lvl), group in sorted(by_level.items()):
        paths = [sheet_dir(s) / f"{s.id}.html" for s in group]
        for s, path in zip(group, paths):
            if not path.exists():
                issues.append(_err(s.id, f"HTML file missing: {path}"))
        present = [(s, p) for s, p in zip(group, paths) if p.exists()]
        results = render_pngs([p for _, p in present], min_child=min_child_px(lvl, subject))
        for (s, _), r in zip(present, results):
            issues += [_err(s.id, f"layout: {p}") for p in r.problems]
            pngs[(subject, lvl)].append(r.png)
    return issues, pngs
