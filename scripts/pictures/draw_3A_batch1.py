"""Puppies Reading (3A) word batch 3A-1 pictures (40 words, approved 2026-11-06 by the orchestrator under
user delegation) in the house style.

Run: uv run python scripts/pictures/draw_3A_batch1.py <out_dir> [slug ...]
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
WOOLW, GOOSE, SILVER = "#C9C0B0", "#B4B8BE", "#A9AEB6"


def seed_shape(x, y, rot_deg):
    body = (p(f"M{x} {y - 16} C{x + 10} {y - 8} {x + 9} {y + 10} {x} {y + 16} C{x - 9} {y + 10} {x - 10} {y - 8} {x} {y - 16} Z", MBROWN)
            + line(f"M{x - 4} {y - 9} L{x - 4} {y + 9} M{x + 4} {y - 9} L{x + 4} {y + 9}", 2.5, WOOL))
    return rot(rot_deg, x, y, body)


def link(cx, cy, rot_deg, fill=GRAY):
    return rot(rot_deg, cx, cy, f'<path d="M{cx - 16} {cy - 8} L{cx + 16} {cy - 8} A8 8 0 0 1 {cx + 16} {cy + 8} '
                                f'L{cx - 16} {cy + 8} A8 8 0 0 1 {cx - 16} {cy - 8} Z M{cx - 14} {cy - 3} L{cx + 14} {cy - 3} '
                                f'A3 3 0 0 1 {cx + 14} {cy + 3} L{cx - 14} {cy + 3} A3 3 0 0 1 {cx - 14} {cy - 3} Z" '
                                f'fill="{fill}" fill-rule="evenodd" {S}/>')


def bee(x, y, s=1.0):
    return (e(x - 3 * s, y - 7 * s, 5 * s, 4 * s, LBLUE) + e(x + 4 * s, y - 7 * s, 5 * s, 4 * s, LBLUE)
            + e(x, y, 9 * s, 6.5 * s, GOLD) + line(f"M{x - 2 * s} {y - 6 * s} L{x - 2 * s} {y + 6 * s} M{x + 3 * s} {y - 6 * s} L{x + 3 * s} {y + 6 * s}", 2.2)
            + c(x + 6 * s, y - 1 * s, 1.4 * s, "#222", False))


PICS = {
    # --- page 1-10: letter pairs -------------------------------------------------------------
    "shark": p("M0 84 C12 78 22 90 34 84 C46 78 56 90 68 84 C80 78 90 90 100 84 L100 100 L0 100 Z", BLUE)
           + p("M18 56 L4 38 L8 56 L4 74 Z", SLATE)
           + p("M44 36 L54 14 L62 38 Z", SLATE)
           + p("M14 56 C24 36 54 30 78 40 C86 44 92 50 94 56 C86 66 62 72 38 70 C26 69 18 62 14 56 Z", SLATE)
           + p("M40 69 C56 70 78 66 90 60 C80 66 62 74 40 69 Z", WOOL)
           + p("M48 66 L42 82 L60 68 Z", SLATE)
           + c(80, 48, 2.6, "#222", False)
           + line("M82 58 C85 61 89 60 92 57", 2.2)
           + line("M68 47 L66 57 M73 46 L71 56", 2.2),
    "wheel": c(50, 50, 44, DARK) + c(50, 50, 33, GRAY)
           + "".join(line(f"M50 50 L{50 + 30 * math.cos(a * math.pi / 4):.1f} {50 + 30 * math.sin(a * math.pi / 4):.1f}", 2.5)
                     for a in range(8))
           + c(50, 50, 33, "none") + c(50, 50, 8, LGRAY)
           + line("M26 20 C34 14 44 11 52 11", 3, LGRAY),
    "beach": c(18, 18, 9, GOLD)
           + p("M0 44 L100 44 L100 66 L0 66 Z", BLUE)
           + line("M8 52 C12 49 16 49 20 52 M44 50 C48 47 52 47 56 50 M76 55 C80 52 84 52 88 55", 2.5, WHITE)
           + p("M0 62 C30 55 70 68 100 60 L100 100 L0 100 Z", TAN)
           + colored_line("M64 38 L74 94", GRAY, 3)
           + p("M42 44 C46 22 82 14 96 34 Z", RED) + line("M60 26 L64 38 M78 22 L74 37", 2.5)
           + p("M18 82 L34 82 L32 96 L20 96 Z", BLUE) + colored_line("M18 82 C18 72 34 72 34 82", GOLD, 2)
           + star(46, 86, 6, ORANGE),
    "couch": colored_line("M18 84 L18 92 M82 84 L82 92", MBROWN, 4)
           + r(14, 26, 72, 36, BLUE, 10)
           + line("M50 30 L50 58", 3)
           + r(10, 56, 80, 26, BLUE, 7)
           + line("M14 66 L86 66", 2.5) + line("M50 58 L50 66", 3)
           + r(4, 42, 18, 42, BLUE, 8) + r(78, 42, 18, 42, BLUE, 8)
           + rot(-12, 30, 46, r(22, 38, 18, 16, GOLD, 5)),
    "tooth": p("M22 30 C18 12 40 8 50 16 C60 8 82 12 78 30 C76 46 72 56 70 76 C69 88 60 90 58 78 "
               "C56 66 54 60 50 60 C46 60 44 66 42 78 C40 90 31 88 30 76 C28 56 24 46 22 30 Z", WOOL)
           + c(40, 34, 2.8, "#222", False) + c(60, 34, 2.8, "#222", False)
           + line("M42 44 C46 49 54 49 58 44", 2.5)
           + c(33, 41, 3.5, PINK, False) + c(67, 41, 3.5, PINK, False)
           + line("M28 22 C30 17 34 15 38 15", 3, WHITE),
    "shower": colored_line("M12 4 L12 20 L40 20", GRAY, 5)
            + p("M34 14 L56 14 L64 30 L26 30 Z", GRAY)
            + "".join(drop(x, y, 3.4, LBLUE) for x, y in ((32, 40), (44, 40), (56, 40), (38, 52), (50, 52), (62, 52), (34, 64), (46, 64), (58, 64)))
            + p("M6 72 L94 72 L88 92 C86 96 14 96 12 92 Z", BLUE)
            + r(2, 66, 96, 9, BLUE, 4)
            + c(80, 62, 4, WHITE) + c(86, 58, 3, WHITE) + c(74, 60, 3, WHITE),
    "chalk": line("M8 86 C20 70 32 92 44 78", 4, PINK) + star(80, 82, 9, "none")
           + rot(-30, 34, 46, r(14, 38, 40, 14, PINK, 5))
           + rot(-15, 52, 30, r(32, 22, 40, 14, BLUE, 5))
           + rot(10, 62, 58, r(42, 50, 40, 14, GOLD, 5)),
    "cheetah": colored_line("M24 52 C10 52 6 64 10 80", GOLD, 6)
             + limb("M32 60 L28 92", GOLD, 7) + limb("M42 62 L44 92", GOLD, 7)
             + limb("M64 60 L60 92", GOLD, 7) + limb("M74 58 L78 92", GOLD, 7)
             + e(52, 52, 30, 14, GOLD)
             + "".join(c(x, y, 2.2, DARK, False) for x, y in ((34, 46), (44, 50), (54, 44), (62, 52), (40, 58), (70, 46), (30, 54), (52, 58)))
             + p("M72 30 L74 22 L80 28 Z", GOLD) + p("M86 28 L90 20 L92 30 Z", GOLD)
             + c(82, 40, 13, GOLD)
             + c(78, 37, 2.4, "#222", False) + c(87, 37, 2.4, "#222", False)
             + line("M77 40 L76 48 M88 40 L90 48", 2, DARK)
             + e(84, 46, 3, 2, "#222", 0, False) + line("M80 50 C82 52 86 52 88 50", 2),
    "throne": colored_line("M30 70 L28 94 M70 70 L72 94", GOLD, 5)
            + p("M28 64 L28 18 C28 6 72 6 72 18 L72 64 Z", RED)
            + p("M34 58 L34 22 C34 14 66 14 66 22 L66 58 Z", "#D76565")
            + c(50, 8, 5, GOLD)
            + r(20, 60, 60, 14, GOLD, 4)
            + r(14, 46, 12, 22, GOLD, 4) + r(74, 46, 12, 22, GOLD, 4)
            + p("M38 60 L37 46 L43 52 L50 42 L57 52 L63 46 L62 60 Z", GOLD)
            + c(50, 44, 2.5, BLUE),
    "wheat": "".join(colored_line(d, GOLD, 3) for d in ("M50 96 L50 30", "M50 96 C46 70 36 50 26 36", "M50 96 C54 70 64 50 74 36"))
           + "".join(rot(a, x, y, e(x, y, 4.5, 7.5, WHEAT)) for x, y, a in
                     ((50, 12, 0), (44, 20, -25), (56, 20, 25), (44, 30, -25), (56, 30, 25), (44, 40, -25), (56, 40, 25),
                      (22, 22, -35), (16, 30, -60), (28, 30, -10), (20, 40, -60), (32, 40, -10),
                      (78, 22, 35), (84, 30, 60), (72, 30, 10), (80, 40, 60), (68, 40, 10))),
    # --- page 11-20: magic e -------------------------------------------------------------------
    "gate": p("M0 84 L100 84 L100 100 L0 100 Z", GREEN)
          + r(4, 28, 12, 62, MBROWN, 3) + r(84, 28, 12, 62, MBROWN, 3)
          + "".join(p(f"M{x} 34 L{x + 5} 28 L{x + 10} 34 L{x + 10} 84 L{x} 84 Z", TAN) for x in (20, 33, 46, 59, 72))
          + r(18, 42, 66, 8, TAN, 2) + r(18, 68, 66, 8, TAN, 2)
          + line("M20 76 L82 44", 6) + line("M20 76 L82 44", 3, TAN)
          + c(76, 58, 3, DARK),
    "snake": colored_line("M14 84 C6 70 30 66 50 72 C70 78 92 74 88 60 C84 46 56 54 44 48 C30 42 34 26 48 24", GREEN, 13)
           + line("M24 74 L26 80 M40 70 L40 76 M58 76 L58 82 M74 76 L72 82 M80 56 L76 52 M60 52 L58 46", 2.5, DGREEN)
           + e(54, 22, 12, 9, GREEN)
           + c(54, 18, 2.4, "#222", False) + c(60, 20, 2.4, "#222", False)
           + line("M64 26 L72 28 L76 24 M72 28 L76 32", 2.5, RED)
           + line("M50 27 C53 29 57 29 60 27", 2),
    "cape": p("M36 30 L64 30 L94 94 C70 88 30 88 6 94 Z", RED)
          + line("M40 40 C32 60 22 76 16 88 M60 40 C68 60 78 76 84 88", 2.5, "#B55757")
          + limb("M44 74 L42 94", BLUE, 8) + limb("M56 74 L58 94", BLUE, 8) + shoe(40, 95) + shoe(60, 95)
          + limb("M38 44 L30 60") + limb("M62 44 L70 60")
          + p("M38 42 C40 34 60 34 62 42 L62 76 L38 76 Z", BLUE)
          + star(50, 56, 7, GOLD)
          + head(50, 22, 13)
          + p("M38 34 L50 40 L62 34 L60 30 L40 30 Z", RED) + c(50, 38, 3.5, GOLD),
    "vase": colored_line("M50 46 L50 22 M50 34 C56 30 60 28 64 30", GREEN, 3)
          + p("M64 30 C66 22 74 22 74 30 C70 34 66 34 64 30 Z", GREEN)
          + "".join(rot(a, 50, 16, e(50, 7, 5, 8, PINK)) for a in (0, 72, 144, 216, 288)) + c(50, 16, 5, GOLD)
          + p("M38 44 L62 44 L60 52 C76 60 76 86 62 94 L38 94 C24 86 24 60 40 52 Z", BLUE)
          + line("M30 70 C42 74 58 74 70 70", 2.5) + line("M34 64 C34 58 38 54 42 54", 3, LBLUE),
    "hive": colored_line("M2 10 L98 14", BARK, 6) + colored_line("M50 12 L50 20", BARK, 4)
          + e(50, 30, 16, 10, GOLD) + e(50, 46, 24, 11, GOLD) + e(50, 62, 26, 11, GOLD) + e(50, 77, 20, 10, GOLD)
          + e(50, 66, 6, 5, DARK, 0, False)
          + bee(80, 48, 1.0) + bee(20, 80, 0.8),
    "lime": e(38, 50, 30, 24, GREEN, -15)
          + line("M20 40 C24 34 30 30 36 30", 3, "#B6DCA4")
          + c(36, 26, 3, DGREEN, False)
          + c(72, 70, 20, GREEN) + c(72, 70, 15, "#BFE3A8")
          + "".join(line(f"M72 70 L{72 + 14 * math.cos(a * math.pi / 3):.1f} {70 + 14 * math.sin(a * math.pi / 3):.1f}", 2, DGREEN) for a in range(6)),
    "rope": colored_line("M50 50 m-30 0 a30 22 0 1 0 60 0 a30 22 0 1 0 -60 0", TAN, 8)
          + colored_line("M50 50 m-19 0 a19 13 0 1 0 38 0 a19 13 0 1 0 -38 0", TAN, 8)
          + colored_line("M50 50 m-8 0 a8 5 0 1 0 16 0", TAN, 8)
          + colored_line("M80 50 C90 64 86 80 94 92", TAN, 8)
          + line("M24 38 L28 42 M36 32 L38 37 M50 29 L50 34 M64 31 L62 36 M76 37 L72 41 M24 62 L28 58 M50 71 L50 66 M72 64 L70 60", 2, MBROWN),
    "bone": rot(-25, 50, 50, c(22, 40, 11, WOOL) + c(22, 60, 11, WOOL) + c(78, 40, 11, WOOL) + c(78, 60, 11, WOOL)
                + r(20, 40, 60, 20, WOOL, 4)
                + '<path d="M22 41 L78 41 L78 59 L22 59 Z" fill="' + WOOL + '"/>'
                + line("M30 46 L60 46", 3, WHITE)),
    "cube": p("M20 34 L50 20 L82 34 L52 48 Z", GLASS)
          + p("M20 34 L52 48 L52 88 L20 74 Z", LBLUE)
          + p("M52 48 L82 34 L82 74 L52 88 Z", "#78A6D8")
          + line("M28 46 L28 60 M34 50 L34 56", 3, WHITE)
          + line("M88 20 L94 14 M90 28 L98 26 M80 14 L82 6", 2.5, LBLUE),
    "flute": rot(-20, 50, 50, r(4, 42, 92, 14, SILVER, 6)
                 + r(4, 42, 14, 14, GRAY, 4)
                 + "".join(c(x, 49, 3, DARK, False) for x in (34, 44, 54, 64, 74))
                 + c(14, 49, 2.5, DARK, False)
                 + line("M20 45 L90 45", 2, WHITE))
          + e(18, 26, 5, 3.6, "#222", -20, False) + line("M22 25 L22 8 L30 12", 2.5)
          + e(34, 20, 5, 3.6, "#222", -20, False) + line("M38 19 L38 2", 2.5),
    # --- page 21-30: ai and ay ----------------------------------------------------------------
    "tail": colored_line("M62 82 C82 84 92 72 88 56 C84 40 70 36 72 22 C74 12 84 10 86 18", ORANGE, 11)
          + line("M78 80 L82 74 M88 66 L82 64 M84 48 L78 50 M74 32 L80 30", 3, "#C46F3A")
          + e(46, 70, 26, 24, ORANGE)
          + p("M26 34 L28 18 L38 28 Z", ORANGE) + p("M54 28 L64 18 L66 34 Z", ORANGE)
          + c(46, 40, 18, ORANGE)
          + line("M38 66 C44 62 50 62 56 66 M36 76 C44 72 52 72 58 76", 3, "#C46F3A")
          + e(34, 92, 8, 4, ORANGE) + e(58, 92, 8, 4, ORANGE),
    "nail": p("M0 80 L100 80 L100 100 L0 100 Z", TAN) + line("M10 88 L40 88 M56 92 L90 92", 2.5, MBROWN)
          + rot(20, 50, 46, r(46, 14, 8, 64, SILVER, 2) + e(50, 13, 16, 5, SILVER) + line("M49 22 L49 70", 2, WHITE))
          + line("M74 22 L84 14 M78 32 L90 30", 3, GRAY),
    "mail": rot(-8, 40, 40, r(10, 18, 60, 40, TAN, 4) + line("M10 18 L40 42 L70 18", 3) + r(56, 22, 10, 12, RED, 1))
          + rot(6, 58, 64, r(28, 44, 62, 42, LBLUE, 4) + line("M28 44 L59 68 L90 44", 3) + r(76, 48, 10, 12, GOLD, 1)
                + line("M40 74 L60 74 M40 80 L54 80", 2.5)),
    "sail": p("M0 84 C12 78 22 90 34 84 C46 78 56 90 68 84 C80 78 90 90 100 84 L100 100 L0 100 Z", BLUE)
          + p("M14 72 L88 72 L78 86 L24 86 Z", RED)
          + colored_line("M52 8 L52 72", MBROWN, 3)
          + p("M56 10 L88 64 L56 64 Z", WOOL)
          + p("M48 18 L48 64 L18 64 Z", WOOL)
          + p("M52 6 L64 9 L52 13 Z", GOLD),
    "braid": p("M24 100 C26 86 36 80 50 80 C64 80 72 86 74 100 Z", GREEN)
           + c(50, 46, 24, SKIN)
           + p("M26 46 C22 16 78 16 74 46 C70 34 62 28 50 28 C38 28 30 34 26 46 Z", BROWN)
           + eyes(50, 41, 59, 2.8) + line("M44 60 C47 63 53 63 56 60", 2.5)
           + c(36, 56, 3.5, PINK, False) + c(64, 56, 3.5, PINK, False)
           + colored_line("M72 40 C80 50 76 60 78 70", BROWN, 8)
           + "".join(e(x, y, 7, 5, BROWN, a) for x, y, a in ((76, 48, 40), (78, 56, -30), (78, 64, 40), (78, 72, -30), (78, 80, 40)))
           + rot(10, 78, 88, e(72, 88, 6, 4, PINK) + e(84, 88, 6, 4, PINK) + c(78, 88, 3, PINK)),
    "chain": link(22, 22, 40) + link(40, 40, -50, GRAY) + link(58, 58, 40) + link(76, 76, -50, GRAY),
    "hay": p("M0 88 L100 88 L100 100 L0 100 Z", GREEN)
         + r(10, 34, 80, 54, WHEAT, 10)
         + line("M18 44 L30 42 M40 50 L54 48 M64 42 L78 44 M20 62 L34 60 M48 66 L60 64 M70 58 L82 60 M24 78 L38 76 M58 80 L74 78", 2.5, MBROWN)
         + colored_line("M32 34 L32 88 M68 34 L68 88", RED, 3)
         + line("M10 34 L4 28 M20 34 L16 26 M90 34 L96 28 M80 34 L84 26", 2.5, MBROWN),
    "tray": p("M6 64 L94 64 L84 84 L16 84 Z", TAN)
          + r(2, 60, 96, 8, TAN, 4) + line("M10 64 L4 56 L20 56 M90 64 L96 56 L80 56", 3)
          + colored_line("M62 44 C72 42 74 54 64 54", BLUE, 3)
          + p("M38 36 L64 36 L62 60 L40 60 Z", BLUE) + e(51, 36, 13, 3, "#7A5230")
          + c(22, 56, 8, TOAST) + c(19, 54, 1.6, BARK, False) + c(25, 58, 1.6, BARK, False)
          + line("M46 30 C44 24 48 20 46 14 M56 30 C54 24 58 20 56 14", 2.5, GRAY),
    "clay": e(26, 74, 18, 12, PINK) + c(70, 72, 14, GOLD)
          + colored_line("M30 48 C36 36 50 44 56 36 C62 28 74 34 78 26", GREEN, 10)
          + c(80, 24, 6, GREEN) + c(81, 22, 1.4, "#222", False)
          + rot(-15, 40, 20, r(26, 12, 26, 14, BLUE, 4))
          + line("M18 70 C22 68 26 68 30 70 M64 68 C68 66 72 68 74 72", 2.5, WHITE),
    "jay": colored_line("M4 82 L96 78", BARK, 6)
         + p("M26 62 L6 78 L14 82 L32 70 Z", BLUE)
         + e(48, 58, 22, 16, BLUE, -15)
         + p("M38 64 C44 76 60 76 66 64 C60 70 46 70 38 64 Z", WOOL)
         + p("M58 28 L54 12 L64 22 L66 10 L70 26 Z", BLUE)
         + c(66, 36, 13, BLUE)
         + p("M60 42 C64 48 74 48 78 40", "none") + line("M56 44 C62 50 72 50 78 44", 3, DARK)
         + p("M78 34 L92 38 L78 41 Z", DARK)
         + c(70, 33, 2.5, "#222", False)
         + line("M36 52 L48 58 M40 46 L52 52", 2.5, DBLUE)
         + line("M46 74 L44 80 M54 74 L54 80", 3),
    # --- page 31-40: ee and ea -----------------------------------------------------------------
    "seed": seed_shape(26, 50, -25) + seed_shape(52, 40, 10) + seed_shape(76, 56, 30) + seed_shape(46, 74, -60),
    "feet": "".join(
        p(f"M{x - 12} {66} C{x - 16} 44 {x - 14} 30 {x} 30 C{x + 14} 30 {x + 14} 46 {x + 10} 66 C{x + 8} 84 {x - 10} 86 {x - 12} 66 Z", SKIN)
        + c(x - 10 + dx, 22, 4.5, SKIN) + c(x - 3 + dx, 19, 4, SKIN) + c(x + 4 + dx, 19, 3.5, SKIN) + c(x + 10 + dx, 22, 3, SKIN)
        for x, dx in ((30, 0), (70, 0))),
    "peel": p("M44 56 C30 64 18 80 10 94 C24 92 40 80 48 66 Z", GOLD)
          + p("M56 56 C70 64 82 80 90 94 C76 92 60 80 52 66 Z", GOLD)
          + p("M46 60 C44 76 46 88 50 96 C54 88 56 76 54 60 Z", PALE)
          + p("M38 58 C36 40 40 24 46 14 L54 14 C60 24 64 40 62 58 C56 64 44 64 38 58 Z", GOLD)
          + r(45, 6, 10, 10, BARK, 2)
          + line("M44 24 C42 34 42 44 44 54", 2.5, "#B88A0F"),
    "eagle": p("M50 44 C36 30 20 22 2 24 C10 32 6 36 14 40 C10 44 14 48 22 50 C28 54 40 54 50 56 Z", BROWN)
           + p("M50 44 C64 30 80 22 98 24 C90 32 94 36 86 40 C90 44 86 48 78 50 C72 54 60 54 50 56 Z", BROWN)
           + p("M40 52 C38 66 44 78 50 80 C56 78 62 66 60 52 Z", BROWN)
           + p("M42 78 L36 92 L50 86 L64 92 L58 78 Z", BROWN)
           + c(50, 36, 11, WOOL)
           + p("M48 40 L58 40 C60 46 54 50 50 46 Z", GOLD)
           + c(46, 34, 2.2, "#222", False) + c(54, 34, 2.2, "#222", False)
           + line("M12 32 L22 36 M88 32 L78 36", 2.5, BARK),
    "bean": rot(-20, 50, 50, p("M14 46 C30 40 50 38 70 40 C82 41 90 44 94 50 C84 58 66 58 50 58 C34 58 22 56 14 54 Z", GREEN)
                + c(30, 50, 4, "#9FD48A", False) + c(44, 50, 4.5, "#9FD48A", False) + c(58, 50, 4.5, "#9FD48A", False) + c(72, 49, 4, "#9FD48A", False)
                + colored_line("M94 50 L98 42", DGREEN, 3))
           + rot(-35, 40, 76, p("M10 72 C26 68 46 68 66 70 C74 71 80 74 82 78 C72 84 54 84 38 84 C24 84 14 80 10 78 Z", GREEN)),
    "beak": p("M2 100 C6 70 20 52 44 50 C60 50 66 64 64 80 L64 100 Z", GOLD)
          + c(42, 44, 26, GOLD)
          + p("M64 34 C80 32 94 40 98 50 C86 48 74 48 64 48 Z", ORANGE)
          + p("M64 48 C76 50 86 52 92 56 C82 60 72 58 64 56 Z", "#D9763F")
          + c(48, 38, 4, "#222", False) + c(49.5, 36.5, 1.3, WHITE, False)
          + p("M30 22 L36 10 L42 20 L48 8 L50 20 Z", GOLD)
          + line("M20 66 C26 60 32 58 38 60", 2.5, "#C48A10"),
    "seat": colored_line("M36 76 L32 96 M64 76 L68 96", GRAY, 4)
          + r(26, 12, 48, 50, RED, 12)
          + line("M40 22 L40 52 M50 22 L50 52 M60 22 L60 52", 2.5, "#C25E5E")
          + p("M18 58 L82 58 C86 58 88 62 86 68 L82 78 L18 78 L14 68 C12 62 14 58 18 58 Z", RED)
          + r(8, 46, 12, 30, GRAY, 4) + r(80, 46, 12, 30, GRAY, 4),
    "tea": e(46, 86, 38, 7, PINK)
         + colored_line("M70 52 C86 50 86 70 70 70", PINK, 4)
         + p("M18 44 L74 44 C74 64 66 82 46 82 C26 82 18 64 18 44 Z", PINK)
         + e(46, 44, 28, 6, "#B0723F")
         + line("M30 36 C26 28 34 24 30 16 M46 36 C42 28 50 24 46 16 M62 36 C58 28 66 24 62 16", 3, GRAY)
         + c(40, 64, 4, WHITE, False) + c(52, 64, 4, WHITE, False) + c(46, 72, 4, WHITE, False),
    "leash": colored_line("M10 14 C4 30 24 34 18 18 C14 8 6 12 10 14", RED, 5)
           + colored_line("M16 30 C30 60 50 48 62 64", RED, 5)
           + r(60, 60, 10, 12, GRAY, 3)
           + p("M60 96 C58 80 64 70 76 70 C88 70 94 80 92 96 Z", TAN)
           + e(78, 62, 16, 13, TAN)
           + e(64, 58, 6, 10, MBROWN, 20) + e(92, 58, 6, 10, MBROWN, -20)
           + c(73, 60, 2.2, "#222", False) + c(83, 60, 2.2, "#222", False) + e(78, 66, 3, 2, "#222", 0, False)
           + colored_line("M64 74 C70 78 86 78 92 74", BLUE, 4),
    "jeans": p("M26 10 L74 10 L80 92 L58 92 L52 40 L48 40 L42 92 L20 92 Z", DBLUE)
           + r(24, 8, 52, 10, DBLUE, 2) + c(50, 13, 2.5, GOLD)
           + line("M50 18 L50 40 M30 22 C34 30 40 30 42 22 M70 22 C66 30 60 30 58 22", 2.5, "#3E6FA8")
           + line("M22 86 L42 86 M58 86 L78 86", 2.5, "#3E6FA8")
           + line("M36 10 L36 18 M64 10 L64 18", 2.5),
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
