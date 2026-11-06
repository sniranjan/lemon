"""Batch-2 pictures in the house style. Color crayons use true hues (exempt from the lightness rule)."""
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
    return d + " Z"


def crayon(color, dark):
    body = (p("M36 30 L64 30 L64 92 L36 92 Z", color) + p("M36 30 L50 6 L64 30 Z", color)
            + p("M44 16 L50 6 L56 16 Z", dark) + line("M36 42 L64 42 M36 80 L64 80")
            + line("M42 54 C46 50 54 58 58 54 M42 66 C46 62 54 70 58 66"))
    return f'<g transform="rotate(30 50 50)">{body}</g>'


PICS = {
    "cow": e(20, 40, 13, 7, TAN, -20) + e(80, 40, 13, 7, TAN, 20)
         + line("M34 24 C30 16 26 14 22 14 M66 24 C70 16 74 14 78 14", 5)
         + e(50, 46, 26, 30, TAN) + p("M38 20 C46 16 58 18 62 26 C56 34 44 32 38 20 Z", BROWN)
         + e(50, 72, 20, 14, PINK) + e(43, 72, 3, 4, "#222", 0, False) + e(57, 72, 3, 4, "#222", 0, False)
         + eyes(46, 40, 60),
    "cake": line("M10 88 L90 88") + p("M18 52 L82 52 L82 86 L18 86 Z", WHEAT)
          + p("M18 52 C18 44 82 44 82 52 L82 58 C76 64 72 56 66 60 C60 64 56 56 50 60 C44 64 40 56 34 60 "
              "C28 64 24 56 18 58 Z", PINK)
          + p("M47 30 L53 30 L53 46 L47 46 Z", BLUE) + p("M50 16 C45 23 46 28 50 29 C54 28 55 23 50 16 Z", GOLD),
    "train": c(30, 14, 6, GRAY) + c(40, 8, 4.5, GRAY)
           + p("M22 26 L32 26 L32 44 L22 44 Z", DARK) + p("M14 44 L54 44 L54 70 L14 70 Z", BLUE)
           + p("M54 26 L84 26 L84 70 L54 70 Z", RED) + p("M50 20 L88 20 L88 26 L50 26 Z", DARK)
           + p("M62 32 L76 32 L76 46 L62 46 Z", GLASS) + p("M14 62 L4 76 L14 76 Z", DARK)
           + wheel(26, 76, 8) + wheel(46, 76, 8) + wheel(72, 74, 10),
    "pig": p("M24 30 L20 10 L40 22 Z", PINK) + p("M76 30 L80 10 L60 22 Z", PINK) + c(50, 52, 34, PINK)
         + e(50, 63, 14, 10, "#D97A96") + e(45, 63, 2.5, 4, "#222", 0, False) + e(55, 63, 2.5, 4, "#222", 0, False)
         + eyes(44, 38, 62),
    "grandma": p("M20 97 C22 80 34 74 50 74 C66 74 78 80 80 97 Z", PURPLE) + c(50, 13, 9, GRAY)
             + e(50, 48, 22, 25, SKIN)
             + p("M26 46 C24 24 36 18 50 18 C64 18 76 24 74 46 C68 36 60 32 50 32 C40 32 32 36 26 46 Z", GRAY)
             + glasses(50, 41, 59) + eyes(50, 41, 59, 2.5) + line("M43 63 C47 67 53 67 57 63"),
    "grandpa": p("M16 97 C18 78 32 72 50 72 C68 72 82 78 84 97 Z", GREEN) + line("M42 73 L50 82 L58 73")
             + c(27, 50, 6, SKIN) + c(73, 50, 6, SKIN) + e(50, 48, 22, 25, SKIN)
             + p("M29 46 C27 36 30 30 35 27 L36 42 Z", GRAY) + p("M71 46 C73 36 70 30 65 27 L64 42 Z", GRAY)
             + glasses(48, 41, 59) + eyes(48, 41, 59, 2.5)
             + p("M39 61 C44 56 48 58 50 60 C52 58 56 56 61 61 C56 65 44 65 39 61 Z", GRAY)
             + line("M44 68 C48 71 52 71 56 68"),
    "bowl": line("M38 34 C34 28 42 24 38 18 M52 34 C48 28 56 24 52 18 M66 34 C62 28 70 24 66 18")
          + p("M12 46 L88 46 C88 70 70 86 50 86 C30 86 12 70 12 46 Z", BLUE) + e(50, 46, 38, 7, DBLUE),
    "plane": p("M14 44 L8 22 L22 22 L34 42 Z", DBLUE)
           + p("M8 52 C8 44 16 42 24 42 L80 42 C90 42 94 48 94 52 C94 56 90 60 80 60 L24 60 C16 60 8 58 8 52 Z", BLUE)
           + p("M44 54 L62 54 L46 82 L34 82 Z", DBLUE) + "".join(c(x, 50, 3, GLASS) for x in (56, 64, 72))
           + p("M84 46 C88 46 90 48 91 51 L84 51 Z", GLASS),
    "orange": c(50, 54, 34, ORANGE) + line("M50 20 L50 12")
            + p("M50 18 C56 8 68 8 72 12 C66 20 56 22 50 18 Z", GREEN)
            + "".join(c(x, y, 1.8, "#D9783E", False) for x, y in ((38, 44), (60, 40), (66, 60), (42, 66), (54, 54))),
    "horse": p("M30 92 L34 60 C30 46 30 30 40 20 L44 8 L50 20 C60 20 70 30 78 44 C84 52 84 60 78 64 "
               "C72 68 64 62 58 58 L54 66 L58 92 Z", BROWN)
           + p("M40 20 C34 30 30 44 34 60 L28 64 C22 46 26 26 38 14 Z", "#7A5236")
           + c(56, 36, 3, "#222", False) + c(77, 55, 2, "#222", False),
    "shirt": p("M30 16 L42 12 C46 20 54 20 58 12 L70 16 L88 32 L78 44 L70 38 L70 88 L30 88 L30 38 L22 44 L12 32 Z", GREEN),
    "kite": p("M50 6 L24 40 L50 78 Z", RED) + p("M50 6 L76 40 L50 78 Z", GOLD) + line("M24 40 L76 40")
          + line("M50 78 C42 84 58 88 50 96") + p("M44 84 L40 80 L40 88 Z", BLUE) + p("M56 90 L60 86 L60 94 Z", BLUE),
    "frog": e(50, 64, 34, 24, GREEN) + c(33, 38, 12, GREEN) + c(67, 38, 12, GREEN)
          + c(33, 37, 6, "#FFFFFF") + c(67, 37, 6, "#FFFFFF") + eyes(37, 33, 67, 3)
          + line("M32 62 C42 72 58 72 68 62") + e(28, 86, 10, 5, GREEN) + e(72, 86, 10, 5, GREEN),
    "leaf": p("M18 86 C14 46 40 14 88 12 C88 58 62 86 18 86 Z", ORANGE)
          + line("M20 84 L76 24 M40 62 L36 44 M40 62 L58 64 M56 44 L54 30 M56 44 L70 46"),
    "table": p("M14 44 L22 44 L22 88 L14 88 Z", BROWN) + p("M78 44 L86 44 L86 88 L78 88 Z", BROWN)
           + p("M22 44 L78 44 L78 52 L22 52 Z", TAN) + p("M8 34 L92 34 L92 44 L8 44 Z", BROWN),
    "sheep": line("M24 74 L24 90 M34 76 L34 90 M54 76 L54 90 M64 74 L64 90", 6)
           + p("M24 46 C16 46 12 54 16 60 C10 64 14 74 22 74 C26 82 38 82 42 76 C48 82 60 80 62 74 "
               "C70 78 80 70 76 62 C82 56 78 46 70 46 C68 38 56 34 50 40 C44 34 30 36 28 44 Z", WOOL)
           + e(80, 48, 11, 14, "#555555") + c(78, 45, 2.5, "#FFFFFF", False) + c(85, 45, 2.5, "#FFFFFF", False)
           + e(72, 38, 6, 3, "#555555", -20),
    "cheese": p("M14 44 L70 24 L90 44 Z", "#E8B84A") + p("M14 44 L90 44 L90 76 L14 76 Z", GOLD)
            + c(32, 58, 5, "#C98E12") + c(58, 64, 6, "#C98E12") + c(74, 54, 4, "#C98E12") + c(46, 36, 3, "#C98E12", False),
    "bike": c(24, 64, 18, "none") + c(76, 64, 18, "none")
          + colored_line("M24 64 L42 40 L68 40 L76 64 M42 40 L50 64 L24 64 M50 64 L68 40", RED)
          + line("M34 32 L50 32", 6) + line("M42 40 L42 32") + line("M68 40 L64 26 L74 24", 4),
    "eye": e(50, 52, 46, 32, SKIN) + p("M16 54 C30 34 70 34 84 54 C70 74 30 74 16 54 Z", "#FFFFFF")
         + c(50, 54, 15, BLUE) + c(50, 54, 7, "#222", False) + c(54, 50, 3, "#FFFFFF", False)
         + line("M24 28 C40 18 60 18 76 28", 4),
    "mouth": p("M10 46 C24 32 40 36 50 42 C60 36 76 32 90 46 C80 74 20 74 10 46 Z", RED)
           + p("M22 48 C34 53 66 53 78 48 C74 57 26 57 22 48 Z", "#FFFFFF"),
    "bee": e(40, 30, 10, 15, GLASS, -25) + e(56, 30, 10, 15, GLASS, 25)
         + e(46, 58, 28, 19, GOLD) + line("M38 41 C34 50 34 66 38 75", 6) + line("M52 40 C48 50 48 66 52 76", 6)
         + c(78, 54, 12, GOLD) + c(82, 51, 2.5, "#222", False) + line("M18 58 L10 58")
         + line("M80 42 C80 34 84 30 88 30 M74 43 C72 36 74 30 78 28"),
    "pants": p("M26 12 L74 12 L80 90 L56 90 L50 40 L44 90 L20 90 Z", BLUE) + p("M26 12 L74 12 L74 22 L26 22 Z", DBLUE)
           + line("M50 22 L50 40"),
    "cloud": p("M24 74 C8 74 6 52 22 48 C20 30 42 24 50 36 C56 20 82 24 80 44 C96 46 96 74 78 74 Z", SNOW),
    "carrot": p("M44 32 C38 18 40 10 46 14 C48 20 48 26 50 30 C52 22 56 8 62 12 C64 20 58 28 56 32 Z", GREEN)
            + p("M36 36 C36 30 64 30 64 36 C62 56 56 76 50 94 C44 76 38 56 36 36 Z", ORANGE)
            + line("M40 48 L48 48 M54 60 L60 60 M44 72 L50 72"),
    "bunny": e(38, 28, 9, 24, GRAY) + e(62, 28, 9, 24, GRAY) + e(38, 30, 4, 15, PINK, 0, False)
           + e(62, 30, 4, 15, PINK, 0, False) + c(50, 64, 27, GRAY) + eyes(58, 40, 60)
           + p("M46 66 L54 66 L50 71 Z", PINK) + line("M50 71 L50 76 M28 68 L40 70 M28 76 L40 74 M72 68 L60 70 M72 76 L60 74"),
    "boots": p("M44 22 L64 22 L64 62 C64 66 68 68 74 68 L80 70 C86 72 86 86 80 86 L44 86 Z", DGOLD)
           + p("M16 18 L38 18 L38 64 C38 68 42 70 48 70 L54 72 C60 74 60 90 54 90 L16 90 Z", GOLD)
           + line("M16 30 L38 30"),
    "grapes": line("M50 26 L50 12") + p("M50 16 C58 8 70 10 72 14 C64 20 56 20 50 16 Z", GREEN)
            + "".join(c(x, y, 10, PURPLE) for x, y in ((34, 36), (50, 34), (66, 36), (42, 52), (58, 52), (50, 68))),
    "mouse": line("M14 70 C4 66 6 54 14 52") + c(54, 36, 11, GRAY) + c(54, 36, 5.5, PINK, False)
           + p("M14 70 C14 50 30 38 50 40 C66 42 80 54 84 64 C86 70 80 74 74 74 L22 74 C16 74 14 72 14 70 Z", GRAY)
           + c(70, 54, 3, "#222", False) + c(85, 65, 3.5, PINK) + line("M78 64 L90 60 M78 68 L90 70"),
    "balloon": line("M50 78 C44 84 56 90 50 96")
             + p("M50 8 C70 8 80 24 80 40 C80 60 62 72 50 72 C38 72 20 60 20 40 C20 24 30 8 50 8 Z", RED)
             + p("M45 72 L55 72 L50 79 Z", RED) + e(38, 28, 5, 9, "#F4B4B4", -20, False),
    "snowman": line("M30 62 L12 50 M70 62 L88 50", 4, BROWN)
             + c(50, 72, 22, SNOW) + c(50, 36, 16, SNOW)
             + p("M36 48 C44 52 56 52 64 48 L64 54 C56 58 44 58 36 54 Z", RED)
             + p("M34 22 L66 22 L66 26 L34 26 Z", DARK) + p("M40 6 L60 6 L60 22 L40 22 Z", DARK)
             + p("M50 36 L64 39 L50 42 Z", ORANGE) + eyes(31, 44, 56, 2.5)
             + c(50, 66, 2.5, "#222", False) + c(50, 76, 2.5, "#222", False),
    "juice": p("M30 20 L70 20 L64 90 L36 90 Z", GLASS) + p("M31 34 L69 34 L64 90 L36 90 Z", ORANGE)
           + colored_line("M58 8 L52 40", RED, 4),
    "dress": p("M38 12 L26 22 L32 32 L40 26 Z", BLUE) + p("M62 12 L74 22 L68 32 L60 26 Z", BLUE)
           + p("M38 10 L44 10 C45 17 55 17 56 10 L62 10 L60 34 C72 50 84 72 88 90 L12 90 C16 72 28 50 40 34 Z", BLUE)
           + p("M40 34 L60 34 L60 41 L40 41 Z", DBLUE),
    "blocks": p("M14 54 L46 54 L46 86 L14 86 Z", RED) + p("M50 54 L82 54 L82 86 L50 86 Z", BLUE)
            + p("M32 18 L64 18 L64 50 L32 50 Z", GOLD)
            + c(30, 70, 7, "#F4B4B4") + p("M66 62 L74 78 L58 78 Z", "#A9CBF0") + p("M42 28 L54 28 L54 40 L42 40 Z", "#F2CF6E"),
    "lion": p(scallop(50, 50, 42, 12, 7), MANE) + c(34, 30, 7, GOLD) + c(66, 30, 7, GOLD) + c(50, 52, 25, GOLD)
          + e(50, 62, 12, 9, WHEAT) + p("M45 56 L55 56 L50 61 Z", "#222") + line("M50 61 L50 65 M45 67 C48 69 52 69 55 67")
          + eyes(48, 41, 59),
    # color words: true hues (exempt from the lightness rule, recorded in LICENSES.yaml)
    "red": crayon("#E53935", "#B71C1C"),
    "blue": crayon("#1E88E5", "#0D47A1"),
    "yellow": crayon("#FDD835", "#F9A825"),
    "green": crayon("#43A047", "#1B5E20"),
    "pink": crayon("#F48FB1", "#D81B60"),
    "purple": crayon("#8E24AA", "#4A148C"),
}

for slug, body in PICS.items():
    (OUT / f"{slug}.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{body}</svg>\n')
print(len(PICS), "pictures written")
