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

THEMES = {
    "english": {"label": "English", "accent": "#0B7A75", "tint": "#E6F4F3"},
    "math": {"label": "Math", "accent": "#B4410C", "tint": "#FDEDE3"},
    "pencil": {"label": "Pencil Skills", "accent": "#6B4FBB", "tint": "#EFEBFA"},
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
async () => {
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
  const page = document.querySelector('.page').getBoundingClientRect();
  if (Math.round(page.width) !== 816 || Math.round(page.height) !== 1056)
    problems.push(`page is ${page.width}x${page.height}, expected 816x1056`);
  return problems;
}
"""


@dataclass
class PageResult:
    html: Path
    png: Path
    problems: list[str]


def render_pngs(html_paths: list[Path]) -> list[PageResult]:
    from playwright.sync_api import sync_playwright

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": PAGE_W, "height": PAGE_H})
        page.emulate_media(media="print")
        for path in html_paths:
            page.goto(path.resolve().as_uri())
            problems = page.evaluate(_CHECK_JS)
            png = path.with_suffix(".png")
            page.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": PAGE_W, "height": PAGE_H})
            results.append(PageResult(path, png, problems))
        browser.close()
    return results


def contact_sheet(pngs: list[Path], out: Path, title: str, grayscale_sample: Path | None = None) -> Path:
    """A grid of page thumbnails (half size), plus one full grayscale page if asked."""
    from playwright.sync_api import sync_playwright

    def rel(p: Path) -> str:
        return html.escape(Path(os.path.relpath(p, out.parent)).as_posix())

    tiles = "".join(
        f'<figure><img src="{rel(p)}"><figcaption>{html.escape(p.stem)}</figcaption></figure>' for p in pngs)
    if grayscale_sample:
        tiles += (f'<figure class="gray"><img src="{rel(grayscale_sample)}">'
                  f'<figcaption>{html.escape(grayscale_sample.stem)} in grayscale</figcaption></figure>')
    doc = f"""<!doctype html><meta charset="utf-8"><style>
body {{ margin: 0; padding: 24px; background: #8a8f94; font: 14px system-ui, sans-serif; }}
h1 {{ color: #fff; font-size: 18px; margin: 0 0 16px; }}
.grid {{ display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-start; }}
figure {{ margin: 0; }}
figure img {{ width: 408px; height: 528px; display: block; background: #fff; box-shadow: 0 2px 8px #0005; }}
figure.gray img {{ filter: grayscale(1); }}
figcaption {{ color: #fff; margin-top: 6px; }}
</style><h1>{html.escape(title)}</h1><div class="grid">{tiles}</div>"""
    out.parent.mkdir(parents=True, exist_ok=True)
    src = out.with_suffix(".html")
    src.write_text(doc)
    cols = min(len(pngs) + bool(grayscale_sample), 5)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 48 + cols * 408 + (cols - 1) * 20, "height": 600})
        page.goto(src.resolve().as_uri())
        page.wait_for_load_state("load")
        page.screenshot(path=str(out), full_page=True)
        browser.close()
    return out
