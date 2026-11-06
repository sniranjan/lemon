"""Render Penguins Reading pages without touching the manifest and report layout problems (overflow,
small text), so writers can check their pages while other sections are being written.

    uv run python scripts/r7_fit.py A            # every planned page of section A
    uv run python scripts/r7_fit.py 1 2 101      # just these pages

Writes HTML and PNGs to out/_fit/R7/ (git-ignored).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ws import content  # noqa: E402
from ws import generate as gen  # noqa: E402
from ws.render import min_child_px, render_pngs, write_html  # noqa: E402
from ws.syllabus import load_level  # noqa: E402

content.clear_caches()
level = load_level("english", "R7")
plan = gen.build_plan(level)
pages: list[int] = []
for a in sys.argv[1:] or [s.code for s in level.sections]:
    if a.isdigit():
        pages.append(int(a))
    else:
        sec = level.section(a)
        pages += range(sec.pages[0], sec.pages[1] + 1)
out = ROOT / "out" / "_fit" / "R7"
shutil.rmtree(out, ignore_errors=True)
paths = []
for page in pages:
    if page not in plan.pages:
        continue
    sheet = gen.build_sheet(level, page, plan)
    path = out / f"{page:03d}-{sheet.sheet_type}.html"
    write_html(sheet, level, path)
    paths.append(path)
bad = 0
for r in render_pngs(paths, min_child_px("R7", "english")):
    bad += bool(r.problems)
    print(f"{r.html.name}: " + ("ok" if not r.problems else f"PROBLEMS: {r.problems}"))
print(f"{len(paths)} pages, {bad} with problems; PNGs in {out}")
