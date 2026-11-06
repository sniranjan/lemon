"""Chicks Reading (7A) word batch 5 pictures (40 words, approved 2026-11-06) in the house style,
plus redraws of two batch-4 pictures (neck: no jewelry look; pour: a milk pitcher, not a watering can).

Run: uv run python scripts/pictures/draw_7A_batch5.py <out_dir> [slug ...]
A record only: the SVGs in assets/pictures/ are the source of truth (STATUS.md, picture workflow).
Helpers merged from draw_7A_batch4.py and draw_batch5.py.
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


def octopus_arms():
    arms = ["M28 54 C18 62 6 60 6 72 C6 80 14 80 14 74",
            "M32 58 C26 70 16 76 18 88 C20 94 28 92 26 86",
            "M38 60 C36 74 28 82 32 94",
            "M45 62 C44 76 42 84 44 96",
            "M55 62 C56 76 58 84 56 96",
            "M62 60 C64 74 72 82 68 94",
            "M68 58 C74 70 84 76 82 88 C80 94 72 92 74 86",
            "M72 54 C82 62 94 60 94 72 C94 80 86 80 86 74"]
    return "".join(colored_line(a, PURPLE, 7) for a in arms)


PICS = {
    # --- page 81: hippo, popcorn ------------------------------------------------------------
    "hippo": r(38, 64, 13, 26, HIPPO, 5) + r(72, 64, 13, 26, HIPPO, 5)
           + line("M92 50 L98 58", 3)
           + e(62, 54, 32, 22, HIPPO)
           + p("M6 64 C6 74 14 78 26 78 C38 78 46 72 48 64 L44 58 L8 58 Z", HIPPO)
           + p("M10 60 L44 60 L46 44 L14 36 Z", "#C97A8A")
           + p("M14 60 L17 52 L20 60 Z", WHITE) + p("M36 60 L39 52 L42 60 Z", WHITE)
           + p("M12 36 C6 24 16 16 28 18 C42 18 52 28 54 42 L46 48 C36 42 22 40 12 36 Z", HIPPO)
           + p("M18 38 L21 45 L24 39 Z", WHITE)
           + e(44, 16, 3.5, 5, HIPPO) + c(36, 26, 3, "#222", False) + c(16, 24, 1.8, "#222", False)
           + line("M4 92 L96 92", 3),
    "popcorn": c(34, 32, 8, WHITE) + c(46, 26, 9, WHITE) + c(58, 24, 8, WHITE) + c(68, 32, 8, WHITE)
             + c(40, 18, 6, WHITE) + c(56, 14, 6, WHITE)
             + p("M24 38 L76 38 L67 94 L33 94 Z", RED)
             + p("M37 38 L44 38 L46.5 94 L42.5 94 Z", WHITE).replace(S, 'stroke="none"')
             + p("M56 38 L63 38 L57.5 94 L53.5 94 Z", WHITE).replace(S, 'stroke="none"')
             + line("M37 38 L42.5 94 M44 38 L46.5 94 M56 38 L53.5 94 M63 38 L57.5 94", 2.5)
             + p("M24 38 L76 38 L67 94 L33 94 Z", "none")
             + r(20, 34, 60, 9, RED, 4),
    # --- page 82: mirror, digger ------------------------------------------------------------
    "mirror": colored_line("M50 74 L50 96", PINK, 9)
            + e(50, 40, 32, 37, PINK) + e(50, 40, 24, 29, LBLUE)
            + head(52, 46, 12)
            + line("M32 26 L38 18 M30 36 L34 31", 3, WHITE),
    "digger": line("M4 92 L96 92", 3)
            + p("M64 92 C68 80 84 78 96 92 Z", DIRT)
            + r(8, 74, 54, 16, DARK, 8) + wheel(18, 82, 5) + wheel(35, 82, 5) + wheel(52, 82, 5)
            + colored_line("M46 58 L66 24 L84 46", GOLD, 8)
            + p("M78 42 L94 46 L92 66 C86 72 76 68 74 58 Z", GRAY) + line("M92 66 L96 70 M86 69 L88 74", 3)
            + r(10, 50, 46, 24, GOLD, 4)
            + r(14, 26, 26, 26, GOLD, 3) + r(19, 31, 16, 14, LBLUE, 2)
            + c(66, 24, 3, DARK, False),
    # --- page 83: paint, stick --------------------------------------------------------------
    "paint": colored_line("M60 30 L52 96 M84 30 L92 96 M72 40 L72 92", MBROWN, 4)
           + r(50, 8, 44, 46, LBLUE, 3)
           + line("M72 14 L72 18 M72 42 L72 46 M58 30 L62 30 M82 30 L86 30 M62 20 L64 22 M80 38 L82 40 M82 20 L80 22 M62 40 L64 38", 3, GOLD)
           + c(72, 30, 8, GOLD, False)
           + '<path d="M50.5 46 C60 42 82 42 93.5 46 L93.5 53.5 L50.5 53.5 Z" fill="#7FBF6A"/>'
           + r(50, 8, 44, 46, "none", 3)
           + limb("M18 80 L16 96", BLUE, 8) + limb("M30 80 L32 96", BLUE, 8) + shoe(14, 96) + shoe(34, 96)
           + p("M12 82 L14 58 C16 52 32 52 34 58 L36 82 Z", RED)
           + colored_line("M44 46 L54 34", MBROWN, 3) + c(55, 33, 3, GOLD)
           + limb("M30 60 L38 54 L44 46")
           + head(24, 40, 13),
    "stick": colored_line("M10 88 L88 14", MBROWN, 10)
           + colored_line("M56 46 L88 52", MBROWN, 7)
           + colored_line("M32 67 L24 48", MBROWN, 6)
           + p("M88 52 C92 42 100 42 98 46 C96 52 92 54 88 52 Z", GREEN)
           + line("M30 72 L36 68 M50 58 L56 53 M68 42 L74 37", 2.5, BARK),
    # --- page 84: apron, panda --------------------------------------------------------------
    "apron": line("M38 20 C36 4 64 4 62 20", 4)
           + colored_line("M22 46 C12 48 8 56 6 66 M78 46 C88 48 92 56 94 66", PINK, 4)
           + p("M36 18 L64 18 L66 42 C78 44 82 52 80 62 L76 92 C68 96 32 96 24 92 L20 62 C18 52 22 44 34 42 Z", PINK)
           + r(36, 60, 28, 18, RED, 4) + line("M36 66 L64 66", 2.5)
           + c(44, 30, 2.5, WHITE, False) + c(56, 30, 2.5, WHITE, False) + c(30, 54, 2.5, WHITE, False)
           + c(70, 54, 2.5, WHITE, False) + c(32, 86, 2.5, WHITE, False) + c(68, 86, 2.5, WHITE, False) + c(50, 86, 2.5, WHITE, False),
    "panda": c(32, 16, 7, DARK) + c(68, 16, 7, DARK)
           + e(50, 66, 28, 26, WOOL)
           + e(30, 88, 12, 9, DARK) + e(70, 88, 12, 9, DARK)
           + e(26, 62, 8, 14, DARK, 20)
           + colored_line("M82 34 L78 96", GREEN, 5) + line("M76 52 L84 52 M75 74 L83 74", 2.5)
           + p("M82 36 C88 28 98 28 98 32 C94 38 88 40 82 36 Z", GREEN)
           + e(74, 60, 8, 14, DARK, -20)
           + c(50, 36, 22, WOOL)
           + e(41, 34, 6, 8, DARK, 30, False) + e(59, 34, 6, 8, DARK, -30, False)
           + c(42, 33, 2.2, WHITE, False) + c(58, 33, 2.2, WHITE, False)
           + e(50, 44, 3.5, 2.5, "#222", 0, False)
           + line("M46 49 C48 51 52 51 54 49", 2),
    # --- page 85: honey, rattle -------------------------------------------------------------
    "honey": colored_line("M60 36 L80 6", MBROWN, 4) + c(81, 5, 3.5, MBROWN)
           + p("M22 40 C10 52 12 84 28 92 L72 92 C88 84 90 52 78 40 Z", TAN)
           + line("M18 70 C40 74 60 74 82 70", 2.5)
           + r(20, 32, 60, 10, TAN, 5)
           + p("M24 37 L76 37 L76 44 C76 52 71 52 71 46 L60 46 C60 60 52 60 52 46 L40 46 C40 54 34 54 34 46 L24 46 Z", GOLD),
    "rattle": line("M80 18 C88 24 90 32 88 40 M86 10 C96 18 98 32 94 42 M20 18 C14 22 12 28 12 34", 3, GRAY)
            + colored_line("M28 92 L46 60", BLUE, 8) + c(26, 94, 6, BLUE) + e(46, 60, 9, 4, GOLD, -60)
            + c(56, 38, 24, RED)
            + line("M33 34 C44 42 66 42 79 34", 3)
            + c(44, 26, 4, GOLD) + c(62, 24, 4, GOLD) + c(48, 52, 4, GOLD) + c(68, 48, 4, GOLD),
    # --- page 86: tongue, bottle ------------------------------------------------------------
    "tongue": p("M18 100 C20 90 32 86 50 86 C68 86 80 90 82 100 Z", BLUE)
            + r(42, 74, 16, 14, SKIN)
            + child_face(50, 44, 30, 34, eyes_kind="happy", mouth=None)
            + c(28, 56, 4.5, PINK, False) + c(72, 56, 4.5, PINK, False)
            + e(50, 62, 9, 4.5, "#7A2E2E")
            + p("M42 62 C41 80 59 80 58 62 Z", "#E0607A")
            + line("M50 65 L50 72", 2),
    "bottle": p("M42 24 C42 14 46 8 50 8 C54 8 58 14 58 24 Z", WHEAT)
            + r(32, 34, 36, 58, LBLUE, 10)
            + '<path d="M33.5 72 L66.5 72 L66.5 82 C66.5 88 63 90.5 58 90.5 L42 90.5 C37 90.5 33.5 88 33.5 82 Z" fill="#F4F1EA"/>'
            + line("M33.5 72 L66.5 72", 2.5) + r(32, 34, 36, 58, "none", 10)
            + line("M38 44 L46 44 M38 52 L44 52 M38 60 L46 60", 2.5)
            + r(32, 22, 36, 13, PINK, 4),
    # --- page 87: octopus, waffle -----------------------------------------------------------
    "octopus": octopus_arms()
             + p("M22 46 C18 12 82 12 78 46 C78 62 22 62 22 46 Z", PURPLE)
             + c(40, 38, 6, WHITE) + c(60, 38, 6, WHITE) + c(41, 39, 3, "#222", False) + c(61, 39, 3, "#222", False)
             + c(32, 48, 3.5, PINK, False) + c(68, 48, 3.5, PINK, False)
             + line("M44 50 C47 54 53 54 56 50", 2.5),
    "waffle": r(14, 14, 72, 72, GOLD, 10)
              + "".join(r(21 + 16.5 * i, 21 + 16.5 * j, 10.5, 10.5, "#D4970F", 2) for i in range(4) for j in range(4))
              + rot(-8, 50, 48, r(40, 42, 20, 14, PALE, 3)),
    # --- page 88: blow, cactus --------------------------------------------------------------
    "blow": line("M4 96 L96 96", 3)
          + p("M4 96 C4 78 10 68 26 68 C40 68 46 78 46 96 Z", GREEN)
          + head(26, 44, 18, mouth=None)
          + c(36, 52, 5, PINK, False) + c(39, 51, 3.2, "#222", False)
          + line("M48 46 L58 44 M48 52 L60 52 M48 58 L58 60", 3, GRAY)
          + r(58, 72, 36, 24, PINK, 4) + p("M58 76 C62 82 66 82 68 76 C72 82 78 82 80 76 C84 82 88 82 94 76 L94 72 L58 72 Z", WHITE)
          + r(73, 50, 7, 22, BLUE, 2)
          + p("M76 50 C72 44 76 38 84 34 C84 40 84 46 78 50 Z", GOLD),
    "cactus": colored_line("M40 52 L28 52 L28 34", GREEN, 11) + colored_line("M60 44 L72 44 L72 26", GREEN, 11)
            + p("M38 74 L38 24 C38 10 62 10 62 24 L62 74 Z", GREEN)
            + line("M44 22 L42 19 M56 30 L58 27 M44 44 L42 41 M56 54 L58 51 M45 64 L43 61 M26 40 L23 39 M74 32 L77 31", 2.5)
            + line("M50 22 L50 70", 2.5, DGREEN)
            + c(50, 10, 4.5, PINK)
            + p("M30 76 L70 76 L66 96 L34 96 Z", ORANGE) + r(26, 70, 48, 9, ORANGE, 3),
    # --- page 89: crown, ladybug ------------------------------------------------------------
    "crown": p("M14 80 L12 28 L26 50 L31 22 L42 48 L50 14 L58 48 L69 22 L74 50 L88 28 L86 80 Z", GOLD)
           + c(12, 26, 4, RED) + c(31, 20, 4, BLUE) + c(50, 12, 4, RED) + c(69, 20, 4, BLUE) + c(88, 26, 4, RED)
           + r(12, 70, 76, 16, GOLD, 3) + c(30, 78, 4.5, RED) + c(50, 78, 4.5, BLUE) + c(70, 78, 4.5, GREEN),
    "ladybug": line("M14 46 L4 42 M12 60 L2 62 M16 74 L6 82 M86 46 L96 42 M88 60 L98 62 M84 74 L94 82", 3)
             + line("M42 18 C38 10 32 8 28 10 M58 18 C62 10 68 8 72 10", 3) + c(28, 10, 3, "#222", False) + c(72, 10, 3, "#222", False)
             + e(50, 26, 17, 13, DARK)
             + c(50, 58, 33, RED)
             + line("M50 26 L50 91", 3)
             + c(35, 46, 6, DARK, False) + c(65, 46, 6, DARK, False) + c(30, 66, 5.5, DARK, False) + c(70, 66, 5.5, DARK, False)
             + c(41, 80, 4.5, DARK, False) + c(59, 80, 4.5, DARK, False)
             + c(43, 22, 2.5, WHITE, False) + c(57, 22, 2.5, WHITE, False),
    # --- page 90: melon, potty --------------------------------------------------------------
    "melon": p("M50 10 L90 72 C70 92 30 92 10 72 Z", DGREEN)
           + p("M50 16 L82 68 C66 81 34 81 18 68 Z", "#D5E8B8")
           + p("M50 18 L78 64 C64 74 36 74 22 64 Z", RED)
           + "".join(e(x, y, 1.8, 3, "#222", 0, False) for x, y in ((50, 36), (42, 50), (58, 50), (34, 62), (50, 62), (66, 62))),
    "potty": colored_line("M24 58 C12 56 12 70 24 70 M76 58 C88 56 88 70 76 70", BLUE, 4)
           + p("M28 58 C26 30 34 20 50 20 C66 20 74 30 72 58 Z", BLUE)
           + p("M22 60 L78 60 L72 88 C70 94 30 94 28 88 Z", BLUE)
           + e(30, 92, 6, 3, BLUE) + e(70, 92, 6, 3, BLUE)
           + e(50, 60, 32, 11, LBLUE) + e(50, 61, 19, 6, DARK, 0, False)
           + p("M42 70 C42 62 58 62 58 70 Z", BLUE)
           + star(50, 80, 6, GOLD),
    # --- page 91: gray, friend --------------------------------------------------------------
    "gray": crayon("#8E8E8E", "#5E5E5E"),
    "friend": heart(50, 14, 6, PINK)
            + limb("M26 70 L24 92", BLUE, 7) + limb("M34 70 L36 92", BLUE, 7) + shoe(22, 93) + shoe(38, 93)
            + limb("M66 74 L65 92") + limb("M74 74 L75 92") + shoe(63, 93, 0, PURPLE) + shoe(77, 93, 0, PURPLE)
            + limb("M22 46 L14 62") + limb("M78 46 L86 62")
            + p("M20 44 C20 38 40 38 40 44 L42 72 L18 72 Z", RED)
            + p("M60 42 C62 38 78 38 80 42 L86 76 L54 76 Z", PURPLE)
            + limb("M38 48 L50 60 L62 48") + c(50, 60, 5, SKIN)
            + head(30, 28, 12) + head(70, 28, 12, hair=GOLD),
    # --- page 92: shovel, dolphin -----------------------------------------------------------
    "shovel": p("M46 96 C54 82 86 80 98 96 Z", TAN)
            + colored_line("M22 16 L58 64", GOLD, 6) + colored_line("M12 22 L30 10", GOLD, 6)
            + p("M50 58 L70 46 L90 78 C88 90 72 94 64 86 Z", BLUE),
    "dolphin": p("M0 88 C12 80 22 94 34 86 C46 78 54 94 66 86 C78 78 88 94 100 86 L100 100 L0 100 Z", BLUE)
             + p("M24 72 L8 68 L14 80 L10 90 L26 80 Z", DOLPHIN)
             + p("M48 34 L54 18 L62 30 Z", DOLPHIN)
             + p("M22 78 C26 42 54 24 80 34 L94 38 L82 44 C70 42 56 46 46 58 C38 66 32 74 28 82 Z", DOLPHIN)
             + p("M52 48 L56 62 L64 48 Z", DOLPHIN)
             + c(76, 36, 2.2, "#222", False) + line("M82 42 C86 42 90 41 93 39", 2)
             + drop(14, 58, 3, LBLUE) + drop(88, 66, 3, LBLUE) + drop(20, 46, 2.5, LBLUE),
    # --- page 93: yawn, bagel ---------------------------------------------------------------
    "yawn": p("M10 100 C12 82 26 74 46 74 C66 74 80 82 82 100 Z", ORANGE)
          + limb("M70 80 L84 52 L86 24", SKIN, 8) + c(86, 20, 6.5, SKIN)
          + c(46, 44, 26, SKIN)
          + p("M20 42 C18 12 74 12 72 42 C64 32 54 26 46 26 C38 26 28 32 20 42 Z", BROWN)
          + line("M31 42 C34 45 38 45 41 42 M51 42 C54 45 58 45 61 42", 2.5)
          + e(46, 58, 7, 9.5, "#7A2E2E") + e(46, 63, 4, 3, "#E0607A", 0, False)
          + palm(24, 62, 25, SKIN, 0.8),
    "bagel": ring(50, 52, 38, 11, TOAST)
           + line("M24 36 C30 26 40 20 52 20", 3, "#F0C890")
           + "".join(e(x, y, 1.6, 2.6, WHITE, a, False) for x, y, a in
                     ((30, 46, 20), (38, 30, -30), (56, 26, 40), (70, 34, -10), (78, 52, 30), (70, 70, -40),
                      (52, 80, 10), (34, 72, 50), (24, 58, -20), (62, 50, 0), (40, 56, 30), (50, 36, 60))),
    # --- page 94: sandal, basket ------------------------------------------------------------
    # side view, toe to the right: heel cup, ankle strap with buckle, instep strap, toe strap, open toe
    "sandal": '<g transform="translate(0 8)">' + p("M10 72 C8 54 12 40 26 36 L32 46 C22 50 20 60 22 72 Z", BLUE)
            + colored_line("M26 40 C36 36 48 40 56 50", BLUE, 6)
            + p("M38 72 L48 46 L57 50 L47 72 Z", BLUE)
            + p("M58 72 C60 54 70 46 82 50 C90 53 92 62 92 72 L83 72 C83 64 80 59 74 59 C68 59 66 65 66 72 Z", BLUE)
            + p("M4 76 C4 70 10 68 18 68 L88 68 C98 68 99 76 95 82 L10 86 C6 86 4 82 4 76 Z", TAN)
            + line("M8 78 L94 76", 2.5, BARK)
            + r(36, 33, 10, 11, GOLD, 2) + "</g>",
    "basket": c(38, 40, 10, RED) + r(52, 30, 15, 15, BLUE, 2) + colored_line("M22 48 C22 6 78 6 78 48", TAN, 6)
            + p("M12 46 L88 46 L80 90 C78 94 22 94 20 90 Z", TAN)
            + line("M16 62 L84 62 M18 76 L82 76 M30 50 L32 90 M44 50 L45 92 M56 50 L55 92 M70 50 L68 90", 2.5, BARK)
            + r(8, 42, 84, 10, MBROWN, 5),
    # --- page 95: worm, cart ----------------------------------------------------------------
    "worm": p("M0 68 L100 68 L100 100 L0 100 Z", DIRT)
          + c(20, 84, 2, BARK, False) + c(46, 90, 2, BARK, False) + c(76, 82, 2, BARK, False) + c(88, 94, 2, BARK, False)
          + e(16, 69, 9, 3, DARK, 0, False)
          + colored_line("M16 68 C20 48 32 44 40 56 C48 68 58 68 64 56 C70 44 78 42 84 50", PINK, 12)
          + line("M28 52 L34 48 M42 60 L48 58 M60 58 L66 62 M74 46 L76 52", 2)
          + c(84, 50, 8, PINK) + c(82, 48, 1.8, "#222", False) + c(88, 48, 1.8, "#222", False)
          + line("M82 53 C84 55 87 55 89 53", 1.8)
          + line("M30 68 L28 60 M32 68 L34 61 M66 68 L64 61 M68 68 L71 62", 2.5, DGREEN),
    "cart": c(40, 26, 8, RED) + r(54, 12, 15, 18, BLUE, 2)
          + line("M28 66 L26 82 L84 82", 5)
          + p("M18 30 L90 30 L82 66 L28 66 Z", GRAY)
          + line("M33 30 L37 66 M47 30 L49 66 M61 30 L61 66 M75 30 L73 66 M21 42 L87 42 M24 54 L85 54", 2.5)
          + colored_line("M18 30 L10 16", GRAY, 4) + colored_line("M4 15 L16 15", RED, 6)
          + wheel(32, 89, 6) + wheel(78, 89, 6),
    # --- page 96: elbow, plum ---------------------------------------------------------------
    "elbow": colored_line("M24 56 L60 76 L72 30", SKIN, 16) + c(72, 22, 10, SKIN)
           + line("M66 18 L76 18 M66 23 L77 23", 2)
           + e(60, 74, 7, 6.5, TINT, 0, False)
           + colored_line("M-4 48 L20 60", BLUE, 22),
    "plum": p("M50 28 C70 22 88 36 88 58 C88 80 70 92 50 92 C30 92 12 80 12 58 C12 36 30 22 50 28 Z", PLUM)
          + line("M50 30 C42 46 42 72 50 90", 2.5)
          + line("M24 50 C26 42 30 38 36 36", 3, WHITE)
          + colored_line("M50 28 L52 16", BARK, 3)
          + p("M52 18 C58 6 76 6 84 12 C76 22 60 24 52 18 Z", GREEN) + line("M54 18 L80 12", 2),
    # --- page 97: seesaw, bush --------------------------------------------------------------
    "seesaw": line("M4 94 L96 94", 3)
            + p("M38 94 L50 66 L62 94 Z", GOLD)
            + limb("M14 80 L10 92", BLUE, 6) + limb("M86 54 L90 66", BLUE, 6)
            + colored_line("M8 84 L92 50", RED, 7)
            + colored_line("M26 76 L26 66 M74 56 L74 46", GRAY, 3)
            + p("M8 78 L10 64 C10 58 22 58 22 64 L24 76 Z", ORANGE) + limb("M20 66 L26 68")
            + p("M76 52 L78 38 C78 32 90 32 90 38 L92 50 Z", GREEN) + limb("M80 40 L74 47")
            + head(16, 50, 9) + head(84, 24, 9, hair=GOLD),
    "bush": line("M4 88 L96 88", 3)
          + p("M10 88 C0 74 8 58 22 62 C20 44 40 38 50 50 C58 34 82 38 80 56 C96 54 100 76 90 88 Z", GREEN)
          + line("M30 70 C34 64 40 64 44 68 M56 62 C60 56 68 58 70 62 M46 80 C50 76 58 76 60 80", 2.5, DGREEN)
          + "".join(c(x, y, 3.5, RED) for x, y in ((24, 74), (38, 56), (60, 50), (76, 66), (64, 76), (16, 66), (82, 78))),
    # --- page 98: build, phone --------------------------------------------------------------
    "build": line("M4 94 L96 94", 3)
           + r(62, 80, 18, 14, RED, 2) + r(62, 66, 18, 14, BLUE, 2) + r(62, 52, 18, 14, GOLD, 2) + r(62, 38, 18, 14, GREEN, 2)
           + r(60, 12, 18, 14, PURPLE, 2)
           + limb("M24 78 L22 92", BLUE, 8) + limb("M36 78 L38 92", BLUE, 8) + shoe(20, 93) + shoe(40, 93)
           + p("M18 80 L20 56 C22 50 38 50 40 56 L42 80 Z", ORANGE)
           + limb("M36 58 L50 40 L60 26")
           + head(30, 38, 13),
    "phone": line("M22 34 C16 40 16 50 22 56 M14 28 C6 38 6 52 14 62 M78 34 C84 40 84 50 78 56 M86 28 C94 38 94 52 86 62", 3, GRAY)
           + r(30, 8, 40, 84, DBLUE, 9) + r(35, 18, 30, 58, LBLUE, 3)
           + line("M44 13 L56 13", 2.5) + c(50, 84, 3.5, GRAY),
    # --- page 99: pickle, whistle -----------------------------------------------------------
    "pickle": p("M14 72 C6 60 16 44 32 38 C50 30 68 20 82 22 C96 24 96 40 86 48 C72 58 54 64 38 74 C28 82 18 80 14 72 Z", PICKLE)
            + "".join(c(x, y, 2.2, DGREEN, False) for x, y in ((28, 50), (44, 44), (60, 36), (76, 30), (36, 62), (52, 56), (68, 46), (84, 36), (24, 66)))
            + line("M22 52 C30 44 44 40 54 36", 3, "#C8E0A0"),
    "whistle": colored_line("M24 32 C8 22 10 4 28 6 C44 8 46 20 36 28", RED, 4)
             + r(46, 32, 46, 16, GOLD, 4)
             + c(40, 54, 21, GOLD)
             + c(26, 36, 5, "none") + r(52, 31, 10, 6, DARK, 1)
             + line("M54 22 L52 14 M62 22 L66 15", 3, GRAY),
    # --- page 100: fan, bell ----------------------------------------------------------------
    "fan": colored_line("M50 64 L50 86", GRAY, 7) + e(50, 90, 24, 6, GRAY)
         + c(50, 38, 30, LBLUE)
         + "".join(rot(a, 50, 38, e(50, 24, 8, 13, BLUE)) for a in (0, 120, 240))
         + c(50, 38, 6, DARK)
         + c(50, 38, 22, "none")
         + line("M86 28 L96 28 M88 40 L98 40 M86 52 L96 52", 3, GRAY),
    "bell": line("M12 50 C8 58 8 66 12 72 M88 50 C92 58 92 66 88 72 M4 44 C-2 56 -2 70 4 80 M96 44 C102 56 102 70 96 80", 3, GRAY)
          + c(50, 88, 6, DARK)
          + p("M24 80 C24 52 32 32 50 30 C68 32 76 52 76 80 L84 86 L16 86 Z", GOLD)
          + line("M34 70 C34 54 38 44 44 40", 3, "#F6D27A")
          + colored_line("M50 8 L50 30", MBROWN, 9) + c(50, 8, 5, MBROWN),
    # --- redraws of batch 4 (page 75 neck, page 73 pour) -------------------------------------
    "neck": p("M10 100 C12 80 26 72 50 72 C74 72 88 80 90 100 Z", GREEN)
          + p("M38 42 L62 42 L63 76 C56 81 44 81 37 76 Z", SKIN)
          + e(50, 64, 9, 10, TINT, 0, False)
          + child_face(50, 28, 22, 24),
    "pour": line("M44 95 L96 95", 3)
          + colored_line("M74 42 C75 50 75 56 75 66", WHITE, 4)
          + p("M60 64 L88 64 L84 93 L64 93 Z", BLUE) + e(74, 64, 13, 3, WHITE)
          + rot(50, 38, 46,
                colored_line("M24 30 C8 30 6 58 20 62", PURPLE, 4)
                + p("M26 22 L50 22 C52 32 58 40 58 52 C58 62 54 68 50 70 L26 70 C22 68 18 62 18 52 C18 40 24 32 26 22 Z", PURPLE)
                + p("M46 22 L58 16 C58 22 56 26 52 30 Z", PURPLE)
                + e(38, 22, 12, 3, WHITE))
          + limb("M12 2 L20 22", SKIN, 8) + colored_line("M10 -6 L12 0", GREEN, 14) + c(21, 26, 6.5, SKIN),
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
