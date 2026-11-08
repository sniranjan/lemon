"""Build an Amazon KDP paperback (interior PDF + full cover PDF) from a finished level strand booklet.

    uv run python scripts/kdp/make_book.py [slug …]      # → out/kdp/<slug>/{interior,cover}.pdf + previews

Interior: 8.5 × 11 in, no bleed, black-and-white friendly. Front matter (title, copyright, for grown-ups, notes),
100 of the strand's sheets exactly as sold on the site (from out/<subject>/<level>/<slug>-level.pdf, built by
`ws render`), two progress-log pages and a "what's next" page. KDP margins for 24–150 pages: inside ≥ 0.375 in (151–300: 0.5 in),
outside/top/bottom ≥ 0.25 in. Our sheets keep 0.58 in at the sides, 0.5 in top and 0.42 in bottom, so they fit as is.

Cover: one PDF spread (back, spine, front) with 0.125 in bleed all round; spine = pages × 0.002252 in (white
paper). The barcode box (2 × 1.2 in, bottom right of the back, KDP prints it) stays empty.

Books are described in BOOKS below. Public names only; no other program's name anywhere (CLAUDE.md §15).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from html import escape as esc
from pathlib import Path

from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "marketing"))
import instagram_launch as L  # noqa: E402  (brand fonts, colors, logo, mascots)

ROOT = L.ROOT
OUT = ROOT / "out" / "kdp"
PX = 96  # CSS px per inch
TRIM_W, TRIM_H, BLEED = 8.5, 11.0, 0.125
PAPER = 0.002252  # in per page, white paper

CHICKS_READING = {
    "level": "chicks",
    "source": ROOT / "out/english/7A/chicks-reading-level.pdf",
    "name": "Chicks",
    "ages": "Ages 3–4",
    "grade": "Preschool",
    "color": L.TEAL,
    "colors_tip": ("A few pages teach color words. After the page, go on a hunt together: find something red "
                   "(or blue, or green) in the room."),
}
BOOKS = {
    # sheets: 1-based pages of the source booklet (page 1 = its cover, sheet n = page n + 1)
    "chicks-reading-1": {
        **CHICKS_READING,
        "sheets": (2, 101),
        "title": "Chicks Reading 1",
        "chip": "Reading · Book 1",
        "subtitle": "First picture words",
        "parts": [("Look and Say", "pages 1–100", "two new picture words a page to look at and say together, plus "
                   "a little strip of words from a few days before")],
        "cover_sheets": [26, 12, 70, 61],  # front left/right, back left/right (no color-word pages)
        "blurb": ("Big pictures, big words and a short tip for you at the top of every page. Your child meets 200 "
                  "everyday words (apple, train, mom, boots) two at a time and says each one again a few days "
                  "later, so the words stick."),
        "bullets": ["100 pages, two new words a page", "A few pages a day, about 5 minutes",
                    "A grown-up tip on every page", "Original pictures, made for little readers"],
        "next": {"mascot": "chicks", "name": "Chicks Reading 2", "line": "Find It and Tiny Stories"},
    },
    "chicks-reading-2": {
        **CHICKS_READING,
        "sheets": (102, 201),
        "title": "Chicks Reading 2",
        "chip": "Reading · Book 2",
        "subtitle": "Find it and tiny stories",
        "parts": [("Find It", "pages 101–140", "four known pictures a page to find and name"),
                  ("Tiny Stories", "pages 141–200", "two to four short sentences built only from words your child "
                   "knows, read together")],
        "cover_sheets": [104, 160, 110, 170],
        "blurb": ("The words from Chicks Reading 1 come back in a picture game, then in tiny stories your child "
                  "reads with you: \"Look at the rainbow. I hug my baby.\" Every sentence uses only words they "
                  "already know."),
        "bullets": ["100 pages, one small step at a time", "A few pages a day, about 5 minutes",
                    "A grown-up tip on every page", "First real sentences to read together"],
        "next": {"mascot": "ducklings", "name": "Ducklings", "line": "Little phrases and numbers to 100"},
    },
}

CSS = L.CSS + f"""
@page {{ size: 8.5in 11in; margin: 0; }}
body {{ overflow: visible; }}
.pg {{ width: 8.5in; height: 11in; position: relative; overflow: hidden; page-break-after: always; background: #fff;
       padding: 0.75in 0.8in; font-size: 15pt; line-height: 1.45; font-weight: 400; }}
