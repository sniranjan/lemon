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
from .models import SUBJECT_PREFIX, Issue, Level, Sheet
from .render import MIN_TIP_PX, THEMES, _CHECK_JS, _env
from .syllabus import ROOT, load_level, sheet_id
from .verify import banned_words

LETTER = (612, 792)


@dataclass
class BookletReport:
    booklets: list[Path] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)


def _level_tag(level: Level, variant: int) -> str:
    prefix = SUBJECT_PREFIX[level.subject]
    base = f"{prefix}-{level.level}" if prefix else level.level
    return base + (f"-v{variant}" if variant > 1 else "")


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
            data, problems, text = printer.pdf(sheet_dir(s) / f"{s.id}.html", min_child_px(level_code))
            pages = _pages(data)
            if len(pages) != 1:
                report.issues.append(Issue(sheet_id=s.id, severity="error",
                                           message=f"prints as {len(pages)} pages, must be 1"))
            elif tuple(round(float(v)) for v in pages[0].mediabox[2:]) != LETTER:
                report.issues.append(Issue(sheet_id=s.id, severity="error",
                                           message=f"page size {pages[0].mediabox}, expected Letter"))
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
            cover = doc("booklet/cover.html.j2", f"{booklet_id}-cover", booklet_id, sections=sections_info,
                        first_page=first, last_page=last, pace=_pace(level))
            log = doc("booklet/progress_log.html.j2", f"{booklet_id}-log", booklet_id)
            report.booklets.append(_write_booklet(
                [cover, *(sheet_pdf[s.id] for s in group), log], level_dir / f"{booklet_id}.pdf",
                f"{tag} pages {first}-{last}"))
            answered = [s for s in group if s.answer_key]
            if answered:
                rows = [{"id": s.id, "page": s.page_number, "answers": ", ".join(map(str, s.answer_key))}
                        for s in answered]
                answers = doc("booklet/answers.html.j2", f"{booklet_id}-answers", booklet_id, rows=rows)
                report.booklets.append(_write_booklet([answers], level_dir / f"{booklet_id}-answers.pdf",
                                                      f"{tag} answers"))

        all_info = []
        for code, group in sorted(by_section.items()):
            section = level.section(code)
            pages = [s.page_number for s in group]
            gaps = sorted(set(range(pages[0], pages[-1] + 1)) - set(pages))
            if gaps:
                report.issues.append(Issue(sheet_id=f"{tag}-{code}", severity="warning",
                                           message=f"section {code} booklet skips pages {gaps}"))
            info = {"code": code, "name": section.name, "first": pages[0], "last": pages[-1]}
            all_info.append(info)
            last_num = pages[-1] - section.pages[0] + 1
            booklet_id = f"{sheet_id(level, section, pages[0], 1)}-{last_num:03d}" + (
                f"-v{variant}" if variant > 1 else "")
            booklet(group, booklet_id, [info])
        booklet(sheets, f"{tag}-level", all_info)
    return report
