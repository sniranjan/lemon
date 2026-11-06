"""Ducklings word batch 1 pictures (36 words, approved 2026-11-06) in the house style.

Run: uv run python scripts/pictures/draw_batch4.py <out_dir> [slug ...]
A record only: the SVGs in assets/pictures/ are the source of truth (STATUS.md, picture workflow).
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


def head(x, y, rad=13, closed=False, mouth="smile"):
    """A child's head: skin, short brown hair, eyes (closed = sleeping curves)."""
    out = c(x, y, rad, SKIN)
    out += p(f"M{x - rad} {y - 1} C{x - rad} {y - rad - 6} {x + rad} {y - rad - 6} {x + rad} {y - 1} "
             f"C{x + rad * 0.5} {y - rad * 0.55} {x - rad * 0.5} {y - rad * 0.55} {x - rad} {y - 1} Z", BROWN)
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


def note(x, y, fill=PURPLE):
    """A music note (no text): head, stem, flag."""
    return (line(f"M{x + 5} {y} L{x + 5} {y - 18} C{x + 9} {y - 14} {x + 14} {y - 13} {x + 13} {y - 6}", 3)
            + e(x, y, 6, 4.5, fill, -20))


def sun(x, y, rad=8):
    rays = " ".join(f"M{x + (rad + 4) * math.cos(a):.1f} {y + (rad + 4) * math.sin(a):.1f} "
                    f"L{x + (rad + 9) * math.cos(a):.1f} {y + (rad + 9) * math.sin(a):.1f}"
                    for a in (i * math.pi / 4 for i in range(8)))
    return line(rays, 3) + c(x, y, rad, GOLD)


def shoe(x, y, rot=0):
    return e(x, y, 7, 4, RED, rot)


