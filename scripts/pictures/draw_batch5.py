"""Ducklings word batch 2 pictures (40 words, approved 2026-11-06) in the house style.

Run: uv run python scripts/pictures/draw_batch5.py <out_dir> [slug ...]
A record only: the SVGs in assets/pictures/ are the source of truth (STATUS.md, picture workflow).
Helpers copied from draw_batch4.py.
"""
import math
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2:])
S = 'stroke="#222" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"'
RED, ORANGE, GOLD, GREEN, BLUE = "#E87878", "#F0935A", "#E6A817", "#7FBF6A", "#6FA3E0"
PURPLE, TAN, BROWN, PINK, GRAY = "#A88FD8", "#C9A27A", "#A57C52", "#E89AB0", "#A0A4AA"
SKIN, WHEAT, GLASS, DARK = "#D9A27E", "#D8B07A", "#BFE0F5", "#444444"
DBLUE, LBLUE, DGREEN, DIRT, LGRAY = "#5A8FCC", "#8FB8E8", "#5FA34C", "#B08A5E", "#C4C7CC"
# new in this batch
WHITE, SLATE, WOOL, PEACH, TOAST = "#F4F1EA", "#7F8A9E", "#C2B8A6", "#F2A585", "#D8A060"
PALE = "#F2D16B"   # butter


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


def moon(x, y, s, fill):
    return p(f"M{x} {y - s} C{x - s * 1.4} {y - s * 0.6} {x - s * 1.4} {y + s * 0.6} {x} {y + s} "
             f"C{x - s * 0.6} {y + s * 0.4} {x - s * 0.6} {y - s * 0.4} {x} {y - s} Z", fill)


def drop(x, y, s, fill):
    """A water drop, point up."""
    return p(f"M{x} {y - s * 1.6} C{x + s * 0.4} {y - s * 0.8} {x + s} {y - s * 0.2} {x + s} {y + s * 0.3} "
             f"C{x + s} {y + s * 1.1} {x - s} {y + s * 1.1} {x - s} {y + s * 0.3} C{x - s} {y - s * 0.2} {x - s * 0.4} {y - s * 0.8} {x} {y - s * 1.6} Z", fill)


def rays(x, y, rin, rout, angles, color=GRAY):
    """Short gray lines around a point: 'look here' (as on knee and finger)."""
    d = " ".join(f"M{x + rin * math.cos(math.radians(a)):.1f} {y + rin * math.sin(math.radians(a)):.1f} "
                 f"L{x + rout * math.cos(math.radians(a)):.1f} {y + rout * math.sin(math.radians(a)):.1f}" for a in angles)
    return line(d, 3, color)


def wheel(x, y, rad):
    return c(x, y, rad, GRAY) + c(x, y, rad * 0.35, DARK)


def ball(x, y, rad=9):
    return c(x, y, rad, BLUE) + line(f"M{x - rad} {y} C{x - rad / 2} {y - rad / 2} {x + rad / 2} {y - rad / 2} {x + rad} {y} "
                                    f"M{x} {y - rad} C{x - rad / 2} {y - rad / 3} {x - rad / 2} {y + rad / 3} {x} {y + rad}", 2.2)


def wagon_body(x, y):
    """The red toy wagon, its back at x, its top at y (54 wide)."""
    return (wheel(x + 12, y + 30, 9) + wheel(x + 44, y + 30, 9)
            + r(x, y, 56, 22, RED, 3) + line(f"M{x + 4} {y + 8} L{x + 52} {y + 8}", 2.5))


