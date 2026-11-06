"""Render the Instagram launch set for @paper.lessons (feed posts, highlight covers, grid preview).

Everything is HTML rendered to PNG with Playwright, using the brand fonts (Fredoka Bold + Gochi Hand from
assets/fonts/brand, Nunito from @fontsource), the logo from assets/brand/, level data from the site's
ladder.json, mascots from apps/web/public, and real pages from the free preview PDFs (out/previews).
No randomness and no network: re-running gives the same files.

    uv run python scripts/marketing/instagram_launch.py

Needs `pdftoppm` (poppler) on PATH and the preview PDFs (`uv run ws preview ...`).
Writes marketing/instagram/posts/<NN>-<slug>/, marketing/instagram/stories/highlights/ and
marketing/instagram/posts/grid-preview.png.
"""

from __future__ import annotations

import base64
import json
import re
import struct
import subprocess
import tempfile
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BRAND_FONTS = ROOT / "assets" / "fonts" / "brand"
NUNITO = ROOT / "node_modules" / "@fontsource" / "nunito" / "files"
BRAND = ROOT / "assets" / "brand"
PICTURES = ROOT / "assets" / "pictures"
WEB = ROOT / "apps" / "web"
PREVIEWS = ROOT / "out" / "previews"
IG = ROOT / "marketing" / "instagram"
POSTS = IG / "posts"
HIGHLIGHTS = IG / "stories" / "highlights"

INK, CREAM, SUN, CORAL, TEAL, SKY, GRAPE, LEAF = (
    "#1f2a44", "#fff8ec", "#ffc83d", "#ff6b5e", "#10a99a", "#4d96ff", "#9b5de5", "#5cc46b",
)
COLORS = {"sun": SUN, "coral": CORAL, "teal": TEAL, "sky": SKY, "grape": GRAPE, "leaf": LEAF}

W, H = 1080, 1350  # feed post (4:5)
SW, SH = 1080, 1920  # story / highlight cover

# ---------------------------------------------------------------------------------------------
# Assets


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def data_uri(path: Path) -> str:
    mime = {".png": "image/png", ".svg": "image/svg+xml"}[path.suffix]
    return f"data:{mime};base64,{b64(path)}"


CSS = f"""
@font-face {{ font-family: Fredoka; font-weight: 700; src: url(data:font/woff2;base64,{b64(BRAND_FONTS / "Fredoka-Bold.woff2")}) format("woff2"); }}
@font-face {{ font-family: Gochi; src: url(data:font/woff2;base64,{b64(BRAND_FONTS / "GochiHand-Regular.woff2")}) format("woff2"); }}
@font-face {{ font-family: Nunito; font-weight: 400; src: url(data:font/woff2;base64,{b64(NUNITO / "nunito-latin-400-normal.woff2")}) format("woff2"); }}
@font-face {{ font-family: Nunito; font-weight: 800; src: url(data:font/woff2;base64,{b64(NUNITO / "nunito-latin-800-normal.woff2")}) format("woff2"); }}
@font-face {{ font-family: Nunito; font-weight: 900; src: url(data:font/woff2;base64,{b64(NUNITO / "nunito-latin-900-normal.woff2")}) format("woff2"); }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; }}
body {{ position: relative; overflow: hidden; font-family: Nunito; font-weight: 800; color: {INK};
       -webkit-font-smoothing: antialiased; }}
.fred {{ font-family: Fredoka; font-weight: 700; letter-spacing: -0.02em; line-height: 1.02; }}
.hand {{ font-family: Gochi; font-weight: 400; }}
.lessons {{ font-family: Gochi; font-weight: 400; color: {CORAL}; display: inline-block; transform: rotate(-3deg); font-size: 1.08em; letter-spacing: 0; line-height: .8; }}
.abs {{ position: absolute; }}
.sticker {{ border: 5px solid {INK}; border-radius: 44px; box-shadow: 10px 10px 0 0 {INK}; }}
.chip {{ display: inline-flex; align-items: center; white-space: nowrap; border: 4px solid {INK}; border-radius: 999px;
         padding: 4px 24px 6px; font-weight: 900; font-size: 36px; line-height: 1.2; background: #fff; }}
.chip.ink {{ background: {INK}; color: #fff; }}
.chip.dashed {{ border-style: dashed; background: rgba(255,255,255,.6); }}
.blob {{ position: absolute; border-radius: 50%; }}
.disc {{ border-radius: 50%; border: 5px solid {INK}; background: #fff; display: flex; align-items: center; justify-content: center; }}
.disc img {{ width: 78%; height: 78%; }}
.sheet {{ position: absolute; background: #fff; border-radius: 6px; overflow: hidden;
          box-shadow: 0 2px 0 rgba(31,42,68,.10), 0 22px 44px rgba(31,42,68,.22); }}
.sheet img {{ display: block; width: 100%; }}
"""


