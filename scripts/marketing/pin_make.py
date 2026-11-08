"""Make Pinterest pins (1000×1500, 2:3) for paperlessons.com from a batch YAML, in the house style.

    uv run python scripts/marketing/pin_make.py marketing/pinterest/pins/batch-01.yaml          # render all
    uv run python scripts/marketing/pin_make.py marketing/pinterest/pins/batch-01.yaml --only foxes-math
    uv run python scripts/marketing/pin_make.py marketing/pinterest/pins/batch-01.yaml --check  # validate, no render

Writes marketing/pinterest/pins/<batch>/<id>.png, <batch>-contact.png (every pin at feed size, ~236px wide,
the size people see them at) and marketing/pinterest/pins/manifest.json (what pin_publish.py posts, in order).

A pin in the batch:

    - id: foxes-math                  # unique slug; the PNG's name and utm_content
      board: grade23                  # key in marketing/pinterest/boards.yaml
      level: foxes                    # optional: chip shows "Foxes · Age 6 · Grade 3 work"; default mascot
      strand: math                    # optional, for the chip: reading | math | pencil
      chip: "..."                     # optional: replaces the level chip
      headline: "Times tables"        # big on the image (Fredoka); 2 lines at most
      subline: "printable, a few pages a day"   # handwritten under it
      pages:                          # 1–2 real pages: {level, page} = page of out/previews/<level>.pdf
        - {level: foxes, page: 7}     #   (never the cover or the closing page)
        - {file: marketing/instagram/posts/.../card.png, crop: 0.68}   # or a PNG in the repo (crop keeps the top)
      mascot: foxes                   # optional level slug ("none" for no mascot)
      background: cream               # cream | sun | coral | teal | sky | grape | leaf
      link: library                   # library | gift | a full https://paperlessons.com/... URL
      campaign: foxes                 # utm_campaign (default: level, else id)
      title: "..."                    # Pinterest title, ≤ 100 characters, search words first
      description: "..."              # ≤ 500 characters: age, grade, skill, printable, homeschool
      alt: "..."                      # alt text, ≤ 500 characters

All text (title, description, alt, image text) is checked against content/banned.yaml (internal level codes,
other programs' names, British spelling) like the Instagram posts.
"""

from __future__ import annotations

import argparse
import hashlib
import html as htmllib
import json
import re
import sys
import urllib.parse
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import instagram_launch as L  # noqa: E402  (fonts, colors, logo, mascots, page_png, banned checks)

ROOT = L.ROOT
PIN_DIR = ROOT / "marketing" / "pinterest"
PINS = PIN_DIR / "pins"
MANIFEST = PINS / "manifest.json"
BOARDS = PIN_DIR / "boards.yaml"
SITE = "https://paperlessons.com"

W, H = 1000, 1500
MAX = {"title": 100, "description": 500, "alt": 500, "headline": 34, "subline": 48, "chip": 44}
BG = {"cream": L.CREAM, **L.COLORS}
STRANDS = {"reading": "Reading", "math": "Math", "pencil": "Pencil skills"}
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Pins live for years and the levels are paid: no prices, no "free printable", no promises.
EXTRA_BANNED = [re.compile(p, re.I) for p in (
    r"\$\s?\d", r"\bfree printables?\b", r"\bguarantee", r"\bboost", r"\bmaster(?:y|ing)?\b", r"\bcommon core\b",
)]


class SpecError(ValueError):
    pass


def esc(s: object) -> str:
    return htmllib.escape(str(s or ""))


# ---------------------------------------------------------------- spec loading and checks

_PAGES: dict[str, int] = {}


def preview_pages(level: str) -> int:
    if level not in _PAGES:
        from pypdf import PdfReader
        pdf = L.PREVIEWS / f"{level}.pdf"
        if not pdf.exists():
            raise SpecError(f"no preview PDF {pdf.relative_to(ROOT)}: run `uv run ws preview` for that level")
        _PAGES[level] = len(PdfReader(str(pdf)).pages)
    return _PAGES[level]


