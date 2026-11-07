"""The "two grades ahead" check (CLAUDE.md §8, §15): section `standards:` tags against `content_grade`.

Each public level (syllabus/ladder.yaml) has a `content_grade` ("Pre-K", "K", "1–2", "3" …). The check:

- **Reach**: the level's highest tagged standard (any strand, any section or part) is at least the
  content grade (the upper bound of a range like "1–2").
- **Floor**: no section is tagged *only* with standards more than one grade below the content grade (the
  lower bound of a range). On-ramp and review sections say so with `on_ramp: true` / `review: true`.
- **Tagged**: every section of a checked level has at least one standard.
- **Readability**: every page whose sheet type scores passages with Flesch-Kincaid must have an explicit
  `fk_grade: [lo, hi]` rule (the scorers' built-in defaults belong to one level only) with
  content grade − 1 ≤ lo ≤ content grade and content grade + 1 ≤ hi ≤ content grade + 2. Passage pages
  with no FK scorer at all (Cubs Read Aloud) get a warning.

Exempt: levels whose content grade is Pre-K (no Common Core codes exist), and pencil strands.
A section's grade is its highest tag (section + parts): a section that mixes a grade-2 on-ramp code with
grade-3 work is a grade-3 section.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .models import Issue, Level, Section
from .syllabus import level_path, load_ladder, load_level, resolve_page

PRE_K = -1

# Sheet types whose verify scores every passage's Flesch-Kincaid grade against `fk_grade`
# (ws/passages.py, ws/longreads.py, ws/spreads.py).
FK_SHEET_TYPES = frozenset({
    "passage_questions", "full_sentence_answer", "word_builder",                     # Foxes
    "long_read_page", "look_back_questions", "word_detective", "big_idea_summary",   # Owls
    "read_then_answer", "clue_words", "figurative_language", "paragraph_summary",    # Otters
    "passage_spread",                                                                # Pandas → Whales
})
# Sheet types with reading passages but no FK scorer.
UNSCORED_PASSAGE_TYPES = frozenset({"read_aloud"})


def grade_of(code: str) -> int:
    """Grade a Common Core code belongs to: K.CC.1 → 0, 3.OA.7 → 3, RL.4.2 → 4, L.K.5c → 0,
    RL.9-10.5 → 9, high-school math (A-REI.4, N-RN.A.1, F-IF.B.6, HSN-RN.A.1, HSN.RN.A.1) → 9."""
    if re.fullmatch(r"(HS[NAFGS][.-]|[NAFGS]-)[A-Z]{2,4}(\.[A-Z])?\.\d+[a-z]?", code):
        return 9
    m = re.fullmatch(r"(?:(?:RL|RI|RF|W|SL|L)\.)?(K|\d{1,2})(?:-\d{1,2})?\.[A-Za-z0-9.]+", code)
    if not m:
        raise ValueError(f"can't tell the grade of standard {code!r}")
    return 0 if m.group(1) == "K" else int(m.group(1))


def parse_content_grade(text: str) -> tuple[int, int]:
    """'Pre-K' → (-1, -1), 'K' → (0, 0), 'K–1' → (0, 1), '1–2' → (1, 2), '9' → (9, 9)."""
    t = text.strip()
    if t.lower() == "pre-k":
        return PRE_K, PRE_K
    parts = [p.strip() for p in re.split(r"[–—-]", t)]
    if not 1 <= len(parts) <= 2 or not all(re.fullmatch(r"K|\d{1,2}", p) for p in parts):
        raise ValueError(f"content_grade {text!r} is not Pre-K, K, a grade or a range like '1–2'")
    lo, hi = (0 if p == "K" else int(p) for p in (parts[0], parts[-1]))
    if lo > hi:
        raise ValueError(f"content_grade {text!r}: range runs backwards")
    return lo, hi


def grade_name(g: int) -> str:
    return "Pre-K" if g == PRE_K else "K" if g == 0 else str(g)


def section_codes(section: Section) -> list[str]:
    return list(section.standards) + [c for p in section.parts for c in p.standards]


def section_grade(section: Section) -> int | None:
    codes = section_codes(section)
    return max(map(grade_of, codes)) if codes else None


@dataclass
class LevelReport:
    public_name: str
    content_grade: str
    exempt: bool
    highest: int | None = None                       # highest standard grade across checked strands
    lowest_section: tuple[int, str] | None = None    # (grade, label) of the lowest-graded section
    tagged: list[str] = field(default_factory=list)  # on-ramp / review sections (label + kind)
    fk: dict[str, tuple[float, float]] = field(default_factory=dict)   # reading strand → fk_grade range


def _label(level: Level, section: Section | None = None) -> str:
    subj = {"english": "Reading", "math": "Math", "pencil": "Pencil skills"}[level.subject]
    out = f"{level.public_name} {subj}"
    if section is not None:
        out += f', "{section.public_name}" ({level.level}-{section.code})'
    else:
        out += f" ({level.level})"
    return out


def _check_readability(level: Level, lo: int, hi: int, rep: LevelReport) -> list[Issue]:
    issues: list[Issue] = []
    bad: dict[tuple, list[int]] = {}
    unscored: dict[str, list[int]] = {}
    for page in range(1, level.pages + 1):
        spec = resolve_page(level, page)
        section = level.section(spec.section)
        if spec.sheet_type in FK_SHEET_TYPES:
            fk = spec.rules.get("fk_grade")
            if fk is None:
                bad.setdefault((section.code, "no fk_grade rule (the scorer would fall back to another level's "
                                              "default range)"), []).append(page)
                continue
            f_lo, f_hi = fk
            rep.fk.setdefault(level.level, (f_lo, f_hi))
            if not (lo - 1 <= f_lo <= lo and hi + 1 <= f_hi <= hi + 2):
                bad.setdefault((section.code, f"fk_grade {list(fk)} doesn't fit content grade {rep.content_grade} "
                                              f"(needs {lo - 1}–{lo} at the bottom, {hi + 1}–{hi + 2} at the top)"),
                               []).append(page)
        elif spec.sheet_type in UNSCORED_PASSAGE_TYPES:
            unscored.setdefault(section.code, []).append(page)
    for (code, why), pages in bad.items():
        issues.append(Issue(sheet_id=rep.public_name, severity="error",
                            message=f"{_label(level, level.section(code))}: pages {pages[0]}–{pages[-1]}: {why}"))
    for code, pages in unscored.items():
        issues.append(Issue(sheet_id=rep.public_name, severity="warning",
                            message=f"{_label(level, level.section(code))}: pages {pages[0]}–{pages[-1]} have "
                                    f"reading passages with no Flesch-Kincaid range, so nothing checks they read "
                                    f"at grade {rep.content_grade}"))
    return issues


def check_ladder() -> tuple[list[Issue], list[LevelReport]]:
    """Run the two-grades-ahead check over every public level. Returns (issues, per-level reports)."""
    issues: list[Issue] = []
    reports: list[LevelReport] = []
    for rung in load_ladder():
        lo, hi = parse_content_grade(rung.content_grade)
        rep = LevelReport(rung.public_name, rung.content_grade, exempt=lo == PRE_K)
        reports.append(rep)
        if rep.exempt:
            continue

        def err(msg: str) -> None:
            issues.append(Issue(sheet_id=rung.public_name, severity="error", message=msg))

        for subject, code in rung.strands.items():
            if subject == "pencil" or not level_path(subject, code).exists():
                continue   # pencil warm-ups have no standards; missing strands are "coming soon"
            level = load_level(subject, code)
            for s in level.sections:
                kind = "on-ramp" if s.on_ramp else "review" if s.review else None
                if kind:
                    rep.tagged.append(f"{_label(level, s)} [{kind}]")
                g = section_grade(s)
                if g is None:
                    err(f"{_label(level, s)}: no standards tagged")
                    continue
                rep.highest = g if rep.highest is None else max(rep.highest, g)
                if rep.lowest_section is None or g < rep.lowest_section[0]:
                    rep.lowest_section = (g, _label(level, s))
                if g < lo - 1 and not kind:
                    err(f"{_label(level, s)}: every standard is grade {grade_name(g)} or below, more than one "
                        f"grade under {rung.public_name}'s content grade {rung.content_grade}; teach on-grade "
                        f"work or mark the section on_ramp/review")
            if subject == "english":
                issues += _check_readability(level, lo, hi, rep)
        if rep.highest is None or rep.highest < hi:
            got = "nothing" if rep.highest is None else f"grade {grade_name(rep.highest)}"
            err(f"{rung.public_name}: its highest standard reaches {got}, short of content grade "
                f"{rung.content_grade}")
    return issues, reports


if __name__ == "__main__":   # uv run python -m ws.standards: the per-level table
    found, reps = check_ladder()
    for r in reps:
        if r.exempt:
            print(f"{r.public_name:10} {r.content_grade:6} exempt (Pre-K)")
            continue
        low = f"{grade_name(r.lowest_section[0])} ({r.lowest_section[1]})" if r.lowest_section else "-"
        print(f"{r.public_name:10} {r.content_grade:6} highest {grade_name(r.highest) if r.highest is not None else '-':3} "
              f"lowest section {low}  fk {r.fk or '-'}  tagged {r.tagged or '-'}")
    for i in found:
        print(f"{i.severity:8} {i.sheet_id}: {i.message}")
