"""Cubs Reading (2A) word batch 1 pictures (28: 16 naming words, 12 doing words), approved 2026-11-06
by the orchestrator under user delegation (syllabus/drafts/2A-words-batch1.md), in the house style.

Run: uv run python scripts/pictures/draw_2A_batch1.py <out_dir> [slug ...]
A record only: the SVGs in assets/pictures/ are the source of truth (STATUS.md, picture workflow).
Helpers copied from draw_7A_batch5.py (plus note() from draw_batch4.py).
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


def note(x, y, fill=PURPLE):
    """A music note (no text): head, stem, flag."""
    return (line(f"M{x + 5} {y} L{x + 5} {y - 18} C{x + 9} {y - 14} {x + 14} {y - 13} {x + 13} {y - 6}", 3)
            + e(x, y, 6, 4.5, fill, -20))


def fork(x, y, rot_deg, fill=LGRAY):
    """A fork, handle down, rotated about (x, y): three wide tines with clear gaps."""
    body = (colored_line(f"M{x} {y + 38} L{x} {y}", fill, 5)
            + p(f"M{x - 9} {y + 2} L{x - 9} {y - 22} L{x - 5} {y - 22} L{x - 5} {y - 8} L{x - 2} {y - 8} "
                f"L{x - 2} {y - 22} L{x + 2} {y - 22} L{x + 2} {y - 8} L{x + 5} {y - 8} L{x + 5} {y - 22} "
                f"L{x + 9} {y - 22} L{x + 9} {y + 2} C{x + 9} {y + 8} {x - 9} {y + 8} {x - 9} {y + 2} Z", fill))
    return rot(rot_deg, x, y, body)


def bubble(x, y, rad):
    return c(x, y, rad, LBLUE) + line(f"M{x - rad * 0.5} {y - rad * 0.2} C{x - rad * 0.4} {y - rad * 0.5} {x - rad * 0.2} {y - rad * 0.6} {x} {y - rad * 0.6}", 1.5, WHITE)


PICS = {
    # --- naming words ---------------------------------------------------------------------
    "pencil": rot(-35, 50, 50,
                  r(8, 41, 12, 18, PINK, 3) + r(20, 41, 8, 18, GRAY) + r(28, 41, 46, 18, GOLD)
                  + line("M28 50 L74 50", 2)
                  + p("M74 41 L94 50 L74 59 Z", WHEAT) + p("M87 46.9 L94 50 L87 53.1 Z", DARK)),
    "button": c(50, 50, 40, BLUE) + c(50, 50, 31, "none")
              + c(41, 41, 5, WHITE) + c(59, 41, 5, WHITE) + c(41, 59, 5, WHITE) + c(59, 59, 5, WHITE),
    "ribbon": p("M46 50 L30 88 L38 84 L42 92 L54 52 Z", PINK) + p("M54 50 L70 88 L62 84 L58 92 L46 52 Z", PINK)
              + p("M50 44 C36 20 8 24 12 44 C14 60 36 58 50 44 Z", PINK)
              + p("M50 44 C64 20 92 24 88 44 C86 60 64 58 50 44 Z", PINK)
              + line("M44 42 C34 34 22 36 20 42 M56 42 C66 34 78 36 80 42", 2.5)
              + r(42, 36, 16, 16, PINK, 5),
    "helmet": colored_line("M30 68 L44 86 L60 68", GRAY, 4) + r(40, 82, 9, 7, DARK, 2)
              + p("M10 66 C10 34 34 16 58 16 C82 16 94 36 94 58 C94 64 90 68 84 68 Z", GREEN)
              + p("M84 48 C92 48 98 52 98 58 L86 62 Z", DGREEN)
              + r(10, 60, 80, 9, DGREEN, 4)
              + r(28, 30, 12, 6, DARK, 3) + r(46, 24, 12, 6, DARK, 3) + r(64, 28, 12, 6, DARK, 3),
    "magnet": line("M30 6 L30 0 M18 8 L14 3 M70 6 L70 0 M82 8 L86 3", 3, GRAY)
              + colored_line("M30 26 L30 56 C30 88 70 88 70 56 L70 26", RED, 18)
              + r(19, 12, 22, 16, LGRAY, 2) + r(59, 12, 22, 16, LGRAY, 2),
    "candle": e(50, 90, 28, 6, LGRAY)
              + r(38, 36, 24, 54, BLUE, 3)
              + line("M38 50 L62 44 M38 64 L62 58 M38 78 L62 72", 4, WHITE)
              + line("M50 36 L50 28", 3)
              + drop(50, 20, 7, GOLD) + drop(50, 22, 3.5, ORANGE),
    "napkin": p("M6 22 L60 22 L74 36 L74 88 L6 88 Z", LBLUE)
              + line("M16 22 L16 88 M6 78 L74 78", 3, DBLUE)
              + p("M60 22 L60 36 L74 36 Z", DBLUE)
              + fork(87, 52, 0),
    "kettle": line("M90 34 C86 28 94 22 90 14 M80 36 C76 30 84 24 80 16", 3, GRAY)
              + colored_line("M30 46 C30 18 70 18 70 46", DARK, 5)
              + p("M74 66 L92 46 L97 50 L82 74 Z", RED)
              + p("M22 86 C18 62 28 42 50 42 C72 42 82 62 78 86 Z", RED)
              + r(18, 84, 64, 8, DARK, 4)
              + e(50, 42, 16, 5, RED) + c(50, 35, 5, DARK),
    "rabbit": line("M8 92 L94 92", 3)
              + e(68, 20, 5, 16, TAN, -12) + e(80, 22, 5, 16, TAN, 14)
              + e(68, 21, 2, 10, PINK, -12, False) + e(80, 23, 2, 10, PINK, 14, False)
              + c(20, 58, 8, WHITE)
              + e(46, 66, 28, 20, TAN) + e(30, 80, 14, 9, TAN)
              + e(66, 88, 9, 4, TAN)
              + c(74, 46, 15, TAN)
              + c(80, 43, 3, "#222", False) + c(88, 49, 2.8, PINK, False)
              + line("M86 54 L96 52 M86 56 L95 59", 1.8),
    "robin": line("M48 76 L46 92 M60 76 L62 92 M40 92 L52 92 M56 92 L68 92", 3)
             + p("M78 50 L98 40 L98 58 L80 62 Z", BROWN)
             + e(54, 58, 28, 20, MBROWN)
             + e(40, 64, 17, 14, ORANGE)
             + p("M50 50 C62 42 80 48 82 60 C70 66 58 64 50 50 Z", BROWN)
             + c(30, 40, 13, MBROWN)
             + p("M18 38 L6 42 L18 46 Z", GOLD)
             + c(27, 37, 3.4, WHITE) + c(27, 37, 2, "#222", False),
    "tulip": colored_line("M50 92 L50 50", DGREEN, 5)
             + p("M50 86 C34 82 24 66 26 52 C40 58 48 70 50 86 Z", GREEN)
             + p("M50 80 C66 76 76 62 74 48 C60 54 52 64 50 80 Z", GREEN)
             + p("M28 14 L40 28 L50 10 L60 28 L72 14 C76 42 66 56 50 56 C34 56 24 42 28 14 Z", RED)
             + line("M40 28 C42 40 46 50 50 56 M60 28 C58 40 54 50 50 56", 2.5),
    "pony": colored_line("M22 50 C10 54 8 70 12 80", BARK, 6)
            + r(30, 62, 9, 26, MBROWN, 3) + r(58, 62, 9, 26, MBROWN, 3)
            + r(24, 62, 9, 28, BROWN, 3) + r(52, 62, 9, 28, BROWN, 3)
            + r(24, 86, 9, 5, DARK, 1) + r(52, 86, 9, 5, DARK, 1)
            + e(46, 56, 28, 16, BROWN)
            + p("M78 20 L80 10 L86 20 Z", BROWN)
            + p("M62 52 L70 26 C72 16 88 16 92 28 L96 40 C96 48 88 50 84 46 L78 40 L76 60 Z", BROWN)
            + p("M64 48 L70 22 C72 14 80 12 84 16 L76 26 L72 50 Z", BARK)
            + c(84, 30, 2.6, "#222", False) + c(93, 42, 1.6, "#222", False),
    "hamster": e(36, 92, 8, 4, PINK) + e(64, 92, 8, 4, PINK)
               + c(28, 26, 9, TOAST) + c(72, 26, 9, TOAST) + c(28, 26, 4.5, PINK, False) + c(72, 26, 4.5, PINK, False)
               + e(50, 58, 36, 34, TOAST)
               + e(50, 74, 20, 16, WHITE)
               + eyes(38, 38, 62, 3.4) + e(50, 47, 3.2, 2.2, PINK, 0, False)
               + line("M46 51 C48 54 52 54 54 51", 2)
               + c(32, 50, 4.5, PINK, False) + c(68, 50, 4.5, PINK, False)
               + line("M42 48 L24 44 M58 48 L76 44", 1.5)
               + e(50, 72, 5, 7, WHEAT) + c(43, 72, 4, PINK) + c(57, 72, 4, PINK),
    "sandwich": p("M10 74 L90 74 L90 84 C90 88 86 90 82 90 L18 90 C14 90 10 88 10 84 Z", WHEAT)
                + p("M12 66 L88 66 L88 74 L66 74 L62 82 L58 74 L12 74 Z", GOLD)
                + r(14, 60, 72, 7, RED, 3)
                + p("M8 58 C14 52 20 60 26 54 C32 60 38 52 44 58 C50 52 56 60 62 54 C68 60 74 52 80 58 C86 54 92 58 92 62 L8 62 Z", GREEN)
                + p("M10 56 L46 14 C48 12 52 12 54 14 L90 56 Z", WHEAT)
                + p("M22 50 L48 22 C49 21 51 21 52 22 L78 50 Z", PALE),
    "pebble": p("M2 88 C30 76 70 76 98 88 L98 98 L2 98 Z", WHEAT)
              + e(18, 86, 6, 4, LGRAY) + e(84, 86, 7, 4.5, LGRAY)
              + e(50, 60, 32, 21, GRAY)
              + line("M30 50 C36 44 46 42 54 43", 3, WHITE)
              + c(62, 64, 1.6, DARK, False) + c(42, 68, 1.6, DARK, False) + c(70, 54, 1.6, DARK, False),
    "lizard": colored_line("M50 72 C50 88 68 94 76 84 C82 76 72 68 66 76", GREEN, 7)
              + colored_line("M43 40 L31 34 L27 25", GREEN, 5) + colored_line("M57 40 L69 34 L73 25", GREEN, 5)
              + colored_line("M43 64 L31 70 L27 79", GREEN, 5) + colored_line("M57 64 L69 70 L73 79", GREEN, 5)
              + e(50, 52, 11, 23, GREEN)
              + e(50, 24, 9, 12, GREEN)
              + c(45, 20, 2.4, "#222", False) + c(55, 20, 2.4, "#222", False)
              + c(47, 46, 2.2, DGREEN, False) + c(54, 54, 2.2, DGREEN, False) + c(47, 62, 2.2, DGREEN, False),

    # --- doing words: a child doing it -------------------------------------------------------
    "carry": line("M6 94 L94 94", 3)
             + limb("M32 62 L28 78 L22 92", BLUE, 8) + limb("M40 62 L46 78 L52 92", BLUE, 8)
             + shoe(20, 92) + shoe(56, 92)
             + p("M26 36 C26 30 44 30 44 36 L44 64 L26 64 Z", GREEN)
             + limb("M36 40 L48 54")
             + r(46, 30, 40, 36, TAN, 3) + r(62, 30, 8, 36, WHEAT, 0)
             + c(48, 64, 5.5, SKIN)
             + head(35, 20, 12),
    "bake": line("M6 94 L94 94", 3)
            + line("M64 26 C60 20 68 16 64 10 M78 26 C74 20 82 16 78 10", 3, GRAY)
            + limb("M26 62 L24 78 L22 92", BLUE, 8) + limb("M34 62 L38 78 L40 92", BLUE, 8)
            + shoe(20, 92) + shoe(44, 92)
            + p("M20 36 C20 30 38 30 38 36 L40 64 L20 64 Z", PURPLE)
            + p("M22 44 L38 44 L39 64 L21 64 Z", WHITE)
            + limb("M34 40 L46 50")
            + r(44, 40, 50, 5, GRAY, 2)
            + e(54, 36, 6, 3.5, TOAST) + e(68, 36, 6, 3.5, TOAST) + e(82, 36, 6, 3.5, TOAST)
            + e(48, 46, 7, 6, RED) + e(90, 46, 7, 6, RED)
            + head(29, 20, 12),
    "sweep": c(78, 88, 2.5, GRAY) + c(86, 84, 2, GRAY) + c(90, 90, 2.5, GRAY) + c(82, 92, 2, GRAY)
             + line("M6 96 L96 96", 3)
             + line("M90 70 L98 66 M88 78 L98 78", 2.5, GRAY)
             + limb("M28 62 L26 78 L22 94", BLUE, 8) + limb("M36 62 L42 78 L44 94", BLUE, 8)
             + shoe(20, 94) + shoe(48, 94)
             + p("M22 36 C22 30 40 30 40 36 L42 64 L22 64 Z", ORANGE)
             + colored_line("M44 24 L68 76", BROWN, 4)
             + p("M60 72 L76 64 L90 88 L70 96 Z", GOLD) + line("M72 76 L80 90 M66 80 L76 93", 2)
             + limb("M36 40 L46 36 L50 38") + limb("M34 46 L50 52 L58 56")
             + head(31, 20, 12),
    "skip": line("M6 96 L96 96", 3)
            + line("M10 80 C14 70 20 70 22 78 M78 84 C82 76 88 76 90 82", 2.5, GRAY)
            + limb("M44 36 L32 46 L24 40") + limb("M56 36 L66 26 L72 16")
            + limb("M46 58 L40 72 L34 84", BLUE, 8) + limb("M54 58 L66 64 L64 76", BLUE, 8)
            + shoe(32, 86, -20) + shoe(66, 78, 10)
            + p("M40 32 C40 26 60 26 60 32 L60 60 L40 60 Z", RED) + head(50, 17, 12),
    "tiptoe": line("M6 94 L94 94", 3)
              + e(20, 92, 4, 2, LGRAY, 0, False) + e(32, 90, 4, 2, LGRAY, 0, False)
              + limb("M46 60 L42 76 L44 86", BLUE, 8) + limb("M54 60 L60 76 L64 86", BLUE, 8)
              + shoe(44, 89, 70) + shoe(65, 89, 70)
              + limb("M44 36 L30 44 L22 40")
              + p("M42 32 C42 26 58 26 58 32 L58 62 L42 62 Z", BLUE)
              + head(50, 18, 12, mouth=None)
              + limb("M56 36 L58 42 L51 34") + colored_line("M51 32 L51 21", SKIN, 3.5),
    "wiggle": line("M14 34 C8 40 14 46 8 52 M20 58 C14 64 20 70 14 76 M86 34 C92 40 86 46 92 52 M80 58 C86 64 80 70 86 76", 3, GRAY)
              + limb("M44 36 L32 30 L30 16") + limb("M56 36 L68 30 L70 16")
              + limb("M44 60 L36 76 L38 90", BLUE, 8) + limb("M56 60 L64 76 L62 90", BLUE, 8)
              + shoe(36, 91) + shoe(64, 91)
              + rot(-12, 50, 46, p("M40 32 C40 26 60 26 60 32 L62 62 L38 62 Z", GOLD))
              + head(50, 17, 12, closed=True),
    "giggle": p("M10 100 C12 82 28 76 50 76 C72 76 88 82 90 100 Z", GREEN)
              + child_face(50, 44, 28, 30, eyes_kind="happy", mouth=None)
              + e(50, 60, 9, 6, "#7A2E2E") + e(50, 57, 7, 2.2, WHITE, 0, False)
              + c(32, 54, 5, PINK, False) + c(68, 54, 5, PINK, False)
              + line("M84 18 C90 22 90 30 86 34 M90 10 C98 16 98 32 92 38 M16 18 C10 22 10 30 14 34", 3, GRAY),
    "munch": p("M6 100 C8 84 22 78 40 78 C58 78 70 84 72 100 Z", BLUE)
             + child_face(40, 46, 26, 28, mouth=None)
             + e(44, 62, 6, 5, "#7A2E2E")
             + colored_line("M78 40 L80 32", BROWN, 3)
             + p("M68 50 C66 40 76 38 80 44 C84 38 98 40 96 54 C94 70 86 78 80 76 C74 78 68 72 68 68 C74 64 74 54 68 50 Z", RED)
             + p("M68 50 C74 54 74 64 68 68 C71 62 71 56 68 50 Z", PALE)
             + c(56, 76, 1.8, WHEAT, False) + c(62, 82, 1.8, WHEAT, False),
    "sniff": p("M6 100 C8 84 22 78 40 78 C58 78 70 84 72 100 Z", PURPLE)
             + child_face(38, 46, 26, 28, eyes_kind="happy")
             + colored_line("M78 96 L72 56", DGREEN, 4)
             + c(72, 40, 7, PINK) + c(82, 46, 7, PINK) + c(80, 58, 7, PINK) + c(66, 58, 7, PINK) + c(62, 46, 7, PINK)
             + c(72, 51, 6, GOLD)
             + line("M58 34 C54 30 58 26 54 22 M66 28 C62 24 66 20 62 16", 2.5, GRAY),
    "stir": colored_line("M54 58 L70 24", BROWN, 5)
            + colored_line("M84 8 L72 24", ORANGE, 12) + c(70, 26, 7, SKIN)
            + p("M12 56 L88 56 C86 82 70 94 50 94 C30 94 14 82 12 56 Z", BLUE)
            + e(50, 56, 38, 9, WHEAT)
            + line("M30 56 C36 50 60 50 66 56 C60 60 42 60 40 56", 2.5, TOAST)
            + line("M20 70 C40 76 60 76 80 70", 3, DBLUE),
    "scrub": colored_line("M8 12 L50 12 L50 24", LGRAY, 9) + r(46, 22, 8, 5, GRAY, 1)
             + drop(50, 34, 2.5, LBLUE) + drop(44, 40, 2, LBLUE) + drop(56, 40, 2, LBLUE)
             + colored_line("M36 72 L26 96", BLUE, 12) + colored_line("M64 72 L74 96", BLUE, 12)
             + e(40, 62, 13, 18, SKIN, -18) + e(28, 58, 4, 8, SKIN, -40)
             + e(60, 62, 13, 18, SKIN, 18) + e(72, 58, 4, 8, SKIN, 40)
             + bubble(50, 54, 6) + bubble(40, 50, 5) + bubble(60, 66, 5) + bubble(44, 70, 4) + bubble(56, 48, 4)
             + bubble(20, 40, 7) + bubble(82, 36, 8) + bubble(88, 58, 5) + bubble(14, 66, 5) + bubble(76, 18, 5),
    "listen": p("M6 100 C8 84 22 78 40 78 C58 78 70 84 72 100 Z", ORANGE)
              + child_face(38, 46, 26, 28)
              + limb("M58 80 C66 74 70 66 68 58")
              + palm(68, 48, -15, s=0.85)
              + note(82, 30, BLUE) + note(70, 14, GOLD) + note(84, 62, PURPLE),
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
