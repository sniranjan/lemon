"""Batch-3 pictures in the house style."""
import math
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
S = 'stroke="#222" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"'
RED, ORANGE, GOLD, GREEN, BLUE = "#E87878", "#F0935A", "#E6A817", "#7FBF6A", "#6FA3E0"
PURPLE, TAN, BROWN, PINK, GRAY = "#A88FD8", "#C9A27A", "#A57C52", "#E89AB0", "#A0A4AA"
SKIN, WHEAT, GLASS, DARK = "#D9A27E", "#D8B07A", "#BFE0F5", "#444444"
DBLUE, DGOLD, SNOW, WOOL, MANE = "#5A8FCC", "#D4951A", "#9DB8D0", "#C8BBA4", "#E0943A"


def p(d, fill):
    return f'<path d="{d}" fill="{fill}" {S}/>'


def c(cx, cy, r, fill, stroke=True):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"' + (f" {S}/>" if stroke else "/>")


def e(cx, cy, rx, ry, fill, rot=0, stroke=True):
    t = f' transform="rotate({rot} {cx} {cy})"' if rot else ""
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}"' + (f" {S}" if stroke else "") + f"{t}/>"


def line(d, w=3, color="#222"):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'


def colored_line(d, color, w=5):
    """A thick colored stroke with a dark outline (bike frame, straw)."""
    return line(d, w + 6) + line(d, w, color)


def eyes(y, x1, x2, r=3.5):
    return c(x1, y, r, "#222", False) + c(x2, y, r, "#222", False)


def glasses(y, x1, x2):
    return (f'<circle cx="{x1}" cy="{y}" r="7" fill="none" {S}/><circle cx="{x2}" cy="{y}" r="7" fill="none" {S}/>'
            + line(f"M{x1 + 7} {y} L{x2 - 7} {y}"))


def wheel(x, y, r=10):
    return c(x, y, r, DARK) + c(x, y, r * 0.4, GRAY)


def scallop(cx, cy, r, bumps, depth):
    pts = []
    for i in range(bumps * 2):
        a = math.pi * i / bumps
        rr = r if i % 2 == 0 else r - depth
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(1, len(pts) + 1, 2):
        ctrl, end = pts[i % len(pts)], pts[(i + 1) % len(pts)]
        d += f" Q{ctrl[0]:.1f} {ctrl[1]:.1f} {end[0]:.1f} {end[1]:.1f}"

DGREEN, LBLUE, BRICK = "#5FA34C", "#8FB8E8", "#C8643C"


def limb(d, color=SKIN, w=7):
    return colored_line(d, color, w)


def head(x, y, r=13, closed=False, mouth="smile"):
    """A child's head: skin, short brown hair, eyes (closed = sleeping curves)."""
    out = c(x, y, r, SKIN)
    out += p(f"M{x - r} {y - 1} C{x - r} {y - r - 6} {x + r} {y - r - 6} {x + r} {y - 1} "
             f"C{x + r * 0.5} {y - r * 0.55} {x - r * 0.5} {y - r * 0.55} {x - r} {y - 1} Z", BROWN)
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


def mitten(x, y, rot, fill=SKIN):
    """A simple hand: palm + thumb, rotated about its center."""
    body = (p(f"M{x - 8} {y + 12} L{x - 8} {y - 6} C{x - 8} {y - 16} {x + 8} {y - 16} {x + 8} {y - 6} "
              f"L{x + 8} {y + 12} Z", fill)
            + p(f"M{x - 8} {y + 2} C{x - 16} {y - 2} {x - 18} {y + 6} {x - 8} {y + 10} Z", fill))
    return f'<g transform="rotate({rot} {x} {y})">{body}</g>'


def drop(x, y, s=1.0, fill=BLUE):
    return p(f"M{x} {y - 9 * s} C{x + 6 * s} {y - 1 * s} {x + 6 * s} {y + 6 * s} {x} {y + 6 * s} "
             f"C{x - 6 * s} {y + 6 * s} {x - 6 * s} {y - 1 * s} {x} {y - 9 * s} Z", fill)


