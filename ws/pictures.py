"""Picture checks and the picture contact sheet (CLAUDE.md §6).

The main fill of a picture is the most common opaque color once the dark outline is set
aside, measured on a real render. Its grayscale lightness (the same weights as CSS
`grayscale()`: 0.2126 R + 0.7152 G + 0.0722 B) must be 50–75%, so pictures stay
distinct when printed in black and white.
"""

from __future__ import annotations

import base64
import html
import os
from dataclasses import dataclass
from pathlib import Path

from .content import PICTURES_DIR, licenses

FILL_LIGHTNESS = (50, 75)   # percent, inclusive
OUTLINE_MAX = 30            # pixels darker than this are outline/eyes, not fill

_MEASURE_JS = """
async ([src, outlineMax]) => {
  const img = new Image();
  img.src = src;
  await img.decode();
  const c = document.createElement('canvas');
  c.width = c.height = 200;
  const g = c.getContext('2d');
  g.drawImage(img, 0, 0, 200, 200);
  const d = g.getImageData(0, 0, 200, 200).data;
  const counts = new Map();
  for (let i = 0; i < d.length; i += 4) {
    if (d[i + 3] < 255) continue;
    const L = (0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2]) / 2.55;
    if (L < outlineMax) continue;
    const key = (d[i] << 16) | (d[i + 1] << 8) | d[i + 2];
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  let best = null, n = 0;
  for (const [k, v] of counts) if (v > n) { best = k; n = v; }
  if (best === null) return null;
  const r = best >> 16, gr = (best >> 8) & 255, b = best & 255;
  return { color: '#' + best.toString(16).padStart(6, '0').toUpperCase(),
           lightness: (0.2126 * r + 0.7152 * gr + 0.0722 * b) / 2.55 };
}
"""


@dataclass
class PictureReport:
    slug: str
    main_fill: str | None
    lightness: float | None
    problems: list[str]


def check_svg_source(path: Path) -> list[str]:
    """Static rules: viewBox, no <style>, no scripts, no rasters, no text."""
    src = path.read_text()
    problems = []
    if 'viewBox="0 0 100 100"' not in src:
        problems.append('missing viewBox="0 0 100 100"')
    for bad, what in (("<style", "<style>"), ("<script", "script"), ("<image", "embedded raster"),
                      ("<text", "text"), ("Gradient", "gradient")):
        if bad in src:
            problems.append(f"contains {what}")
    return problems


def check_pictures(slugs: list[str] | None = None) -> list[PictureReport]:
    from playwright.sync_api import sync_playwright

    slugs = slugs or sorted(p.stem for p in PICTURES_DIR.glob("*.svg"))
    lic = licenses()
    reports = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for slug in slugs:
            path = PICTURES_DIR / f"{slug}.svg"
            problems = check_svg_source(path)
            if slug not in lic:
                problems.append("no LICENSES.yaml entry")
            # a data URL keeps the canvas readable (file:// images taint it)
            data_url = "data:image/svg+xml;base64," + base64.b64encode(path.read_bytes()).decode()
            m = page.evaluate(_MEASURE_JS, [data_url, OUTLINE_MAX])
            if m is None:
                problems.append("no fill color found")
                reports.append(PictureReport(slug, None, None, problems))
                continue
            lo, hi = FILL_LIGHTNESS
            if not lo <= round(m["lightness"]) <= hi:
                problems.append(f"main fill {m['color']} is {m['lightness']:.0f}% in grayscale (needs {lo}–{hi}%)")
            reports.append(PictureReport(slug, m["color"], m["lightness"], problems))
        browser.close()
    return reports


def picture_sheet(reports: list[PictureReport], out: Path) -> Path:
    """Each picture in color and in grayscale, with its main fill; problems in red."""
    from playwright.sync_api import sync_playwright

    def rel(p: Path) -> str:
        return html.escape(Path(os.path.relpath(p, out.parent)).as_posix())

    tiles = []
    for r in reports:
        src = rel(PICTURES_DIR / f"{r.slug}.svg")
        note = (f"{r.main_fill} · {r.lightness:.0f}%" if r.lightness is not None else "no fill")
        bad = "".join(f"<div class=bad>{html.escape(p)}</div>" for p in r.problems)
        tiles.append(f'<figure class="{"flag" if r.problems else ""}"><div class=pair>'
                     f'<img src="{src}"><img class=gray src="{src}"></div>'
                     f'<figcaption><b>{html.escape(r.slug)}</b> {note}</figcaption>{bad}</figure>')
    doc = f"""<!doctype html><meta charset="utf-8"><style>
body {{ margin: 0; padding: 24px; background: #fff; font: 14px system-ui, sans-serif; color: #222; }}
.grid {{ display: grid; grid-template-columns: repeat(5, 260px); gap: 18px; }}
figure {{ margin: 0; border: 1px solid #ccc; border-radius: 10px; padding: 10px; }}
figure.flag {{ border: 3px solid #c00; }}
.pair {{ display: flex; gap: 8px; }}
.pair img {{ width: 116px; height: 116px; }}
.gray {{ filter: grayscale(1); }}
.bad {{ color: #c00; font-size: 12px; margin-top: 4px; }}
</style><div class="grid">{"".join(tiles)}</div>"""
    out.parent.mkdir(parents=True, exist_ok=True)
    src = out.with_suffix(".html")
    src.write_text(doc)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 48 + 5 * 260 + 4 * 18 + 40, "height": 400})
        page.goto(src.resolve().as_uri())
        page.wait_for_load_state("load")
        page.screenshot(path=str(out), full_page=True)
        browser.close()
    return out