def build_link(pin: dict) -> str:
    kind = pin.get("link", "library")
    params = {"utm_source": "pinterest", "utm_medium": "pin",
              "utm_campaign": pin.get("campaign") or pin.get("level") or pin["id"], "utm_content": pin["id"]}
    query = urllib.parse.urlencode(params)
    if kind == "library":
        return f"{SITE}/?{query}#library"  # the query must come before the fragment
    if kind == "gift":
        return f"{SITE}/gift?{query}"
    parts = urllib.parse.urlsplit(kind)
    if parts.scheme != "https" or parts.netloc not in ("paperlessons.com", "www.paperlessons.com"):
        raise SpecError(f"{pin['id']}: link must be library, gift or an https://paperlessons.com URL")
    q = f"{parts.query}&{query}" if parts.query else query
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path or "/", q, parts.fragment))


def check_strings(where: str, texts: list[str], pats: list[re.Pattern]) -> None:
    for text in texts:
        for p in pats + EXTRA_BANNED:
            m = p.search(text)
            if m:
                raise SpecError(f"banned text {m.group(0)!r} in {where}")


def validate(pin: dict, boards: dict, pats: list[re.Pattern]) -> dict:
    """Check one pin spec; return it with defaults filled in and `link` built. Raises SpecError."""
    pid = pin.get("id", "")
    if not ID_RE.match(str(pid)):
        raise SpecError(f"bad pin id {pid!r} (lowercase-with-dashes)")
    for key in ("board", "headline", "title", "description", "alt", "pages"):
        if not pin.get(key):
            raise SpecError(f"{pid}: {key} is required")
    if pin["board"] not in boards:
        raise SpecError(f"{pid}: unknown board {pin['board']!r} (boards.yaml has {', '.join(boards)})")
    text = {k: " ".join(str(pin.get(k) or "").split()) for k in MAX}
    for key, limit in MAX.items():
        if len(text[key]) > limit:
            raise SpecError(f"{pid}: {key} is {len(text[key])} characters (at most {limit})")
    level = pin.get("level")
    if level and level not in L.BY_SLUG:
        raise SpecError(f"{pid}: unknown level {level!r}")
    if pin.get("strand") and pin["strand"] not in STRANDS:
        raise SpecError(f"{pid}: strand must be one of {', '.join(STRANDS)}")
    mascot = pin.get("mascot", level)
    if mascot not in (None, "none") and mascot not in L.BY_SLUG:
        raise SpecError(f"{pid}: unknown mascot {mascot!r}")
    if pin.get("background", "cream") not in BG:
        raise SpecError(f"{pid}: background must be one of {', '.join(BG)}")
    pages = pin["pages"]
    if not 1 <= len(pages) <= 2:
        raise SpecError(f"{pid}: 1 or 2 pages")
    for p in pages:
        if "file" in p:
            f = ROOT / p["file"]
            if f.suffix != ".png" or not f.exists():
                raise SpecError(f"{pid}: page file {p['file']} must be an existing PNG")
            if not 0.3 <= float(p.get("crop", 1)) <= 1:
                raise SpecError(f"{pid}: crop keeps 0.3–1 of the image height")
        else:
            if p.get("level") not in L.BY_SLUG:
                raise SpecError(f"{pid}: page level {p.get('level')!r} unknown")
            n, total = int(p["page"]), preview_pages(p["level"])
            if not 2 <= n <= total - 1:
                raise SpecError(f"{pid}: {p['level']} page {n}: use a real sheet, pages 2–{total - 1} "
                                "(1 is the preview cover, the last is the closing page)")
    link = build_link(pin)
    check_strings(pid, [text["title"], text["description"], text["alt"], text["headline"], text["subline"],
                        text["chip"], boards[pin["board"]]["name"], link], pats)
    return {**pin, "title": text["title"], "description": text["description"], "alt": text["alt"],
            "mascot": mascot, "link": link}