def html(body: str, w: int, h: int, bg: str, extra_css: str = "") -> str:
    return (
        f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}"
        f"body {{ width: {w}px; height: {h}px; background: {bg}; }}{extra_css}</style></head>"
        f"<body>{body}</body></html>"
    )


LOGO = data_uri(BRAND / "logo-horizontal.png")  # 1400x360, transparent, mark + wordmark like the site header
MARK = data_uri(BRAND / "mark.png")
AVATAR = data_uri(BRAND / "avatar-mark.png")


def logo(width: int) -> str:
    return f'<img src="{LOGO}" style="width:{width}px;display:block" alt="">'


# Level data: names/ages/grades from the site's ladder.json; mascot + color mirror apps/web/src/data/levels.ts.
LADDER = json.loads((WEB / "src" / "data" / "ladder.json").read_text())


def _looks() -> dict[str, tuple[str, str]]:
    src = (WEB / "src" / "data" / "levels.ts").read_text()
    found = re.findall(r'(\w+): \{\s*mascot: "([^"]+)",\s*color: "(\w+)"', src)
    return {slug: (mascot, color) for slug, mascot, color in found}


LOOKS = _looks()
LEVELS = []
for row in LADDER:
    mascot, color = LOOKS[row["slug"]]
    LEVELS.append({**row, "mascot": data_uri(WEB / "public" / mascot.lstrip("/")), "color": COLORS[color]})
BY_SLUG = {lv["slug"]: lv for lv in LEVELS}


def grade_label(grade: str) -> str:
    return f"Grade {grade} work" if grade[0].isdigit() else f"{grade} work"


def pic(name: str) -> str:
    return data_uri(PICTURES / f"{name}.svg")


# Real pages from the preview PDFs, rasterized once per run into a temp dir.
_TMP = Path(tempfile.mkdtemp(prefix="ig-pages-"))


def page_png(level: str, n: int) -> str:
    out = _TMP / f"{level}-{n}"
    subprocess.run(
        ["pdftoppm", "-r", "200", "-png", "-singlefile", "-f", str(n), "-l", str(n),
         str(PREVIEWS / f"{level}.pdf"), str(out)],
        check=True,
    )
    return data_uri(out.with_suffix(".png"))


def sheet(src: str, x: int, y: int, w: int, rot: float, z: int = 1) -> str:
    return (f'<div class="sheet" style="left:{x}px;top:{y}px;width:{w}px;transform:rotate({rot}deg);z-index:{z}">'
            f'<img src="{src}" alt=""></div>')


# Lucide icons (ISC licence), as used on the site's "How it works".
ICONS = {
    "sprout": '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
    "printer": '<path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 9V3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v6"/><rect x="6" y="14" width="12" height="8" rx="1"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
}


def icon(name: str, size: int, stroke: float = 2.2) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{INK}" stroke-width="{stroke}" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


PENCIL = f"""<svg viewBox="0 0 400 60" xmlns="http://www.w3.org/2000/svg">
<path d="M60 8 H330 V52 H60 Z" fill="{SUN}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>
<path d="M60 23 H330 M60 37 H330" stroke="#e0a91f" stroke-width="4"/>
<path d="M330 8 L392 30 L330 52 Z" fill="#f6d7a7" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>
<path d="M372 23 L392 30 L372 37 Z" fill="{INK}"/>
<path d="M30 8 H60 V52 H30 Q8 52 8 30 Q8 8 30 8 Z" fill="{CORAL}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>
<path d="M44 8 V52" stroke="{INK}" stroke-width="5"/></svg>"""

# ---------------------------------------------------------------------------------------------
# Feed posts