.pg b, .pg strong {{ font-weight: 800; }}
.pg h1 {{ font-family: Fredoka; font-weight: 700; margin: 0; letter-spacing: -0.01em; }}
.pg h2 {{ font-family: Fredoka; font-weight: 700; font-size: 26pt; margin: 0 0 .25in; }}
.rule {{ height: 3px; background: currentColor; margin: .12in 0 .3in; }}
.lines div {{ border-bottom: 1.5px solid #9aa3b5; height: .42in; }}
.log {{ width: 100%; border-collapse: collapse; font-size: 12pt; }}
.log th {{ text-align: left; font-weight: 800; padding: 6px 4px; border-bottom: 3px solid currentColor; }}
.log td {{ border-bottom: 1.2px solid #9aa3b5; height: .44in; }}
.small {{ font-size: 11pt; color: #475069; }}
"""


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def png(pdf: Path, page: int, tmp: Path, dpi: int = 150) -> str:
    out = tmp / f"p{page}"
    run(["pdftoppm", "-r", str(dpi), "-png", "-singlefile", "-f", str(page), "-l", str(page), str(pdf), str(out)])
    return L.data_uri(out.with_suffix(".png"))


def doc(body: str, extra: str = "") -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}{extra}</style></head><body>{body}</body></html>"


def front_matter(b: dict) -> str:
    lv = L.BY_SLUG[b["level"]]
    c = b["color"]
    parts = "".join(f"<li><b>{esc(n)}</b> · {esc(p)}: {esc(d)}</li>" for n, p, d in b["parts"])
    title = f"""<div class="pg" style="display:flex;flex-direction:column;align-items:center;text-align:center">
  <div style="margin-top:.4in">{L.logo(300)}</div>
  <img src="{lv['mascot']}" style="width:2.6in;margin-top:.7in" alt="">
  <h1 style="font-size:58pt;margin-top:.3in;color:{c}">{esc(b['title'])}</h1>
  <div class="hand" style="font-size:28pt;color:{L.CORAL};transform:rotate(-1.5deg)">{esc(b['subtitle'])}</div>
  <div style="font-weight:800;font-size:16pt;margin-top:.2in">{esc(b['ages'])} · {esc(b['grade'])}</div>
  <div style="margin-top:auto;width:100%;text-align:left;font-weight:800;font-size:18pt">This book belongs to
    <div style="border-bottom:2px solid {L.INK};height:.55in"></div></div>
</div>"""
    copyright_ = f"""<div class="pg" style="display:flex;flex-direction:column;justify-content:flex-end;font-size:11pt">
  <p><b>{esc(b['title'])}: {esc(b['subtitle'])}</b><br>{esc(b['ages'])}</p>
  <p>Copyright © 2026 paperlessons. All rights reserved. You may copy pages from this book for the children in
  your own home. No other part of this book may be reproduced, sold or shared, in print or digitally, without
  written permission.</p>
  <p>Words, sentences, pictures and page designs are original to paperlessons.</p>
  <p>paperlessons.com</p>
</div>"""
    grownups = f"""<div class="pg" style="color:{L.INK}">
  <h2 style="color:{c}">For grown-ups</h2>
  <p><b>A few pages a day, with you beside your child.</b> About five pages a day is plenty; at this age, two or
  three is fine too. Read the short tip at the top of each page first, then do the page together.</p>
  <p><b>What's inside</b></p><ul style="margin-top:0">{parts}</ul>
  <p><b>When to move on.</b> When your child finishes 3 pages in a row in about 5 minutes without help, they're ready
  for the next page. If a page is still hard, go back a few pages and do them again; repeating is part of the plan,
  and there's no rush.</p>
  <p><b>Color words.</b> {esc(b['colors_tip'])}</p>
  <p><b>Keep it happy.</b> Stop while it's still fun. Praise the trying, not just the right answers.</p>
  <p class="small" style="margin-top:.35in">Free preview pages of every level, and printable copies of this book, at
  <b>paperlessons.com</b>.</p>
</div>"""
    notes = f"""<div class="pg" style="color:{c}"><h2>Notes</h2>
  <div class="lines">{'<div></div>' * 20}</div></div>"""
    return title + copyright_ + grownups + notes


def back_matter(b: dict) -> str:
    c = b["color"]
    log = f"""<div class="pg" style="color:{c}"><h2>Progress log</h2>
  <table class="log"><tr><th style="width:22%">Date</th><th style="width:20%">Pages</th><th style="width:18%">Minutes</th>
  <th>Notes</th></tr>{'<tr><td></td><td></td><td></td><td></td></tr>' * 19}</table></div>"""
    nxt = b["next"]
    n = b["sheets"][1] - b["sheets"][0] + 1
    road = "".join(
        f'<div style="text-align:center;width:.85in"><img src="{lv["mascot"]}" style="width:.6in" alt="">'
        f'<div style="font-size:9.5pt;font-weight:800">{esc(lv["name"])}</div></div>'
        for lv in L.LEVELS
    )
    whats_next = f"""<div class="pg" style="text-align:center">
  <h2 style="color:{c};font-size:30pt;margin-top:.3in">You did it!</h2>
  <p style="font-size:16pt">All {n} pages. That's a lot of words, and a lot of mornings together.</p>
  <img src="{L.BY_SLUG[nxt['mascot']]['mascot']}" style="width:2in;margin-top:.25in" alt="">
  <p style="font-size:16pt;margin-top:.1in"><b>Next up: {esc(nxt['name'])}</b><br>{esc(nxt['line'])}</p>
  <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:.08in;margin:.45in 0 .2in">{road}</div>
  <p class="small">Thirteen levels for ages 3 to 12, reading and math, one small step at a time.</p>
  <div style="margin-top:.35in;display:flex;justify-content:center">{L.logo(260)}</div>
  <p style="font-size:15pt;margin-top:.1in"><b>paperlessons.com</b> · free preview pages of every level</p>
</div>"""
    lv = L.BY_SLUG[b["level"]]
    certificate = f"""<div class="pg" style="padding:.6in">
  <div style="border:6px solid {L.INK};border-radius:28px;height:100%;padding:.55in;text-align:center;display:flex;
    flex-direction:column;align-items:center;box-shadow:inset 0 0 0 10px #fff, inset 0 0 0 13px {c}">
    <div class="hand" style="font-size:30pt;color:{L.CORAL};transform:rotate(-2deg)">Hooray!</div>
    <h1 style="font-size:40pt;color:{c};margin-top:.1in">Certificate</h1>
    <img src="{lv['mascot']}" style="width:2.4in;margin:.35in 0" alt="">
    <div style="font-size:16pt;font-weight:400">This is to say that</div>
    <div style="border-bottom:2px solid {L.INK};width:80%;height:.6in"></div>
    <div style="font-size:16pt;font-weight:400;margin-top:.25in">finished all {n} pages of</div>
    <div class="fred" style="font-size:30pt;margin-top:.1in">{esc(b['title'])}</div>
    <div style="margin-top:auto;display:flex;gap:.6in;width:100%;font-size:13pt;font-weight:400">
      <div style="flex:1;border-top:2px solid {L.INK};padding-top:4px">Date</div>
      <div style="flex:1;border-top:2px solid {L.INK};padding-top:4px">Signed</div></div>
  </div></div>"""
    return log + log + certificate + whats_next


def cover(b: dict, pages: int, tmp: Path) -> tuple[str, float, float]:
    spine = pages * PAPER
    w, h = 2 * TRIM_W + spine + 2 * BLEED, TRIM_H + 2 * BLEED
    lv = L.BY_SLUG[b["level"]]
    c = b["color"]
    imgs = [png(b["source"], p, tmp) for p in b["cover_sheets"]]
    x_front = BLEED + TRIM_W + spine  # left edge of the front panel
    sheet = lambda src, x, y, wi, rot, z=1: (  # noqa: E731
        f'<div class="sheet" style="left:{x}in;top:{y}in;width:{wi}in;transform:rotate({rot}deg);z-index:{z};'
        f'border:1.5px solid #d9dce4"><img src="{src}" alt=""></div>')
    bullets = "".join(f"<li>{esc(t)}</li>" for t in b["bullets"])
    body = f"""
<div class="abs" style="left:0;top:0;width:{w}in;height:{h}in;background:{L.CREAM}"></div>
<!-- front -->
<div class="abs" style="left:{x_front}in;top:0;width:{TRIM_W + BLEED}in;height:{h}in;background:{L.SUN}"></div>
<div class="blob" style="left:{x_front + 5.6}in;top:-.9in;width:3.8in;height:3.8in;background:#ffd970"></div>
<div class="blob" style="left:{x_front - 1.2}in;top:7.6in;width:3.6in;height:3.6in;background:#ffd970"></div>
<div class="abs" style="left:{x_front + .55}in;top:.6in">{L.logo(250)}</div>
<div class="abs fred" style="left:{x_front + .55}in;top:1.25in;font-size:92pt;color:{L.INK}">{esc(b['name'])}</div>
<div class="abs" style="left:{x_front + .6}in;top:2.75in"><span class="chip ink" style="font-size:26pt;padding:2px 26px 6px">{esc(b['chip'])}</span></div>
<div class="abs hand" style="left:{x_front + .6}in;top:3.55in;font-size:30pt;color:{L.INK};transform:rotate(-1.5deg)">{esc(b['subtitle'])}</div>
<div class="abs disc" style="left:{x_front + 6.05}in;top:1.45in;width:1.95in;height:1.95in;flex-direction:column;
  font-weight:900;font-size:21pt;line-height:1.05;text-align:center;background:{L.CORAL};color:#fff;transform:rotate(8deg)">
  {esc(b['ages'])}<span style="font-size:12pt;font-weight:800">{esc(b['grade'])}</span></div>
{sheet(imgs[0], x_front + .7, 4.55, 3.55, -5, 2)}
{sheet(imgs[1], x_front + 4.15, 4.75, 3.55, 4, 1)}
<img class="abs" src="{lv['mascot']}" style="left:{x_front + 3.05}in;top:8.45in;width:2.3in;z-index:5" alt="">
<div class="abs" style="left:{x_front + .55}in;top:{BLEED + TRIM_H - .95}in;font-weight:900;font-size:15pt;z-index:6">
  <span class="chip" style="font-size:15pt;border-width:3px;padding:2px 16px 4px">{b['sheets'][1] - b['sheets'][0] + 1} pages</span>
  <span class="chip" style="font-size:15pt;border-width:3px;padding:2px 16px 4px">a few pages a day</span></div>
<!-- spine -->
<div class="abs" style="left:{BLEED + TRIM_W}in;top:0;width:{spine}in;height:{h}in;background:{c}"></div>
<div class="abs" style="left:{BLEED + TRIM_W + spine / 2}in;top:{h / 2}in;width:{TRIM_H - 1.2}in;transform:translate(-50%,-50%) rotate(90deg);
  display:flex;justify-content:space-between;align-items:center;color:#fff;font-size:{min(15, (spine - .14) * 72):.1f}pt;font-weight:900;white-space:nowrap">
  <span class="fred">{esc(b['title'])}</span><span>{esc(b['ages'])}</span><span>paper<span class="lessons" style="color:#fff">lessons</span></span></div>
<!-- back -->
<div class="abs" style="left:{BLEED + .55}in;top:{BLEED + .6}in;width:{TRIM_W - 1.1}in">
  <div class="fred" style="font-size:27pt;line-height:1.1">Little lessons,<br>one page at a time.</div>
  <p style="font-weight:400;font-size:13pt;line-height:1.45;margin:.18in 0 .1in">{esc(b['blurb'])}</p>
  <ul style="font-size:13pt;line-height:1.5;margin:0;padding-left:.25in">{bullets}</ul>
</div>
{sheet(imgs[2], BLEED + .7, 4.2, 3.2, -3)}
{sheet(imgs[3], BLEED + 4.3, 4.35, 3.2, 3)}
<div class="abs" style="left:{BLEED + .55}in;top:{BLEED + TRIM_H - 1.55}in;width:4.6in;font-size:12pt;line-height:1.35">
  <b>Free preview pages of every level at paperlessons.com.</b><br>
  <span style="font-weight:400">Thirteen levels for ages 3 to 12, reading and math.</span>
  <div style="margin-top:.12in">{L.logo(190)}</div></div>
<!-- KDP barcode area: 2 x 1.2 in, kept empty -->
<div class="abs" style="left:{BLEED + TRIM_W - .25 - 2}in;top:{BLEED + TRIM_H - .25 - 1.2}in;width:2in;height:1.2in;background:#fff"></div>
"""
    extra = f"@page {{ size: {w}in {h}in; margin: 0; }} body {{ width: {w}in; height: {h}in; overflow: hidden; }}"
    return doc(body, extra), w, h


def pdf_from_html(page, html: str, out: Path, w: float, h: float) -> None:
    page.set_content(html, wait_until="load")
    page.evaluate("document.fonts.ready")
    page.pdf(path=str(out), width=f"{w}in", height=f"{h}in", print_background=True, prefer_css_page_size=True)


def main(slug: str) -> None:
    from playwright.sync_api import sync_playwright

    b = BOOKS[slug]
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="kdp-"))
    src = PdfReader(str(b["source"]))
    first, last = b["sheets"]
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page()
        pdf_from_html(pg, doc(front_matter(b)), tmp / "front.pdf", TRIM_W, TRIM_H)
        pdf_from_html(pg, doc(back_matter(b)), tmp / "back.pdf", TRIM_W, TRIM_H)
        w = PdfWriter()
        for part in (PdfReader(str(tmp / "front.pdf")).pages, src.pages[first - 1:last], PdfReader(str(tmp / "back.pdf")).pages):
            for page in part:
                w.add_page(page)
        n = len(w.pages)
        if n % 2:
            sys.exit(f"interior has an odd page count ({n})")
        w.add_metadata({"/Title": f"{b['title']}: {b['subtitle']}", "/Author": "paperlessons"})
        with open(out / "interior.pdf", "wb") as f:
            w.write(f)
        html, cw, ch = cover(b, n, tmp)
        pdf_from_html(pg, html, out / "cover.pdf", cw, ch)
        br.close()
    # Chromium rounds the page to whole CSS px; trim the box to the exact KDP size (the cut is inside the bleed)
    c = PdfReader(str(out / "cover.pdf"))
    cw_ = PdfWriter()
    for pp in c.pages:
        pp.mediabox.upper_right = (cw * 72, ch * 72)
        pp.cropbox.upper_right = (cw * 72, ch * 72)
        cw_.add_page(pp)
    with open(out / "cover.pdf", "wb") as f:
        cw_.write(f)
    for pdf in ("interior.pdf", "cover.pdf"):
        r = PdfReader(str(out / pdf))
        sizes = {(round(float(pp.mediabox.width) / 72, 3), round(float(pp.mediabox.height) / 72, 3)) for pp in r.pages}
        print(f"{pdf}: {len(r.pages)} pages, {sizes}")
    print(f"spine {n * PAPER:.4f} in; cover {cw:.4f} × {ch:.4f} in")
    run(["pdftoppm", "-r", "40", "-png", "-singlefile", str(out / "cover.pdf"), str(out / "cover-preview")])


if __name__ == "__main__":
    for slug in sys.argv[1:] or list(BOOKS):
        main(slug)
