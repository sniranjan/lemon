"""Make a new Instagram post (images + caption.md) from a small YAML file, in the house style.

    uv run python scripts/marketing/ig_post.py new 2026-11-20-bunnies-is-here   # scaffold the folder + post.yaml
    # edit marketing/instagram/posts/2026-11-20-bunnies-is-here/post.yaml
    uv run python scripts/marketing/ig_post.py render marketing/instagram/posts/2026-11-20-bunnies-is-here

`render` writes post.png (or slide-1.png … for a carousel) and caption.md next to post.yaml, checks every
piece of text against content/banned.yaml (internal level codes, other programs' names, British spelling),
and checks the caption has 8–15 hashtags. Then publish it with ig_publish.py. See marketing/instagram/API.md.

One layout, `announce`, adapts to what you give it:
  - headline (Fredoka, big), subline (handwritten, coral), optional chip (pill under the subline)
  - pages: 0–3 real pages from the free preview PDFs (out/previews/<level>.pdf), as {level, page}
  - mascots: 0–3 level slugs (chicks … whales), or pictures: 0–3 worksheet pictures (assets/pictures)
  - sticker + sticker_sub: the call to action in the corner ("Try it free" / "link in bio ↑")
  - background: cream (default) or sun, coral, teal, sky, grape, leaf
`slides:` (optional) is a list of more slides with the same keys; the post becomes a carousel.
"""

from __future__ import annotations

import html as htmllib
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import instagram_launch as L  # noqa: E402  (fonts, colors, logo, mascots, page_png, sheet, checks)

TEMPLATE = """\
# Instagram post. Render: uv run python scripts/marketing/ig_post.py render {folder}
# Rules: public level names only (Chicks … Whales), never codes; no other programs' names; no children's faces;
# American spelling; say "a few pages a day", "about two grades ahead"; never promise results.
layout: announce
background: cream            # cream | sun | coral | teal | sky | grape | leaf
headline: "Something new"    # short: 2–4 words read best (Fredoka, ~100px)
subline: "a handwritten line under it"
chip: ""                     # optional pill, e.g. "Reading & math for age 4"
pages:                       # 0–3 real pages from out/previews/<level>.pdf
  - {{level: ducklings, page: 3}}
mascots: []                  # 0–3 level slugs: chicks ducklings bunnies kittens puppies cubs foxes ...
pictures: []                 # or 0–3 worksheet pictures by name (assets/pictures/<name>.svg)
sticker: "Try it free"
sticker_sub: "link in bio ↑"
# slides:                    # optional: more slides (same keys) → carousel
#   - headline: ...

caption: |
  First line is the hook.

  Two or three short paragraphs. End with what to do: "Free previews at the link in bio."
tags: "#printableworksheets #kidsworksheets #homelearning #preschoolactivities #kindergartenreadiness #printables #learnathome #paperlessons"
alt: >-
  Describe each image for screen readers: background, headline, what the pictures show.
"""

BG = {"cream": L.CREAM, **L.COLORS}
MAX_SLIDES = 10


def esc(s: str) -> str:
    return htmllib.escape(str(s or ""))