def post_hello() -> str:
    c2 = page_png("chicks", 2)
    d3 = page_png("ducklings", 3)
    c6 = page_png("chicks", 6)
    body = f"""
<div class="blob" style="left:-120px;top:150px;width:360px;height:360px;background:{SUN};opacity:.45"></div>
<div class="blob" style="right:-150px;top:-90px;width:440px;height:440px;background:{SKY};opacity:.22"></div>
<div class="blob" style="right:-60px;top:560px;width:200px;height:200px;background:{CORAL};opacity:.18"></div>
<div class="abs" style="left:0;right:0;top:76px;display:flex;justify-content:center">{logo(560)}</div>
<div class="abs fred" style="left:60px;right:60px;top:278px;text-align:center;font-size:118px">
  Little <span class="lessons">lessons</span>,<br>one page<br>at a time.</div>
<div class="abs" style="left:0;right:0;top:700px;display:flex;justify-content:center">
  <span class="chip" style="font-size:42px;padding:10px 36px 12px;box-shadow:8px 8px 0 {INK}">Printable reading &amp; math, ages 3&ndash;12</span></div>
{sheet(c6, 70, 880, 380, -9, 1)}
{sheet(c2, 630, 880, 380, 8, 1)}
{sheet(d3, 340, 850, 400, -1.5, 2)}
<img class="abs" src="{BY_SLUG['chicks']['mascot']}" style="left:40px;top:812px;width:130px;transform:rotate(-8deg);z-index:3" alt="">
<img class="abs" src="{pic('duck')}" style="right:44px;top:800px;width:140px;transform:rotate(6deg);z-index:3" alt="">
"""
    return html(body, W, H, CREAM)


def level_road() -> str:
    """Slide 1 of 'Meet the levels': all 13 mascots on a winding road up a hill."""
    xs = [195, 425, 655, 885]
    rows = [1100, 878, 656]
    pts: list[tuple[int, int]] = []
    for r, y in enumerate(rows):
        row = xs if r % 2 == 0 else xs[::-1]
        pts += [(x, y) for x in row]
    pts.append((540, 440))  # whales at the top
    d = f"M{pts[0][0]} {pts[0][1]}"
    for i in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[i - 1], pts[i]
        if y0 == y1:
            d += f" L{x1} {y1}"
        else:  # a rounded switchback on the outside of the row
            bulge = 120 if x0 > 540 else -120
            d += f" C{x0 + bulge} {y0} {x1 + bulge} {y1} {x1} {y1}" if x0 == x1 else f" C{x0 + bulge} {y0 - 40} {x1 + 60} {y1 + 90} {x1} {y1}"
    road = (f'<svg class="abs" style="left:0;top:0" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="62" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{CREAM}" stroke-width="50" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{SUN}" stroke-width="6" stroke-dasharray="18 18" stroke-linecap="round"/></svg>')
    stops = ""
    for lv, (x, y) in zip(LEVELS, pts):
        size = 150 if lv["slug"] != "whales" else 170
        stops += (f'<div class="abs disc" style="left:{x - size // 2}px;top:{y - size // 2}px;width:{size}px;height:{size}px;'
                  f'background:#fff;box-shadow:6px 6px 0 {INK}"><img src="{lv["mascot"]}" alt=""></div>'
                  f'<div class="abs fred" style="left:{x - 110}px;width:220px;top:{y + size // 2 + 6}px;text-align:center;'
                  f'font-size:38px;color:{INK};-webkit-text-stroke:12px {SKY};paint-order:stroke fill">{lv["name"]}</div>')
    flag = (f'<svg class="abs" style="left:600px;top:285px" width="110" height="110" viewBox="0 0 110 110">'
            f'<path d="M14 104 V10" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
            f'<path d="M14 12 H86 L72 32 L86 52 H14 Z" fill="{CORAL}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/></svg>')
    body = f"""
<div class="abs" style="left:60px;top:66px"><span class="chip">13 levels &middot; ages 3 to 12</span></div>
<div class="abs fred" style="left:60px;top:150px;font-size:96px;width:760px">Thirteen levels,<br>one big climb</div>
<div class="abs hand" style="left:690px;top:390px;font-size:46px;transform:rotate(-4deg)">the top!</div>
{road}{flag}{stops}
<div class="abs hand" style="left:62px;top:1236px;font-size:40px;transform:rotate(-1.5deg)">start at the bottom and climb!</div>
<div class="abs" style="right:60px;top:1240px;font-size:38px;font-weight:900">swipe &rarr;</div>
"""
    return html(body, W, H, SKY)


