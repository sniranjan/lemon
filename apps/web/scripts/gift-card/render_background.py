"""The gift card PDF's fixed background: drawn once here with Chromium, from the on-screen card's design
(src/components/GiftCard.tsx), and committed. The Worker (worker/giftCard.ts) draws the gift's own words on top
with pdf-lib: who it's for, who it's from, the message, the gift line and the code.

Everything is placed in CSS px on an 816 x 1056 page (US Letter at 96 dpi). The boxes the Worker fills are in
worker/giftCard.ts (LAYOUT); keep the two in step.

    uv run python apps/web/scripts/gift-card/render_background.py
    node apps/web/scripts/gift-card/bundle.mjs
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
WEB = HERE.parents[1]
REPO = WEB.parents[1]
FONTSOURCE = REPO / "node_modules" / "@fontsource"
OUT = HERE / "background.pdf"

# Everything sits in one 816 x 1056 box that clips the paper circles: anything wider makes Chromium shrink the
# whole page to fit.
# The six mascots along the bottom, first rung to last (same as GiftCard.tsx).
MASCOTS = [
    WEB / "public/brand/chick.svg",
    REPO / "assets/pictures/bunny.svg",
    WEB / "public/brand/fox.svg",
    REPO / "assets/pictures/owl.svg",
    WEB / "public/brand/panda.svg",
    WEB / "public/brand/whale.svg",
]

LOGO = """<svg viewBox="0 0 64 64" width="56" height="56">
  <path d="M12 6 H42 L54 18 V56 a2 2 0 0 1-2 2 H12 a2 2 0 0 1-2-2 V8 a2 2 0 0 1 2-2 Z" fill="#ffc83d" stroke="#1f2a44" stroke-width="4" stroke-linejoin="round"/>
  <path d="M42 6 V18 H54" fill="#fff" stroke="#1f2a44" stroke-width="4" stroke-linejoin="round"/>
  <circle cx="24" cy="32" r="3.2" fill="#1f2a44"/><circle cx="40" cy="32" r="3.2" fill="#1f2a44"/>
  <path d="M23 41 Q32 49 41 41" fill="none" stroke="#1f2a44" stroke-width="4" stroke-linecap="round"/>
</svg>"""


def font(family: str, weight: int, files: list[str]) -> str:
    srcs = ", ".join(f"url('{(FONTSOURCE / f).as_uri()}') format('woff2')" for f in files)
    return f"@font-face {{ font-family: '{family}'; font-weight: {weight}; src: {srcs}; }}"


def html() -> str:
    mascots = "".join(
        f'<img src="{p.as_uri()}" style="transform: rotate({6 if i % 2 else -6}deg)">' for i, p in enumerate(MASCOTS)
    )
    fonts = "\n".join(
        [
            font("Fredoka", 700, ["fredoka/files/fredoka-latin-700-normal.woff2"]),
            font("Nunito", 700, ["nunito/files/nunito-latin-700-normal.woff2"]),
            font("Nunito", 800, ["nunito/files/nunito-latin-800-normal.woff2"]),
            font("Gochi Hand", 400, ["gochi-hand/files/gochi-hand-latin-400-normal.woff2"]),
        ]
    )
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{fonts}
@page {{ size: 816px 1056px; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; }}
html, body {{ width: 816px; height: 1056px; overflow: hidden; background: #fff; color: #1f2a44; font-family: Nunito; }}
.page {{ position: relative; width: 816px; height: 1056px; overflow: hidden; }}
.abs {{ position: absolute; }}
.sun {{ left: 624px; top: -64px; width: 256px; height: 256px; border-radius: 50%; background: #ffc83d; }}
.sky {{ left: -80px; top: 848px; width: 288px; height: 288px; border-radius: 50%; background: #d3e5ff; }}
.head {{ left: 57px; top: 74px; display: flex; align-items: center; gap: 12px; }}
.word {{ font-size: 41.6px; line-height: 1; white-space: nowrap; }}
.paper {{ font-family: Fredoka; font-weight: 700; letter-spacing: -0.025em; }}
.lessons {{ display: inline-block; font-family: 'Gochi Hand'; font-size: 1.12em; color: #ff6b5e; transform: translateY(2px) rotate(-3deg); }}
.for {{ left: 57px; top: 166px; font-family: 'Gochi Hand'; font-size: 32px; line-height: 48px; color: #ff6b5e; }}
.box {{ left: 57px; top: 734px; width: 702px; height: 180px; border: 3px dashed #1f2a44; border-radius: 16px; background: #fff; padding: 16px 24px; }}
.label {{ font-size: 14px; line-height: 20px; font-weight: 800; letter-spacing: 0.15em; text-transform: uppercase; color: #8f95a2; }}
.open {{ position: absolute; left: 24px; top: 99px; font-size: 18.4px; line-height: 28px; font-weight: 700; }}
.open b {{ color: #ff6b5e; }}
.never {{ position: absolute; left: 24px; top: 127px; font-size: 15.2px; line-height: 22px; font-weight: 700; color: #7a8090; }}
.mascots {{ left: 57px; top: 934px; display: flex; gap: 12px; }}
.mascots img {{ width: 48px; height: 48px; border: 3px solid #1f2a44; border-radius: 50%; background: #fff; padding: 4px; }}
</style></head><body><div class="page">
<div class="abs sun"></div><div class="abs sky"></div>
<div class="abs head">{LOGO}<span class="word"><span class="paper">paper</span><span class="lessons">lessons</span></span></div>
<p class="abs for">a gift for</p>
<div class="abs box"><p class="label">Your gift code</p>
  <p class="open">Open it at <b>paperlessons.com/redeem</b></p>
  <p class="never">The code never expires. Open it whenever you're ready.</p></div>
<div class="abs mascots">{mascots}</div>
</div></body></html>"""


def main() -> None:
    page_html = HERE / "background.html"
    page_html.write_text(html(), encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 816, "height": 1056})
        page.goto(page_html.as_uri())
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(200)
        page.pdf(path=str(OUT), width="816px", height="1056px", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        browser.close()
    page_html.unlink()
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