def load_batch(path: Path) -> list[dict]:
    """Read and validate a batch YAML ({pins: [...]}) or a single-pin YAML. Raises SpecError."""
    data = yaml.safe_load(path.read_text())
    raw = data["pins"] if isinstance(data, dict) and "pins" in data else [data] if isinstance(data, dict) else data
    boards = yaml.safe_load(BOARDS.read_text())
    pats = L.banned_patterns()
    pins = [validate(p, boards, pats) for p in raw]
    ids = [p["id"] for p in pins]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise SpecError(f"duplicate pin ids: {', '.join(sorted(dupes))}")
    return pins


# ---------------------------------------------------------------- rendering

PIN_CSS = f"""
body {{ display: flex; flex-direction: column; }}
.head {{ flex: none; padding: 54px 60px 0; text-align: center; position: relative; z-index: 6; }}
.chiprow {{ display: flex; justify-content: center; }}
.chiprow .chip {{ font-size: 34px; padding: 4px 26px 6px; box-shadow: 6px 6px 0 {L.INK}; }}
.headline {{ margin-top: 30px; text-wrap: balance; }}
.sub {{ text-wrap: balance; margin-top: 14px; font-size: 54px; line-height: 1.1; transform: rotate(-1.5deg); }}
.art {{ flex: 1; position: relative; margin: 34px 0 18px; }}
.pg {{ position: absolute; aspect-ratio: 816 / 1056; background: #fff; border-radius: 8px; overflow: hidden;
       box-shadow: 0 2px 0 rgba(31,42,68,.12), 0 24px 48px rgba(31,42,68,.26); }}
.pg img {{ display: block; width: 100%; }}
.foot {{ flex: none; height: 150px; display: flex; align-items: center; justify-content: space-between;
         padding: 0 64px 18px; position: relative; z-index: 6; }}
.url {{ font-family: Fredoka; font-weight: 700; font-size: 46px; letter-spacing: -0.01em; }}
.mascot {{ position: absolute; width: 190px; z-index: 5; filter: drop-shadow(4px 6px 0 rgba(31,42,68,.18)); }}
"""


def page_src(p: dict) -> tuple[str, float]:
    """(data URI, aspect height/width) for one page."""
    if "file" in p:
        path = ROOT / p["file"]
        w, h = L.png_size(path)
        return L.data_uri(path), h / w * float(p.get("crop", 1))
    return L.page_png(p["level"], int(p["page"])), 1056 / 816