def level_cards(levels: list[dict], heading: str, sub: str, idx: int, total: int) -> str:
    n = len(levels)
    card_h, gap = 196, 34 if n == 4 else 52
    stack_h = n * card_h + (n - 1) * gap
    top0 = 320 + (1190 - 320 - stack_h) // 2
    step = 80 // (n - 1)
    cards = ""
    note = "keep climbing!" if idx < total else "Free previews for Chicks &amp; Ducklings: link in bio"
    # Bottom card = lowest level; climbing up and to the right.
    for i, lv in enumerate(levels):
        y = top0 + (n - 1 - i) * (card_h + gap)
        x = 86 + i * step
        num = LADDER.index(next(r for r in LADDER if r["slug"] == lv["slug"])) + 1
        status = ('<span class="chip">Free preview</span>' if lv["ready"]
                  else '<span class="chip dashed">Coming soon</span>')
        cards += f"""
<div class="abs sticker" style="left:{x}px;top:{y}px;width:854px;height:{card_h}px;background:{lv['color']};
     display:flex;align-items:center;gap:28px;padding:0 30px">
  <div class="disc" style="width:146px;height:146px;flex:none"><img src="{lv['mascot']}" alt=""></div>
  <div style="flex:1;display:flex;flex-direction:column;gap:14px">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:16px">
      <span class="fred" style="font-size:72px;line-height:1">{lv['name']}</span>{status}</div>
    <div style="display:flex;gap:14px"><span class="chip">Age {lv['age']}</span><span class="chip ink">{grade_label(lv['grade'])}</span></div>
  </div>
  <div class="abs disc" style="left:-26px;top:-26px;width:72px;height:72px;background:{INK};color:#fff;border-color:{INK};
       font-weight:900;font-size:38px">{num}</div>
</div>"""
    body = f"""
<div class="blob" style="right:-140px;top:-140px;width:420px;height:420px;background:{SKY};opacity:.20"></div>
<div class="abs" style="left:60px;top:66px;font-size:38px;font-weight:900;opacity:.75">The climb &middot; {idx} of {total}</div>
<div class="abs fred" style="left:60px;top:122px;font-size:96px">{heading}</div>
<div class="abs hand" style="left:62px;top:228px;font-size:46px;color:{CORAL};transform:rotate(-1.5deg);transform-origin:left">{sub}</div>
{cards}
<div class="abs hand" style="left:60px;top:1236px;font-size:46px;transform:rotate(-1.5deg);transform-origin:left">{note}</div>
<div class="abs" style="right:60px;top:1240px;font-size:38px;font-weight:900">{'swipe &rarr;' if idx < total else ''}</div>
"""
    return html(body, W, H, CREAM)


def post_levels() -> list[str]:
    groups = [
        (["chicks", "ducklings", "bunnies", "kittens"], "Ages 3 &amp; 4", "first words, counting, letters"),
        (["puppies", "cubs", "foxes"], "Ages 5 &amp; 6", "spelling, reading aloud, times tables"),
        (["owls", "otters", "pandas"], "Ages 7 to 9", "chapter books, fractions, ratios"),
        (["penguins", "lions", "whales"], "Ages 10 to 12", "big ideas, equations, algebra"),
    ]
    slides = [level_road()]
    for i, (slugs, head, sub) in enumerate(groups, start=2):
        slides.append(level_cards([BY_SLUG[s] for s in slugs], head, sub, i, len(groups) + 1))
    return slides


def post_real_page() -> str:
    d3 = page_png("ducklings", 3)
    body = f"""
<div class="blob" style="left:-160px;top:420px;width:520px;height:520px;background:{SUN};opacity:.40"></div>
<div class="blob" style="right:-120px;top:-120px;width:380px;height:380px;background:{TEAL};opacity:.18"></div>
<div class="abs fred" style="left:60px;top:64px;font-size:92px">A real page</div>
<div class="abs hand" style="left:66px;top:160px;font-size:50px;color:{CORAL};transform:rotate(-2deg);transform-origin:left">
  from Ducklings Reading</div>
{sheet(d3, 200, 244, 720, 3, 1)}
<div class="abs" style="left:620px;top:120px;width:400px;transform:rotate(16deg);z-index:2">{PENCIL}</div>
<div class="abs sticker" style="left:560px;top:1118px;z-index:3;background:{CORAL};padding:18px 34px 22px;
     transform:rotate(-4deg);border-radius:36px">
  <div class="fred" style="font-size:52px">Try it free</div>
  <div style="font-size:36px;font-weight:900;margin-top:4px">link in bio &uarr;</div></div>
"""
    return html(body, W, H, CREAM)


