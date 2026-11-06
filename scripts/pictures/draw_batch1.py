"""Write the batch-1 pictures in the house style (run once; the SVGs are the source of truth)."""
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
S = 'stroke="#222" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"'
# palette: all mid-tones (grayscale lightness in brackets)
RED, ORANGE, GOLD, GREEN, BLUE = "#E87878", "#F0935A", "#E6A817", "#7FBF6A", "#6FA3E0"   # 56 64 67 67 61
PURPLE, TAN, BROWN, PINK, GRAY = "#A88FD8", "#C9A27A", "#A57C52", "#E89AB0", "#A0A4AA"   # 60 66 51 67 64
SKIN, SKIN2, HAIR, SKY, WHEAT = "#D9A27E", "#C98A64", "#A57C52", "#8CC4E8", "#D8B07A"   # 67 58 51 73 71
DARK, GLASS = "#444444", "#BFE0F5"


def p(d, fill, extra=""):
    return f'<path d="{d}" fill="{fill}" {S}{extra}/>'


def c(cx, cy, r, fill, stroke=True):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"' + (f" {S}/>" if stroke else "/>")


def line(d):
    return f'<path d="{d}" fill="none" {S}/>'


def eyes(y, x1, x2, r=3.5):
    return c(x1, y, r, "#222", False) + c(x2, y, r, "#222", False)


def wheel(x, y):
    return c(x, y, 10, DARK) + c(x, y, 4, GRAY)