def slide_html(spec: dict) -> str:
    bg_name = spec.get("background", "cream")
    if bg_name not in BG:
        sys.exit(f"unknown background {bg_name!r} (use {', '.join(BG)})")
    bg = BG[bg_name]
    on_color = bg_name != "cream"
    sub_color = {"cream": L.CORAL, "sun": L.INK}.get(bg_name, "#fff")

    pages = spec.get("pages") or []
    mascots = spec.get("mascots") or []
    pictures = spec.get("pictures") or []
    if len(pages) > 3 or len(mascots) > 3 or len(pictures) > 3:
        sys.exit("at most 3 pages, 3 mascots and 3 pictures per slide")
    for m in mascots:
        if m not in L.BY_SLUG:
            sys.exit(f"unknown level {m!r} (use {', '.join(L.BY_SLUG)})")
    imgs = [L.BY_SLUG[m]["mascot"] for m in mascots] + [L.pic(p) for p in pictures]

    headline = esc(spec.get("headline", ""))
    size = 112 if len(spec.get("headline", "")) <= 16 else 92 if len(spec.get("headline", "")) <= 24 else 76
    top = f"""
<div class="blob" style="left:-150px;top:380px;width:480px;height:480px;background:{'#fff' if on_color else L.SUN};opacity:{.22 if on_color else .40}"></div>
<div class="blob" style="right:-130px;top:-130px;width:400px;height:400px;background:{'#fff' if on_color else L.TEAL};opacity:.18"></div>
<div class="abs fred" style="left:90px;right:90px;top:70px;text-align:center;font-size:{size}px">{headline}</div>
<div class="abs hand" style="left:90px;right:90px;top:{80 + int(size * 1.1)}px;text-align:center;font-size:50px;color:{sub_color};transform:rotate(-1.5deg)">{esc(spec.get('subline'))}</div>
"""
    y = 80 + int(size * 1.1) + 84
    if spec.get("chip"):
        top += (f'<div class="abs" style="left:0;right:0;top:{y + 6}px;display:flex;justify-content:center">'
                f'<span class="chip" style="font-size:40px;padding:8px 32px 10px;box-shadow:8px 8px 0 {L.INK}">'
                f'{esc(spec["chip"])}</span></div>')
        y += 100

    art = ""
    srcs = [L.page_png(p["level"], int(p["page"])) for p in pages]
    if len(srcs) == 1:
        art += L.sheet(srcs[0], 230, y + 40, 620, 2.5, 1)
    elif len(srcs) == 2:
        art += L.sheet(srcs[0], 110, y + 70, 470, -6, 1) + L.sheet(srcs[1], 500, y + 50, 470, 5, 2)
    elif len(srcs) == 3:
        art += (L.sheet(srcs[0], 80, y + 110, 400, -9, 1) + L.sheet(srcs[2], 600, y + 110, 400, 8, 1)
                + L.sheet(srcs[1], 330, y + 60, 420, -1.5, 2))
    if srcs:
        # mascots/pictures peek over the pages' top corners
        spots = [(60, y - 10, -10), (880, y - 20, 8), (470, y - 60, 0)]
        for src, (x, yy, r) in zip(imgs, spots):
            art += (f'<img class="abs" src="{src}" style="left:{x}px;top:{yy}px;width:150px;'
                    f'transform:rotate({r}deg);z-index:5" alt="">')
    elif imgs:
        n = len(imgs)
        w = {1: 440, 2: 360, 3: 290}[n]
        gap = (1080 - n * w) // (n + 1)
        for i, src in enumerate(imgs):
            r = [-6, 4, -3][i]
            art += (f'<div class="abs disc" style="left:{gap + i * (w + gap)}px;top:{y + (1080 - y - w) // 2}px;width:{w}px;'
                    f'height:{w}px;transform:rotate({r}deg);box-shadow:10px 10px 0 {L.INK}"><img src="{src}" alt=""></div>')
    else:
        art += f'<div class="abs" style="left:0;right:0;top:{y + 200}px;display:flex;justify-content:center">{L.logo(640)}</div>'

    sticker = ""
    if spec.get("sticker"):
        sticker_bg = "#fff" if bg_name in ("coral", "sun") else L.CORAL
        sticker = f"""
<div class="abs sticker" style="right:96px;top:1108px;z-index:9;background:{sticker_bg};padding:18px 34px 22px;
     transform:rotate(-4deg);border-radius:36px;text-align:center">
  <div class="fred" style="font-size:52px">{esc(spec['sticker'])}</div>
  <div style="font-size:36px;font-weight:900;margin-top:4px">{esc(spec.get('sticker_sub'))}</div></div>"""
    footer = (f'<div class="abs" style="left:96px;top:1200px;z-index:8">{L.logo(330)}</div>'
              if (srcs or imgs) else "")
    return L.html(top + art + sticker + footer, L.W, L.H, bg)


def caption_md(folder: Path, spec: dict, files: list[str]) -> str:
    tags = str(spec.get("tags", "")).split()
    if not 8 <= len(tags) <= 15:
        sys.exit(f"tags: use 8–15 hashtags (found {len(tags)})")
    if len(set(tags)) != len(tags) or not all(t.startswith("#") for t in tags):
        sys.exit("tags: each must start with # and appear once")
    caption = str(spec.get("caption", "")).strip()
    alt = str(spec.get("alt", "")).strip()
    if not caption or not alt:
        sys.exit("post.yaml needs caption and alt")
    if len(caption) + len(" ".join(tags)) > 2100:
        sys.exit("caption + tags must stay under Instagram's 2,200 characters")
    images = ", ".join(f"`{f}`" for f in files)
    return (f"# {folder.name}\n\nImages: {images}\n\n## Caption\n\n{caption}\n\n{' '.join(tags)}\n\n"
            f"## Alt text\n\n{alt}\n")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(L.ROOT))
    except ValueError:
        return str(path)


def render(folder: Path) -> None:
    spec = yaml.safe_load((folder / "post.yaml").read_text())
    if spec.get("layout", "announce") != "announce":
        sys.exit("only layout: announce exists so far (add new layouts in ig_post.py)")
    shared = {k: v for k, v in spec.items() if k not in ("slides", "caption", "tags", "alt")}
    slides = [spec] + [{**shared, "pages": [], "mascots": [], "pictures": [], "chip": "", **s}
                       for s in (spec.get("slides") or [])]
    if len(slides) > MAX_SLIDES:
        sys.exit(f"at most {MAX_SLIDES} slides")
    files = ["post.png"] if len(slides) == 1 else [f"slide-{i}.png" for i in range(1, len(slides) + 1)]

    pats = L.banned_patterns()
    with L.sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name, s in zip(files, slides):
            path = folder / name
            pg = browser.new_page(viewport={"width": L.W, "height": L.H}, device_scale_factor=1)
            pg.set_content(slide_html(s))
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(150)
            L.check_text(rel(path), pg.inner_text("body"), pats)
            pg.screenshot(path=str(path))
            pg.close()
            print(rel(path))
        browser.close()
    text = caption_md(folder, spec, files)
    L.check_text(f"{folder.name}/caption.md", text, pats)
    (folder / "caption.md").write_text(text)
    print(rel(folder / "caption.md"))


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] not in ("new", "render"):
        sys.exit(__doc__)
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "new":
        folder = L.POSTS / arg
        if folder.exists():
            sys.exit(f"{folder.relative_to(L.ROOT)} already exists")
        folder.mkdir(parents=True)
        (folder / "post.yaml").write_text(TEMPLATE.format(folder=folder.relative_to(L.ROOT)))
        print(f"edit {(folder / 'post.yaml').relative_to(L.ROOT)}, then render it")
    else:
        folder = Path(arg).resolve()
        if not (folder / "post.yaml").exists():
            sys.exit(f"no post.yaml in {folder}")
        render(folder)


if __name__ == "__main__":
    main()