PICS = {
    # --- actions: a child doing it -------------------------------------------------------
    "hop": e(46, 93, 13, 3, LGRAY, 0, False)
         + line("M18 78 C20 66 28 62 34 70 M66 92 C68 84 72 82 76 86", 2.5, GRAY)
         + limb("M42 36 L28 40 L16 32") + limb("M58 36 L72 40 L84 32")
         + limb("M46 58 L45 80", BLUE, 8) + limb("M54 58 L68 64 L74 52", BLUE, 8)
         + shoe(41, 82) + shoe(76, 48, 80)
         + p("M40 32 C40 26 60 26 60 32 L60 60 L40 60 Z", GREEN) + head(50, 17),
    "sing": p("M14 98 C16 80 28 74 42 74 C56 74 68 80 70 98 Z", GREEN)
          + c(42, 50, 26, SKIN)
          + p("M16 48 C14 22 30 16 42 16 C56 16 70 24 68 48 C62 36 54 30 42 30 C32 30 22 36 16 48 Z", BROWN)
          + line("M28 46 C31 43 35 43 38 46 M46 46 C49 43 53 43 56 46", 2.5)
          + e(42, 62, 7, 9, "#7A2E2E") + c(28, 56, 4, PINK, False) + c(56, 56, 4, PINK, False)
          + note(76, 30) + note(88, 56, BLUE) + note(70, 68, GOLD),
    "dance": line("M14 74 C6 64 10 50 22 48 M88 52 C96 60 92 74 80 78", 3, GRAY)
           + limb("M44 36 L32 26 L34 10") + limb("M56 36 L70 40 L84 30")
           + limb("M46 60 L44 86") + limb("M54 60 L66 72 L80 70")
           + shoe(42, 88) + shoe(84, 70, 70)
           + p("M42 32 C42 26 58 26 58 32 L70 64 L30 64 Z", PURPLE) + line("M40 50 L60 50", 2.5)
           + head(50, 17),
    "nap": sun(80, 16)
         + p("M6 40 C6 34 14 32 20 34 L22 62 L6 62 Z", BLUE) + p("M94 40 C94 34 86 32 80 34 L78 62 L94 62 Z", BLUE)
         + r(6, 60, 88, 20, BLUE, 4) + line("M14 80 L14 90 M86 80 L86 90", 5)
         + e(30, 54, 12, 7, PURPLE) + head(30, 48, 11, closed=True, mouth=None)
         + p("M38 50 C40 44 76 44 80 50 L80 62 L38 62 Z", GREEN) + c(52, 52, 2.5, "#222", False) + c(64, 54, 2.5, "#222", False) + c(72, 50, 2.5, "#222", False),
    "dig": p("M40 96 C46 74 78 68 98 96 Z", DIRT) + c(84, 52, 3.5, DIRT) + c(92, 62, 3, DIRT) + c(76, 44, 2.5, DIRT)
         + colored_line("M44 30 L66 74", BROWN, 4) + p("M58 72 L72 66 L80 84 C76 90 68 90 64 86 Z", GRAY)
         + limb("M20 60 L18 76 L22 92", BLUE, 8) + limb("M28 60 L36 76 L34 92", BLUE, 8)
         + shoe(26, 93) + shoe(38, 93)
         + p("M14 36 C14 30 32 30 32 36 L32 62 L14 62 Z", RED)
         + limb("M28 40 L42 38 L48 40") + limb("M26 46 L44 52 L54 54")
         + head(24, 20),
    "walk": e(12, 92, 4, 2, LGRAY, 0, False) + e(22, 89, 4, 2, LGRAY, 0, False) + line("M6 94 L94 94", 3)
          + limb("M46 58 L42 74 L36 88", BLUE, 8) + limb("M54 58 L58 74 L64 88", BLUE, 8)
          + shoe(32, 89) + shoe(68, 89)
          + limb("M44 34 L38 46 L34 56")
          + p("M42 30 C42 26 58 26 58 32 L58 60 L42 60 Z", ORANGE)
          + limb("M56 34 L62 46 L68 54")
          + head(50, 17),
    "kick": line("M66 52 L60 46 M64 74 L58 80 M96 50 L90 54 M96 78 L90 74", 3, GRAY)
          + c(80, 64, 13, BLUE) + line("M67 64 C74 58 86 58 93 64 M80 51 C76 58 76 70 80 77", 2.5)
          + limb("M30 58 L30 88", BLUE, 8) + limb("M38 58 L52 66 L62 66", BLUE, 8)
          + shoe(26, 90) + shoe(64, 64, 80)
          + limb("M28 34 L16 42 L10 36") + limb("M42 34 L52 38 L60 32")
          + p("M26 30 C26 26 44 26 44 30 L44 60 L26 60 Z", RED) + head(35, 16),
    "wave": line("M70 16 C64 20 62 28 64 34 M96 12 C100 18 100 30 94 36", 3, GRAY)
          + limb("M34 56 L26 72 L26 84") + limb("M60 56 L74 48 L80 34")
          + palm(80, 24, 15, s=0.9)
          + p("M30 56 C30 50 36 48 42 48 L54 48 C60 48 64 50 64 56 L66 98 L28 98 Z", BLUE)
          + head(47, 32, 15),
    "read": p("M14 98 C16 72 30 62 50 62 C70 62 84 72 86 98 Z", GOLD)
          + head(50, 30, 18)
          + p("M20 70 C32 66 44 68 50 74 C56 68 68 66 80 70 L80 98 C68 94 56 94 50 98 C44 94 32 94 20 98 Z", GREEN)
          + p("M24 72 C34 70 44 72 50 77 L50 94 C44 90 34 90 24 92 Z", "#F4F1EA")
          + p("M76 72 C66 70 56 72 50 77 L50 94 C56 90 66 90 76 92 Z", "#F4F1EA")
          + line("M30 78 L44 80 M30 84 L44 86 M56 80 L70 78 M56 86 L70 84", 2, GRAY)
          + c(20, 84, 6, SKIN) + c(80, 84, 6, SKIN),
    "draw": p("M8 12 L74 12 L74 70 L8 70 Z", "none")
          + c(28, 32, 9, "none").replace('stroke="#222"', f'stroke="{GOLD}"')
          + line("M14 32 L10 32 M28 18 L28 14 M42 32 L46 32 M18 22 L15 19 M38 22 L41 19", 3, GOLD)
          + line("M22 62 L22 46 L36 38 L50 46 L50 62 Z", 3, RED) + line("M54 62 C58 54 62 54 66 62", 3, DGREEN)
          + line("M50 52 C54 56 58 58 62 56", 4, BLUE)
          + p("M60 60 L66 52 L86 70 L80 78 Z", BLUE) + p("M60 60 L66 52 L58 54 Z", BLUE)
          + p("M70 62 C66 74 74 92 90 96 L98 96 L98 70 C90 64 80 60 70 62 Z", SKIN)
          + p("M74 66 C70 60 76 56 82 62 Z", SKIN),
    "climb": colored_line("M22 2 L22 98 M78 2 L78 98", BROWN, 6)
           + colored_line("M22 12 L78 12 M22 34 L78 34 M22 56 L78 56 M22 78 L78 78", TAN, 5)
           + limb("M42 60 L36 74 L36 78", BLUE, 9) + limb("M58 60 L68 60 L64 56", BLUE, 9)
           + e(34, 78, 8, 4.5, RED) + e(62, 56, 8, 4.5, RED)
           + limb("M38 38 L30 24 L32 12", SKIN, 8) + limb("M62 38 L70 24 L68 12", SKIN, 8)
           + c(32, 11, 5.5, SKIN) + c(68, 11, 5.5, SKIN)
           + p("M34 36 C34 30 66 30 66 36 L66 64 L34 64 Z", RED)
           + c(50, 26, 13, BROWN) + e(37, 27, 3, 4.5, SKIN) + e(63, 27, 3, 4.5, SKIN),
    "hide": head(54, 40, 16)
          + p("M6 96 C2 80 10 66 22 64 C22 52 36 46 46 54 C52 44 70 44 74 56 C86 52 98 64 94 78 C100 86 96 96 90 96 Z", GREEN)
          + line("M24 76 C28 80 32 80 36 76 M60 72 C64 76 68 76 72 72 M42 86 C46 90 50 90 54 86", 2.5, DGREEN)
          + palm(36, 52, -10, s=0.7) + palm(72, 52, 10, s=0.7),
    # --- body ------------------------------------------------------------------------------
    "face": e(14, 54, 6, 9, SKIN) + e(86, 54, 6, 9, SKIN)
          + e(50, 54, 36, 40, SKIN)
          + p("M14 46 C10 16 32 8 50 8 C68 8 90 16 86 46 C80 30 66 24 50 24 C34 24 20 30 14 46 Z", BROWN)
          + line("M30 40 C34 37 39 37 42 39 M58 39 C61 37 66 37 70 40", 2.5)
          + c(36, 50, 6, "#FFFFFF") + c(64, 50, 6, "#FFFFFF") + c(37, 51, 3.5, "#222", False) + c(65, 51, 3.5, "#222", False)
          + line("M50 54 C48 60 47 64 52 65", 2.5) + c(28, 66, 6, PINK, False) + c(72, 66, 6, PINK, False)
          + p("M38 74 C44 82 56 82 62 74 Z", "#7A2E2E"),
    "head": p("M16 98 C18 82 32 76 50 76 C68 76 82 82 84 98 Z", BLUE)
          + limb("M24 84 L10 54 L30 24", SKIN, 7) + limb("M76 84 L90 54 L70 24", SKIN, 7)
          + head(50, 52, 24)
          + palm(36, 26, -50, s=0.8) + palm(64, 26, 50, s=0.8),
    "knee": line("M4 94 L96 94", 3)
          + line("M40 22 L34 14 M50 16 L50 6 M62 20 L68 12", 3, GRAY)
          + p("M8 58 L30 52 L52 40 L58 54 L36 70 L14 78 Z", SKIN)
          + p("M4 56 L26 50 L32 70 L10 78 Z", BLUE)
          + p("M46 42 L58 54 L76 84 L64 88 Z", SKIN)
          + c(52, 40, 12, SKIN)
          + p("M62 84 L80 82 C90 82 96 86 96 92 L60 92 Z", RED),
    "finger": p("M44 10 C44 4 56 4 56 10 L56 50 L44 50 Z", SKIN)
            + p("M30 50 C30 44 36 42 40 44 L70 44 C76 44 78 48 78 54 L78 76 C78 88 68 94 56 94 C42 94 30 88 30 76 Z", SKIN)
            + line("M44 56 L70 56 M44 66 L70 66", 2.5)
            + p("M30 60 C22 58 20 68 26 72 L40 72 C44 70 44 62 40 60 Z", SKIN)
            + line("M47 16 L53 16", 2) + line("M22 18 L14 12 M78 18 L86 12 M20 34 L10 34 M80 34 L90 34", 3, GRAY),
    "tummy": head(50, 16, 12)
           + limb("M30 32 L22 50 L28 64") + limb("M70 32 L78 50 L72 64")
           + p("M28 76 L72 76 L74 98 L26 98 Z", BLUE)
           + e(50, 62, 24, 18, SKIN)
           + line("M50 64 C47 62 48 59 51 60", 2.5)
           + p("M30 30 C30 26 70 26 70 30 L72 48 C60 46 40 46 28 48 Z", RED)
           + c(28, 64, 6, SKIN) + c(72, 64, 6, SKIN),
    # --- clothes ---------------------------------------------------------------------------
    "jacket": p("M36 16 C36 4 64 4 64 16 L58 22 L42 22 Z", GREEN)
            + p("M30 18 L42 18 L50 26 L58 18 L70 18 L84 30 L92 80 L80 82 L72 46 L72 92 L28 92 L28 46 L20 82 L8 80 L16 30 Z", GREEN)
            + line("M50 26 L50 92", 3) + r(32, 62, 12, 10, DGREEN, 2) + r(56, 62, 12, 10, DGREEN, 2)
            + c(50, 34, 3, GRAY) + line("M28 84 L72 84", 3),
    "mitten": p("M30 64 L30 30 C30 12 64 10 66 30 L68 44 C74 34 86 38 82 50 L72 66 Z", BLUE)
            + r(26, 64, 50, 26, LBLUE, 4) + line("M34 64 L34 90 M42 64 L42 90 M50 64 L50 90 M58 64 L58 90 M66 64 L66 90", 2.5),
    "skirt": r(26, 16, 48, 12, PINK, 3)
           + p("M28 28 L72 28 L90 84 C70 92 30 92 10 84 Z", PINK)
           + line("M40 30 L32 88 M50 30 L50 90 M60 30 L68 88", 2.5),
    # --- toys ------------------------------------------------------------------------------
    "teddy": c(30, 20, 9, TAN) + c(70, 20, 9, TAN) + c(30, 20, 4, WHEAT, False) + c(70, 20, 4, WHEAT, False)
           + e(22, 62, 9, 14, TAN, 30) + e(78, 62, 9, 14, TAN, -30)
           + e(32, 86, 12, 9, TAN) + e(68, 86, 12, 9, TAN) + c(28, 88, 5, WHEAT, False) + c(72, 88, 5, WHEAT, False)
           + e(50, 68, 22, 24, TAN) + e(50, 72, 12, 13, WHEAT, 0, False)
           + c(50, 34, 20, TAN) + e(50, 40, 9, 7, WHEAT)
           + e(50, 37, 3.5, 2.5, "#222", 0, False) + line("M50 40 L50 43 M46 44 C48 46 52 46 54 44", 2)
           + eyes(29, 43, 57, 2.6)
           + p("M50 52 L40 46 L40 58 Z M50 52 L60 46 L60 58 Z", RED),
    "bag": p("M36 22 C36 4 64 4 64 22", "none")
         + p("M22 34 C22 24 30 20 40 20 L60 20 C70 20 78 24 78 34 L78 86 C78 92 74 94 68 94 L32 94 C26 94 22 92 22 86 Z", RED)
         + p("M30 56 L70 56 L70 82 C70 86 68 88 64 88 L36 88 C32 88 30 86 30 82 Z", RED)
         + line("M30 66 L70 66", 3) + r(46, 62, 8, 8, GOLD, 2) + line("M34 34 L66 34", 3),
    "puzzle": p("M14 30 L28 30 C24 18 42 18 38 30 L52 30 L52 42 C64 38 64 56 52 52 L52 70 L40 70 C44 82 26 82 30 70 L14 70 Z", BLUE)
            + p("M60 36 L96 36 L96 76 L60 76 L60 62 C72 66 72 48 60 52 Z", GOLD)
            + p("M14 76 L30 76 C26 86 44 86 40 76 L52 76 L52 96 L14 96 Z", RED),
    "robot": line("M50 8 L50 18", 3) + c(50, 7, 4, RED)
           + r(30, 18, 40, 28, GRAY, 6) + c(41, 31, 5, GLASS) + c(59, 31, 5, GLASS)
           + line("M42 40 C46 43 54 43 58 40", 2.5)
           + colored_line("M28 58 L16 72 M72 58 L84 72", GRAY, 5) + c(14, 74, 5, GRAY) + c(86, 74, 5, GRAY)
           + r(40, 82, 7, 12, GRAY, 2) + r(53, 82, 7, 12, GRAY, 2)
           + r(26, 48, 48, 36, BLUE, 6) + c(40, 62, 4, RED) + c(50, 62, 4, GOLD) + c(60, 62, 4, GREEN)
           + line("M36 74 L64 74", 2.5),
    "bucket": p("M24 34 C24 6 76 6 76 34", "none")
            + p("M18 30 L82 30 L74 92 L26 92 Z", RED)
            + p("M18 30 L82 30 L80 42 L20 42 Z", GOLD)
            + p("M50 54 L54 63 L64 64 L56 70 L59 80 L50 74 L41 80 L44 70 L36 64 L46 63 Z", GOLD),
    # --- home ------------------------------------------------------------------------------
    "brush": colored_line("M62 62 L88 90", PURPLE, 9)
           + e(40, 40, 24, 30, PURPLE, -45)
           + e(38, 38, 15, 21, LGRAY, -45)
           + "".join(c(x, y, 1.8, "#222", False) for x, y in
                     ((30, 30), (38, 30), (46, 30), (26, 38), (34, 38), (42, 38), (50, 38),
                      (30, 46), (38, 46), (46, 46), (34, 54), (42, 54), (38, 22))),
    "comb": p("M8 30 L92 30 C94 30 94 46 92 46 L8 46 C6 46 6 30 8 30 Z", BLUE)
          + "".join(p(f"M{x} 46 L{x + 5} 46 L{x + 5} 74 C{x + 5} 77 {x} 77 {x} 74 Z", BLUE) for x in range(12, 89, 9)),
    "fork": colored_line("M50 54 L50 94", GRAY, 7)
          + p("M30 8 L36 8 L36 34 L40 34 L40 8 L46 8 L46 34 L54 34 L54 8 L60 8 L60 34 L64 34 L64 8 L70 8 "
              "L70 40 C70 52 60 58 50 58 C40 58 30 52 30 40 Z", GRAY),
    "sofa": line("M18 84 L18 92 M82 84 L82 92", 6)
          + r(16, 22, 68, 40, BLUE, 8)
          + r(6, 44, 20, 42, BLUE, 8) + r(74, 44, 20, 42, BLUE, 8)
          + r(24, 58, 26, 14, LBLUE, 4) + r(50, 58, 26, 14, LBLUE, 4)
          + r(24, 70, 52, 16, BLUE, 2),
    "box": p("M20 40 L4 28 L36 20 L50 32 Z", WHEAT) + p("M80 40 L96 28 L64 20 L50 32 Z", WHEAT)
         + p("M20 40 L50 32 L80 40 L50 48 Z", BROWN)
         + p("M20 40 L50 48 L50 92 L20 82 Z", WHEAT) + p("M80 40 L50 48 L50 92 L80 82 Z", TAN)
         + line("M28 58 L42 62", 2.5),
    # --- animals -----------------------------------------------------------------------------
    "puppy": line("M78 72 C88 66 90 56 86 50", 6) + line("M78 72 C88 66 90 56 86 50", 2, TAN)
           + e(58, 74, 24, 18, TAN) + e(40, 88, 8, 6, TAN) + e(64, 90, 8, 6, TAN)
           + p("M22 24 C22 14 58 14 58 24 L60 46 C60 60 50 66 40 66 C30 66 20 60 20 46 Z", TAN)
           + p("M22 22 C10 24 8 42 14 50 C20 46 22 38 24 32 Z", BROWN)
           + p("M58 22 C70 24 72 42 66 50 C60 46 58 38 56 32 Z", BROWN)
           + eyes(38, 32, 48, 3.5) + e(40, 50, 5, 4, "#222", 0, False)
           + p("M37 56 L43 56 L43 62 C43 65 37 65 37 62 Z", PINK),
    "kitten": line("M74 84 C92 84 94 64 84 58", 7) + line("M74 84 C92 84 94 64 84 58", 3, GRAY)
            + e(54, 74, 22, 20, GRAY) + e(40, 92, 7, 4, GRAY) + e(62, 92, 7, 4, GRAY)
            + p("M24 30 L22 10 L38 22 Z", GRAY) + p("M66 30 L68 10 L52 22 Z", GRAY)
            + e(45, 40, 24, 20, GRAY)
            + line("M40 22 L42 28 M50 22 L48 28", 2.5)
            + eyes(40, 36, 54, 3.5) + p("M42 46 L48 46 L45 50 Z", PINK)
            + line("M45 50 L45 53 M40 54 C42 56 44 56 45 53 C46 56 48 56 50 54", 2)
            + line("M30 48 L18 46 M30 52 L18 54 M60 48 L72 46 M60 52 L72 54", 1.8),
    "chick": line("M42 86 L42 94 M36 97 L42 94 L46 98 M58 86 L58 94 M52 97 L58 94 L62 98", 3)
           + p("M46 24 C40 14 48 10 50 20 C52 10 60 14 54 24 Z", GOLD)
           + c(50, 56, 32, GOLD)
           + p("M64 54 C76 54 80 66 70 74 C66 70 62 62 64 54 Z", "#D4951A")
           + eyes(46, 40, 56, 3.5) + p("M44 52 L52 52 L48 60 Z", ORANGE)
           + c(34, 56, 3.5, ORANGE, False),
    "whale": line("M40 26 C36 14 30 12 26 16 M40 26 C42 14 48 10 54 14 M40 26 L40 34", 3, BLUE)
           + p("M80 54 C86 44 96 40 96 34 C90 38 86 40 84 44 C82 38 78 32 72 32 C76 38 78 46 76 54 Z", DBLUE)
           + p("M6 62 C6 40 24 34 44 34 C66 34 80 46 80 60 C80 76 62 84 40 84 C20 84 6 76 6 62 Z", DBLUE)
           + p("M10 70 C20 80 60 82 76 68 C70 80 56 84 40 84 C22 84 12 78 10 70 Z", LBLUE)
           + c(26, 54, 3.5, "#222", False) + line("M12 64 C20 70 32 70 40 64", 2.5)
           + p("M40 74 C46 84 56 84 56 76 Z", DBLUE),
    "crab": line("M24 66 L8 76 M26 72 L12 86 M76 66 L92 76 M74 72 L88 86", 6) + line("M24 66 L8 76 M26 72 L12 86 M76 66 L92 76 M74 72 L88 86", 2, RED)
          + colored_line("M28 54 L16 40 M72 54 L84 40", RED, 4)
          + p("M10 36 C4 26 10 14 20 16 L16 28 L26 24 C28 34 20 40 10 36 Z", RED)
          + p("M90 36 C96 26 90 14 80 16 L84 28 L74 24 C72 34 80 40 90 36 Z", RED)
          + line("M40 50 L38 34 M60 50 L62 34", 3)
          + c(38, 32, 5, "#FFFFFF") + c(62, 32, 5, "#FFFFFF") + c(38, 32, 2.5, "#222", False) + c(62, 32, 2.5, "#222", False)
          + e(50, 64, 30, 18, RED) + line("M42 68 C46 72 54 72 58 68", 2.5),
    "snail": line("M28 56 L22 36 M36 56 L34 38", 3) + c(22, 34, 3.5, GREEN) + c(34, 36, 3.5, GREEN)
           + p("M10 84 C10 70 18 56 30 56 C36 56 40 62 40 70 L40 78 L90 78 C94 78 94 86 88 86 L14 86 C12 86 10 86 10 84 Z", GREEN)
           + c(28, 66, 2.5, "#222", False)
           + c(64, 56, 24, ORANGE)
           + line("M64 56 C64 50 72 50 72 56 C72 64 58 66 56 56 C54 44 72 40 78 52 C84 64 72 78 58 74", 3),
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
