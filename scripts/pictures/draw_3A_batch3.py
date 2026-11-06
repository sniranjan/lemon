"""Puppies Reading (3A) word batch 3A-3 pictures (10 words that replace Puppies words Kittens Reading now owns, approved 2026-11-06 by the orchestrator under
user delegation) in the house style.

Run: uv run python scripts/pictures/draw_3A_batch3.py <out_dir> [slug ...]
A record only: the SVGs in assets/pictures/ are the source of truth (STATUS.md, picture workflow).
Helpers copied from draw_7A_batch5.py.
"""
import math
import sys
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else None
ONLY = set(sys.argv[2:])
S = 'stroke="#222" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"'
RED, ORANGE, GOLD, GREEN, BLUE = "#E87878", "#F0935A", "#E6A817", "#7FBF6A", "#6FA3E0"
PURPLE, TAN, BROWN, PINK, GRAY = "#A88FD8", "#C9A27A", "#A57C52", "#E89AB0", "#A0A4AA"
SKIN, WHEAT, GLASS, DARK = "#D9A27E", "#D8B07A", "#BFE0F5", "#444444"
DBLUE, LBLUE, DGREEN, DIRT, LGRAY = "#5A8FCC", "#8FB8E8", "#5FA34C", "#B08A5E", "#C4C7CC"
WHITE, SLATE, WOOL, PEACH, TOAST = "#F4F1EA", "#7F8A9E", "#C2B8A6", "#F2A585", "#D8A060"
PALE, MBROWN, BARK, TINT = "#F2D16B", "#B48858", "#6B4A2E", "#F6D27A"
# new in this batch
HIPPO, DOLPHIN, PLUM, PICKLE = "#9A93AE", "#7FA7C9", "#A47CC4", "#8DB85A"


def p(d, fill):
    return f'<path d="{d}" fill="{fill}" {S}/>'


def c(cx, cy, r, fill, stroke=True):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"' + (f" {S}/>" if stroke else "/>")


def e(cx, cy, rx, ry, fill, rot=0, stroke=True):
    t = f' transform="rotate({rot} {cx} {cy})"' if rot else ""
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}"' + (f" {S}" if stroke else "") + f"{t}/>"