def post_how() -> str:
    steps = [
        (LEAF, "sprout", "Pick a level", "Start with the animal that fits. Little ones begin with Chicks."),
        (SKY, "printer", "Get the whole level", "One PDF, every page in order. Black and white is fine."),
        (SUN, "sun", "A little every day", "A few pages, about ten minutes. Then off to play!"),
    ]
    cards = ""
    y = 296
    for i, (color, ic, title, text) in enumerate(steps):
        x = 86 if i != 1 else 126
        cards += f"""
<div class="abs sticker" style="left:{x}px;top:{y}px;width:854px;height:262px;background:#fff;display:flex;align-items:center;gap:34px;padding:0 40px">
  <div class="disc" style="width:160px;height:160px;flex:none;background:{color}">{icon(ic, 92)}</div>
  <div><div class="fred" style="font-size:62px">{title}</div>
       <div style="font-size:37px;line-height:1.3;margin-top:10px;font-weight:800;opacity:.85">{text}</div></div>
  <div class="abs disc" style="left:-26px;top:-26px;width:74px;height:74px;background:{INK};color:#fff;border-color:{INK};font-weight:900;font-size:40px">{i + 1}</div>
</div>"""
        y += 262 + 46
    body = f"""
<div class="blob" style="right:-130px;top:-150px;width:440px;height:440px;background:#fff;opacity:.35"></div>
<div class="blob" style="left:-110px;bottom:-140px;width:360px;height:360px;background:#fff;opacity:.30"></div>
<div class="abs fred" style="left:60px;top:70px;font-size:110px">How it works</div>
<div class="abs hand" style="left:64px;top:194px;font-size:50px;transform:rotate(-1.5deg);transform-origin:left">three little steps</div>
{cards}
<div class="abs" style="left:60px;right:60px;top:1222px;display:flex;align-items:center;justify-content:space-between">
  {logo(380)}<span style="font-size:38px;font-weight:900">paperlessons.com</span></div>
"""
    return html(body, W, H, SUN)


def post_two_grades() -> str:
    rows = [("whales", 12), ("pandas", 9), ("foxes", 6), ("chicks", 3)]
    out = ""
    y = 506
    for i, (slug, age) in enumerate(rows):
        lv = BY_SLUG[slug]
        assert lv["age"] == age
        x = 60 + i * 40
        hi = slug == "foxes"
        out += f"""
<div class="abs sticker" style="left:{x}px;top:{y}px;width:820px;height:146px;background:{SUN if hi else '#fff'};
     display:flex;align-items:center;gap:26px;padding:0 30px;border-radius:36px">
  <div class="disc" style="width:112px;height:112px;flex:none;background:#fff"><img src="{lv['mascot']}" alt=""></div>
  <span class="fred" style="font-size:64px;width:250px">Age {age}</span>
  <svg width="70" height="40" viewBox="0 0 70 40"><path d="M4 20 H60 M44 6 L62 20 L44 34" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></svg>
  <span class="chip" style="font-size:40px;background:{lv['color'] if not hi else '#fff'}">{grade_label(lv['grade'])}</span>
</div>"""
        y += 146 + 28
    body = f"""
<div class="blob" style="right:-150px;top:-120px;width:460px;height:460px;background:{GRAPE};opacity:.16"></div>
<div class="blob" style="left:-140px;top:1000px;width:360px;height:360px;background:{LEAF};opacity:.20"></div>
<div class="abs fred" style="left:60px;top:70px;font-size:124px">Age 6?<br><span style="color:{CORAL}">Grade 3</span> work.</div>
<div class="abs" style="left:60px;top:360px;width:900px;font-size:42px;line-height:1.3;font-weight:800">
  Every level runs about two grades ahead of school, one small step at a time.</div>
{out}
<div class="abs hand" style="left:60px;right:60px;top:1228px;font-size:42px;text-align:center;white-space:nowrap;transform:rotate(-1deg)">
  Start where it feels easy, climb at your own pace.</div>
"""
    return html(body, W, H, CREAM)


def post_previews() -> str:
    # Covers on top so both level names show; inner pages tucked behind them.
    pages = [page_png("chicks", 2), page_png("chicks", 1), page_png("ducklings", 1), page_png("ducklings", 4)]
    zs = [1, 3, 4, 2]
    fan = ""
    rots = [-12, -4, 4, 12]
    xs = [56, 206, 462, 612]
    ys = [560, 510, 510, 560]
    for src, r, x, y, z in zip(pages, rots, xs, ys, zs):
        fan += sheet(src, x, y, 392, r, z)
    body = f"""
<div class="blob" style="left:-150px;top:-150px;width:460px;height:460px;background:#fff;opacity:.18"></div>
<div class="blob" style="right:-140px;top:280px;width:320px;height:320px;background:{SUN};opacity:.55"></div>
<div class="abs fred" style="left:60px;right:60px;top:66px;text-align:center;font-size:118px">Try it free</div>
<div class="abs" style="left:0;right:0;top:214px;display:flex;justify-content:center">
  <span class="chip" style="font-size:42px;padding:10px 34px 12px;box-shadow:8px 8px 0 {INK}">Free preview for every level</span></div>
<div class="abs hand" style="left:60px;right:60px;top:318px;text-align:center;font-size:48px;color:#fff;transform:rotate(-1.5deg)">
  print a few pages and see how they feel</div>
{fan}
<img class="abs" src="{BY_SLUG['chicks']['mascot']}" style="left:46px;top:470px;width:150px;transform:rotate(-10deg);z-index:9" alt="">
<img class="abs" src="{BY_SLUG['ducklings']['mascot']}" style="right:40px;top:470px;width:160px;transform:rotate(8deg);z-index:9" alt="">
<div class="abs" style="left:0;right:0;top:1158px;display:flex;justify-content:center;z-index:10">
  <span class="sticker" style="background:#fff;padding:14px 48px 18px;border-radius:999px;font-family:Fredoka;font-weight:700;font-size:64px">paperlessons.com</span></div>
"""
    return html(body, W, H, CORAL)