PICS = {
    "mom": p("M22 52 C20 24 34 12 50 12 C66 12 80 24 78 52 L82 84 C70 88 30 88 18 84 Z", HAIR)
         + p("M20 97 C22 80 34 74 50 74 C66 74 78 80 80 97 Z", PINK)
         + '<ellipse cx="50" cy="48" rx="22" ry="25" fill="%s" %s/>' % (SKIN, S)
         + p("M28 44 C30 26 44 20 56 22 C66 24 72 32 72 44 C62 36 50 32 40 34 C36 38 32 41 28 44 Z", HAIR)
         + eyes(51, 42, 58, 3) + line("M43 62 C47 66 53 66 57 62"),
    "dad": p("M16 97 C18 78 32 72 50 72 C68 72 82 78 84 97 Z", BLUE) + line("M42 73 L50 82 L58 73")
         + c(27, 50, 6, SKIN) + c(73, 50, 6, SKIN)
         + '<ellipse cx="50" cy="48" rx="22" ry="25" fill="%s" %s/>' % (SKIN, S)
         + p("M28 42 C26 24 38 16 50 16 C62 16 74 24 72 42 C66 34 60 30 50 30 C40 30 34 34 28 42 Z", HAIR)
         + eyes(50, 42, 58, 3) + line("M43 62 C47 66 53 66 57 62"),
    "baby": c(16, 54, 7, SKIN) + c(84, 54, 7, SKIN) + c(50, 52, 34, SKIN)
          + line("M50 18 C44 10 54 5 57 12") + c(34, 63, 5, PINK, False) + c(66, 63, 5, PINK, False)
          + eyes(52, 40, 60) + line("M46 67 C48 70 52 70 54 67"),
    "milk": p("M28 36 L64 36 L64 90 L28 90 Z", BLUE) + p("M64 36 L78 30 L78 84 L64 90 Z", "#4F86C6")
          + p("M28 36 L46 18 L64 36 Z", "#FFFFFF") + p("M46 18 L60 12 L78 30 L64 36 Z", "#FFFFFF")
          + p("M36 56 L56 56 L56 72 L36 72 Z", "#FFFFFF")
          + p("M46 58 C43 63 41 66 46 70 C51 66 49 63 46 58 Z", BLUE),
    "banana": p("M16 26 C14 66 44 92 86 74 C91 72 91 63 84 62 C56 68 36 52 34 26 Z", GOLD)
            + line("M24 34 C26 60 46 76 76 70") + p("M16 26 L15 15 L27 14 L34 26 Z", BROWN),
    "car": p("M8 66 L8 54 C8 49 12 46 16 46 L28 46 L38 30 L66 30 L78 46 L86 46 C90 46 92 50 92 54 L92 66 Z", RED)
         + p("M41 34 L50 34 L50 46 L33 46 Z", GLASS) + p("M54 34 L64 34 L73 46 L54 46 Z", GLASS)
         + wheel(28, 68) + wheel(72, 68),
    "bus": p("M6 30 C6 26 10 24 14 24 L86 24 C92 24 94 28 94 34 L94 72 L6 72 Z", GOLD)
         + "".join(p(f"M{x} 30 L{x + 14} 30 L{x + 14} 46 L{x} 46 Z", GLASS) for x in (12, 30, 48, 66))
         + line("M6 56 L94 56") + wheel(24, 74) + wheel(76, 74),
    "duck": p("M20 60 C20 46 34 42 46 48 C50 40 46 34 46 28 C46 16 58 10 68 16 C76 20 76 32 70 38 "
              "C66 44 66 48 72 52 C86 58 84 82 60 84 L36 84 C24 84 20 72 20 60 Z", GOLD)
          + p("M74 25 L91 28 L76 34 Z", ORANGE) + c(63, 24, 3, "#222", False)
          + p("M34 62 C42 55 58 57 62 66 C54 72 42 72 34 62 Z", "#D4951A"),
    "bed": p("M10 34 L24 34 L24 84 L10 84 Z", BROWN) + p("M80 50 L92 50 L92 84 L80 84 Z", BROWN)
         + p("M24 56 L80 56 L80 74 L24 74 Z", BLUE) + p("M26 46 C26 40 44 40 44 46 L44 56 L26 56 Z", "#FFFFFF"),
    "shoe": p("M10 70 L10 42 C10 38 14 36 18 36 L34 36 C38 46 48 52 60 52 C78 54 90 60 90 70 Z", ORANGE)
          + p("M8 70 L92 70 C92 78 88 80 84 80 L12 80 C8 80 8 76 8 70 Z", "#FFFFFF")
          + line("M25 40 L31 46 M33 44 L39 50"),
    "hat": p("M66 60 C80 58 96 62 96 70 C90 72 76 72 64 70 Z", RED)
         + p("M10 68 C10 40 26 28 44 28 C62 28 76 42 76 68 Z", RED)
         + line("M44 30 C38 42 36 54 36 68 M44 30 C52 42 56 54 56 68") + c(44, 27, 4, RED),
    "book": p("M76 18 L84 22 L84 90 L76 86 Z", "#FFFFFF") + p("M20 86 L76 86 L84 90 L28 90 Z", "#FFFFFF")
          + p("M20 14 L76 14 L76 86 L20 86 Z", GREEN) + p("M20 14 L30 14 L30 86 L20 86 Z", "#5E9E4A")
          + p("M40 30 L68 30 L68 44 L40 44 Z", "#FFFFFF"),
    "tree": p("M44 60 L56 60 L58 90 L42 90 Z", BROWN)
          + p("M50 10 C64 10 72 20 72 28 C84 30 88 44 82 52 C88 62 78 72 66 68 C60 76 40 76 34 68 "
              "C22 72 12 62 18 52 C12 44 16 30 28 28 C28 18 36 10 50 10 Z", GREEN),
    "flower": line("M50 56 L50 92") + p("M50 78 C40 68 28 70 26 74 C32 82 44 82 50 78 Z", GREEN)
            + "".join(c(x, y, 13, PINK) for x, y in ((50, 22), (65, 33), (59, 51), (41, 51), (35, 33)))
            + c(50, 38, 9, GOLD),
    "bird": p("M24 56 L8 46 L12 63 Z", BLUE)
          + p("M22 58 C22 38 40 28 56 32 C62 22 76 20 82 30 C86 36 84 44 78 48 C80 66 64 80 44 78 "
              "C30 76 22 70 22 58 Z", BLUE)
          + p("M82 31 L94 36 L82 40 Z", ORANGE) + c(71, 31, 3, "#222", False)
          + p("M36 54 C44 46 60 48 64 58 C54 64 44 64 36 54 Z", "#5A8FCC") + line("M47 78 L45 90 M58 78 L60 90"),
    "hand": "".join(f'<rect x="{x}" y="{y}" width="9" height="{52 - y}" rx="4.5" fill="{SKIN}" {S}/>'
                    for x, y in ((31, 22), (41, 13), (51, 15), (61, 23)))
          + p("M34 74 C26 70 16 60 13 52 C11 46 17 42 21 46 C25 52 30 56 36 58 Z", SKIN)
          + p("M30 50 C30 46 33 44 37 44 L67 44 C70 44 72 47 72 50 L72 74 C72 86 62 94 51 94 "
              "C39 94 30 86 30 74 Z", SKIN),
    "nose": c(50, 50, 38, SKIN) + eyes(40, 35, 65, 3)
          + p("M50 34 C46 48 39 58 41 64 C43 69 57 69 59 64 C61 58 54 48 50 34 Z", SKIN2)
          + line("M40 78 C46 82 54 82 60 78"),
    "foot": "".join(c(x, y, r, SKIN) for x, y, r in ((40, 22, 8), (54, 19, 6.5), (64, 23, 5.5), (71, 30, 5), (76, 38, 4.5)))
          + p("M34 34 C44 30 64 32 67 46 C69 60 65 72 63 82 C61 93 40 95 36 85 C32 75 30 60 30 48 "
              "C30 40 30 36 34 34 Z", SKIN),
    "ear": p("M40 14 C62 8 80 24 78 46 C76 62 64 66 60 76 C56 88 44 92 36 86 C28 80 34 70 40 66 "
             "C34 54 28 26 40 14 Z", SKIN) + line("M46 26 C60 22 68 34 64 46 C60 56 50 54 52 64"),
    "spoon": p("M44 50 L50 44 L88 82 C90 86 86 90 82 88 Z", GRAY)
           + f'<ellipse cx="34" cy="34" rx="17" ry="24" fill="{GRAY}" {S} transform="rotate(-45 34 34)"/>'
           + '<ellipse cx="32" cy="32" rx="8" ry="13" fill="#C4C8CC" transform="rotate(-45 32 32)"/>',
    "egg": p("M50 10 C68 10 80 40 80 60 C80 80 66 92 50 92 C34 92 20 80 20 60 C20 40 32 10 50 10 Z", WHEAT),
    "bread": p("M12 52 C12 30 30 24 50 24 C70 24 88 30 88 52 C88 57 84 60 84 60 L84 82 C84 86 80 88 76 88 "
               "L24 88 C20 88 16 86 16 82 L16 60 C16 60 12 57 12 52 Z", WHEAT)
           + line("M32 36 L40 46 M48 32 L56 42 M64 34 L72 44"),
    "cookie": c(50, 50, 38, TAN)
            + "".join(c(x, y, r, "#6B4A33", False) for x, y, r in
                      ((36, 34, 5), (60, 30, 4.5), (66, 52, 5), (44, 56, 4.5), (32, 68, 4), (56, 72, 5), (50, 42, 3.5))),
    "bear": c(26, 26, 12, BROWN) + c(74, 26, 12, BROWN) + c(26, 26, 6, TAN, False) + c(74, 26, 6, TAN, False)
          + c(50, 54, 34, BROWN) + f'<ellipse cx="50" cy="67" rx="15" ry="12" fill="{TAN}" {S}/>'
          + '<ellipse cx="50" cy="61" rx="6" ry="4.5" fill="#222"/>' + line("M50 65 L50 70 M44 72 C47 75 53 75 56 72")
          + eyes(46, 38, 62),
    "truck": p("M6 30 L60 30 L60 70 L6 70 Z", GOLD) + p("M60 42 L80 42 L92 56 L92 70 L60 70 Z", RED)
           + p("M64 46 L78 46 L86 56 L64 56 Z", GLASS) + wheel(22, 72) + wheel(76, 72),
    "boat": line("M50 14 L50 64") + p("M52 16 L80 58 L52 58 Z", SKY) + p("M48 22 L48 58 L24 58 Z", GOLD)
          + p("M10 64 L90 64 L78 82 L22 82 Z", RED)
          + line("M6 91 C14 87 22 95 30 91 C38 87 46 95 54 91 C62 87 70 95 78 91 C86 87 90 93 94 91"),
    "moon": p("M62 10 C36 12 18 30 18 52 C18 76 38 92 62 90 C44 82 34 68 34 50 C34 34 44 18 62 10 Z", GOLD)
,
    "star": p("M50 6 L61 37 L94 38 L68 58 L77 90 L50 71 L23 90 L32 58 L6 38 L39 37 Z", GOLD),
    "sock": p("M36 10 L64 10 L64 56 C64 60 66 62 70 64 L82 70 C92 76 88 92 76 90 L44 82 C34 80 30 72 32 64 L36 52 Z", BLUE)
          + p("M36 10 L64 10 L64 22 L36 22 Z", "#FFFFFF") + line("M36 32 L64 32 M36 42 L64 42"),
    "coat": p("M30 16 L42 12 C46 20 54 20 58 12 L70 16 L82 28 L92 78 L80 80 L72 46 L72 90 L28 90 L28 46 "
              "L20 80 L8 78 L18 28 Z", RED)
          + line("M50 22 L50 90 M34 64 L44 64 M56 64 L66 64"),
    "chair": p("M28 12 L72 12 L72 46 L28 46 Z", BROWN) + line("M40 18 L40 40 M50 18 L50 40 M60 18 L60 40")
           + p("M26 58 L34 58 L34 92 L26 92 Z", BROWN) + p("M66 58 L74 58 L74 92 L66 92 Z", BROWN)
           + p("M22 46 L78 46 L78 58 L22 58 Z", TAN),
    "door": p("M24 8 L76 8 L76 94 L24 94 Z", TAN) + p("M32 16 L68 16 L68 44 L32 44 Z", "#B88C62")
          + p("M32 54 L68 54 L68 86 L32 86 Z", "#B88C62") + c(64, 50, 4, GOLD),
}

for slug, body in PICS.items():
    (OUT / f"{slug}.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{body}</svg>\n')
print(len(PICS), "pictures written")
