"""Export the paperlessons logo as image files (social avatars, wordmark), matching the site exactly.

Same mark as apps/web/src/components/Logo.tsx and the same fonts as the PDFs (assets/fonts/brand):
"paper" in Fredoka Bold (ink), "lessons" in Gochi Hand (coral, tilted -3deg, 1.12em).

    uv run python scripts/brand/export.py      # writes assets/brand/*.png and mark.svg
"""

from __future__ import annotations

import base64
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "assets" / "fonts" / "brand"
OUT = ROOT / "assets" / "brand"

INK, CREAM, SUN, CORAL = "#1f2a44", "#fff8ec", "#ffc83d", "#ff6b5e"

MARK = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<path d="M12 6 H42 L54 18 V56 a2 2 0 0 1-2 2 H12 a2 2 0 0 1-2-2 V8 a2 2 0 0 1 2-2 Z" fill="{SUN}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>
<path d="M42 6 V18 H54" fill="#fff" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>
<circle cx="24" cy="32" r="3.2" fill="{INK}"/><circle cx="40" cy="32" r="3.2" fill="{INK}"/>
<path d="M23 41 Q32 49 41 41" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>
</svg>"""


def _font(name: str) -> str:
    return base64.b64encode((FONTS / name).read_bytes()).decode()


CSS = f"""
@font-face {{ font-family: Fredoka; font-weight: 700; src: url(data:font/woff2;base64,{_font("Fredoka-Bold.woff2")}) format("woff2"); }}
@font-face {{ font-family: Gochi; src: url(data:font/woff2;base64,{_font("GochiHand-Regular.woff2")}) format("woff2"); }}
html, body {{ margin: 0; }}
.word {{ white-space: nowrap; line-height: 1; }}
.paper {{ font-family: Fredoka; font-weight: 700; letter-spacing: -0.025em; color: {INK}; }}
.lessons {{ font-family: Gochi; color: {CORAL}; display: inline-block; transform: translateY(0.07em) rotate(-3deg); font-size: 1.12em; }}
"""

WORD = '<span class="word"><span class="paper">paper</span><span class="lessons">lessons</span></span>'


def page(body: str, w: int, h: int, bg: str) -> str:
    return f"""<!doctype html><html><head><style>{CSS}
body {{ width: {w}px; height: {h}px; background: {bg}; display: flex; align-items: center; justify-content: center; }}
</style></head><body>{body}</body></html>"""


# name: (html body, width, height, background)  ("transparent" backgrounds get omit_background)
EXPORTS: dict[str, tuple[str, int, int, str]] = {
    # Instagram / social avatar: the mark alone, kept inside the circle crop (~62% of the width).
    "avatar-mark.png": (f'<div style="width:620px;height:620px">{MARK}</div>', 1080, 1080, CREAM),
    # Avatar with the name under the mark (reads at profile size, still inside the circle).
    "avatar-mark-name.png": (
        f'<div style="display:flex;flex-direction:column;align-items:center;gap:30px;margin-top:20px">'
        f'<div style="width:440px;height:440px">{MARK}</div>'
        f'<div style="font-size:118px">{WORD}</div></div>',
        1080, 1080, CREAM,
    ),
    # Horizontal logo exactly like the site header (mark + wordmark), transparent and on cream.
    "logo-horizontal.png": (
        f'<div style="display:flex;align-items:center;gap:42px;font-size:160px">'
        f'<div style="width:210px;height:210px">{MARK}</div>{WORD}</div>',
        1400, 360, "transparent",
    ),
    "logo-horizontal-cream.png": (
        f'<div style="display:flex;align-items:center;gap:42px;font-size:160px">'
        f'<div style="width:210px;height:210px">{MARK}</div>{WORD}</div>',
        1400, 360, CREAM,
    ),
    "mark.png": (f'<div style="width:1024px;height:1024px">{MARK}</div>', 1024, 1024, "transparent"),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "mark.svg").write_text(MARK + "\n")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name, (body, w, h, bg) in EXPORTS.items():
            pg = browser.new_page(viewport={"width": w, "height": h})
            pg.set_content(page(body, w, h, bg))
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(100)
            pg.screenshot(path=str(OUT / name), omit_background=bg == "transparent")
            print(OUT / name)
        browser.close()


if __name__ == "__main__":
    main()