# ---------------------------------------------------------------------------------------------
# Story highlight covers (Instagram shows the middle ~60% of the width as a circle)


def highlight(bg: str, inner: str) -> str:
    body = f"""
<div class="abs disc" style="left:{SW // 2 - 205}px;top:{SH // 2 - 205}px;width:410px;height:410px;border-width:7px;
     box-shadow:9px 9px 0 {INK}"><div style="transform:scale(.74);display:flex">{inner}</div></div>"""
    return html(body, SW, SH, bg)


def hl_previews() -> str:
    return highlight(SUN, f'<img src="{MARK}" style="width:330px;height:330px;margin-top:-6px" alt="">')


def hl_levels() -> str:
    steps = ""
    for i, c in enumerate([LEAF, SKY, CORAL]):
        h = 90 + i * 70
        steps += (f'<div class="abs" style="left:{48 + i * 102}px;top:{370 - h}px;width:106px;height:{h}px;'
                  f'background:{c};border:7px solid {INK};border-radius:12px"></div>')
    return highlight(SKY, f"""<div style="position:relative;width:400px;height:400px">{steps}
      <img class="abs" src="{BY_SLUG['chicks']['mascot']}" style="left:236px;top:-2px;width:150px" alt=""></div>""")


def hl_how() -> str:
    dots = "".join(
        f'<div class="disc" style="width:146px;height:146px;background:{c};font-family:Fredoka;font-weight:700;font-size:92px;'
        f'border-width:7px;transform:translateY({m}px)">{n}</div>'
        for n, c, m in [(1, LEAF, 56), (2, SKY, 0), (3, SUN, -56)]
    )
    return highlight(LEAF, f'<div style="display:flex;align-items:center;gap:12px">{dots}</div>')


def hl_real() -> str:
    mini = f"""
<div style="width:280px;height:360px;background:#fff;border:8px solid {INK};border-radius:22px;transform:rotate(-6deg);
            padding:26px 24px;display:flex;flex-direction:column;gap:18px">
  <div style="height:12px;border-radius:6px;background:{TEAL};width:70%"></div>
  <div style="flex:1;border:6px solid {INK};border-radius:18px;display:flex;align-items:center;gap:14px;padding:0 12px">
    <img src="{pic('duck')}" style="width:96px" alt=""><div style="flex:1;height:14px;border-radius:7px;background:{INK}"></div></div>
  <div style="flex:1;border:6px solid {INK};border-radius:18px;display:flex;align-items:center;gap:14px;padding:0 12px">
    <img src="{pic('apple')}" style="width:96px" alt=""><div style="flex:1;height:14px;border-radius:7px;background:{INK}"></div></div>
</div>"""
    return highlight(CORAL, mini)


# ---------------------------------------------------------------------------------------------
# Captions

TAGS_BASE = "#printableworksheets #kidsworksheets #homelearning #preschoolactivities #kindergartenreadiness"