def pin_html(pin: dict) -> str:
    bg_name = pin.get("background", "cream")
    bg = BG[bg_name]
    sub_color = {"cream": L.CORAL, "sun": L.INK}.get(bg_name, "#fff")
    lv = L.BY_SLUG.get(pin.get("level") or "")
    chip = pin.get("chip")
    if not chip and lv:
        strand = STRANDS.get(pin.get("strand", ""), "")
        name = f"{lv['name']} {strand}".strip()
        chip = f"{name} · Age {lv['age']} · {L.grade_label(lv['grade'])}"
    chip_bg = lv["color"] if lv and bg_name == "cream" else "#fff"

    headline = str(pin["headline"])
    n = len(headline)
    size = 124 if n <= 14 else 108 if n <= 20 else 94 if n <= 26 else 82
    head = (f'<div class="head">'
            + (f'<div class="chiprow"><span class="chip" style="background:{chip_bg}">{esc(chip)}</span></div>' if chip else "")
            + f'<div class="fred headline" style="font-size:{size}px">{esc(headline)}</div>'
            + (f'<div class="hand sub" style="color:{sub_color}">{esc(pin.get("subline"))}</div>' if pin.get("subline") else "")
            + "</div>")

    srcs = [page_src(p) for p in pin["pages"]]
    art = ""
    if len(srcs) == 1:
        src, ratio = srcs[0]
        # height-driven so a tall header never pushes the page off the pin; capped at 780px wide
        # height-driven so a tall header never pushes the page off the pin; capped at 780px wide. The wrapper
        # carries the mascot so it always sits on the page's corner, however tall the page ends up.
        wrap = (f'position:absolute;left:50%;top:50%;transform:translate(-50%, -50%);'
                f'height:min(100%, {int(780 * ratio)}px);aspect-ratio:1/{ratio}')
        art += (f'<div style="{wrap}"><div class="pg" style="left:0;top:0;width:100%;height:100%;aspect-ratio:auto;transform:rotate(2deg);z-index:2">'
                f'<img src="{src}" alt=""></div>{{MASCOT}}</div>')
    else:
        (a, ra), (b, rb) = srcs
        art += (f'<div class="pg" style="left:44px;top:0;height:min(86%, {int(600 * ra)}px);aspect-ratio:1/{ra};'
                f'transform:rotate(-5deg);z-index:2"><img src="{a}" alt=""></div>'
                f'<div class="pg" style="right:44px;bottom:0;height:min(86%, {int(600 * rb)}px);aspect-ratio:1/{rb};'
                f'transform:rotate(4deg);z-index:3"><img src="{b}" alt=""></div>')
    mascot = pin.get("mascot")
    if mascot and mascot != "none":
        src = L.BY_SLUG[mascot]["mascot"]
        if len(srcs) == 1:
            art = art.replace("{MASCOT}", f'<img class="mascot" src="{src}" style="right:-70px;top:-90px;'
                                          f'transform:rotate(8deg)" alt="">')
        else:
            art += f'<img class="mascot" src="{src}" style="right:24px;top:-62px;transform:rotate(8deg)" alt="">'
    art = art.replace("{MASCOT}", "")

    # on a colored background the logo's coral "lessons" needs white behind it: one white bar for the footer
    bar = (f"background:#fff;border:4px solid {L.INK};border-radius:999px;padding:12px 36px 10px;"
           f"box-shadow:6px 6px 0 {L.INK};" if bg_name != "cream" else "")
    foot = (f'<div class="foot"><div style="flex:1;display:flex;align-items:center;justify-content:space-between;{bar}">'
            f'{L.logo(300 if not bar else 270)}<span class="url"{" style=font-size:40px" if bar else ""}>paperlessons.com</span></div></div>')
    blobs = (f'<div class="blob" style="left:-170px;top:520px;width:480px;height:480px;'
             f'background:{"#fff" if bg_name != "cream" else (lv["color"] if lv else L.SUN)};opacity:{.22 if bg_name != "cream" else .30}"></div>'
             f'<div class="blob" style="right:-150px;top:-150px;width:420px;height:420px;'
             f'background:{"#fff" if bg_name != "cream" else L.TEAL};opacity:.16"></div>')
    return L.html(blobs + head + f'<div class="art">{art}</div>' + foot, W, H, bg, PIN_CSS)


LAYOUT_JS = """() => {
  const r = e => e.getBoundingClientRect();
  const head = r(document.querySelector('.head')), art = r(document.querySelector('.art')),
        foot = r(document.querySelector('.foot'));
  const hl = document.querySelector('.headline');
  const lines = Math.round(hl.getBoundingClientRect().height / parseFloat(getComputedStyle(hl).lineHeight));
  const pages = [...document.querySelectorAll('.pg')].map(e => {const b = r(e); return [b.left, b.top, b.right, b.bottom, b.width];});
  const out = [...document.querySelectorAll('.head *, .foot *')].filter(e => {const b = r(e);
     return b.left < -1 || b.right > innerWidth + 1 || b.bottom > innerHeight + 1;}).length;
  return {headBottom: head.bottom, footTop: foot.top, artTop: art.top, artHeight: art.height, lines, pages, out};
}"""


def check_layout(pid: str, m: dict) -> list[str]:
    problems = []
    if m["lines"] > 2:
        problems.append(f"headline wraps to {m['lines']} lines")
    if m["artHeight"] < 640:
        problems.append(f"art area only {m['artHeight']:.0f}px tall (header too big)")
    if m["out"]:
        problems.append("header/footer text runs off the pin")
    for left, top, right, bottom, width in m["pages"]:
        if left < -30 or right > W + 30 or top < m["headBottom"] - 70:
            problems.append(f"page off the pin or over the header ({left:.0f},{top:.0f},{right:.0f})")
        if bottom > m["footTop"] + 20:
            problems.append(f"page runs into the footer (bottom {bottom:.0f}, footer at {m['footTop']:.0f})")
        if width < 380:
            problems.append(f"page only {width:.0f}px wide")
    return [f"{pid}: {p}" for p in problems]


