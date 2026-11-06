"""HTML rendering (Jinja2), page PNGs with layout checks (Playwright), contact sheets."""

from __future__ import annotations

import html
import os
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from . import registry
from .models import Level, Sheet
from .syllabus import ROOT

TEMPLATES = Path(__file__).parent / "templates"
PAGE_W, PAGE_H = 816, 1056

# Labels are the public subject names (ws/public.py SUBJECT_LABEL).
THEMES = {
    "english": {"label": "Reading", "accent": "#0B7A75", "tint": "#E6F4F3"},
    "math": {"label": "Math", "accent": "#B4410C", "tint": "#FDEDE3"},
    "pencil": {"label": "Pencil skills", "accent": "#6B4FBB", "tint": "#EFEBFA"},
}

_env = Environment(loader=FileSystemLoader(TEMPLATES), undefined=StrictUndefined,
                   autoescape=True, trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)


def write_html(sheet: Sheet, level: Level, path: Path) -> None:
    """Asset links are relative to the HTML file, so output is the same on any machine."""
    path.parent.mkdir(parents=True, exist_ok=True)
    root = Path(os.path.relpath(ROOT, path.parent)).as_posix()
    template = _env.get_template(registry.get(sheet.sheet_type).template)
    path.write_text(template.render(sheet=sheet, level=level, theme=THEMES[sheet.subject], root=root))


# --- Playwright: PNGs + layout checks -------------------------------------------------------

_CHECK_JS = """
async ([minChild, minTip]) => {
  await document.fonts.ready;
  await Promise.all([document.fonts.load('400 20px Andika'), document.fonts.load('700 20px Andika')]);
  const problems = [];
  const andika = [...document.fonts].filter(f => f.family.replace(/"/g, '') === 'Andika');
  if (andika.length < 2 || andika.some(f => f.status !== 'loaded'))
    problems.push('Andika font did not load: ' + andika.map(f => f.weight + ':' + f.status).join(', '));
  for (const el of document.querySelectorAll('.page, .card, .strip, .tip')) {
    if (el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1)
      problems.push(`overflow in .${el.className.split(' ')[0]} (${el.scrollWidth}x${el.scrollHeight} > ${el.clientWidth}x${el.clientHeight})`);
  }
  for (const img of document.images)
    if (!img.complete || img.naturalWidth === 0) problems.push('image did not load: ' + img.getAttribute('src'));
  // SVG <image> elements (line-path targets) aren't in document.images: load each href to check it
  for (const im of document.querySelectorAll('svg image')) {
    const href = im.getAttribute('href');
    const ok = await new Promise(res => { const t = new Image(); t.onload = () => res(t.naturalWidth > 0); t.onerror = () => res(false); t.src = new URL(href, location.href).href; });
    if (!ok) problems.push('image did not load: ' + href);
  }
  // text sizes: child-facing text (anything not inside [data-audience=parent]) and the parent tip
  const walker = document.createTreeWalker(document.querySelector('.page'), NodeFilter.SHOW_TEXT);
  const small = new Set();
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (!n.textContent.trim()) continue;
    const el = n.parentElement;
    const size = parseFloat(getComputedStyle(el).fontSize);
    if (el.closest('.tip')) { if (size < minTip) small.add(`tip text ${size}px < ${minTip}px`); }
    else if (!el.closest('[data-audience="parent"]') && size < minChild)
      small.add(`child-facing text "${n.textContent.trim().slice(0, 20)}" is ${size}px < ${minChild}px`);
  }
  problems.push(...small);
  const page = document.querySelector('.page').getBoundingClientRect();
  if (Math.round(page.width) !== 816 || Math.round(page.height) !== 1056)
    problems.push(`page is ${page.width}x${page.height}, expected 816x1056`);
  return problems;
}
"""

# §8: child-facing text ≥ 28px up to 5A (and the pencil levels), ≥ 20px from 4A; parent tip ≥ 16px.
MIN_TIP_PX = 16


def min_child_px(level: str) -> int:
    return 20 if level in {"4A", "3A", "2A"} else 28


@dataclass
class PageResult:
    html: Path
    png: Path
    problems: list[str]


def render_pngs(html_paths: list[Path], min_child: int = 28) -> list[PageResult]:
    from playwright.sync_api import sync_playwright

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": PAGE_W, "height": PAGE_H})
        page.emulate_media(media="print")
        for path in html_paths:
            page.goto(path.resolve().as_uri())
            problems = page.evaluate(_CHECK_JS, [min_child, MIN_TIP_PX])
            png = path.with_suffix(".png")
            page.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": PAGE_W, "height": PAGE_H})
            results.append(PageResult(path, png, problems))
        browser.close()
    return results


def contact_sheet(pngs: list[Path], out: Path, title: str, grayscale_sample: Path | None = None) -> Path:
    """A grid of page thumbnails, plus one grayscale page if asked.

    Up to 10 pages: half-size thumbnails (408 px wide), 5 per row, readable on their own.
    More: quarter-size (204 px), 10 per row, for an overview of a whole level.
    """
    from playwright.sync_api import sync_playwright

    def rel(p: Path) -> str:
        return html.escape(Path(os.path.relpath(p, out.parent)).as_posix())

    n = len(pngs) + bool(grayscale_sample)
    tw, per_row, gap = (408, 5, 20) if n <= 10 else (204, 10, 12)
    tiles = "".join(
        f'<figure><img src="{rel(p)}"><figcaption>{html.escape(p.stem)}</figcaption></figure>' for p in pngs)
    if grayscale_sample:
        tiles += (f'<figure class="gray"><img src="{rel(grayscale_sample)}">'
                  f'<figcaption>{html.escape(grayscale_sample.stem)} in grayscale</figcaption></figure>')
    doc = f"""<!doctype html><meta charset="utf-8"><style>
body {{ margin: 0; padding: 24px; background: #8a8f94; font: {14 if tw > 300 else 11}px system-ui, sans-serif; }}
h1 {{ color: #fff; font-size: 18px; margin: 0 0 16px; }}
.grid {{ display: flex; flex-wrap: wrap; gap: {gap}px; align-items: flex-start; }}
figure {{ margin: 0; }}
figure img {{ width: {tw}px; height: {tw * PAGE_H // PAGE_W}px; display: block; background: #fff; box-shadow: 0 2px 8px #0005; }}
figure.gray img {{ filter: grayscale(1); }}
figcaption {{ color: #fff; margin-top: 4px; }}
</style><h1>{html.escape(title)}</h1><div class="grid">{tiles}</div>"""
    out.parent.mkdir(parents=True, exist_ok=True)
    src = out.with_suffix(".html")
    src.write_text(doc)
    cols = min(n, per_row)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 48 + cols * tw + (cols - 1) * gap, "height": 600})
        page.goto(src.resolve().as_uri())
        page.wait_for_load_state("load")
        page.screenshot(path=str(out), full_page=True)
        browser.close()
    return out
