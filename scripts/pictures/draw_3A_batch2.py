"""Puppies Reading (3A) word batch 3A-2 pictures (30 words, approved 2026-11-06 by the orchestrator under
user delegation) in the house style.

Run: uv run python scripts/pictures/draw_3A_batch2.py <out_dir> [slug ...]
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
WOOLW, GOOSE, SILVER, NIGHT, HOUSE = "#C9C0B0", "#B4B8BE", "#A9AEB6", "#6A8CCB", "#E8B860"


def cookie(x, y, rad=8):
    return c(x, y, rad, TOAST) + c(x - rad * 0.35, y - rad * 0.2, 1.6, BARK, False) + c(x + rad * 0.3, y + rad * 0.3, 1.6, BARK, False)


def person(x, top, shirt, legs, hair=BROWN, long_hair=False, dress=False):
    """A standing child, front view, about 80 tall."""
    out = ""
    if long_hair:
        out += p(f"M{x - 15} {top + 16} C{x - 18} {top + 34} {x - 14} {top + 42} {x - 8} {top + 40} L{x + 8} {top + 40} "
                 f"C{x + 14} {top + 42} {x + 18} {top + 34} {x + 15} {top + 16} Z", hair)
    out += limb(f"M{x - 6} {top + 62} L{x - 7} {top + 82}", legs, 8) + limb(f"M{x + 6} {top + 62} L{x + 7} {top + 82}", legs, 8)
    out += shoe(x - 9, top + 83) + shoe(x + 9, top + 83, 0, BLUE)
    out += limb(f"M{x - 12} {top + 34} L{x - 22} {top + 54}") + limb(f"M{x + 12} {top + 34} L{x + 22} {top + 54}")
    if dress:
        out += p(f"M{x - 11} {top + 30} C{x - 8} {top + 26} {x + 8} {top + 26} {x + 11} {top + 30} L{x + 20} {top + 66} L{x - 20} {top + 66} Z", shirt)
    else:
        out += p(f"M{x - 13} {top + 32} C{x - 10} {top + 26} {x + 10} {top + 26} {x + 13} {top + 32} L{x + 13} {top + 64} L{x - 13} {top + 64} Z", shirt)
    out += head(x, top + 16, 13, hair=hair)
    return out


PICS = {
    # --- page 41-50: oa, ow, igh ----------------------------------------------------------------
    "road": p("M0 40 L100 40 L100 100 L0 100 Z", GREEN)
          + p("M40 40 L60 40 L92 100 L8 100 Z", GRAY)
          + p("M48.5 46 L51.5 46 L52 54 L48 54 Z M47.5 62 L52.5 62 L53.5 74 L46.5 74 Z M46 84 L54 84 L55.5 100 L44.5 100 Z", GOLD)
          + c(16, 22, 8, GOLD) + c(82, 30, 10, DGREEN) + colored_line("M82 40 L82 48", BARK, 3)
          + r(56, 68, 26, 12, RED, 4) + r(60, 60, 16, 10, RED, 3) + c(62, 81, 4, DARK) + c(76, 81, 4, DARK),
    "toad": e(24, 86, 12, 6, MBROWN) + e(76, 86, 12, 6, MBROWN)
          + e(50, 66, 34, 24, TAN)
          + "".join(c(x, y, 3, MBROWN, False) for x, y in ((30, 60), (44, 54), (62, 56), (72, 66), (38, 72), (58, 74), (24, 70)))
          + c(34, 42, 10, TAN) + c(66, 42, 10, TAN)
          + c(34, 41, 5, GOLD) + c(66, 41, 5, GOLD) + e(34, 41, 2.2, 3.5, "#222", 0, False) + e(66, 41, 2.2, 3.5, "#222", 0, False)
          + line("M36 70 C44 76 56 76 64 70", 2.5)
          + e(36, 90, 6, 4, TAN) + e(64, 90, 6, 4, TAN),
    "loaf": p("M8 70 C6 44 18 30 50 30 C82 30 94 44 92 70 C92 82 86 86 78 86 L22 86 C14 86 8 82 8 70 Z", TOAST)
          + line("M28 44 L36 56 M44 40 L52 52 M60 40 L68 52 M76 44 L82 54", 3, "#B37A3A")
          + line("M16 70 L84 70", 2.5, "#B37A3A")
          + line("M20 46 C24 38 30 36 36 36", 3, "#F0C890"),
    "goal": p("M0 70 L100 70 L100 100 L0 100 Z", GREEN)
          + "".join(line(f"M{x} 26 L{x - 4} 70", 1.8, GRAY) for x in range(18, 88, 8))
          + "".join(line(f"M14 {y} L86 {y}", 1.8, GRAY) for y in range(34, 70, 8))
          + colored_line("M12 74 L12 22 L88 22 L88 74", WOOL, 5)
          + ball(70, 84, 10),
    "oatmeal": colored_line("M70 44 L90 14", GRAY, 4)
             + p("M10 50 L90 50 C88 74 72 90 50 90 C28 90 12 74 10 50 Z", BLUE)
             + e(50, 50, 40, 9, WHEAT)
             + "".join(e(x, y, 2.5, 1.6, "#B88A4E", a, False) for x, y, a in ((30, 49, 20), (44, 52, -10), (58, 48, 30), (70, 51, 0), (38, 47, 0)))
             + c(60, 50, 4, PURPLE) + c(52, 46, 3.5, PURPLE)
             + line("M34 36 C30 28 38 24 34 16 M50 36 C46 28 54 24 50 16", 3, GRAY)
             + line("M18 62 C22 72 30 80 40 84", 3, LBLUE),
    "crow": colored_line("M30 84 L30 96 M70 84 L70 96", BARK, 6) + r(6, 76, 88, 10, MBROWN, 3)
          + line("M40 74 L38 78 M48 74 L48 78", 3)
          + p("M22 58 L4 74 L12 76 L30 64 Z", SLATE)
          + e(44, 56, 22, 16, SLATE, -10)
          + c(66, 36, 13, SLATE)
          + p("M76 32 L94 38 L76 42 Z", DARK)
          + c(68, 33, 2.6, "#222", False) + c(69, 32, 1, WHITE, False)
          + line("M30 52 L46 60 M34 46 L50 54", 2.5, "#606A7C"),
    "bow": p("M50 50 C40 36 18 24 10 32 C4 40 8 62 18 68 C28 74 42 60 50 50 Z", PINK)
         + p("M50 50 C60 36 82 24 90 32 C96 40 92 62 82 68 C72 74 58 60 50 50 Z", PINK)
         + p("M46 54 L34 88 L44 84 L48 92 L52 58 Z", PINK) + p("M54 54 L66 88 L56 84 L52 92 L48 58 Z", PINK)
         + r(42, 42, 16, 16, "#D27B95", 5)
         + line("M22 40 C28 44 34 48 38 50 M78 40 C72 44 66 48 62 50", 2.5, "#C76D88"),
    "light": line("M18 26 L8 20 M14 46 L4 46 M18 66 L8 72 M82 26 L92 20 M86 46 L96 46 M82 66 L92 72 M50 8 L50 2", 3, GOLD)
           + p("M36 70 C36 60 24 54 24 40 C24 24 36 14 50 14 C64 14 76 24 76 40 C76 54 64 60 64 70 Z", GOLD)
           + line("M44 70 L44 52 L50 58 L56 52 L56 70", 2.5, "#B88A0F")
           + r(36, 70, 28, 18, GRAY, 3) + line("M36 76 L64 76 M36 82 L64 82", 2.5)
           + p("M42 88 L58 88 L54 94 L46 94 Z", DARK)
           + line("M32 34 C34 28 38 24 44 22", 3, PALE),
    "night": r(4, 4, 92, 92, NIGHT, 14)
           + p("M62 14 C48 16 42 30 46 42 C50 54 64 58 74 52 C64 54 54 46 54 34 C54 24 58 18 62 14 Z", GOLD)
           + star(20, 22, 6, GOLD) + star(84, 20, 4.5, GOLD) + star(30, 48, 4, GOLD) + star(86, 46, 5, GOLD)
           + p("M18 96 L18 70 L40 54 L62 70 L62 96 Z", TAN) + p("M14 72 L40 50 L66 72", "none")
           + r(26, 74, 12, 12, GOLD, 2) + r(44, 80, 10, 16, MBROWN, 2),
    "rowboat": p("M0 76 C12 70 22 82 34 76 C46 70 56 82 68 76 C80 70 90 82 100 76 L100 100 L0 100 Z", BLUE)
             + colored_line("M14 40 L40 74 M86 40 L60 74", MBROWN, 3)
             + e(12, 38, 4, 8, MBROWN, -40) + e(88, 38, 4, 8, MBROWN, 40)
             + p("M6 58 L94 58 C88 74 74 82 50 82 C26 82 12 74 6 58 Z", RED)
             + line("M12 66 L88 66", 2.5, "#B55757")
             + r(36, 52, 28, 7, TAN, 2),
    # --- page 51-60: bossy r -------------------------------------------------------------------
    "barn": p("M0 90 L100 90 L100 100 L0 100 Z", GREEN)
          + p("M14 90 L14 44 L30 22 L70 22 L86 44 L86 90 Z", RED)
          + p("M10 46 L30 18 L70 18 L90 46 L84 48 L67 25 L33 25 L16 48 Z", GRAY)
          + r(36, 56, 28, 34, "#C95F5F", 2) + line("M36 56 L64 90 M64 56 L36 90", 3, WOOL)
          + r(40, 32, 20, 14, WOOL, 2) + line("M50 32 L50 46", 2.5),
    "jar": r(26, 10, 48, 12, RED, 4)
         + p("M24 24 L76 24 L80 34 L80 86 C80 92 76 94 70 94 L30 94 C24 94 20 92 20 86 L20 34 Z", LBLUE)
         + cookie(36, 80, 10) + cookie(60, 78, 11) + cookie(48, 60, 10) + cookie(68, 56, 8) + cookie(32, 56, 8)
         + line("M28 40 L28 66", 3, WHITE)
         + p("M20 30 L80 30", "none") + line("M22 28 L78 28", 3),
    "yarn": colored_line("M80 70 C90 78 86 90 96 94", BLUE, 3)
          + c(48, 52, 34, BLUE)
          + line("M20 38 C34 50 58 54 80 44 M16 56 C34 66 62 68 82 58 M24 74 C40 80 60 80 76 72 M34 22 C30 40 34 64 46 84 M52 18 C46 38 48 64 60 84", 2.5, DBLUE)
          + colored_line("M10 92 L40 70 M18 96 L46 76", GRAY, 3) + c(10, 92, 3, GOLD) + c(18, 96, 3, GOLD),
    "card": p("M16 22 L52 14 L52 86 L16 92 Z", "#9BC48A")
          + p("M52 14 L86 22 L86 92 L52 86 Z", LBLUE)
          + heart(70, 46, 12, RED)
          + line("M60 70 L78 72 M62 77 L76 78", 2.5, DBLUE)
          + star(32, 40, 6, GOLD) + star(34, 66, 4, GOLD),
    "harp": colored_line("M24 92 L80 92", MBROWN, 5)
          + "".join(line(f"M{x} {94 - (x - 30) * 0.2} L{x} {30 + (x - 30) * 0.55}", 1.8, GRAY) for x in range(34, 76, 7))
          + colored_line("M28 92 L28 20 C30 10 40 10 46 18 C56 30 70 30 80 26 L82 92", GOLD, 6)
          + c(28, 16, 5, GOLD),
    "horn": colored_line("M26 50 L44 50", GRAY, 6)
          + p("M42 42 L78 30 C86 28 92 40 92 50 C92 60 86 72 78 70 L42 58 Z", GOLD)
          + e(86, 50, 6, 18, "#C9900F")
          + line("M50 46 L76 38", 3, PALE)
          + c(18, 50, 14, RED)
          + line("M90 26 L96 18 M94 50 L100 50 M90 74 L96 82", 3, GRAY),
    "fort": colored_line("M12 30 L12 92 M88 30 L88 92 M24 60 L24 92 M76 60 L76 92", MBROWN, 4)
          + p("M4 92 L14 28 C30 20 70 20 86 28 L96 92 L64 92 C62 74 58 64 50 64 C42 64 38 74 36 92 Z", PURPLE)
          + p("M38 92 C40 76 44 68 50 68 C56 68 60 76 62 92 Z", DARK)
          + head(50, 80, 9)
          + line("M24 40 L20 70 M40 34 L38 56 M60 34 L62 56 M76 40 L80 70", 2.5, "#8C72C0")
          + star(30, 50, 4, GOLD) + star(70, 50, 4, GOLD),
    "girl": person(50, 8, PINK, SKIN, BROWN, long_hair=True, dress=True)
          + e(36, 14, 6, 4, PINK) + e(64, 14, 6, 4, PINK),
    "nurse": person(50, 10, LBLUE, LBLUE, GOLD, long_hair=True)
           + p("M38 14 C38 6 62 6 62 14 L60 18 L40 18 Z", WOOL) + heart(50, 12, 3, RED)
           + line("M42 38 C40 52 46 56 50 52 M58 38 C60 52 54 56 50 52", 2.5, DARK) + c(50, 54, 3, GRAY),
    "purse": colored_line("M30 40 C30 12 70 12 70 40", MBROWN, 5)
           + p("M14 42 L86 42 L80 88 C78 92 22 92 20 88 Z", RED)
           + p("M14 42 L86 42 L84 56 C70 62 30 62 16 56 Z", "#D76565")
           + c(50, 58, 5, GOLD)
           + line("M24 72 L76 72", 2.5, "#B55757"),
    # --- page 61-70: ou, ow, oi, oy, oo ------------------------------------------------------------
    "house": p("M0 92 L100 92 L100 100 L0 100 Z", GREEN)
           + r(64, 14, 10, 20, MBROWN, 1)
           + p("M18 92 L18 48 L82 48 L82 92 Z", HOUSE)
           + p("M8 50 L50 12 L92 50 Z", RED)
           + r(42, 64, 16, 28, BLUE, 2) + c(54, 79, 1.8, GOLD, False)
           + r(24, 58, 12, 12, LBLUE, 2) + r(64, 58, 12, 12, LBLUE, 2)
           + line("M30 58 L30 70 M24 64 L36 64 M70 58 L70 70 M64 64 L76 64", 2),
    "coin": c(36, 58, 26, GOLD) + c(36, 58, 19, "none") + star(36, 58, 10, "#F2C54B")
          + c(70, 38, 22, GOLD) + c(70, 38, 16, "none") + star(70, 38, 8, "#F2C54B")
          + line("M20 46 C24 40 28 38 32 38 M58 26 C60 22 64 20 68 20", 3, PALE),
    "oil": r(42, 8, 16, 10, GREEN, 3)
         + p("M44 18 L56 18 L56 30 C70 36 74 46 74 56 L74 88 C74 92 70 94 66 94 L34 94 C30 94 26 92 26 88 L26 56 C26 46 30 36 44 30 Z", GOLD)
         + r(30, 56, 40, 24, WOOLW, 4)
         + e(46, 68, 5, 7, DGREEN, -20) + e(56, 66, 4, 6, GREEN, 20) + line("M50 60 L52 56", 2)
         + line("M32 42 C34 38 38 36 42 34", 3, PALE),
    "boy": person(50, 8, GREEN, BLUE, BROWN),
    "brownie": e(50, 80, 42, 10, LBLUE)
             + p("M14 52 L50 40 L86 52 L86 72 L50 86 L14 72 Z", BROWN)
             + p("M14 52 L50 40 L86 52 L50 64 Z", "#B88A60")
             + line("M50 64 L50 86", 3)
             + c(36, 52, 2, BARK, False) + c(52, 48, 2, BARK, False) + c(64, 54, 2, BARK, False) + c(46, 56, 2, BARK, False)
             + line("M22 60 L22 68 M34 66 L34 72 M66 66 L66 74 M78 60 L78 68", 2, BARK),
    "pool": p("M8 40 L92 40 L98 90 L2 90 Z", WOOL)
          + p("M16 46 L84 46 L88 84 L12 84 Z", LBLUE)
          + line("M20 58 C26 54 32 54 38 58 C44 62 50 62 56 58 M42 72 C48 68 54 68 60 72 C66 76 72 76 78 72", 3, WHITE)
          + colored_line("M70 20 L70 60 M84 20 L84 60", GRAY, 3) + line("M70 30 L84 30 M70 40 L84 40 M70 50 L84 50", 3)
          + c(30, 70, 7, RED) + c(30, 70, 3, LBLUE, False),
    "roof": p("M2 100 L2 66 L98 66 L98 100 Z", HOUSE)
          + r(70, 18, 12, 30, MBROWN, 2)
          + p("M0 70 L50 30 L100 70 Z", RED)
          + line("M14 59 L86 59 M28 48 L72 48 M40 38 L60 38", 2.5, "#B55757")
          + p("M44 30 C40 22 46 16 52 18 C56 14 64 16 62 22 L66 24 L60 26 C58 30 50 32 44 30 Z", BLUE)
          + c(56, 20, 1.6, "#222", False) + line("M50 30 L50 34 M54 30 L54 34", 2.2)
          + r(38, 76, 24, 16, LBLUE, 2) + line("M50 76 L50 92", 2),
    "hoop": colored_line("M50 50 m-38 0 a38 34 0 1 0 76 0 a38 34 0 1 0 -76 0", PURPLE, 9)
          + "".join(line(f"M{50 + 33 * math.cos(a):.1f} {50 + 29 * math.sin(a):.1f} L{50 + 43 * math.cos(a):.1f} {50 + 39 * math.sin(a):.1f}", 4, GOLD)
                    for a in [i * math.pi / 6 for i in range(12)]),
    "goose": e(30, 92, 8, 3, ORANGE) + e(56, 92, 8, 3, ORANGE)
           + line("M34 80 L32 90 M54 80 L56 90", 4, ORANGE)
           + p("M10 60 C10 46 30 40 50 46 C62 50 70 56 70 66 C70 80 50 84 32 82 C18 80 10 72 10 60 Z", GOOSE)
           + p("M4 50 L16 58 L10 66 Z", GOOSE)
           + colored_line("M62 56 C70 40 62 30 66 20", GOOSE, 10)
           + c(70, 18, 9, GOOSE)
           + p("M77 14 L92 20 L77 24 Z", ORANGE)
           + c(72, 15, 2.2, "#222", False)
           + line("M26 58 C34 54 44 54 52 60", 2.5, "#8A8F96"),
    "zoo": p("M0 90 L100 90 L100 100 L0 100 Z", GREEN)
         + "".join(colored_line(f"M{x} 54 L{x} 90", GRAY, 3) for x in range(16, 90, 9))
         + colored_line("M10 62 L90 62", GRAY, 3)
         + r(4, 36, 12, 56, MBROWN, 2) + r(84, 36, 12, 56, MBROWN, 2)
         + p("M4 40 C20 20 80 20 96 40 L96 46 C80 30 20 30 4 46 Z", GREEN)
         + colored_line("M40 60 L44 20", GOLD, 9)
         + e(48, 16, 10, 7, GOLD, -15) + line("M42 10 L40 4 M46 9 L46 3", 3) + c(51, 14, 2, "#222", False)
         + c(42, 34, 2.5, MBROWN, False) + c(44, 46, 2.5, MBROWN, False)
         + c(76, 66, 10, DGREEN) + c(68, 60, 8, DGREEN),
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
