"""Render the Owls Reading pages that one section's reads fill, without touching the manifest, and
report layout problems (overflow, small text) and the free space left on each page (px).

    uv run python scripts/r4_fit.py B          # pages planned from content/passages/R4/B.yaml

Writes HTML and PNGs to out/_fit/R4-<section>/ (git-ignored), so writers can check their pages
while other sections are being written.
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

FREE_JS = """() => {
  for (const e of document.querySelectorAll('.qs')) { e.style.flex = 'none'; e.style.justifyContent = 'flex-start'; }
  for (const e of document.querySelectorAll('.done')) { e.style.marginTop = '0'; }
  const f = document.querySelector('.fit'); const r = f.getBoundingClientRect(); let m = 0;
  for (const c of f.children) m = Math.max(m, c.getBoundingClientRect().bottom);
  return Math.round(r.bottom - m);
}"""

code = sys.argv[1]
content.clear_caches()
level = load_level("english", "R4")
sec = level.section(code)
plan = gen.build_plan(level)
out = ROOT / "out" / "_fit" / f"R4-{code}"
shutil.rmtree(out, ignore_errors=True)
paths = []
for page in range(sec.pages[0], sec.pages[1] + 1):
    if page not in plan.pages:
        continue
    sheet = gen.build_sheet(level, page, plan)
    path = out / f"{page:03d}-{sheet.sheet_type}.html"
    write_html(sheet, level, path)
    paths.append(path)

from playwright.sync_api import sync_playwright  # noqa: E402

bad = 0
results = {r.html: r.problems for r in render_pngs(paths, min_child_px("R4", "english"))}
with sync_playwright() as p:
    page = p.chromium.launch().new_page(viewport={"width": 816, "height": 1056})
    page.emulate_media(media="print")
    for path in paths:
        page.goto(path.resolve().as_uri())
        free = page.evaluate(FREE_JS)
        probs = results[path]
        bad += bool(probs) or free < 0
        print(f"{path.name}: free {free}px" + (f"  PROBLEMS: {probs}" if probs else ""))
print(f"{len(paths)} pages, {bad} with problems; PNGs in {out}")
