"""PDF booklets (CLAUDE.md §9): cover + sheets in page order + progress log, one per section
and one for the whole level; answer keys in a separate `-answers.pdf`.

Each sheet is printed to its own PDF by Chromium and must be exactly one Letter page
(612×792 pt). Booklets are merged with pypdf and written with fixed metadata and no dates,
so the same sheets always give byte-identical files.
"""

from __future__ import annotations

import io
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from .generate import OUT_DIR, load_manifest, sheet_dir
from .models import Issue, Level, Sheet
from .public import SUBJECT_LABEL, public_label, public_tag
from .render import MIN_TIP_PX, THEMES, _CHECK_JS, _env
from .syllabus import ROOT, STRAND_ORDER, ladder_level, level_path, load_level
from .verify import _ranges, banned_words, color_word_pages

LETTER = (612, 792)


@dataclass
class BookletReport:
    booklets: list[Path] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)


def _level_tag(level: Level, variant: int) -> str:
    """Public file-name stem (`chicks-reading`); buyers download these files, so no internal codes."""
    return public_tag(level, variant)


def _pace(level: Level) -> str:
    if level.sct_minutes_per_page:
        lo, hi = level.sct_minutes_per_page
        return f"within about {lo:g}–{hi:g} minutes a page"
    return "in about 5 minutes each"


def _write_doc(template: str, out: Path, **ctx) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    root = Path(os.path.relpath(ROOT, out.parent)).as_posix()
    out.write_text(_env.get_template(template).render(root=root, **ctx))
    return out


class _Printer:
    """One Chromium session that prints HTML files to PDF bytes and runs the layout checks."""

    def __enter__(self):
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch()
        self.page = self._browser.new_page(viewport={"width": 816, "height": 1056})
        self.page.emulate_media(media="print")
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._pw.stop()

    def pdf(self, html: Path, min_child: int = 28) -> tuple[bytes, list[str], str]:
        self.page.goto(html.resolve().as_uri())
        problems = self.page.evaluate(_CHECK_JS, [min_child, MIN_TIP_PX])
        text = self.page.evaluate("document.body.innerText")
        data = self.page.pdf(print_background=True, prefer_css_page_size=True)
        return data, problems, text


def _pages(data: bytes) -> list:
    return list(PdfReader(io.BytesIO(data)).pages)


def _write_booklet(parts: list[bytes], out: Path, title: str) -> Path:
    writer = PdfWriter()
    for data in parts:
        writer.append(PdfReader(io.BytesIO(data)))
    writer.add_metadata({"/Title": title, "/Producer": "ws", "/Creator": "ws"})
    buf = io.BytesIO()
    writer.write(buf)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(buf.getvalue())
    return out


def _answer_rows(sheets: list[Sheet], by_line: bool) -> list[dict]:
    """One row per sheet. With `by_line` (level rule `answers: by_line`, for reading sheets with sample
    sentences), a key with any long answer gets one line per answer, and short keys are spaced out."""
    rows = []
    for s in sheets:
        key = [str(a) for a in s.answer_key]
        lines = key if by_line and any(len(a) > 30 for a in key) else None
        joined = (" · " if by_line else ", ").join(key)
        rows.append({"id": s.id, "page": s.page_number, "answers": joined, "lines": lines, "by_line": by_line})
    return rows


