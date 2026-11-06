"""Chicks Reading (7A) word batch 4 pictures (40 words, approved 2026-11-06) in the house style.

Run: uv run python scripts/pictures/draw_7A_batch4.py <out_dir> [slug ...]
A record only: the SVGs in assets/pictures/ are the source of truth (STATUS.md, picture workflow).
(draw_batch4.py is the Ducklings batch 1 record; this file is named for the Chicks batch.)
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
DBLUE, LBLUE, DGREEN, LGRAY = "#5A8FCC", "#8FB8E8", "#5FA34C", "#C4C7CC"
MBROWN, DEER, NUT, SPUD = "#B48858", "#C08A5A", "#D0A060", "#C49A6C"
LEMON, CREAM, BARK, TINT = "#E8B828", "#F4F1EA", "#6B4A2E", "#F6D27A"


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


def shoe(x, y, rot=0):
    return e(x, y, 7, 4, RED, rot)


def crayon(color, dark, deco="#222"):
    body = (p("M36 30 L64 30 L64 92 L36 92 Z", color) + p("M36 30 L50 6 L64 30 Z", color)
            + p("M44 16 L50 6 L56 16 Z", dark) + line("M36 42 L64 42 M36 80 L64 80", 3, deco)
            + line("M42 54 C46 50 54 58 58 54 M42 66 C46 62 54 70 58 66", 3, deco))
    return f'<g transform="rotate(30 50 50)">{body}</g>'


def sun(x, y, rad=8):
    rays = " ".join(f"M{x + (rad + 4) * math.cos(a):.1f} {y + (rad + 4) * math.sin(a):.1f} "
                    f"L{x + (rad + 9) * math.cos(a):.1f} {y + (rad + 9) * math.sin(a):.1f}"
                    for a in (i * math.pi / 4 for i in range(8)))
    return line(rays, 3) + c(x, y, rad, GOLD)


def bubble(x, y, rad):
    return c(x, y, rad, LBLUE) + line(f"M{x - rad * 0.55} {y - rad * 0.1} C{x - rad * 0.5} {y - rad * 0.45} "
                                      f"{x - rad * 0.3} {y - rad * 0.6} {x} {y - rad * 0.62}", 2.5, "#FFFFFF")


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


PICS = {
    # --- page 61: fox, sink -----------------------------------------------------------------
    "fox": p("M58 90 C84 94 98 74 92 52 C88 40 76 40 76 50 C80 60 78 76 60 80 Z", ORANGE)
         + p("M92 52 C88 40 76 40 76 50 C82 54 88 56 92 52 Z", CREAM)
         + p("M30 92 C26 72 32 56 50 52 C68 56 74 72 70 92 Z", ORANGE)
         + p("M42 92 C40 78 44 64 50 62 C56 64 60 78 58 92 Z", CREAM)
         + e(42, 93, 7, 4, "#7A3E1E") + e(58, 93, 7, 4, "#7A3E1E")
         + p("M26 34 L26 6 L46 22 Z", ORANGE) + p("M74 34 L74 6 L54 22 Z", ORANGE)
         + p("M30 26 L30 14 L38 21 Z", "#7A3E1E") + p("M70 26 L70 14 L62 21 Z", "#7A3E1E")
         + p("M22 32 C26 20 74 20 78 32 C74 46 62 54 50 60 C38 54 26 46 22 32 Z", ORANGE)
         + p("M30 40 C38 40 46 46 50 58 C54 46 62 40 70 40 C66 48 58 56 50 60 C42 56 34 48 30 40 Z", CREAM)
         + eyes(36, 40, 60, 3.2) + c(50, 56, 3.5, "#222", False),
    "sink": line("M14 92 L86 92", 3)
          + r(18, 50, 64, 42, TAN, 3) + line("M50 50 L50 92", 3) + c(44, 70, 2.5, "#222", False) + c(56, 70, 2.5, "#222", False)
          + r(10, 42, 80, 12, LGRAY, 4) + e(50, 47, 24, 3.5, DBLUE)
          + colored_line("M50 42 L50 24 L66 24 L66 30", GRAY, 5)
          + r(30, 32, 10, 8, GRAY, 2) + r(60, 32, 10, 8, GRAY, 2)
          + p("M66 34 C64 38 68 40 66 36 Z", DBLUE) + c(66, 38, 2.5, DBLUE),
    # --- page 62: lemon, scooter ------------------------------------------------------------
    "lemon": p("M10 64 C6 60 8 54 14 52 C20 30 64 22 80 38 C86 34 94 38 90 46 C96 70 56 92 26 76 C20 80 12 72 10 64 Z", LEMON)
           + line("M26 52 C32 42 44 38 54 38", 3, "#FFFFFF")
           + p("M60 32 C62 16 78 8 88 12 C86 26 72 34 60 32 Z", GREEN) + line("M62 30 L84 14", 2.5),
    "scooter": line("M8 96 L92 96", 3)
             + colored_line("M64 18 L74 70 L80 84", BLUE, 6)
             + p("M14 70 L70 70 C74 70 76 72 76 76 L76 78 L14 78 C10 78 10 70 14 70 Z", BLUE)
             + line("M54 20 L76 16", 7) + line("M54 20 L60 19", 7, RED) + line("M70 17 L76 16", 7, RED)
             + c(22, 86, 9, GRAY) + c(22, 86, 3, "#222", False) + c(80, 86, 9, GRAY) + c(80, 86, 3, "#222", False),
    # --- page 63: drink, nest ---------------------------------------------------------------
    "drink": p("M8 98 C10 80 22 74 40 74 C58 74 70 80 72 98 Z", GREEN)
           + c(40, 42, 26, SKIN)
           + p("M14 38 C14 10 66 10 66 38 C56 30 46 26 40 26 C32 28 22 32 14 38 Z", BROWN)
           + line("M24 40 C27 37 31 37 34 40 M40 40 C43 37 47 37 50 40", 2.5)
           + limb("M56 92 L66 76 L70 66", SKIN, 7)
           + p("M52 44 L58 60 L86 48 L80 32 Z", BLUE) + e(55, 52, 3.5, 8.5, LBLUE, -22)
           + line("M66 56 C66 70 80 70 80 54", 6) + line("M66 56 C66 70 80 70 80 54", 2, BLUE)
           + c(72, 64, 6, SKIN),
    "nest": e(50, 54, 42, 9, MBROWN)
          + e(36, 48, 9, 12, LBLUE) + e(64, 48, 9, 12, LBLUE) + e(50, 44, 9, 12, LBLUE)
          + p("M8 54 C10 80 30 90 50 90 C70 90 90 80 92 54 C76 64 24 64 8 54 Z", TAN)
          + line("M14 64 C30 74 62 76 86 64 M20 74 C36 84 64 84 80 74 M30 86 L42 80 M58 84 L70 78 M8 54 L2 50 M92 54 L98 48", 2.5, BARK),
    # --- page 64: belt, koala ---------------------------------------------------------------
    "belt": colored_line("M50 80 C20 80 8 70 8 56 C8 42 26 32 50 32 C74 32 92 42 92 56 C92 70 80 80 50 80", MBROWN, 11)
          + colored_line("M60 80 L74 80", MBROWN, 11) + c(70, 80, 1.8, "#222", False)
          + r(36, 68, 26, 24, GOLD, 4) + r(42, 74, 14, 12, MBROWN, 2) + line("M42 80 L62 80", 3),
    "koala": r(64, 2, 18, 96, MBROWN, 4) + line("M70 14 L70 26 M76 60 L76 74", 2.5, BARK)
           + e(46, 66, 22, 26, GRAY) + e(48, 72, 12, 14, LGRAY, 0, False)
           + e(66, 50, 8, 5, GRAY) + e(68, 76, 8, 5, GRAY)
           + c(24, 22, 12, GRAY) + c(64, 22, 12, GRAY) + c(24, 22, 6, LGRAY, False) + c(64, 22, 6, LGRAY, False)
           + c(44, 34, 20, GRAY) + eyes(30, 36, 52, 3) + e(44, 40, 5, 7, DARK),
    # --- page 65: rice, rocket --------------------------------------------------------------
    "rice": p("M18 50 C20 34 34 26 50 26 C66 26 80 34 82 50 Z", CREAM)
          + "".join(f'<ellipse cx="{x}" cy="{y}" rx="2.8" ry="1.5" fill="none" stroke="#B5AE9C" stroke-width="1.5" transform="rotate({rot} {x} {y})"/>' for x, y, rot in
                    ((34, 40, 20), (46, 34, -15), (58, 38, 30), (68, 44, -20), (42, 46, 10), (54, 46, -30), (28, 47, 0)))
          + colored_line("M70 40 L90 12", GRAY, 5)
          + p("M8 50 L92 50 C92 74 72 92 50 92 C28 92 8 74 8 50 Z", RED)
          + line("M14 62 L86 62", 3),
    "rocket": line("M20 30 L20 46 M80 30 L80 46 M12 54 L12 64 M88 54 L88 64", 3, GRAY)
            + p("M38 72 C38 84 46 92 50 98 C54 92 62 84 62 72 Z", ORANGE) + p("M44 72 C44 80 48 86 50 90 C52 86 56 80 56 72 Z", GOLD)
            + p("M34 50 L18 76 L36 72 Z", BLUE) + p("M66 50 L82 76 L64 72 Z", BLUE)
            + p("M50 4 C66 16 70 40 66 74 L34 74 C30 40 34 16 50 4 Z", RED)
            + p("M50 4 C58 10 62 16 64 22 L36 22 C38 16 42 10 50 4 Z", DBLUE)
            + c(50, 42, 9, GLASS) + c(50, 42, 4, "#FFFFFF", False),
    # --- page 66: chin, puppet --------------------------------------------------------------
    "chin": p("M18 100 C20 88 32 84 50 84 C68 84 80 88 82 100 Z", BLUE)
          + r(42, 70, 16, 16, SKIN)
          + child_face(50, 44, 30, 34)
          + e(50, 72, 13, 6, TINT, 0, False)
          + c(28, 56, 4.5, PINK, False) + c(72, 56, 4.5, PINK, False)
          + limb("M84 100 L76 84 L60 78", SKIN, 7) + c(58, 77, 4.5, SKIN),
    "puppet": r(26, 80, 40, 20, PURPLE, 3) + line("M26 88 L66 88", 3)
            + p("M28 82 L28 44 C28 22 44 12 62 14 C80 16 90 30 88 46 C88 56 80 60 70 60 L66 60 L66 82 Z", GREEN)
            + p("M66 52 C74 56 84 56 88 48 L88 54 C84 64 70 64 66 58 Z", "#7A2E2E")
            + e(78, 60, 6, 3, PINK)
            + line("M40 16 C36 6 42 4 44 12 M48 13 C48 2 56 2 54 12 M56 14 C60 4 68 6 62 16", 3, ORANGE)
            + c(48, 34, 7, "#FFFFFF") + c(66, 32, 7, "#FFFFFF") + c(50, 35, 3.2, "#222", False) + c(68, 33, 3.2, "#222", False),
    # --- page 67: smile, broom --------------------------------------------------------------
    "smile": c(14, 52, 9, BROWN) + c(86, 52, 9, BROWN)
           + e(50, 54, 34, 38, SKIN)
           + p("M16 50 C10 18 34 10 50 10 C66 10 90 18 84 50 C78 34 66 26 50 26 C34 26 22 34 16 50 Z", BROWN)
           + line("M28 46 C31 40 37 40 40 46 M60 46 C63 40 69 40 72 46", 3)
           + c(28, 62, 6, PINK, False) + c(72, 62, 6, PINK, False)
           + p("M30 64 C38 84 62 84 70 64 C58 68 42 68 30 64 Z", "#FFFFFF")
           + line("M34 69 C44 72 56 72 66 69", 2),
    "broom": f'<g transform="rotate(-12 50 50)">'
             + colored_line("M50 4 L50 58", MBROWN, 5)
             + p("M30 94 L36 62 L64 62 L70 94 Z", GOLD)
             + line("M40 66 L38 92 M46 66 L45 92 M54 66 L55 92 M60 66 L62 92", 2.5)
             + r(34, 56, 32, 9, RED, 3) + "</g>",
    # --- page 68: potato, parrot ------------------------------------------------------------
    "potato": p("M14 56 C10 36 30 24 50 28 C62 30 70 24 80 30 C94 38 92 62 82 72 C70 86 46 86 30 80 C18 76 16 66 14 56 Z", SPUD)
            + line("M30 44 C32 42 34 42 35 44 M58 40 C60 38 62 38 63 40 M72 60 C74 58 76 58 77 60 M44 66 C46 64 48 64 49 66", 2.5)
            + c(40, 54, 1.8, "#222", False) + c(66, 50, 1.8, "#222", False) + c(56, 72, 1.8, "#222", False)
            + line("M68 28 C70 22 74 20 78 20", 3, DGREEN),
    "parrot": colored_line("M6 72 L94 72", MBROWN, 5)
            + p("M48 66 L40 98 L50 98 L58 66 Z", RED) + p("M54 66 L56 96 L64 94 L60 66 Z", BLUE)
            + p("M40 34 C38 20 58 16 64 30 C70 44 68 60 60 70 L46 70 C40 60 38 46 40 34 Z", GREEN)
            + p("M54 38 C66 38 70 54 62 66 C56 60 52 50 54 38 Z", BLUE)
            + c(50, 26, 14, GREEN)
            + p("M38 20 C28 20 26 34 34 40 C34 34 38 30 42 30 Z", GOLD)
            + c(48, 22, 4.5, "#FFFFFF") + c(48, 22, 2.2, "#222", False)
            + line("M48 72 L46 76 M56 72 L58 76", 3),
    # --- page 69: bubbles, deer -------------------------------------------------------------
    "bubbles": colored_line("M8 94 L28 74", PURPLE, 6)
             + c(34, 67, 9, "none").replace('stroke-width="3"', 'stroke-width="9"')
             + f'<circle cx="34" cy="67" r="9" fill="none" stroke="{PURPLE}" stroke-width="4"/>'
             + bubble(62, 32, 22) + bubble(84, 70, 11) + bubble(28, 26, 9) + bubble(58, 74, 6),
    "deer": colored_line("M38 60 L36 92 M46 62 L46 92 M66 62 L68 92 M74 60 L78 92", DEER, 5)
          + line("M33 93 L39 93 M43 93 L49 93 M65 93 L71 93 M75 93 L81 93", 4)
          + p("M24 28 C26 40 32 50 40 56 L52 46 C44 42 40 34 38 22 Z", DEER)
          + e(58, 52, 24, 13, DEER) + e(82, 44, 4, 6, CREAM)
          + c(52, 46, 2, CREAM, False) + c(62, 44, 2, CREAM, False) + c(70, 48, 2, CREAM, False)
                    + line("M36 18 L42 4 M39 11 L46 8 M30 18 L22 4 M26 11 L18 9", 4, BARK)
          + e(26, 22, 6, 3.5, DEER, -30) + e(42, 18, 6, 3.5, DEER, 30)
          + p("M28 20 C36 18 42 26 38 34 C34 38 22 38 16 34 C12 30 20 22 28 20 Z", DEER)
          + c(16, 33, 2.5, "#222", False) + c(32, 26, 2.5, "#222", False),
    # --- page 70: ride, hose ----------------------------------------------------------------
    "ride": c(24, 80, 16, "none") + c(76, 80, 16, "none")
          + colored_line("M24 80 L42 58 L68 58 L76 80 M42 58 L50 80 L24 80 M50 80 L68 58", BLUE, 4)
          + line("M68 58 L64 42 L74 40", 4)
          + limb("M44 46 L60 54 L52 78", PURPLE, 8) + e(53, 80, 7, 4, RED)
          + p("M34 48 C32 36 38 24 48 24 C56 26 58 34 54 48 Z", GREEN)
          + line("M34 49 L52 49", 6)
          + limb("M50 30 L62 38 L72 40")
          + head(52, 14, 10, mouth="smile")
          + p("M40 12 C40 -2 64 -2 64 12 Z", RED),
    "hose": colored_line("M14 64 A32 24 0 1 0 78 64 A32 24 0 1 0 14 64", GREEN, 8)
          + colored_line("M22 62 A24 17 0 1 0 70 62 A24 17 0 1 0 22 62", GREEN, 8)
          + colored_line("M78 64 C86 54 86 38 78 30", GREEN, 8)
          + p("M70 30 L74 18 L84 16 L86 26 L80 32 Z", ORANGE) + r(72, 8, 10, 10, GRAY, 2)
          + line("M90 10 L96 4 M92 18 L98 18 M60 10 L54 4", 3, DBLUE),
    # --- page 71: tomato, crib --------------------------------------------------------------
    "tomato": p("M10 58 C10 36 30 28 50 32 C70 28 90 36 90 58 C90 80 72 92 50 92 C28 92 10 80 10 58 Z", RED)
            + line("M36 36 C30 50 30 70 36 86 M64 36 C70 50 70 70 64 86", 2.5)
            + line("M24 54 C26 46 32 42 38 42", 3, "#FFFFFF")
            + p("M50 34 L40 26 L46 32 L34 34 L46 38 L50 44 L54 38 L66 34 L54 32 L60 26 Z", DGREEN)
            + colored_line("M50 32 L52 18", DGREEN, 4),
    "crib": r(20, 56, 60, 18, LBLUE, 4) + c(36, 50, 9, SKIN)
          + line("M31 51 C33 53 35 53 37 51 M38 51 C39 53 40 53 41 51", 1.8) + p("M44 48 C56 44 70 46 78 54 L78 74 L44 74 Z", PINK)
          + colored_line("M30 32 L30 74 M44 32 L44 74 M58 32 L58 74 M72 32 L72 74", TAN, 3)
          + r(10, 18, 10, 76, TAN, 3) + r(80, 18, 10, 76, TAN, 3)
          + r(18, 26, 64, 8, TAN, 3) + r(18, 72, 64, 8, TAN, 3),
    # --- page 72: brown, camel --------------------------------------------------------------
    "brown": crayon("#8B5A2B", "#5C3A1A"),
    "camel": colored_line("M40 64 L38 94 M48 66 L48 94 M70 66 L70 94 M78 64 L80 94", TAN, 5)
           + line("M35 95 L41 95 M45 95 L51 95 M67 95 L73 95 M77 95 L83 95", 4)
           + line("M88 54 C94 60 94 70 90 74", 3)
           + p("M32 64 C32 48 40 44 46 46 C52 20 74 20 78 46 C88 46 90 54 88 64 C80 72 40 72 32 64 Z", TAN)
           + p("M34 58 C26 52 22 38 22 26 L30 22 C32 34 36 44 42 52 Z", TAN)
           + p("M12 24 C12 14 30 12 32 22 C32 30 24 32 16 30 C12 30 12 28 12 24 Z", TAN)
           + c(24, 20, 2.5, "#222", False) + e(28, 14, 3, 5, TAN, 30) + line("M12 26 L16 26", 2),
    # --- page 73: pour, feather -------------------------------------------------------------
    "pour": line("M44 95 L96 95", 3)
          + p("M62 66 L88 66 L84 93 L66 93 Z", BLUE) + e(75, 66, 13, 3, CREAM)
          + colored_line("M73 54 C74 58 75 62 75 66", "#FFFFFF", 4)
          + '<g transform="rotate(50 40 54)">'
          + line("M26 40 C10 40 10 66 24 66", 9) + line("M26 40 C10 40 10 66 24 66", 3, ORANGE)
          + p("M28 32 L52 32 L56 74 C56 80 24 80 24 74 Z", ORANGE) + p("M50 32 L62 26 L54 40 Z", ORANGE)
          + line("M28 46 L53 46", 2.5) + "</g>"
          + limb("M4 18 L20 38", SKIN, 8) + colored_line("M-6 4 L6 20", GREEN, 13) + c(22, 40, 6.5, SKIN),
    "feather": p("M18 88 C20 58 40 24 84 8 C90 30 72 66 30 84 Z", PURPLE)
             + line("M40 50 L30 42 M52 38 L44 28 M64 28 L60 18 M50 62 L58 66 M62 48 L72 52", 2.5)
             + line("M10 96 C30 70 56 34 84 8", 3),
    # --- page 74: bib, cherry ---------------------------------------------------------------
    "bib": line("M24 22 C18 10 8 14 4 6 M76 22 C82 10 92 14 96 6", 3)
         + p("M20 30 C20 18 34 14 38 24 C42 34 58 34 62 24 C66 14 80 18 80 30 L82 68 C82 88 66 96 50 96 C34 96 18 88 18 68 Z", PINK)
         + p("M50 50 L54 60 L64 61 L56 68 L59 78 L50 72 L41 78 L44 68 L36 61 L46 60 Z", GOLD),
    "cherry": colored_line("M30 54 C34 34 46 18 56 10 M70 56 C68 36 62 20 56 10", GREEN, 3)
            + p("M56 10 C64 2 82 4 88 12 C78 18 64 18 56 10 Z", GREEN)
            + c(30, 70, 19, RED) + c(70, 72, 19, RED)
            + line("M20 64 C22 58 26 56 30 56 M60 66 C62 60 66 58 70 58", 3, "#FFFFFF"),
    # --- page 75: neck, tent ----------------------------------------------------------------
    "neck": p("M10 100 C12 80 26 72 50 72 C74 72 88 80 90 100 Z", GREEN)
          + p("M36 74 L50 88 L64 74 Z", "#FFFFFF")
          + p("M38 44 L62 44 L64 78 C56 84 44 84 36 78 Z", SKIN)
          + p("M41 52 L59 52 L60 75 C54 79 46 79 40 75 Z", "#F9E2A8").replace(S, 'stroke="none"')
          + child_face(50, 30, 22, 24)
          + bubble(24, 60, 5) + bubble(78, 58, 6) + bubble(72, 46, 4),
    "tent": line("M4 90 L96 90", 3)
          + line("M24 56 L8 82 M76 56 L92 82", 2.5, GRAY)
          + p("M10 90 L50 18 L90 90 Z", ORANGE)
          + p("M50 40 L36 90 L64 90 Z", "#7A4A2A")
          + p("M50 40 L64 90 L72 90 Z", GOLD)
          + line("M50 18 L50 6", 3) + p("M50 6 L62 9 L50 12 Z", RED),
    # --- page 76: cook, acorn ---------------------------------------------------------------
    "cook": line("M20 22 C16 16 22 12 18 6 M76 30 C72 24 78 20 74 14 M88 34 C84 28 90 24 86 18", 3, GRAY)
          + p("M4 98 C4 78 12 68 28 68 C44 68 50 78 50 98 Z", BLUE)
          + head(28, 50, 16)
          + p("M14 40 C8 34 12 26 18 28 C18 18 38 18 38 28 C44 26 48 34 42 40 Z", "#FFFFFF")
          + colored_line("M72 64 L80 30", MBROWN, 4)
          + p("M48 62 L96 62 L92 96 L52 96 Z", RED) + e(72, 62, 24, 5, ORANGE)
          + line("M44 70 L52 70 M92 70 L100 70", 5)
          + limb("M40 74 L60 56 L76 44") + c(78, 44, 5.5, SKIN),
    "acorn": colored_line("M50 22 C50 12 54 6 60 6", MBROWN, 4)
           + p("M26 46 L74 46 C74 74 60 92 50 94 C40 92 26 74 26 46 Z", NUT)
           + line("M34 58 C34 70 40 80 46 84", 3, "#FFFFFF")
           + p("M18 50 C18 28 32 20 50 20 C68 20 82 28 82 50 C66 56 34 56 18 50 Z", MBROWN)
           + line("M30 30 L62 52 M44 24 L74 44 M24 40 L44 54 M70 30 L38 52 M56 24 L26 44 M80 40 L60 54", 2, BARK),
    # --- page 77: noodles, donkey -----------------------------------------------------------
    "noodles": colored_line("M60 8 L60 40", GRAY, 4)
             + line("M52 2 L52 12 C52 18 68 18 68 12 L68 2 M60 2 L60 12", 3)
             + colored_line("M54 18 C46 30 62 34 52 50 M60 18 C54 32 68 36 60 52 M66 18 C62 32 74 36 66 52", GOLD, 3)
             + p("M8 50 L92 50 C92 74 72 92 50 92 C28 92 8 74 8 50 Z", PURPLE)
             + e(50, 50, 42, 7, GOLD)
             + line("M18 50 C24 46 28 54 34 50 C40 46 44 54 50 50 C56 46 60 54 66 50 C72 46 76 54 82 50", 2.5),
    "donkey": colored_line("M38 62 L36 92 M48 64 L48 92 M68 64 L68 92 M76 62 L78 92", GRAY, 6)
            + line("M33 93 L40 93 M45 93 L51 93 M65 93 L71 93 M75 93 L81 93", 4)
            + line("M84 50 C92 56 92 66 90 72", 3) + e(90, 74, 3, 5, DARK)
            + e(60, 54, 26, 14, GRAY)
            + p("M22 30 C24 44 30 54 40 60 L52 46 C44 40 40 32 38 24 Z", GRAY)
            + line("M38 22 C40 32 44 40 52 46", 5, DARK)
            + p("M24 22 L18 2 L30 16 Z", GRAY) + p("M34 20 L38 0 L42 18 Z", GRAY)
            + p("M18 22 C24 14 36 16 38 28 L36 40 C36 48 18 50 10 44 C4 40 8 28 18 22 Z", GRAY)
            + p("M6 38 C8 32 18 34 22 40 C20 48 8 48 6 38 Z", LGRAY)
            + c(26, 28, 2.5, "#222", False) + c(10, 40, 1.5, "#222", False),
    # --- page 78: black, bathtub ------------------------------------------------------------
    "black": crayon("#3A3A3A", "#1A1A1A", "#BDBDBD"),
    "bathtub": colored_line("M86 54 L86 28 L74 28", GRAY, 5) + line("M74 32 L74 36", 3, DBLUE)
             + c(22, 46, 8, CREAM) + c(36, 40, 10, CREAM) + c(52, 42, 9, CREAM) + c(66, 46, 7, CREAM)
             + p("M50 40 C50 30 60 30 60 38 L66 36 L62 42 C64 46 62 52 56 52 L46 52 C42 46 44 42 50 40 Z", GOLD)
             + c(55, 36, 1.5, "#222", False)
             + p("M6 50 L94 50 L88 74 C84 80 76 84 68 84 L32 84 C24 84 16 80 12 74 Z", BLUE)
             + r(4, 48, 92, 8, DBLUE, 4)
             + e(24, 90, 5, 6, GOLD) + e(76, 90, 5, 6, GOLD),
    # --- page 79: roll, pumpkin -------------------------------------------------------------
    "roll": line("M4 96 L96 96", 3)
          + line("M54 74 L62 74 M50 82 L60 82 M54 90 L62 90", 3, GRAY)
          + c(80, 82, 13, RED) + line("M67 82 C74 76 86 76 93 82 M80 69 C76 76 76 88 80 95", 2.5)
          + limb("M24 70 L40 84 L18 92", BLUE, 9) + e(14, 92, 7, 4, RED)
          + p("M14 44 C16 36 30 34 36 40 L44 64 L24 72 Z", ORANGE)
          + limb("M32 46 L46 66 L52 76")
          + head(26, 28, 13),
    "pumpkin": colored_line("M54 26 C58 14 70 12 72 20", DGREEN, 3)
             + p("M45 30 L44 16 C44 12 54 12 54 16 L55 30 Z", "#8A6A3A")
             + e(30, 62, 22, 30, ORANGE) + e(70, 62, 22, 30, ORANGE) + e(50, 62, 22, 32, ORANGE),
    # --- page 80: hill, rug -----------------------------------------------------------------
    "hill": sun(16, 18, 7)
          + p("M2 94 C12 56 38 36 58 38 C80 40 94 62 98 94 Z", GREEN)
          + colored_line("M66 22 L66 40", MBROWN, 4) + c(66, 20, 11, DGREEN)
          + line("M44 94 C40 80 56 72 52 58 C50 50 58 46 62 42", 3, DGREEN)
          + line("M2 94 L98 94", 3),
    "rug": line("M14 30 L6 30 M14 38 L6 38 M14 46 L6 46 M14 54 L6 54 M14 62 L6 62 M14 70 L6 70 "
              "M86 30 L94 30 M86 38 L94 38 M86 46 L94 46 M86 54 L94 54 M86 62 L94 62 M86 70 L94 70", 3)
         + r(14, 24, 72, 52, RED, 4)
         + '<path d="M26 24 L36 24 L36 76 L26 76 Z M64 24 L74 24 L74 76 L64 76 Z" fill="#E6A817"/>'
         + '<path d="M44 24 L56 24 L56 76 L44 76 Z" fill="#6FA3E0"/>'
         + line("M26 24 L26 76 M36 24 L36 76 M44 24 L44 76 M56 24 L56 76 M64 24 L64 76 M74 24 L74 76", 2.5)
         + r(14, 24, 72, 52, "none", 4),
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