PICS = {
    # --- animals -----------------------------------------------------------------------------
    "zebra": line("M80 48 C88 54 88 62 86 68", 3) + p("M84 66 L90 74 L82 74 Z", DARK)
           + limb("M66 62 L68 90", GRAY, 7) + limb("M38 62 L36 90", GRAY, 7)
           + e(56, 52, 26, 15, GRAY)
           + line("M44 40 C42 46 42 56 44 64 M52 38 C50 46 50 56 52 66 M60 38 C58 46 58 56 60 66 "
                  "M68 40 C66 46 66 54 68 62 M76 46 C74 50 74 56 76 58", 3.5, DARK)
           + limb("M72 62 L74 90", GRAY, 7) + limb("M44 62 L42 90", GRAY, 7)
           + line("M36 78 L44 78 M66 78 L74 78 M38 86 L46 86 M68 86 L76 86", 2.5, DARK)
           + p("M30 52 L22 24 L36 20 L46 46 Z", GRAY)
           + line("M27 30 L36 28 M29 38 L39 36 M32 46 L42 44", 3.5, DARK)
           + colored_line("M27 14 L37 20 L46 42", DARK, 5)
           + p("M18 14 L20 4 L26 12 Z", GRAY) + p("M24 14 L30 6 L32 16 Z", GRAY)
           + e(18, 28, 9, 15, GRAY, 35)
           + line("M17 18 L24 21 M14 24 L22 28 M12 30 L19 34", 3, DARK)
           + e(11, 38, 6, 5.5, DARK, 35)
           + c(22, 22, 2.8, "#222", False),
    "tiger": line("M80 52 C92 46 94 30 88 24", 9) + line("M80 52 C92 46 94 30 88 24", 4, ORANGE)
           + line("M91 36 L86 34 M92 28 L87 28", 2.5)
           + limb("M66 66 L68 90", ORANGE, 9) + limb("M44 66 L42 90", ORANGE, 9)
           + e(60, 58, 26, 15, ORANGE)
           + line("M54 44 L56 54 M62 43 L63 53 M70 45 L70 54 M78 50 L76 57 M58 72 L60 64 M68 72 L68 64", 3.5, DARK)
           + limb("M74 66 L76 90", ORANGE, 9) + limb("M50 66 L50 90", ORANGE, 9)
           + e(50, 91, 6, 3.5, ORANGE) + e(77, 91, 6, 3.5, ORANGE)
           + c(14, 26, 6, ORANGE) + c(40, 26, 6, ORANGE) + c(14, 26, 2.5, PINK, False) + c(40, 26, 2.5, PINK, False)
           + c(27, 42, 18, ORANGE)
           + line("M27 25 L27 31 M21 26 L22 30 M33 26 L32 30 M10 40 L16 41 M10 46 L16 45 M44 40 L38 41 M44 46 L38 45", 2.8, DARK)
           + e(27, 50, 9, 7, WHITE)
           + eyes(38, 21, 33, 3) + p("M24 45 L30 45 L27 49 Z", PINK)
           + line("M27 49 L27 52 M23 53 C25 55 27 55 27 52 C27 55 29 55 31 53", 2),
    "giraffe": line("M18 56 C12 62 12 70 14 74", 3) + p("M12 72 L16 80 L10 78 Z", BROWN)
             + limb("M26 66 L24 96", GOLD, 7) + limb("M50 66 L52 96", GOLD, 7)
             + e(38, 58, 22, 13, GOLD)
             + p("M50 54 L64 18 L74 22 L62 62 Z", GOLD)
             + limb("M32 66 L32 96", GOLD, 7) + limb("M56 64 L60 96", GOLD, 7)
             + "".join(e(x, y, rx, ry, BROWN, rot, False) for x, y, rx, ry, rot in
                       ((26, 54, 5, 4, 10), (38, 52, 5, 4, -10), (50, 56, 4, 4, 0), (32, 63, 4, 3, 0), (44, 63, 4, 3, 0),
                        (58, 44, 3, 4, 20), (63, 32, 3, 4, 20), (66, 46, 2.5, 3.5, 20), (60, 54, 3, 3, 0)))
             + line("M66 14 L64 6 M74 14 L76 6", 3) + c(64, 5, 3, BROWN) + c(76, 5, 3, BROWN)
             + e(60, 16, 6, 3, GOLD, -30)
             + e(78, 20, 13, 8, GOLD, 25)
             + c(86, 26, 1.8, "#222", False) + c(75, 15, 2.6, "#222", False)
             + line("M84 30 C86 31 88 30 89 28", 2),
    "hen": line("M44 80 L44 94 M38 96 L44 94 L48 97 M58 80 L58 94 M52 96 L58 94 L62 97", 3, "#222")
         + line("M44 80 L44 94 M58 80 L58 94", 2, GOLD)
         + p("M74 50 C78 30 86 22 92 24 C90 32 92 40 86 50 C94 44 96 56 88 62 Z", BROWN)
         + e(56, 62, 26, 20, TAN)
         + p("M44 58 C52 52 68 54 72 64 C66 74 52 74 44 66 Z", BROWN)
         + line("M54 62 C58 64 62 64 66 62 M52 68 C56 70 62 70 66 68", 2)
         + c(30, 38, 13, TAN)
         + p("M24 26 C22 18 28 16 30 22 C30 14 38 14 36 22 C40 18 44 22 40 28 Z", RED)
         + p("M18 38 L8 42 L18 46 Z", GOLD)
         + p("M18 46 C16 52 20 56 24 52 L22 46 Z", RED)
         + c(28, 35, 2.8, "#222", False),
    "ant": line("M36 58 L28 74 L22 80 M42 60 L42 78 L38 86 M48 58 L58 74 L64 80", 3)
         + line("M18 40 L10 26 L4 24 M24 40 L26 24 L22 18", 3) + c(4, 24, 2.5, "#222", False) + c(22, 18, 2.5, "#222", False)
         + e(72, 54, 22, 16, RED)
         + e(43, 54, 9, 7, RED)
         + c(22, 50, 12, RED)
         + c(20, 47, 2.8, "#222", False) + line("M14 54 C16 57 20 57 22 55", 2)
         + line("M66 44 C64 50 64 58 66 64 M78 42 C76 50 76 58 78 66", 2.5),
    "seal": p("M4 86 C20 80 40 84 50 86 C64 88 80 84 96 86 L96 96 L4 96 Z", LBLUE)
          + p("M82 74 L96 62 L94 76 Z", GRAY) + p("M82 76 L96 84 L86 86 Z", GRAY)
          + p("M86 78 C70 86 42 86 30 74 C20 64 18 50 22 40 C26 26 44 24 50 36 C54 50 62 64 86 72 Z", GRAY)
          + p("M38 70 C42 80 52 84 54 78 C50 74 46 70 44 66 Z", GRAY)
          + c(32, 32, 2.8, "#222", False) + c(44, 33, 2.8, "#222", False)
          + e(39, 41, 4, 3, "#222", 0, False)
          + line("M33 44 L22 42 M33 46 L22 48 M45 44 L56 42 M45 46 L56 48", 1.8)
          + line("M36 47 C38 49 40 49 42 47", 2),
    "penguin": e(40, 92, 9, 4, ORANGE) + e(60, 92, 9, 4, ORANGE)
             + e(22, 60, 7, 18, SLATE, 20) + e(78, 60, 7, 18, SLATE, -20)
             + e(50, 54, 28, 38, SLATE)
             + e(50, 64, 16, 24, WHITE)
             + c(41, 32, 5, WHITE) + c(59, 32, 5, WHITE) + c(42, 33, 2.6, "#222", False) + c(58, 33, 2.6, "#222", False)
             + p("M44 40 L56 40 L50 48 Z", ORANGE),
    "lamb": line("M30 82 C36 86 40 86 46 82 M60 84 C66 88 70 88 76 84", 2.5, GRAY)
          + limb("M44 60 L40 72 L34 74", WOOL, 5) + limb("M72 60 L76 72 L82 74", WOOL, 5)
          + "".join(c(x, y, 11, WOOL) for x, y in ((48, 40), (60, 36), (72, 42), (76, 54), (64, 60), (50, 58), (42, 50)))
          + e(60, 48, 18, 12, WOOL, 0, False)
          + limb("M52 62 L54 74 L48 78", WOOL, 5) + limb("M64 64 L68 76 L64 80", WOOL, 5)
          + c(48, 79, 2.5, "#222", False) + c(64, 81, 2.5, "#222", False) + c(34, 74, 2.5, "#222", False) + c(82, 74, 2.5, "#222", False)
          + e(12, 34, 8, 4, PINK, -20) + e(36, 30, 8, 4, PINK, 20)
          + e(24, 40, 11, 13, "#E4D8C4")
          + c(20, 27, 5, WOOL) + c(28, 26, 5, WOOL)
          + eyes(38, 20, 29, 2.6) + e(24, 47, 3, 2, PINK, 0, False)
          + line("M21 50 C23 52 25 52 27 50", 2),
    # --- actions: a child doing it -------------------------------------------------------
    "hug": heart(84, 18, 7, PINK) + heart(16, 24, 5, PINK)
         + limb("M44 82 L42 96", BLUE, 9) + limb("M56 82 L58 96", BLUE, 9)
         + p("M34 38 C34 32 66 32 66 38 L68 84 L32 84 Z", RED)
         + c(40, 50, 6, TAN) + c(60, 50, 6, TAN) + c(40, 50, 2.5, WHEAT, False) + c(60, 50, 2.5, WHEAT, False)
         + c(50, 62, 13, TAN) + e(50, 67, 6.5, 5, WHEAT)
         + c(45, 59, 2, "#222", False) + c(55, 59, 2, "#222", False) + e(50, 65, 2.2, 1.6, "#222", 0, False)
         + limb("M36 40 C26 56 30 74 46 76") + limb("M64 40 C74 56 70 74 54 76")
         + head(50, 22, 14, closed=True),
    "push": line("M8 94 L96 94", 3)
          + wagon_body(40, 54)
          + limb("M16 66 L8 80 L6 92", BLUE, 8) + limb("M22 66 L32 78 L30 92", BLUE, 8)
          + shoe(6, 92, -10) + shoe(34, 92)
          + limb("M30 44 L36 54 L42 58")
          + p("M14 64 L22 40 C24 34 36 36 36 42 L28 68 Z", GREEN)
          + limb("M32 46 L38 56 L44 60")
          + head(32, 24, 12)
          + line("M80 44 L94 44 M84 38 L96 38", 2.5, GRAY),
    "throw": line("M6 94 L94 94", 3)
           + line("M58 12 C66 4 76 6 80 12", 2.5, GRAY) + line("M60 20 C66 16 72 16 76 20", 2.5, GRAY)
           + ball(88, 22, 9)
           + limb("M36 64 L26 78 L20 92", BLUE, 8) + limb("M44 64 L54 78 L60 92", BLUE, 8)
           + shoe(18, 92) + shoe(64, 92)
           + limb("M34 42 L24 52 L16 60")
           + p("M32 40 C32 34 48 34 48 40 L48 66 L32 66 Z", GOLD)
           + limb("M46 42 L54 30 L52 14")
           + palm(52, 12, 10, s=0.6)
           + head(40, 24, 12),
    "catch": line("M6 94 L94 94", 3)
           + line("M86 30 L96 26 M88 40 L98 40 M86 50 L96 54", 2.5, GRAY)
           + limb("M30 64 L22 78 L18 92", BLUE, 8) + limb("M40 64 L48 78 L50 92", BLUE, 8)
           + shoe(16, 92) + shoe(54, 92)
           + limb("M30 42 L48 40 L62 34")
           + p("M26 40 C26 34 42 34 42 40 L44 66 L26 66 Z", PURPLE)
           + ball(72, 44, 11)
           + limb("M38 46 L52 56 L64 56")
           + c(64, 33, 5.5, SKIN) + c(65, 56, 5.5, SKIN)
           + head(34, 22, 12, mouth="open"),
    "crawl": line("M4 88 L96 88", 3)
           + limb("M44 58 L44 84 L16 84", DBLUE, 9) + shoe(12, 82, 0)
           + limb("M58 60 L60 84", SKIN, 7) + c(62, 85, 4, SKIN)
           + limb("M40 58 L38 84 L10 82", BLUE, 9) + shoe(8, 80, -10)
           + p("M36 48 C36 40 72 40 74 48 L74 62 C60 66 46 66 36 62 Z", GREEN)
           + limb("M68 58 L72 84", SKIN, 7) + c(74, 85, 4.5, SKIN)
           + head(80, 40, 13),
    "splash": e(50, 86, 42, 9, LBLUE)
            + line("M26 86 C34 90 46 90 54 86 M60 88 C66 90 72 90 76 88", 2.5, DBLUE)
            + drop(14, 64, 4, LBLUE) + drop(22, 52, 3.5, LBLUE) + drop(10, 48, 3, LBLUE)
            + drop(86, 64, 4, LBLUE) + drop(78, 52, 3.5, LBLUE) + drop(90, 46, 3, LBLUE)
            + p("M20 82 C22 72 26 70 30 78 C32 70 36 70 36 80 Z", LBLUE)
            + p("M64 80 C64 70 68 70 70 78 C74 70 78 72 80 82 Z", LBLUE)
            + limb("M44 60 L38 70 L42 78", BLUE, 8) + limb("M56 60 L62 70 L58 78", BLUE, 8)
            + r(34, 70, 12, 14, GOLD, 3) + r(54, 70, 12, 14, GOLD, 3)
            + limb("M40 36 L28 30 L24 16") + limb("M60 36 L72 30 L76 16")
            + p("M40 32 C40 26 60 26 60 32 L66 64 L34 64 Z", RED) + line("M50 32 L50 62", 2.5)
            + head(50, 17, 12, mouth="open"),
    # --- food --------------------------------------------------------------------------------
    "peach": line("M50 22 L52 12", 4, BROWN)
           + p("M52 14 C60 4 76 6 80 12 C72 20 60 20 52 14 Z", GREEN) + line("M54 14 C62 12 70 12 78 12", 2)
           + p("M50 24 C34 14 10 24 12 52 C14 78 32 92 50 92 C68 92 86 78 88 52 C90 24 66 14 50 24 Z", PEACH)
           + p("M62 30 C76 30 82 44 80 56 C72 52 64 42 62 30 Z", PINK)
           + line("M50 26 C42 44 42 70 50 90", 2.5),
    "muffin": p("M24 56 L76 56 L68 94 L32 94 Z", BLUE)
            + line("M34 58 L38 92 M44 58 L46 92 M56 58 L54 92 M66 58 L62 92", 2.5)
            + p("M16 58 C12 34 30 18 50 18 C70 18 88 34 84 58 C70 64 30 64 16 58 Z", TAN)
            + "".join(c(x, y, 4, PURPLE) for x, y in ((34, 36), (52, 28), (66, 40), (42, 50), (60, 54), (24, 50), (74, 54))),
    "toast": p("M14 94 L14 44 C2 40 4 8 28 10 C40 2 60 2 72 10 C96 8 98 40 86 44 L86 94 Z", BROWN)
           + p("M22 88 L22 40 C12 36 12 16 30 17 C42 10 58 10 70 17 C88 16 88 36 78 40 L78 88 Z", TOAST)
           + f'<g transform="rotate(-12 50 54)">{r(36, 42, 26, 20, PALE, 4)}</g>'
           + line("M30 76 L40 76 M58 80 L68 78 M34 30 L42 28", 2.5, BROWN),
    "pancake": e(50, 86, 44, 8, BLUE)
             + r(14, 66, 72, 16, TAN, 8) + r(16, 52, 68, 16, TAN, 8) + r(18, 38, 64, 16, TAN, 8)
             + e(50, 40, 30, 5, WHEAT)
             + p("M30 40 C30 34 70 34 70 40 L70 48 C68 52 66 52 66 46 L64 42 C60 44 58 50 56 50 C54 50 54 44 50 42 "
                 "C44 44 42 56 38 56 C34 56 36 46 32 44 Z", BROWN)
             + f'<g transform="rotate(-8 50 30)">{r(42, 24, 16, 11, PALE, 2)}</g>',
    "yogurt": colored_line("M56 34 L78 4", GRAY, 5)
            + p("M22 30 L78 30 L70 92 L30 92 Z", PINK)
            + e(50, 30, 28, 6, WHITE)
            + line("M42 30 C46 26 52 34 58 29", 2.5, LGRAY)
            + line("M25 48 L75 48 M28 76 L72 76", 2.5)
            + p("M50 54 C60 54 62 62 58 68 C55 72 52 74 50 74 C48 74 45 72 42 68 C38 62 40 54 50 54 Z", RED)
            + p("M44 54 L50 50 L56 54 L50 57 Z", GREEN)
            + c(46, 62, 1.2, "#222", False) + c(54, 62, 1.2, "#222", False) + c(50, 67, 1.2, "#222", False),
    "peas": p("M6 50 C18 24 70 18 94 36 C86 64 34 82 6 50 Z", GREEN)
          + p("M14 50 C28 34 64 30 86 40 C76 58 36 68 14 50 Z", DGREEN)
          + "".join(c(x, y, 7.5, GREEN) for x, y in ((24, 50), (38, 48), (52, 46), (66, 44), (78, 42)))
          + line("M94 36 C96 30 92 26 88 26", 3)
          + c(30, 82, 7, GREEN) + c(46, 86, 7, GREEN),
    # --- toys ------------------------------------------------------------------------------
    "crayon": line("M10 86 C16 62 26 62 28 78 C30 94 40 92 44 74 C48 56 58 58 60 76 C62 92 74 90 78 72 C80 62 88 62 92 70", 5, RED)
            + f'<g transform="rotate(-14 50 34)">'
            + p("M6 22 L74 22 L74 46 L6 46 Z", RED)
            + p("M74 22 L96 34 L74 46 Z", RED) + p("M89 30 L96 34 L89 38 Z", "#222")
            + r(18, 22, 44, 24, RED, 0)
            + line("M26 22 L26 46 M54 22 L54 46", 3)
            + "</g>",
    "wagon": colored_line("M24 60 L10 34", DARK, 3) + colored_line("M5 32 L14 38", DARK, 4)
           + wheel(36, 82, 11) + wheel(76, 82, 11)
           + r(22, 48, 70, 26, RED, 4) + line("M26 58 L88 58", 2.5),
    "sled": line("M4 90 C24 84 40 92 60 88 C76 84 88 90 96 86", 3, GRAY)
          + colored_line("M28 58 L26 74 M70 58 L72 74", RED, 4)
          + colored_line("M10 76 L74 76 C90 76 94 60 84 54", RED, 4)
          + r(14, 46, 70, 12, TAN, 4) + line("M32 46 L32 58 M50 46 L50 58 M68 46 L68 58", 2.5)
          + line("M84 52 C92 36 76 30 66 38", 3, BROWN),
    # --- home ------------------------------------------------------------------------------
    "blanket": p("M24 62 L90 62 L90 90 L24 90 C10 90 10 62 24 62 Z", GREEN)
             + line("M40 62 L40 90 M64 62 L64 90 M24 76 L90 76", 4, DGREEN)
             + line("M22 66 C16 70 16 82 22 86", 2.5)
             + p("M20 32 L86 32 L86 60 L20 60 C6 60 6 32 20 32 Z", GREEN)
             + line("M36 32 L36 60 M60 32 L60 60 M20 46 L86 46", 4, DGREEN)
             + line("M18 36 C12 40 12 52 18 56", 2.5)
             + p("M86 32 L86 60 L72 32 Z", GOLD)
             + line("M90 66 L94 66 M90 72 L94 72 M90 78 L94 78 M90 84 L94 84", 2.5),
    "window": colored_line("M6 10 L94 10", BROWN, 3)
            + r(16, 16, 68, 64, WHEAT, 3)
            + r(22, 22, 26, 26, LBLUE, 2) + r(52, 22, 26, 26, LBLUE, 2) + r(22, 52, 26, 24, LBLUE, 2) + r(52, 52, 26, 24, LBLUE, 2)
            + line("M28 34 L36 26 M28 42 L42 28 M58 64 L66 56 M58 72 L72 58", 3, WHITE)
            + p("M8 10 L18 10 C22 30 14 50 20 84 L8 84 Z", RED) + p("M92 10 L82 10 C78 30 86 50 80 84 L92 84 Z", RED)
            + r(10, 80, 80, 8, WHEAT, 2),
    "oven": r(14, 8, 72, 86, GRAY, 6)
          + line("M14 24 L86 24", 3)
          + c(26, 16, 3.5, "#222", False) + c(40, 16, 3.5, "#222", False) + c(60, 16, 3.5, "#222", False) + c(74, 16, 3.5, "#222", False)
          + colored_line("M28 34 L72 34", LGRAY, 4)
          + r(24, 42, 52, 38, ORANGE, 4)
          + line("M28 66 L72 66", 2.5)
          + line("M38 60 C34 54 42 50 38 46 M50 60 C46 54 54 50 50 46 M62 60 C58 54 66 50 62 46", 2.5, "#7A2E2E")
          + r(20, 90, 10, 6, DARK, 1) + r(70, 90, 10, 6, DARK, 1),
    "pot": line("M34 20 C28 14 40 8 34 2 M50 18 C44 12 56 6 50 0 M66 20 C60 14 72 8 66 2", 3, GRAY)
         + colored_line("M18 50 L6 48 M82 50 L94 48", DARK, 4)
         + p("M18 44 L82 44 L78 86 C78 92 74 94 68 94 L32 94 C26 94 22 92 22 86 Z", RED)
         + p("M14 42 C14 26 86 26 86 42 Z", GRAY) + c(50, 26, 5, DARK)
         + line("M26 60 L74 60", 2.5),
    "fridge": r(22, 4, 56, 90, LBLUE, 6)
            + line("M22 34 L78 34", 3)
            + colored_line("M30 14 L30 26 M30 44 L30 64", GRAY, 3)
            + star(62, 18, 6, GOLD) + heart(64, 50, 5, RED)
            + r(52, 62, 16, 18, WHITE, 1) + c(60, 68, 2.5, GOLD, False) + line("M55 77 L65 77", 2, GREEN)
            + r(26, 94, 8, 4, DARK, 1) + r(66, 94, 8, 4, DARK, 1),
    # --- clothes ---------------------------------------------------------------------------
    "cap": p("M22 70 C24 72 76 72 78 70 C86 76 90 88 84 92 C64 98 36 98 16 92 C10 88 14 76 22 70 Z", DBLUE)
         + p("M14 66 C10 26 34 14 50 14 C66 14 90 26 86 66 C70 74 30 74 14 66 Z", BLUE)
         + line("M50 14 L50 70 M34 18 C26 34 26 56 30 70 M66 18 C74 34 74 56 70 70", 2.5)
         + c(50, 14, 4, DBLUE),
    "sweater": p("M30 14 L42 12 C44 20 56 20 58 12 L70 14 L86 26 L94 78 L80 82 L72 44 L72 90 L28 90 L28 44 L20 82 L6 78 L14 26 Z", GREEN)
             + p("M40 12 C42 24 58 24 60 12", "none")
             + r(28, 80, 44, 10, GREEN, 2) + line("M34 80 L34 90 M40 80 L40 90 M46 80 L46 90 M52 80 L52 90 M58 80 L58 90 M64 80 L64 90", 2)
             + line("M8 70 L21 74 M7 75 L20 79 M79 74 L92 70 M80 79 L93 75", 2)
             + line("M28 50 L36 42 L44 50 L52 42 L60 50 L68 42 L72 46", 4, WHITE)
             + line("M28 58 L72 58", 3, DGREEN),
    "pajamas": limb("M42 60 L40 94 M58 60 L60 94", BLUE, 14)
             + p("M36 56 L64 56 L66 70 L34 70 Z", BLUE)
             + p("M30 8 L42 6 L50 14 L58 6 L70 8 L86 20 L92 44 L80 48 L72 30 L72 64 L28 64 L28 30 L20 48 L8 44 L14 20 Z", BLUE)
             + line("M50 14 L50 64", 2.5) + c(50, 26, 2, "#222", False) + c(50, 38, 2, "#222", False) + c(50, 50, 2, "#222", False)
             + star(38, 26, 5, GOLD) + moon(64, 40, 5, GOLD) + star(36, 52, 4, GOLD) + star(80, 34, 3.5, GOLD)
             + star(40, 80, 3.5, GOLD) + moon(62, 84, 4, GOLD),
    "shorts": p("M16 28 L84 28 L92 80 L58 84 L50 50 L42 84 L8 80 Z", RED)
            + r(16, 16, 68, 12, RED, 3)
            + line("M46 28 C44 36 40 38 38 42 M54 28 C56 36 60 38 62 42", 2.5)
            + line("M10 72 L44 76 M56 76 L90 72", 2.5),
    # --- nature ------------------------------------------------------------------------------
    "sand": p("M2 88 C12 58 30 38 50 38 C70 38 88 58 98 88 Z", WHEAT)
          + "".join(c(x, y, 1.6, BROWN, False) for x, y in
                    ((40, 48), (54, 46), (62, 52), (30, 58), (46, 58), (70, 62), (24, 72), (38, 68), (54, 66),
                     (66, 74), (80, 76), (16, 82), (32, 80), (48, 78), (62, 84), (86, 84), (76, 66), (44, 86)))
          + line("M0 90 L100 90", 3)
          + colored_line("M62 34 L74 10", BROWN, 4) + p("M70 6 L80 10 L78 14 L68 10 Z", BROWN)
          + p("M54 40 L68 40 L66 48 C62 50 58 50 56 48 Z", RED),
    "shell": p("M50 88 L16 44 C12 26 30 10 50 10 C70 10 88 26 84 44 Z", PINK)
           + line("M50 86 L28 18 M50 86 L40 12 M50 86 L60 12 M50 86 L72 18 M50 86 L20 32 M50 86 L80 32", 2.5)
           + p("M50 84 L40 82 L42 92 L50 92 Z", PINK) + p("M50 84 L60 82 L58 92 L50 92 Z", PINK),
    "grass": p("M8 84 L10 50 L18 80 L22 30 L30 78 L38 20 L44 76 L52 34 L56 78 L64 22 L70 76 L78 38 L82 78 L90 46 L92 84 Z", GREEN)
           + line("M22 74 L22 44 M38 72 L38 34 M64 72 L64 36", 2, DGREEN)
           + r(4, 82, 92, 12, DIRT, 4),
    "puddle": drop(24, 14, 4, LBLUE) + drop(50, 8, 4, LBLUE) + drop(76, 18, 4, LBLUE) + drop(38, 34, 3.5, LBLUE) + drop(66, 38, 3.5, LBLUE)
            + p("M10 74 C6 62 22 56 36 60 C46 50 66 52 72 60 C88 56 98 66 92 76 C96 88 76 92 62 88 C50 94 30 94 22 88 C10 90 4 82 10 74 Z", LBLUE)
            + line("M26 70 C32 66 44 66 50 70 M32 76 C36 74 40 74 44 76 M60 80 C64 77 72 77 76 80", 2.5, DBLUE),
    "ice": star(14, 18, 6, WHITE) + star(86, 14, 5, WHITE)
         + p("M10 60 L34 52 L56 60 L32 68 Z", GLASS) + p("M10 60 L32 68 L32 94 L10 86 Z", LBLUE) + p("M32 68 L56 60 L56 86 L32 94 Z", DBLUE)
         + p("M50 60 L72 52 L92 60 L70 68 Z", GLASS) + p("M50 60 L70 68 L70 94 L50 86 Z", LBLUE) + p("M70 68 L92 60 L92 86 L70 94 Z", DBLUE)
         + p("M30 30 L52 22 L74 30 L52 38 Z", GLASS) + p("M30 30 L52 38 L52 64 L30 56 Z", LBLUE) + p("M52 38 L74 30 L74 56 L52 64 Z", DBLUE)
         + line("M16 70 L16 80 M36 40 L36 50 M56 70 L56 80", 3, WHITE),
    # --- body ------------------------------------------------------------------------------
    "toe": rays(36, 20, 15, 22, (-160, -125, -90, -55, -20))
         + p("M14 100 C8 70 12 48 22 40 C40 34 70 34 84 46 C94 60 92 84 88 100 Z", SKIN)
         + e(34, 30, 15, 17, SKIN)
         + e(56, 30, 8.5, 10, SKIN) + e(70, 36, 7, 8.5, SKIN) + e(81, 45, 6, 7, SKIN) + e(89, 56, 5, 6, SKIN)
         + e(34, 22, 7, 6, WHEAT),
    "thumb": rays(36, 12, 13, 20, (-170, -135, -90, -45, -10))
           + r(26, 82, 40, 16, BLUE, 3)
           + p("M24 46 C24 38 30 36 36 38 L66 38 C74 38 76 46 74 52 L74 74 C74 82 68 84 60 84 L34 84 C28 84 24 80 24 74 Z", SKIN)
           + r(28, 10, 16, 40, SKIN, 8) + e(36, 16, 5, 4, WHEAT)
           + r(48, 40, 28, 12, SKIN, 6) + r(48, 51, 28, 12, SKIN, 6) + r(48, 62, 26, 11, SKIN, 5.5) + r(48, 72, 22, 11, SKIN, 5.5),
    "family": line("M2 96 L98 96", 3)
            # dad (left, tall, blue)
            + limb("M18 66 L16 92 M26 66 L28 92", GRAY, 8)
            + p("M10 36 C10 30 34 30 34 36 L32 68 L12 68 Z", BLUE)
            + limb("M14 40 L8 64") + limb("M30 40 L42 62")
            + head(22, 20, 12)
            # mom (right, long hair, pink)
            + limb("M74 72 L72 92 M82 72 L84 92", SKIN, 6)
            + p("M72 40 C76 30 82 30 86 36 L94 74 L62 74 Z", PINK)
            + limb("M90 44 L94 64") + limb("M70 44 L58 64")
            + p("M64 26 C62 6 92 6 90 26 L92 44 L62 44 Z", BROWN)
            + head(77, 26, 12) + p("M65 24 C66 14 88 14 89 24 C82 18 72 18 65 24 Z", BROWN)
            # child (middle, small, gold)
            + limb("M46 80 L45 92 M54 80 L55 92", BLUE, 7)
            + p("M42 62 C42 58 58 58 58 62 L58 82 L42 82 Z", GOLD)
            + limb("M44 64 L40 66") + limb("M56 64 L60 66")
            + c(41, 63, 4.5, SKIN) + c(59, 64, 4.5, SKIN)
            + head(50, 48, 10),
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