def _answer_pages(rows: list[dict], by_line: bool, per_page: int = 20, height: int = 760) -> list[list[dict]]:
    """Answer rows split into pages: 20 a page, or with `by_line` as many as fit (an estimated 24px per
    printed line (with room to spare) at about 66 characters a line, plus 14px a row)."""
    if not by_line:
        return [rows[i:i + per_page] for i in range(0, len(rows), per_page)]
    pages: list[list[dict]] = [[]]
    used = 0
    for r in rows:
        h = 14 + 28 * sum(-(-len(a) // 66) for a in (r["lines"] or [r["answers"]]))
        if pages[-1] and used + h > height:
            pages.append([])
            used = 0
        pages[-1].append(r)
        used += h
    return pages


def build_booklets(subject: str, level_code: str, variant: int = 1) -> BookletReport:
    level = load_level(subject, level_code)
    theme = THEMES[subject]
    report = BookletReport()
    sheets = [s for s in load_manifest(subject, level_code) if s.variant == variant]
    if not sheets:
        report.issues.append(Issue(sheet_id=f"{level_code}", severity="error",
                                   message=f"no generated sheets for {subject} {level_code} variant {variant}"))
        return report
    sheets.sort(key=lambda s: s.page_number)
    by_section: dict[str, list[Sheet]] = defaultdict(list)
    for s in sheets:
        by_section[s.section].append(s)

    tag = _level_tag(level, variant)
    level_dir = OUT_DIR / subject / level_code
    work = level_dir / "_booklet"

    from .render import min_child_px

    with _Printer() as printer:
        sheet_pdf: dict[str, bytes] = {}
        for s in sheets:
            data, problems, text = printer.pdf(sheet_dir(s) / f"{s.id}.html", min_child_px(level_code, subject))
            pages = _pages(data)
            if len(pages) != 1:
                report.issues.append(Issue(sheet_id=s.id, severity="error",
                                           message=f"prints as {len(pages)} pages, must be 1"))
            elif tuple(round(float(v)) for v in pages[0].mediabox[2:]) != LETTER:
                report.issues.append(Issue(sheet_id=s.id, severity="error",
                                           message=f"page size {pages[0].mediabox}, expected Letter"))
            for w in banned_words(text):
                report.issues.append(Issue(sheet_id=s.id, severity="error", message=f"banned word {w!r}"))
            sheet_pdf[s.id] = data

        def doc(template: str, name: str, booklet_id: str, **ctx) -> bytes:
            html = _write_doc(template, work / f"{name}.html", level=level, theme=theme, variant=variant,
                              booklet_id=booklet_id, doc_title=name, **ctx)
            data, problems, text = printer.pdf(html)
            for p in problems:
                report.issues.append(Issue(sheet_id=name, severity="error", message=f"layout: {p}"))
            for w in banned_words(text):
                report.issues.append(Issue(sheet_id=name, severity="error", message=f"banned word {w!r}"))
            return data

        def booklet(group: list[Sheet], booklet_id: str, sections_info: list[dict]) -> None:
            first, last = group[0].page_number, group[-1].page_number
            colors = color_word_pages(group)
            cover = doc("booklet/cover.html.j2", f"{booklet_id}-cover", booklet_id, sections=sections_info,
                        first_page=first, last_page=last, pace=_pace(level),
                        color_pages=_ranges(colors) if colors else "")
            log = doc("booklet/progress_log.html.j2", f"{booklet_id}-log", booklet_id)
            report.booklets.append(_write_booklet(
                [cover, *(sheet_pdf[s.id] for s in group), log], level_dir / f"{booklet_id}.pdf",
                f"paperlessons {public_label(level)} pages {first}-{last}"))
            answered = [s for s in group if s.answer_key]
            if answered:
                by_line = level.rules.get("answers") == "by_line"
                answers = doc("booklet/answers.html.j2", f"{booklet_id}-answers", booklet_id,
                              chunks=_answer_pages(_answer_rows(answered, by_line), by_line))
                report.booklets.append(_write_booklet([answers], level_dir / f"{booklet_id}-answers.pdf",
                                                      f"paperlessons {public_label(level)} answers"))

        all_info = []
        for code, group in sorted(by_section.items()):
            section = level.section(code)
            pages = [s.page_number for s in group]
            gaps = sorted(set(range(pages[0], pages[-1] + 1)) - set(pages))
            if gaps:
                report.issues.append(Issue(sheet_id=f"{tag}-{code}", severity="warning",
                                           message=f"section {code} booklet skips pages {gaps}"))
            info = {"code": code, "name": section.public_name, "first": pages[0], "last": pages[-1]}
            all_info.append(info)
            # page numbers within the level, as printed in each sheet's page pill
            booklet_id = f"{public_tag(level)}-pages-{pages[0]:03d}-{pages[-1]:03d}" + (
                f"-v{variant}" if variant > 1 else "")
            booklet(group, booklet_id, [info])
        booklet(sheets, f"{tag}-level", all_info)
    return report


# --- free previews (CLAUDE.md §15) ---------------------------------------------------------

def preview_dir() -> Path:
    return OUT_DIR / "previews"   # looked up at call time, so tests can point OUT_DIR elsewhere


def build_preview(slug: str) -> BookletReport:
    """`out/previews/<slug>.pdf` for one public level: a preview cover, each strand's `preview_pages`
    (reading, then math, then pencil warm-ups), and a closing page.

    The pages must already be generated (variant 1); `ws preview` regenerates them first so they use
    the current templates. Every page gets the booklet checks: one Letter page, layout, banned words
    (which include internal level codes).
    """
    rung = ladder_level(slug)
    report = BookletReport()
    strands: list[tuple[Level, list[Sheet]]] = []
    for subject in STRAND_ORDER:
        if subject not in rung.strands:
            continue
        code = rung.strands[subject]
        if not level_path(subject, code).exists():
            report.issues.append(Issue(sheet_id=slug, severity="error",
                                       message=f"{SUBJECT_LABEL[subject]} for {rung.public_name} isn't built yet"))
            continue
        level = load_level(subject, code)
        if not level.preview_pages:
            report.issues.append(Issue(sheet_id=slug, severity="error",
                                       message=f"{subject} {code} has no preview_pages in its syllabus"))
            continue
        by_page = {s.page_number: s for s in load_manifest(subject, code) if s.variant == 1}
        missing = [p for p in level.preview_pages if p not in by_page]
        if missing:
            report.issues.append(Issue(sheet_id=slug, severity="error",
                                       message=f"{subject} {code} preview pages not generated yet: {missing}"))
            continue
        strands.append((level, [by_page[p] for p in sorted(level.preview_pages)]))
    if report.issues:
        return report

    from .render import min_child_px

    work = preview_dir() / "_work" / slug
    theme = THEMES["english"]
    subjects = [SUBJECT_LABEL[lvl.subject] for lvl, _ in strands]
    label = f"{rung.public_name} · " + (", ".join(subjects[:-1]) + " and " + subjects[-1] if len(subjects) > 1 else subjects[0])
    with _Printer() as printer:
        parts: list[bytes] = []

        def check(name: str, data: bytes, problems: list[str], text: str) -> None:
            for p in problems:
                report.issues.append(Issue(sheet_id=name, severity="error", message=f"layout: {p}"))
            for w in banned_words(text):
                report.issues.append(Issue(sheet_id=name, severity="error", message=f"banned word {w!r}"))
            if len(_pages(data)) != 1:
                report.issues.append(Issue(sheet_id=name, severity="error",
                                           message=f"prints as {len(_pages(data))} pages, must be 1"))

        def doc(template: str, name: str, **ctx) -> bytes:
            html = _write_doc(template, work / f"{name}.html", rung=rung, theme=theme, variant=1,
                              doc_title=f"{rung.public_name} free preview", label=label, **ctx)
            data, problems, text = printer.pdf(html)
            check(name, data, problems, text)
            return data

        groups = []
        for level, sheets in strands:
            sections = []
            for section in level.sections:
                pages = [s.page_number for s in sheets if s.section == section.code]
                if pages:
                    sections.append({"name": section.public_name, "pages": pages})
            groups.append({"subject": SUBJECT_LABEL[level.subject], "pages": level.pages, "sections": sections})
        all_sheets = [s for _, sheets in strands for s in sheets]
        color = [f"{SUBJECT_LABEL[lvl.subject]} {_ranges(c)}" for lvl, sh in strands if (c := color_word_pages(sh))]
        parts.append(doc("booklet/preview_cover.html.j2", "cover", groups=groups, n_pages=len(all_sheets),
                         color_pages=", ".join(color)))
        for level, sheets in strands:
            for s in sheets:
                data, problems, text = printer.pdf(sheet_dir(s) / f"{s.id}.html", min_child_px(level.level, level.subject))
                check(s.id, data, problems, text)
                parts.append(data)
        parts.append(doc("booklet/preview_end.html.j2", "end", groups=groups))

    if not any(i.severity == "error" for i in report.issues):
        report.booklets.append(_write_booklet(parts, preview_dir() / f"{slug}.pdf",
                                              f"paperlessons {rung.public_name} free preview"))
    return report