def contact_html(items: list[tuple[str, Path]]) -> str:
    cells = "".join(
        f'<div class="c"><img src="{L.data_uri(path)}"><div>{esc(pid)}</div></div>' for pid, path in items)
    css = (".grid{display:grid;grid-template-columns:repeat(8,236px);gap:22px 18px;padding:28px}"
           ".c img{width:236px;height:354px;display:block;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.18)}"
           ".c div{font:700 15px Nunito;margin-top:6px;color:#1f2a44;overflow:hidden;white-space:nowrap}")
    rows = (len(items) + 7) // 8
    return L.html(f'<div class="grid">{cells}</div>', 8 * 236 + 7 * 18 + 56, rows * 392 + 56, "#efe9dd", css)


def render(batch: Path, only: list[str] | None) -> None:
    pins = load_batch(batch)
    out_dir = PINS / batch.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    pats = L.banned_patterns()
    problems: list[str] = []
    todo = [p for p in pins if not only or p["id"] in only]
    with L.sync_playwright() as pw:
        browser = pw.chromium.launch()
        for pin in todo:
            path = out_dir / f"{pin['id']}.png"
            pg = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            pg.set_content(pin_html(pin))
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(150)
            try:
                check_strings(str(path.relative_to(ROOT)), [pg.inner_text("body")], pats)
            except SpecError as e:
                sys.exit(str(e))
            problems += check_layout(pin["id"], pg.evaluate(LAYOUT_JS))
            pg.screenshot(path=str(path))
            pg.close()
            assert L.png_size(path) == (W, H), (path, L.png_size(path))
            print(path.relative_to(ROOT))
        if not only:
            sheet = PINS / f"{batch.stem}-contact.png"
            items = [(p["id"], out_dir / f"{p['id']}.png") for p in pins]
            html = contact_html(items)
            pg = browser.new_page(viewport={"width": 8 * 236 + 7 * 18 + 56, "height": 400}, device_scale_factor=1)
            pg.set_content(html)
            pg.wait_for_timeout(150)
            pg.screenshot(path=str(sheet), full_page=True)
            pg.close()
            print(sheet.relative_to(ROOT))
        browser.close()
    write_manifest(batch, pins, out_dir)
    if problems:
        sys.exit("layout problems:\n  " + "\n  ".join(problems))


def write_manifest(batch: Path, pins: list[dict], out_dir: Path) -> None:
    """manifest.json keeps every batch's pins (this batch replaced), in order, for pin_publish.py."""
    data = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"pins": []}
    keep = [p for p in data["pins"] if p.get("batch") != batch.stem]
    rows = []
    for p in pins:
        img = out_dir / f"{p['id']}.png"
        if not img.exists():
            continue
        rows.append({
            "id": p["id"], "batch": batch.stem, "board": p["board"], "image": str(img.relative_to(ROOT)),
            "sha256": hashlib.sha256(img.read_bytes()).hexdigest(),
            "title": p["title"], "description": p["description"], "link": p["link"], "alt_text": p["alt"],
        })
    ids = {r["id"] for r in keep}
    clash = ids & {r["id"] for r in rows}
    if clash:
        sys.exit(f"pin ids already used by another batch: {', '.join(sorted(clash))}")
    MANIFEST.write_text(json.dumps({"pins": keep + rows}, indent=2, ensure_ascii=False) + "\n")
    print(f"{MANIFEST.relative_to(ROOT)} ({len(keep) + len(rows)} pins)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch", help="batch YAML (marketing/pinterest/pins/batch-NN.yaml)")
    ap.add_argument("--only", nargs="+", metavar="ID", help="render only these pins")
    ap.add_argument("--check", action="store_true", help="validate the specs and stop")
    args = ap.parse_args()
    batch = Path(args.batch).resolve()
    try:
        if args.check:
            pins = load_batch(batch)
            print(f"{len(pins)} pins OK")
            return
        render(batch, args.only)
    except SpecError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