def r(x, y, w, h, fill, rx=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {S}/>'


def line(d, w=3, color="#222"):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'


def colored_line(d, color, w=5):
    """A thick colored stroke with a dark outline (limbs, handles)."""
    return line(d, w + 6) + line(d, w, color)


def limb(d, color=SKIN, w=7):
    return colored_line(d, color, w)


def eyes(y, x1, x2, rad=3.5):
    return c(x1, y, rad, "#222", False) + c(x2, y, rad, "#222", False)


def head(x, y, rad=13, closed=False, mouth="smile", hair=BROWN):
    """A child's head: skin, short hair, eyes (closed = sleeping curves)."""
    out = c(x, y, rad, SKIN)
    out += p(f"M{x - rad} {y - 1} C{x - rad} {y - rad - 6} {x + rad} {y - rad - 6} {x + rad} {y - 1} "
             f"C{x + rad * 0.5} {y - rad * 0.55} {x - rad * 0.5} {y - rad * 0.55} {x - rad} {y - 1} Z", hair)
    if closed:
        out += line(f"M{x - 7} {y + 2} C{x - 5} {y + 4} {x - 3} {y + 4} {x - 1} {y + 2} "
                    f"M{x + 1} {y + 2} C{x + 3} {y + 4} {x + 5} {y + 4} {x + 7} {y + 2}", 2)
    else:
        out += eyes(y + 2, x - 4.5, x + 4.5, 2.2)
    if mouth == "smile":
        out += line(f"M{x - 4} {y + 7} C{x - 2} {y + 9} {x + 2} {y + 9} {x + 4} {y + 7}", 2)
    elif mouth == "open":
        out += e(x, y + 8, 3, 2.5, "#222", 0, False)
    return out


def palm(x, y, rot, fill=SKIN, s=1.0):
    """A simple open hand: palm + thumb, rotated about its center."""
    body = (p(f"M{x - 8 * s} {y + 12 * s} L{x - 8 * s} {y - 6 * s} C{x - 8 * s} {y - 16 * s} {x + 8 * s} {y - 16 * s} "
              f"{x + 8 * s} {y - 6 * s} L{x + 8 * s} {y + 12 * s} Z", fill)
            + p(f"M{x - 8 * s} {y + 2 * s} C{x - 16 * s} {y - 2 * s} {x - 18 * s} {y + 6 * s} {x - 8 * s} {y + 10 * s} Z", fill))
    return f'<g transform="rotate({rot} {x} {y})">{body}</g>'


def shoe(x, y, rot=0, fill=RED):
    return e(x, y, 7, 4, fill, rot)


def star(x, y, ro, fill, ri=None):
    ri = ri or ro * 0.45
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rad = ro if i % 2 == 0 else ri
        pts.append(f"{x + rad * math.cos(a):.1f} {y + rad * math.sin(a):.1f}")
    return p("M" + " L".join(pts) + " Z", fill)


def heart(x, y, s, fill):
    return p(f"M{x} {y - s * 0.4} C{x - s * 0.5} {y - s * 1.2} {x - s * 1.4} {y - s * 0.4} {x - s * 0.7} {y + s * 0.3} "
             f"L{x} {y + s} L{x + s * 0.7} {y + s * 0.3} C{x + s * 1.4} {y - s * 0.4} {x + s * 0.5} {y - s * 1.2} {x} {y - s * 0.4} Z", fill)


def drop(x, y, s, fill):
    """A water drop, point up."""
    return p(f"M{x} {y - s * 1.6} C{x + s * 0.4} {y - s * 0.8} {x + s} {y - s * 0.2} {x + s} {y + s * 0.3} "
             f"C{x + s} {y + s * 1.1} {x - s} {y + s * 1.1} {x - s} {y + s * 0.3} C{x - s} {y - s * 0.2} {x - s * 0.4} {y - s * 0.8} {x} {y - s * 1.6} Z", fill)


def wheel(x, y, rad):
    return c(x, y, rad, GRAY) + c(x, y, rad * 0.35, DARK)


def ball(x, y, rad=9):
    return c(x, y, rad, BLUE) + line(f"M{x - rad} {y} C{x - rad / 2} {y - rad / 2} {x + rad / 2} {y - rad / 2} {x + rad} {y} "
                                    f"M{x} {y - rad} C{x - rad / 2} {y - rad / 3} {x - rad / 2} {y + rad / 3} {x} {y + rad}", 2.2)


def crayon(color, dark, deco="#222"):
    body = (p("M36 30 L64 30 L64 92 L36 92 Z", color) + p("M36 30 L50 6 L64 30 Z", color)
            + p("M44 16 L50 6 L56 16 Z", dark) + line("M36 42 L64 42 M36 80 L64 80", 3, deco)
            + line("M42 54 C46 50 54 58 58 54 M42 66 C46 62 54 70 58 66", 3, deco))
    return f'<g transform="rotate(30 50 50)">{body}</g>'


def child_face(cx, cy, rx, ry, eyes_kind="open", mouth="smile"):
    """A big front-on child face with ears and hair (for body-part pictures)."""
    out = e(cx - rx, cy + 2, 5, 8, SKIN) + e(cx + rx, cy + 2, 5, 8, SKIN) + e(cx, cy, rx, ry, SKIN)
    out += p(f"M{cx - rx + 1} {cy - 4} C{cx - rx - 2} {cy - ry - 8} {cx + rx + 2} {cy - ry - 8} {cx + rx - 1} {cy - 4} "
             f"C{cx + rx * 0.6} {cy - ry * 0.55} {cx - rx * 0.6} {cy - ry * 0.55} {cx - rx + 1} {cy - 4} Z", BROWN)
    ey = cy - ry * 0.05
    if eyes_kind == "happy":
        out += line(f"M{cx - 14} {ey + 2} C{cx - 12} {ey - 4} {cx - 6} {ey - 4} {cx - 4} {ey + 2} "
                    f"M{cx + 4} {ey + 2} C{cx + 6} {ey - 4} {cx + 12} {ey - 4} {cx + 14} {ey + 2}", 3)
    else:
        out += eyes(ey, cx - 9, cx + 9, 3.2)
    if mouth == "smile":
        out += line(f"M{cx - 7} {cy + ry * 0.42} C{cx - 3} {cy + ry * 0.56} {cx + 3} {cy + ry * 0.56} {cx + 7} {cy + ry * 0.42}", 2.5)
    return out


def ring(cx, cy, ro, ri, fill):
    """A filled ring (bagel), outlined inside and out."""
    return (f'<path d="M{cx - ro} {cy} a{ro} {ro} 0 1 0 {2 * ro} 0 a{ro} {ro} 0 1 0 {-2 * ro} 0 Z '
            f'M{cx - ri} {cy} a{ri} {ri} 0 1 0 {2 * ri} 0 a{ri} {ri} 0 1 0 {-2 * ri} 0 Z" fill="{fill}" fill-rule="evenodd" {S}/>')


def rot(deg, x, y, body):
    return f'<g transform="rotate({deg} {x} {y})">{body}</g>'



# new in Puppies Reading
WOOLW, HOUSE, BRICKISH = "#C9C0B0", "#E8B860", "#C97A5A"


def person(x, top, shirt, legs, hair=BROWN, long_hair=False):
    """A standing grown-up/child, front view, about 80 tall (as in draw_3A_batch2.py)."""
    out = ""
    if long_hair:
        out += p(f"M{x - 15} {top + 16} C{x - 18} {top + 34} {x - 14} {top + 42} {x - 8} {top + 40} L{x + 8} {top + 40} "
                 f"C{x + 14} {top + 42} {x + 18} {top + 34} {x + 15} {top + 16} Z", hair)
    out += limb(f"M{x - 6} {top + 62} L{x - 7} {top + 82}", legs, 8) + limb(f"M{x + 6} {top + 62} L{x + 7} {top + 82}", legs, 8)
    out += shoe(x - 9, top + 83) + shoe(x + 9, top + 83, 0, BLUE)
    out += limb(f"M{x - 12} {top + 34} L{x - 22} {top + 54}")
    out += p(f"M{x - 13} {top + 32} C{x - 10} {top + 26} {x + 10} {top + 26} {x + 13} {top + 32} L{x + 13} {top + 64} L{x - 13} {top + 64} Z", shirt)
    out += head(x, top + 16, 13, hair=hair)
    return out


PICS = {
    # Word Patterns part 1 (letter pairs) and the other swaps for words Kittens Reading now owns
    "shampoo": r(40, 6, 20, 12, PINK, 3) + r(44, 0, 8, 8, PINK, 2)
             + p("M30 22 C30 18 34 16 38 16 L62 16 C66 16 70 18 70 22 L74 86 C74 92 70 94 64 94 L36 94 C30 94 26 92 26 86 Z", PURPLE)
             + r(34, 44, 32, 30, WOOLW, 4)
             + c(44, 54, 4, LBLUE) + c(54, 60, 5, LBLUE) + c(46, 66, 3, LBLUE)
             + c(82, 20, 6, LBLUE) + c(90, 32, 4, LBLUE) + c(16, 30, 5, LBLUE)
             + line("M34 26 C34 22 36 20 40 20", 3, "#C8B6EC"),
    "teacher": r(54, 14, 42, 30, DGREEN, 3) + line("M62 24 L80 24 M62 32 L74 32", 2.5, WHITE)
             + colored_line("M40 46 L58 30", MBROWN, 3)
             + person(30, 12, RED, BLUE, BROWN, long_hair=True)
             + limb("M42 46 L52 36"),
    "chimney": p("M0 100 L0 72 L100 40 L100 100 Z", RED)
             + line("M0 86 L100 56 M30 100 L30 63 M70 100 L70 51", 2.5, "#B55757")
             + r(52, 22, 22, 40, BRICKISH, 2)
             + line("M52 32 L74 32 M52 42 L74 42 M52 52 L74 52 M63 22 L63 32 M58 32 L58 42 M68 42 L68 52", 2.5, "#9A5A3A")
             + r(48, 16, 30, 8, GRAY, 2)
             + line("M60 12 C54 6 66 2 60 -4 M70 12 C64 6 76 2 70 -4", 3, GRAY),
    "chest": p("M12 46 C12 22 88 22 88 46 Z", MBROWN)
           + r(12, 46, 76, 44, MBROWN, 4)
           + colored_line("M30 30 L30 90 M70 30 L70 90", GOLD, 4)
           + r(42, 42, 16, 16, GOLD, 3) + c(50, 50, 2.5, DARK, False)
           + line("M16 62 L84 62 M16 76 L84 76", 2.5, BARK)
           + star(86, 18, 6, GOLD) + star(14, 16, 4, GOLD),
    "thread": e(46, 20, 26, 8, TAN) + e(46, 82, 26, 8, TAN)
            + r(26, 20, 40, 62, BLUE)
            + line("M28 30 L64 26 M28 40 L64 36 M28 50 L64 46 M28 60 L64 56 M28 70 L64 66", 2.5, DBLUE)
            + e(46, 20, 26, 8, TAN) + e(46, 20, 8, 3, BARK, 0, False)
            + colored_line("M66 70 C80 72 90 80 86 92", BLUE, 3),
    "shed": p("M0 90 L100 90 L100 100 L0 100 Z", GREEN)
          + p("M16 90 L16 44 L84 44 L84 90 Z", TAN)
          + line("M28 44 L28 90 M40 44 L40 54 M60 44 L60 54 M72 44 L72 90", 2.5, MBROWN)
          + p("M8 46 L50 16 L92 46 Z", GREEN)
          + r(38, 56, 24, 34, MBROWN, 2) + c(56, 74, 2, GOLD, False)
          + r(66, 56, 12, 12, LBLUE, 2),
    "lake": p("M0 40 L100 40 L100 100 L0 100 Z", GREEN)
          + e(50, 70, 46, 20, BLUE)
          + line("M24 66 C28 63 32 63 36 66 M56 74 C60 71 64 71 68 74 M40 80 C44 77 48 77 52 80", 2.5, WHITE)
          + p("M10 40 L22 14 L34 40 Z", DGREEN) + p("M70 40 L82 8 L94 40 Z", DGREEN)
          + c(50, 20, 8, GOLD)
          + e(70, 64, 7, 4, GOLD) + c(76, 59, 3.5, GOLD) + p("M79 58 L83 59 L79 61 Z", ORANGE),
    "spray": p("M30 40 L58 40 L62 92 L26 92 Z", GREEN)
           + r(34, 56, 24, 22, WOOLW, 3)
           + p("M34 40 L36 26 L56 26 L58 40 Z", BLUE)
           + p("M36 26 L36 14 L64 14 L70 20 L56 26 Z", BLUE)
           + colored_line("M54 28 C60 34 58 38 56 40", BLUE, 3)
           + "".join(c(x, y, 2.2, LBLUE) for x, y in ((76, 12), (82, 20), (78, 26), (88, 14), (90, 26), (84, 32), (94, 20))),
    "mower": colored_line("M70 70 L90 20", GRAY, 4) + colored_line("M82 18 L98 24", DARK, 5)
           + p("M10 74 C10 58 24 52 44 52 C64 52 76 58 78 74 Z", RED)
           + r(6, 70, 76, 10, RED, 4)
           + wheel(20, 84, 9) + wheel(68, 84, 9)
           + r(30, 44, 22, 10, DARK, 3)
           + line("M0 96 L100 96", 3) + line("M86 96 L84 90 M92 96 L94 90", 2.5, DGREEN),
    "guitar": rot(-35, 50, 50,
                  r(44, 2, 12, 46, MBROWN, 3) + r(41, 0, 18, 10, BARK, 3)
                  + c(50, 62, 18, ORANGE) + c(50, 80, 22, ORANGE)
                  + '<path d="M50 44 m-17 0 L67 44" fill="none"/>'
                  + c(50, 70, 7, DARK, False)
                  + r(42, 86, 16, 5, BARK, 2)
                  + line("M47 6 L47 88 M50 6 L50 88 M53 6 L53 88", 1.2, WOOL)),
}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for slug, body in PICS.items():
        if ONLY and slug not in ONLY:
            continue
        (OUT / f"{slug}.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{body}</svg>\n')
        n += 1
    print(n, "pictures written")