CAPTIONS = {
    "01-hello": {
        "files": ["post.png"],
        "caption": """Hello! We're paperlessons 📄✏️

Little lessons, one page at a time. We make printable reading and math worksheets for ages 3 to 12, from first picture words and counting all the way to fractions and algebra.

Every level is one PDF: print it at home, sit down together, and do a few pages a day. That's it.

Free previews are at the link in bio. Say hi in the comments and tell us how old your little learner is 👋""",
        "tags": f"{TAGS_BASE} #printables #learnathome #earlyreading #earlymath #preschoolmom #homeschoolresources #paperlessons",
        "alt": "Cream background with the paperlessons logo, the words \"Little lessons, one page at a time.\" and \"Printable reading & math, ages 3–12\". Three real worksheet pages peek up from the bottom, with a chick and a duckling beside them.",
    },
    "02-meet-the-levels": {
        "files": ["slide-1.png", "slide-2.png", "slide-3.png", "slide-4.png", "slide-5.png"],
        "caption": """Meet the levels 🐥🦆🐰🐱🐶🐻🦊🦉🦦🐼🐧🦁🐳

Thirteen levels, one big climb, from Chicks at age 3 to Whales at age 12. Every level has reading and math, and the work runs about two grades ahead of school.

Swipe to see each level's age and grade. Chicks and Ducklings are ready now, with a free preview for each. The rest are on the way.

Not sure where to start? Pick the level that feels a little easy. Link in bio.""",
        "tags": f"{TAGS_BASE} #readingpractice #mathpractice #homeschooling #homeschoolcurriculum #printables #paperlessons",
        "alt": """Slide 1: Thirteen animal mascots on a winding road up a hill, from Chicks at the bottom to Whales at the top, titled "Thirteen levels, one big climb".

Slide 2: "Ages 3 & 4". Level cards: Chicks, age 3, Pre-K work, free preview. Ducklings, age 3, K work, free preview. Bunnies, age 4, K–1 work, coming soon. Kittens, age 4, grade 1 work, coming soon.

Slide 3: "Ages 5 & 6". Puppies, age 5, grade 1–2 work. Cubs, age 5, grade 2 work. Foxes, age 6, grade 3 work. All coming soon.

Slide 4: "Ages 7 to 9". Owls, age 7, grade 4 work. Otters, age 8, grade 5 work. Pandas, age 9, grade 6 work. All coming soon.

Slide 5: "Ages 10 to 12". Penguins, age 10, grade 7 work. Lions, age 11, grade 8 work. Whales, age 12, grade 9 work. All coming soon. "Free previews for Chicks & Ducklings: link in bio".""",
    },
    "03-a-real-page": {
        "files": ["post.png"],
        "caption": """A real page from Ducklings Reading 🦆

\"a blue dress, a yellow moon, a green frog.\" Your child looks at the picture and says the little phrase out loud with you. A short tip for grown-ups sits at the top of every page.

Big pictures, big letters, lots of white space, and it prints fine in black and white.

Try a few pages free: link in bio.""",
        "tags": f"{TAGS_BASE} #earlyreading #learningtoread #phonicsfun #preschoolathome #printables #paperlessons",
        "alt": "A printed worksheet titled \"Say the words\" lies slightly tilted on a cream background next to a yellow pencil. It shows a blue dress, a yellow moon and a green frog, each with its phrase. A coral sticker says \"Try it free, link in bio\".",
    },
    "04-how-it-works": {
        "files": ["post.png"],
        "caption": """How it works, in three little steps:

1️⃣ Pick a level. Start with the animal that fits. Little ones begin with Chicks; older kids jump in higher up.
2️⃣ Get the whole level. One PDF with every page in order. Print it all, or a week at a time. Black and white is fine.
3️⃣ A little every day. A few pages, about ten minutes, then off to play.

Free previews at the link in bio.""",
        "tags": f"{TAGS_BASE} #dailyroutine #learnathome #homeschoolmom #printables #worksheetsforkids #paperlessons",
        "alt": "Yellow background titled \"How it works\" with three numbered cards: 1, Pick a level, with a sprout icon; 2, Get the whole level, with a printer icon; 3, A little every day, a few pages, about ten minutes, with a sun icon. The paperlessons logo and paperlessons.com sit at the bottom.",
    },
    "05-two-grades-ahead": {
        "files": ["post.png"],
        "caption": """Age 6? Grade 3 work. 🦊

Every paperlessons level runs about two grades ahead of school, in small, steady steps. Age 3 starts with Pre-K work, age 9 does grade 6 work, and age 12 does grade 9 work.

It's never a race. Start where it feels easy, do a few pages a day, and move up when three pages in a row feel comfortable.

See all thirteen levels at the link in bio.""",
        "tags": f"{TAGS_BASE} #readingpractice #mathpractice #homeschooling #afterschoolactivities #printables #paperlessons",
        "alt": "Cream background with the headline \"Age 6? Grade 3 work.\" and the line \"Every level runs about two grades ahead of school, one small step at a time.\" Below, four cards climb like a ladder: Age 3 to Pre-K work with a chick, Age 6 to Grade 3 work with a fox, Age 9 to Grade 6 work with a panda, Age 12 to Grade 9 work with a whale.",
    },
    "06-free-previews": {
        "files": ["post.png"],
        "caption": """Try it free 🎁

Every level gets a free preview: a handful of real pages to print and try before you buy. Chicks and Ducklings previews are ready now, and each new level gets its own as it opens.

Print a few pages, sit down together, and see how they feel.

👉 paperlessons.com (link in bio)""",
        "tags": f"{TAGS_BASE} #freeprintables #freeworksheets #learnathome #preschoolmom #printables #paperlessons",
        "alt": "Coral background titled \"Try it free\" with a white label \"Free preview for every level\". Four real preview pages from Chicks and Ducklings are fanned out like playing cards, with a chick and a duckling peeking over them, and paperlessons.com at the bottom.",
    },
}