def flake(x, y, r=7):
    return line(" ".join(f"M{x + r * math.cos(a):.1f} {y + r * math.sin(a):.1f} "
                         f"L{x - r * math.cos(a):.1f} {y - r * math.sin(a):.1f}"
                         for a in (0, math.pi / 3, 2 * math.pi / 3)), 2.5)


HAND = Path("assets/pictures/hand.svg").read_text().split(">", 1)[1].rsplit("</svg>", 1)[0]


def hand(x, y, rot=0, s=0.5, flip=False):
    """The batch-1 hand picture, scaled (outline kept at 3px) and placed at (x, y)."""
    body = HAND.replace('stroke-width="3"', f'stroke-width="{3 / s:g}"')
    fx = -s if flip else s
    return f'<g transform="translate({x} {y}) rotate({rot}) scale({fx:g} {s:g}) translate(-50 -54)">{body}</g>'


CLOUD = ("M22 52 C10 52 8 36 20 34 C20 20 38 16 44 26 C50 12 72 14 72 30 C86 28 92 50 78 52 Z")

PICS = {
    "drum": line("M30 8 L52 34 M70 8 L48 34", 4, BROWN) + c(30, 8, 4, WHEAT) + c(70, 8, 4, WHEAT)
          + p("M16 40 L16 78 C16 92 84 92 84 78 L84 40 Z", RED)
          + line("M16 52 L30 80 L44 52 L58 80 L72 52 L84 74")
          + e(50, 40, 34, 10, WHEAT),
    "lamp": p("M28 82 C28 74 72 74 72 82 L72 88 L28 88 Z", BROWN) + line("M50 52 L50 76", 6)
          + line("M50 52 L50 76", 2, GRAY)
          + p("M32 14 L68 14 L82 52 L18 52 Z", GOLD),
    "clock": line("M34 82 L26 92 M66 82 L74 92", 5)
           + p("M18 26 C14 14 26 6 36 14 Z", GOLD) + p("M82 26 C86 14 74 6 64 14 Z", GOLD)
           + c(50, 52, 38, RED) + c(50, 52, 22, "#FFFFFF")
           + line("M50 52 L50 38 M50 52 L60 57", 4) + c(50, 52, 3, "#222", False),
    "key": p("M14 50 C14 30 46 30 46 50 C46 70 14 70 14 50 Z M24 50 C24 58 36 58 36 50 C36 42 24 42 24 50 Z", GOLD)
           .replace('fill="', 'fill-rule="evenodd" fill="', 1)
         + p("M45 44 L88 44 L88 56 L82 56 L82 68 L74 68 L74 56 L68 56 L68 64 L60 64 L60 56 L45 56 Z", GOLD),
    "plate": e(50, 56, 44, 30, BLUE) + e(50, 54, 28, 18, LBLUE)
           + c(42, 52, 5, GREEN) + c(52, 50, 5, GREEN) + c(48, 59, 5, GREEN) + c(59, 57, 5, GREEN),
    "towel": line("M10 16 L90 16", 6) + c(10, 16, 4, GRAY) + c(90, 16, 4, GRAY)
           + p("M24 12 C24 8 76 8 76 12 L76 88 L24 88 Z", BLUE)
           + p("M24 62 L76 62 L76 72 L24 72 Z", LBLUE) + line("M30 88 L30 94 M40 88 L40 94 M50 88 L50 94 "
                                                             "M60 88 L60 94 M70 88 L70 94", 2.5),
    "run": line("M8 40 L22 40 M4 52 L18 52 M10 64 L22 64", 3, GRAY)
         + limb("M50 48 L36 60 L30 52") + limb("M56 48 L70 42 L80 32")
         + limb("M50 66 L40 80 L28 82", BLUE, 8) + limb("M54 66 L66 78 L68 92", BLUE, 8)
         + e(26, 84, 7, 4, RED) + e(72, 93, 7, 4, RED)
         + p("M44 40 C46 34 62 34 62 42 L58 68 L46 68 Z", RED) + head(56, 24),
    "owl": p("M26 26 L32 8 L42 20 Z", TAN) + p("M74 26 L68 8 L58 20 Z", TAN)
         + e(50, 54, 32, 38, TAN) + e(50, 66, 20, 22, WHEAT)
         + p("M18 50 C10 64 14 80 24 84 C26 70 26 58 18 50 Z", BROWN)
         + p("M82 50 C90 64 86 80 76 84 C74 70 74 58 82 50 Z", BROWN)
         + c(38, 38, 11, "#FFFFFF") + c(62, 38, 11, "#FFFFFF") + c(38, 38, 5, "#222", False) + c(62, 38, 5, "#222", False)
         + p("M45 48 L55 48 L50 58 Z", ORANGE) + line("M40 92 L40 86 M60 92 L60 86", 3),
    "pear": line("M52 22 C52 14 56 10 58 6", 4) + p("M56 14 C64 6 76 8 78 12 C70 18 62 18 56 14 Z", DGREEN)
          + p("M50 20 C40 20 38 32 38 40 C38 48 22 56 22 72 C22 88 36 94 50 94 C64 94 78 88 78 72 "
              "C78 56 62 48 62 40 C62 32 60 20 50 20 Z", GREEN)
          + e(38, 70, 4, 8, "#A9D69A", -15, False),
    "hair": p("M14 54 C10 20 30 6 50 6 C70 6 90 20 86 54 C90 70 92 84 84 94 L16 94 C8 84 10 70 14 54 Z", BROWN)
          + e(50, 54, 22, 26, SKIN)
          + p("M28 44 C30 26 42 20 50 20 C62 20 72 28 72 44 C66 38 60 30 54 30 C48 38 38 42 28 44 Z", BROWN)
          + eyes(56, 42, 58, 3) + line("M44 68 C47 71 53 71 56 68"),
    "jump": line("M14 92 L86 92", 3) + line("M30 84 L36 80 M70 84 L64 80 M44 86 L46 82 M56 86 L54 82", 2.5, GRAY)
          + limb("M42 38 L28 22 L24 10") + limb("M58 38 L72 22 L76 10")
          + limb("M44 58 L34 66 L38 76", BLUE, 8) + limb("M56 58 L66 66 L62 76", BLUE, 8)
          + e(36, 78, 7, 4, RED) + e(64, 78, 7, 4, RED)
          + p("M40 34 C40 28 60 28 60 34 L60 60 L40 60 Z", GOLD) + head(50, 20),
    "swing": colored_line("M10 94 L26 10 L42 94 M58 94 L74 10 L90 94", BLUE, 6)
           + line("M20 12 L80 12", 10) + line("M20 12 L80 12", 4, BLUE)
           + line("M38 13 L38 66 M62 13 L62 66", 3) + p("M30 66 L70 66 L70 74 L30 74 Z", RED),
    "rain": p(CLOUD, GRAY) + drop(28, 70) + drop(50, 76) + drop(72, 70) + drop(38, 90, 0.8) + drop(62, 90, 0.8),
    "sister": c(22, 34, 9, BROWN) + c(78, 34, 9, BROWN) + c(14, 30, 4, PINK) + c(86, 30, 4, PINK)
            + p("M24 97 C26 82 36 76 50 76 C64 76 74 82 76 97 Z", PURPLE)
            + e(50, 50, 22, 24, SKIN)
            + p("M28 46 C26 26 38 18 50 18 C62 18 74 26 72 46 C66 36 58 32 50 32 C42 32 34 36 28 46 Z", BROWN)
            + eyes(52, 42, 58, 3) + c(36, 62, 4, PINK, False) + c(64, 62, 4, PINK, False)
            + line("M44 64 C47 67 53 67 56 64"),
    "eat": e(50, 84, 30, 12, BLUE) + p("M20 80 C20 96 80 96 80 80 Z", BLUE)
         + c(50, 38, 26, SKIN)
         + p("M24 34 C24 12 76 12 76 34 C66 26 56 22 50 22 C40 26 32 30 24 34 Z", BROWN)
         + eyes(34, 40, 60, 3) + e(50, 52, 6, 5, "#222", 0, False)
         + limb("M86 80 L72 60 L56 54", GRAY, 4) + e(56, 54, 6, 4, GRAY),
    "goat": p("M36 22 C30 10 22 8 18 14 C26 14 30 18 32 26 Z", TAN) + p("M64 22 C70 10 78 8 82 14 C74 14 70 18 68 26 Z", TAN)
          + e(20, 38, 13, 6, GRAY, -25) + e(80, 38, 13, 6, GRAY, 25)
          + p("M30 36 C30 20 70 20 70 36 L64 72 C60 82 40 82 36 72 Z", GRAY)
          + p("M44 78 L50 94 L56 78 Z", "#FFFFFF") + eyes(44, 40, 60)
          + e(44, 68, 2.5, 3, "#222", 0, False) + e(56, 68, 2.5, 3, "#222", 0, False),
    "corn": p("M40 92 C22 80 18 50 24 34 C32 52 40 70 44 90 Z", DGREEN)
          + p("M60 92 C78 80 82 50 76 34 C68 52 60 70 56 90 Z", DGREEN)
          + p("M50 6 C64 6 66 30 64 54 C62 76 58 90 50 90 C42 90 38 76 36 54 C34 30 36 6 50 6 Z", GOLD)
          + line("M38 24 L62 24 M37 38 L63 38 M37 52 L63 52 M38 66 L62 66 M40 78 L60 78 M50 8 L50 88"),
    "arm": p("M26 84 L70 84 C82 84 86 76 84 66 L80 34 L60 34 L62 58 C56 44 38 42 26 56 Z", SKIN)
         + p("M56 34 C54 20 60 10 70 10 C80 10 86 18 84 34 Z", SKIN)
         + line("M62 18 C66 16 70 18 72 22 M64 26 L80 26", 2.5)
         + p("M8 50 L30 50 L30 90 L8 90 Z", BLUE),
    "sleep": p("M10 50 L22 50 L22 90 L10 90 Z", BROWN) + p("M82 62 L92 62 L92 90 L82 90 Z", BROWN)
           + e(32, 56, 14, 8, "#FFFFFF") + head(36, 52, 11, closed=True, mouth=None)
           + p("M44 58 C44 52 82 52 84 60 L84 80 L44 80 Z", BLUE) + line("M44 68 L84 68", 2.5)
           + p("M64 14 C54 18 54 34 64 38 C56 38 48 32 48 26 C48 18 56 12 64 14 Z", GOLD),
    "brother": p("M22 97 C24 80 36 74 50 74 C64 74 76 80 78 97 Z", GREEN)
             + line("M26 86 L74 86", 3) + c(28, 50, 6, SKIN) + c(72, 50, 6, SKIN)
             + e(50, 48, 22, 25, SKIN)
             + p("M28 42 C24 22 38 14 50 14 C62 14 76 22 72 42 L66 32 L60 36 L54 28 L46 34 L40 28 L34 36 Z", BROWN)
             + eyes(50, 42, 58, 3) + line("M43 62 C47 66 53 66 57 62"),
    "van": p("M6 70 L6 40 C6 30 14 24 24 24 L64 24 C72 24 78 30 84 44 L94 52 L94 70 Z", RED)
         + p("M16 34 L36 34 L36 48 L16 48 Z", GLASS) + p("M42 34 L62 34 L62 48 L42 48 Z", GLASS)
         + p("M68 34 L74 34 L82 48 L68 48 Z", GLASS) + line("M64 52 L64 68 M40 52 L40 68", 2.5)
         + wheel(26, 72) + wheel(74, 72),
    "soap": e(44, 88, 34, 6, "#BCC0C6") + p("M14 56 C14 46 20 42 30 42 L66 42 C76 42 80 46 80 56 L80 74 C80 82 76 86 66 86 "
                                            "L30 86 C20 86 14 82 14 74 Z", PINK)
          + e(46, 56, 22, 6, "#F4B4C6", 0, False)
          + c(58, 26, 9, GLASS) + c(76, 18, 6, GLASS) + c(40, 22, 6, GLASS) + c(88, 34, 4, GLASS),
    "sit": p("M60 46 L68 46 L68 92 L60 92 Z", BROWN) + p("M28 66 L68 66 L68 72 L28 72 Z", TAN)
         + line("M32 72 L32 92", 6) + line("M32 72 L32 92", 2, BROWN)
         + limb("M38 60 L20 62 L20 84", BLUE, 8) + e(16, 86, 7, 4, RED)
         + p("M36 36 C36 30 56 30 56 36 L56 64 L36 64 Z", RED) + limb("M42 42 L30 54 L22 54")
         + head(46, 22),
    "monkey": c(18, 44, 12, BROWN) + c(82, 44, 12, BROWN) + c(18, 44, 6, TAN, False) + c(82, 44, 6, TAN, False)
            + c(50, 48, 34, BROWN)
            + p("M50 30 C40 18 22 26 26 44 C20 58 32 78 50 78 C68 78 80 58 74 44 C78 26 60 18 50 30 Z", TAN)
            + eyes(42, 40, 60, 3.5) + e(46, 56, 2, 2.5, "#222", 0, False) + e(54, 56, 2, 2.5, "#222", 0, False)
            + line("M40 64 C46 70 54 70 60 64"),
    "pizza": p("M50 92 L14 22 C30 12 70 12 86 22 Z", GOLD)
           + p("M12 18 C30 6 70 6 88 18 L86 24 C70 14 30 14 14 24 Z", BROWN)
           + c(42, 36, 7, RED) + c(62, 38, 7, RED) + c(52, 58, 7, RED) + c(48, 78, 5, RED),
    "leg": p("M28 6 L64 6 L66 34 L30 34 Z", BLUE)
         + p("M34 34 L60 34 L56 74 L38 74 Z", SKIN)
         + p("M36 72 L58 72 L60 80 C78 80 88 84 88 90 L88 94 L34 94 Z", RED) + line("M34 88 L88 88", 2.5),
    "scarf": p("M14 30 C14 14 86 14 86 30 C86 44 70 50 50 50 C30 50 14 44 14 30 Z M28 30 C28 38 72 38 72 30 "
               "C72 24 28 24 28 30 Z", RED).replace('fill="', 'fill-rule="evenodd" fill="', 1)
           + p("M54 44 L70 44 L74 86 L58 88 Z", RED) + p("M40 44 L54 46 L48 84 L32 82 Z", RED)
           + line("M37 60 L51 62 M35 72 L49 74 M57 60 L71 59 M58 72 L73 71", 5, GOLD)
           + line("M35 83 L33 92 M41 84 L40 93 M47 85 L46 94 M60 88 L60 96 M66 88 L66 96 M72 87 L72 95", 3),
    "wash": p("M6 10 L46 10 L46 20 L18 20 L18 30 L6 30 Z", GRAY) + drop(12, 42, 0.8) + drop(12, 56, 0.8)
          + hand(40, 66, 14, 0.55, flip=True) + hand(62, 66, -14, 0.55)
          + c(36, 50, 6, GLASS) + c(56, 44, 5, GLASS) + c(68, 54, 6, GLASS) + c(84, 30, 6, GLASS) + c(90, 72, 5, GLASS),
    "snow": p("M4 96 C10 70 34 62 52 70 C66 58 92 64 96 96 Z", SNOW)
          + flake(22, 22) + flake(50, 12) + flake(78, 26) + flake(36, 44, 5) + flake(66, 48, 5),
    "turtle": e(84, 58, 9, 8, WHEAT) + c(86, 56, 2, "#222", False)
            + p("M22 68 L22 82 L34 82 L34 70 Z", WHEAT) + p("M62 68 L62 82 L74 82 L74 70 Z", WHEAT)
            + p("M10 70 C10 30 82 30 82 70 Z", GREEN)
            + line("M28 70 L34 52 L46 46 L58 52 L64 70 M34 52 L22 46 M58 52 L72 46 M46 46 L46 36"),
    "clap": line("M14 30 L6 22 M50 14 L50 4 M86 30 L94 22 M12 60 L2 60 M88 60 L98 60", 3.5)
          + hand(38, 56, 12, 0.62, flip=True) + hand(62, 56, -12, 0.62),
    "tractor": line("M66 34 L66 16", 6) + p("M24 58 L24 40 L52 40 L52 20 L80 20 L80 58 Z", GREEN)
             + p("M58 26 L74 26 L74 42 L58 42 Z", GLASS) + p("M8 46 L26 46 L26 62 L8 62 Z", GREEN)
             + c(70, 70, 20, DARK) + c(70, 70, 9, GOLD) + c(20, 76, 12, DARK) + c(20, 76, 5, GOLD),
    "pillow": p("M10 20 C30 26 70 26 90 20 C84 40 84 60 90 80 C70 74 30 74 10 80 C16 60 16 40 10 20 Z", PURPLE)
            + line("M28 40 C34 46 34 54 28 60 M72 40 C66 46 66 54 72 60", 2.5),
    "diaper": p("M10 24 L90 24 L86 40 C76 52 66 62 62 88 L38 88 C34 62 24 52 14 40 Z", LBLUE)
            + p("M8 22 L22 22 L22 34 L8 34 Z", GOLD) + p("M78 22 L92 22 L92 34 L78 34 Z", GOLD)
            + c(36, 44, 4, PINK, False) + c(50, 54, 4, PINK, False) + c(64, 44, 4, PINK, False)
            + line("M14 30 L86 30", 2.5),
    "swim": c(26, 22, 6, GLASS) + c(76, 16, 4, GLASS)
          + limb("M60 50 L72 36 L80 24") + head(46, 44)
          + p("M4 56 C14 50 22 50 32 56 C42 62 50 62 60 56 C70 50 78 50 88 56 L96 56 L96 96 L4 96 Z", BLUE)
          + line("M14 76 C22 72 28 72 36 76 M56 84 C64 80 70 80 78 84", 3),
    "rock": p("M10 86 C6 66 18 46 34 40 C46 26 70 28 80 44 C92 52 96 72 90 86 Z", GRAY)
          + line("M40 54 L48 62 L44 72 M66 46 L70 56", 2.5) + e(36, 52, 6, 3, "#C4C7CC", -20, False),
    "doll": limb("M36 54 L22 70") + limb("M64 54 L78 70") + limb("M42 80 L40 94") + limb("M58 80 L60 94")
          + p("M36 46 C36 42 64 42 64 46 L74 84 L26 84 Z", PURPLE)
          + c(32, 24, 8, BRICK) + c(68, 24, 8, BRICK) + c(50, 28, 18, SKIN)
          + p("M32 24 C32 6 68 6 68 24 C60 16 40 16 32 24 Z", BRICK)
          + eyes(29, 43, 57, 2.5) + line("M45 36 C48 39 52 39 55 36", 2.5),
    "soup": line("M36 26 C30 18 42 14 36 6 M52 26 C46 18 58 14 52 6", 3, GRAY)
          + p("M12 50 C12 90 88 90 88 50 Z", RED) + e(50, 50, 38, 10, ORANGE)
          + colored_line("M62 50 L84 26", GRAY, 4),
    "teeth": p("M6 50 C20 18 80 18 94 50 C80 86 20 86 6 50 Z", RED)
           + p("M16 50 C28 30 72 30 84 50 C72 72 28 72 16 50 Z", PINK)
           + "".join(p(f"M{x} 38 L{x + 10} 37 L{x + 10} 48 C{x + 10} 51 {x} 51 {x} 48 Z", "#FFFFFF")
                     for x in (28, 39, 50, 61))
           + "".join(p(f"M{x} 62 L{x + 10} 63 L{x + 10} 54 C{x + 10} 52 {x} 52 {x} 54 Z", "#FFFFFF")
                     for x in (33, 45, 57)),
    "slide": colored_line("M24 92 L24 20 M40 92 L40 20", GRAY, 4) + line("M24 36 L40 36 M24 52 L40 52 M24 68 L40 68 M24 84 L40 84", 3)
           + p("M36 18 L46 18 C60 34 72 76 92 84 L92 92 C66 90 52 44 36 28 Z", RED),
}

for slug, body in PICS.items():
    (OUT / f"{slug}.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{body}</svg>\n')
print(len(PICS), "pictures written")