def write_caption(slug: str) -> str:
    c = CAPTIONS[slug]
    tags = c["tags"].split()
    assert 8 <= len(tags) <= 15, (slug, len(tags))
    assert len(set(tags)) == len(tags), slug
    images = ", ".join(f"`{f}`" for f in c["files"])
    text = (f"# {slug}\n\nImages: {images}\n\n## Caption\n\n{c['caption']}\n\n{' '.join(tags)}\n\n"
            f"## Alt text\n\n{c['alt']}\n")
    (POSTS / slug / "caption.md").write_text(text)
    return text


# ---------------------------------------------------------------------------------------------
# Grid preview (profile view: 3 columns, newest top-left; the grid shows posts cropped to 3:4)

POSTING_ORDER = ["01-hello", "02-meet-the-levels", "03-a-real-page", "04-how-it-works",
                 "05-two-grades-ahead", "06-free-previews"]


def grid_preview() -> str:
    newest_first = POSTING_ORDER[::-1]
    tiles = ""
    for slug in newest_first:
        first = POSTS / slug / CAPTIONS[slug]["files"][0]
        tiles += f'<div style="aspect-ratio:3/4;background:url({data_uri(first)}) center/cover"></div>'
    body = f"""
<div style="padding:44px 40px 30px;display:flex;align-items:center;gap:40px">
  <img src="{AVATAR}" style="width:190px;height:190px;border-radius:50%;border:2px solid #ddd" alt="">
  <div style="font-family:Nunito;color:#111">
    <div style="font-size:40px;font-weight:900">paper.lessons</div>
    <div style="font-size:30px;font-weight:800;margin-top:8px">paperlessons &middot; printable practice</div>
    <div style="font-size:27px;font-weight:400;margin-top:8px;line-height:1.35;max-width:790px">Printable reading &amp; math for ages 3&ndash;12 ✏️ About two grades ahead of school. A few pages a day. Free previews ↓</div>
    <div style="font-size:28px;font-weight:800;margin-top:6px;color:#00376b">paperlessons.com</div>
  </div></div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:4px">{tiles}</div>
"""
    return html(body, 1080, 1300, "#fff")


# ---------------------------------------------------------------------------------------------
# Rendering + checks


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    return struct.unpack(">II", data[16:24])


def banned_patterns() -> list[re.Pattern]:
    cfg = yaml.safe_load((ROOT / "content" / "banned.yaml").read_text())
    words = [w for group in cfg.values() for w in group]
    pats = [re.compile(rf"(?<![\w-]){re.escape(str(w))}(?![\w-])", re.I) for w in words]
    pats.append(re.compile(r"\b5 pages\b", re.I))
    pats.append(re.compile(r"\bcolour|\bfavourite|\bpractise\b", re.I))  # American spelling
    return pats


def check_text(where: str, text: str, pats: list[re.Pattern]) -> None:
    for p in pats:
        m = p.search(text)
        if m:
            raise SystemExit(f"banned text {m.group(0)!r} in {where}")


def main() -> None:
    jobs: list[tuple[Path, str, int, int]] = []
    for slug, maker in [("01-hello", post_hello), ("03-a-real-page", post_real_page), ("04-how-it-works", post_how),
                        ("05-two-grades-ahead", post_two_grades), ("06-free-previews", post_previews)]:
        jobs.append((POSTS / slug / "post.png", maker(), W, H))
    for i, page in enumerate(post_levels(), start=1):
        jobs.append((POSTS / "02-meet-the-levels" / f"slide-{i}.png", page, W, H))
    for name, maker in [("free-previews", hl_previews), ("levels", hl_levels), ("how-it-works", hl_how),
                        ("real-pages", hl_real)]:
        jobs.append((HIGHLIGHTS / f"{name}.png", maker(), SW, SH))

    pats = banned_patterns()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        def render(path: Path, content: str, w: int, h: int) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            pg = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            pg.set_content(content)
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(150)
            check_text(str(path.relative_to(ROOT)), pg.inner_text("body"), pats)
            pg.screenshot(path=str(path))
            pg.close()
            assert png_size(path) == (w, h), (path, png_size(path))
            print(path.relative_to(ROOT))

        for path, content, w, h in jobs:
            render(path, content, w, h)
        for slug in CAPTIONS:
            check_text(f"{slug}/caption.md", write_caption(slug), pats)
        render(POSTS / "grid-preview.png", grid_preview(), 1080, 1300)
        browser.close()


if __name__ == "__main__":
    main()
