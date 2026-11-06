"""Kittens Reading (4A) word batches 1 and 2 pictures (50 words, approved by the orchestrator under user
delegation 2026-11-06) in the house style.

Run: uv run python scripts/pictures/draw_4A_batch1.py <out_dir> [slug ...]
A record only: the SVGs in assets/pictures/ are the source of truth (STATUS.md, picture workflow).
Helpers and palette come from draw_7A_batch5.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draw_7A_batch5 import (  # noqa: E402
    BLUE, BROWN, DARK, GOLD, GRAY, GREEN, LBLUE, LGRAY, MBROWN, ORANGE, PINK, PURPLE, RED, S, SKIN, SLATE, TAN,
    TOAST, WHEAT, WHITE, c, child_face, colored_line, e, line, p, palm, r, rot, star,
)

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else None
ONLY = set(sys.argv[2:])
BRICK, BRICK_TOP, STEEL, CREAM = "#C8775A", "#D99A7E", "#868A92", "#EDE6D3"
GROUND = "M4 92 L96 92"


def nos(svg):
    """Same shape without its outline (highlights, inner fills)."""
    return svg.replace(S, 'stroke="none"')


def bricks(x0, y0, cols, rows, w=20, h=12):
    out = ""
    for j in range(rows):
        off = 0 if j % 2 == 0 else -w / 2
        for i in range(cols + (1 if j % 2 else 0)):
            x = x0 + off + i * w
            x1, x2 = max(x, x0), min(x + w, x0 + cols * w)
            if x2 - x1 > 2:
                out += r(x1, y0 + j * h, x2 - x1, h, BRICK, 1)
    return out


def face_eyes(x, y, gap=8, rad=3):
    return c(x - gap / 2, y, rad, "#222", False) + c(x + gap / 2, y, rad, "#222", False)


def smile(x, y, w=6):
    return line(f"M{x - w} {y} C{x - w / 2} {y + w * 0.6} {x + w / 2} {y + w * 0.6} {x + w} {y}", 2.5)


PICS = {
    # --- batch 1, unit 1: double letters at the end ----------------------------------------------
    "glass": p("M28 12 L72 12 L66 90 L34 90 Z", LBLUE)
           + p("M30.5 40 L69.5 40 L66 90 L34 90 Z", BLUE)
           + e(50, 40, 19.5, 4, LBLUE)
           + line("M38 20 L36 34 M40 52 L38 80", 3, WHITE)
           + e(50, 12, 22, 4, LBLUE),
    "wall": line(GROUND, 3) + bricks(10, 32, 4, 5) + p("M6 92 C14 84 22 92 30 86 C38 92 46 84 54 92 Z", GREEN),
    "well": line(GROUND, 3)
          + colored_line("M24 64 L24 22 M76 64 L76 22", MBROWN, 6)
          + p("M14 28 L50 6 L86 28 Z", RED)
          + line("M24 34 L76 34", 4) + line("M50 34 L50 48", 2.5)
          + p("M42 48 L58 48 L56 60 L44 60 Z", GRAY)
          + p("M14 60 L86 60 L82 92 L18 92 Z", GRAY)
          + line("M14 70 L86 70 M16 81 L84 81 M30 60 L30 70 M54 60 L54 70 M78 60 L78 70 M42 70 L42 81 M66 70 L66 81 "
                 "M26 81 L26 92 M50 81 L50 92 M74 81 L74 92", 2.5)
          + p("M14 60 L86 60 L82 92 L18 92 Z", "none"),
    "bull": line(GROUND, 3)
          + r(26, 62, 10, 28, BROWN, 4) + r(64, 62, 10, 28, BROWN, 4)
          + e(50, 62, 32, 20, BROWN)
          + p("M30 30 C18 28 12 18 16 10 C20 18 26 22 34 24 Z", WHITE)
          + p("M70 30 C82 28 88 18 84 10 C80 18 74 22 66 24 Z", WHITE)
          + e(22, 36, 9, 5, BROWN, -20) + e(78, 36, 9, 5, BROWN, 20)
          + e(50, 42, 20, 22, BROWN)
          + e(50, 56, 15, 10, PINK) + c(44, 56, 2.5, "#222", False) + c(56, 56, 2.5, "#222", False)
          + face_eyes(50, 38, 16, 3.2),
    "grill": line(GROUND, 3)
           + colored_line("M36 66 L24 90 M64 66 L76 90 M50 68 L50 90", DARK, 3)
           + p("M18 50 L82 50 C82 64 68 72 50 72 C32 72 18 64 18 50 Z", RED)
           + p("M18 46 C18 26 32 18 50 18 C68 18 82 26 82 46 Z", RED)
           + r(16, 45, 68, 6, GRAY, 3)
           + colored_line("M44 14 L56 14", DARK, 4)
           + line("M34 12 C30 6 38 4 34 -2 M64 12 C60 6 68 4 64 -2", 2.5, GRAY),
    # --- unit 2: sh -------------------------------------------------------------------------------
    "ship": colored_line("M64 18 L64 40", DARK, 1) + r(58, 18, 12, 22, GOLD, 2)
          + r(30, 30, 44, 22, WHITE, 3) + c(41, 41, 4, LBLUE) + c(55, 41, 4, LBLUE)
          + p("M8 52 L92 52 L80 76 L20 76 Z", RED)
          + line("M14 60 L86 60", 3, WHITE)
          + p("M0 80 C10 74 20 86 30 80 C40 74 50 86 60 80 C70 74 80 86 90 80 C95 77 100 79 100 80 L100 96 L0 96 Z", BLUE),
    "dish": e(50, 54, 44, 14, PINK) + p("M6 54 C10 76 30 84 50 84 C70 84 90 76 94 54 Z", PINK)
          + e(50, 54, 34, 9, "#F2C4D0")
          + line("M18 70 C30 78 70 78 82 70", 2.5, WHITE),
    "shark": p("M42 44 L52 14 L64 44 Z", GRAY)
           + p("M84 52 L98 34 L96 56 L98 76 L84 60 Z", GRAY)
           + p("M6 58 C14 38 50 32 86 50 C88 56 88 58 86 62 C60 78 20 78 6 58 Z", GRAY)
           + nos(p("M9 62 C24 75 60 75 84 62 C62 79 22 78 9 62 Z", WHITE))
           + c(24, 52, 3.4, "#222", False) + line("M12 62 C18 66 26 66 32 62", 2.5)
           + line("M40 52 L38 60 M46 52 L44 60", 2.5),
    "shelf": r(16, 18, 10, 34, RED, 2) + r(27, 22, 10, 30, BLUE, 2) + r(38, 16, 9, 36, GREEN, 2)
           + rot(14, 54, 34, r(49, 20, 9, 32, GOLD, 2))
           + p("M68 52 L86 52 L83 38 L71 38 Z", BRICK) + c(72, 30, 7, GREEN) + c(82, 28, 7, GREEN) + c(77, 22, 6, GREEN)
           + r(8, 52, 84, 8, MBROWN, 2)
           + p("M18 60 L18 76 L32 60 Z", MBROWN) + p("M82 60 L82 76 L68 60 Z", MBROWN),
    "shower": colored_line("M10 0 L10 16 C10 24 16 26 24 26 L44 26", STEEL, 6)
            + p("M40 18 L52 18 L74 38 L18 38 L40 18 Z", STEEL)
            + e(46, 38, 28, 5, LGRAY)
            + "".join(colored_line(f"M{x} {y} L{x + dx} {y + 12}", BLUE, 3) for x, y, dx in
                      [(26, 50, -3), (36, 48, -1), (46, 50, 0), (56, 48, 1), (66, 50, 3),
                       (22, 70, -3), (32, 72, -2), (44, 70, 0), (56, 72, 2), (70, 70, 3)])
            + p("M10 92 L90 92 L86 98 L14 98 Z", LBLUE),
    # --- unit 3: ch, tch --------------------------------------------------------------------------
    "bench": line(GROUND, 3)
           + colored_line("M18 64 L14 92 M82 64 L86 92 M22 64 L22 30 M78 64 L78 30", DARK, 3)
           + r(10, 24, 80, 10, MBROWN, 3) + r(10, 38, 80, 10, MBROWN, 3)
           + r(6, 56, 88, 10, MBROWN, 3),
    "watch": r(36, 2, 28, 30, BLUE, 6) + r(36, 68, 28, 30, BLUE, 6)
           + line("M44 14 L56 14 M44 84 L56 84", 2.5, LBLUE)
           + c(50, 50, 26, GRAY) + c(50, 50, 19, WHITE)
           + line("M50 50 L50 37 M50 50 L60 54", 4)
           + r(76, 46, 6, 8, GRAY, 2),
    "couch": line(GROUND, 3)
           + colored_line("M18 80 L18 90 M82 80 L82 90", DARK, 3)
           + r(14, 24, 72, 34, PURPLE, 10)
           + r(6, 46, 22, 36, PURPLE, 8) + r(72, 46, 22, 36, PURPLE, 8)
           + r(26, 56, 48, 24, PURPLE, 4) + line("M50 56 L50 80 M50 26 L50 56", 2.5),
    "beach": p("M0 52 L100 52 L100 70 L0 70 Z", BLUE)
           + line("M8 60 C14 56 20 64 26 60 M60 58 C66 54 72 62 78 58", 2.5, WHITE)
           + p("M0 66 C30 60 70 62 100 68 L100 100 L0 100 Z", TAN)
           + c(84, 18, 10, GOLD)
           + colored_line("M34 26 L46 92", DARK, 2)
           + p("M10 34 C12 16 36 6 56 16 C48 20 40 24 34 26 C28 26 18 28 10 34 Z", RED)
           + nos(p("M24 28 C26 18 34 12 42 12 C38 18 36 22 34 26 Z", WHITE))
           + p("M10 34 C12 16 36 6 56 16 C48 20 40 24 34 26 C28 26 18 28 10 34 Z", "none")
           + c(66, 84, 5, PINK) + p("M64 80 L74 78 L70 86 Z", PINK),
    "cheek": child_face(46, 48, 30, 32)
             + nos(c(26, 60, 7, "#E88A9A")) + nos(c(66, 60, 7, "#E88A9A"))
             + colored_line("M96 100 L74 66", SKIN, 9) + c(73, 64, 5.5, SKIN),
    # --- unit 4: th, wh ---------------------------------------------------------------------------
    "tooth": c(50, 50, 46, LBLUE, False)
           + p("M28 22 C34 14 44 18 50 22 C56 18 66 14 72 22 C80 34 74 48 70 60 C66 74 64 86 58 86 "
               "C52 86 54 66 50 66 C46 66 48 86 42 86 C36 86 34 74 30 60 C26 48 20 34 28 22 Z", CREAM)
           + face_eyes(50, 40, 12, 2.6) + smile(50, 48, 5)
           + line("M34 28 C36 24 40 24 42 26", 2.5, WHITE),
    "path": p("M0 30 L100 30 L100 100 L0 100 Z", GREEN)
          + p("M44 30 L56 30 C60 44 44 52 52 66 C58 78 72 88 74 100 L26 100 C30 86 38 76 34 64 C30 50 46 44 44 30 Z", TAN)
          + c(18, 60, 4, PINK) + c(82, 50, 4, GOLD) + line("M18 64 L18 72 M82 54 L82 62", 2.5)
          + line("M10 84 L12 78 M14 84 L16 78 M86 80 L88 74 M90 80 L92 74", 2.5)
          + p("M0 30 L100 30", "none"),
    "moth": colored_line("M46 24 C40 12 32 10 28 8 M54 24 C60 12 68 10 72 8", DARK, 1)
          + p("M48 34 C30 10 4 18 8 40 C10 54 30 56 48 50 Z", TAN)
          + p("M52 34 C70 10 96 18 92 40 C90 54 70 56 52 50 Z", TAN)
          + p("M48 52 C30 56 18 74 28 82 C38 88 46 72 48 60 Z", WHEAT)
          + p("M52 52 C70 56 82 74 72 82 C62 88 54 72 52 60 Z", WHEAT)
          + c(28, 34, 6, BROWN) + c(72, 34, 6, BROWN)
          + e(50, 52, 6, 22, BROWN) + face_eyes(50, 34, 6, 2),
    "wheel": c(50, 50, 44, STEEL) + c(50, 50, 28, LGRAY) + c(50, 50, 8, GRAY)
           + line("M50 42 L50 24 M50 58 L50 76 M42 50 L24 50 M58 50 L76 50 M44 44 L32 32 M56 56 L68 68 "
                  "M56 44 L68 32 M44 56 L32 68", 3)
           + line("M20 30 C24 24 28 20 34 16", 3, LGRAY),
    "whisk": colored_line("M50 58 L50 96", RED, 10)
           + "".join(colored_line(d, GRAY, 3) for d in [
               "M50 58 C24 44 26 4 50 4 C74 4 76 44 50 58",
               "M50 58 C36 44 36 4 50 4 C64 4 64 44 50 58",
               "M50 58 L50 4"])
           + r(44, 54, 12, 8, GRAY, 2),
    # --- unit 5: ck -------------------------------------------------------------------------------
    "lock": colored_line("M32 46 L32 28 C32 4 68 4 68 28 L68 46", STEEL, 7)
          + r(20, 44, 60, 48, GOLD, 8)
          + c(50, 62, 6, DARK) + p("M47 64 L53 64 L55 80 L45 80 Z", DARK),
    "pocket": p("M0 0 L100 0 L100 100 L0 100 Z", BLUE)
            + p("M22 22 L78 22 L78 70 L50 86 L22 70 Z", "#5A8FCC")
            + line("M26 28 L74 28 M26 30 L26 68 L50 81 L74 68 L74 30", 2, GOLD)
            + line("M8 6 L8 94 M92 6 L92 94", 2, GOLD)
            + p("M0 0 L100 0 L100 100 L0 100 Z", "none"),
    "chicken": line(GROUND, 3)
             + colored_line("M44 74 L42 90 M58 74 L60 90", GOLD, 3)
             + p("M84 24 C96 30 96 52 84 58 C88 46 88 36 84 24 Z", BROWN)
             + p("M30 40 C16 52 22 78 48 78 C72 78 86 64 84 48 C76 52 62 50 52 42 C44 36 36 36 30 40 Z", TOAST)
             + p("M48 56 C56 50 68 52 72 60 C64 64 54 64 48 56 Z", BROWN)
             + c(30, 30, 13, TOAST)
             + p("M24 18 C22 10 28 8 30 14 C30 8 36 6 37 14 C39 10 44 12 42 20 Z", RED)
             + p("M17 30 L8 34 L17 37 Z", GOLD) + e(20, 42, 3, 5, RED)
             + c(28, 28, 2.6, "#222", False),
    "sticker": r(12, 12, 76, 76, LBLUE, 12)
             + star(48, 50, 30, GOLD)
             + p("M88 64 L88 76 C88 82 82 88 76 88 L64 88 Z", WHITE)
             + face_eyes(48, 48, 10, 2.4) + smile(48, 55, 4),
    "cracker": r(14, 14, 72, 72, WHEAT, 8)
             + "".join(c(x, y, 2.6, MBROWN, False) for x in (30, 50, 70) for y in (30, 50, 70))
             + line("M14 22 C18 18 18 18 22 14", 2.5, WHITE),
    "flag": colored_line("M24 6 L24 96", MBROWN, 5) + c(24, 6, 5, GOLD)
          + p("M27 12 L88 30 L27 50 Z", RED)
          + line(GROUND, 3),
    "glove": p("M30 94 L30 76 L70 76 L70 94 Z", GREEN)
           + line("M30 84 L70 84", 2.5, "#5FA34C")
           + p("M28 76 C24 64 24 54 24 44 C24 38 32 38 32 44 L32 54 L34 22 C34 16 42 16 42 22 L42 50 L44 14 "
               "C44 8 52 8 52 14 L52 50 L54 18 C54 12 62 12 62 18 L62 52 L64 30 C64 24 72 24 72 30 L72 60 "
               "C72 70 70 74 70 76 Z", GREEN),
    "plant": p("M50 60 C30 56 16 40 18 22 C34 26 46 40 50 60 Z", GREEN)
           + p("M50 60 C70 56 84 40 82 22 C66 26 54 40 50 60 Z", GREEN)
           + p("M50 60 C42 44 42 22 50 8 C58 22 58 44 50 60 Z", GREEN)
           + line("M50 60 L50 50 M30 34 L44 52 M70 34 L56 52", 2.5, "#5FA34C")
           + r(26, 58, 48, 10, BRICK, 3) + p("M30 68 L70 68 L64 94 L36 94 Z", BRICK),
    "glue": r(30, 36, 40, 58, LBLUE, 10) + r(36, 54, 28, 22, PINK, 3)
          + nos(p("M50 58 C46 64 46 70 50 70 C54 70 54 64 50 58 Z", WHITE))
          + r(36, 24, 28, 14, ORANGE, 4) + p("M44 24 L50 6 L56 24 Z", ORANGE)
          + p("M50 0 C47 3 47 5 50 6 C53 5 53 3 50 0 Z", WHITE),
    "slipper": p("M6 80 C4 72 8 66 18 66 L80 62 C92 62 96 70 94 78 C92 84 84 86 76 86 L16 86 C10 86 6 84 6 80 Z", BROWN)
             + p("M36 74 C34 50 64 34 86 44 C96 50 98 64 94 76 Z", PINK)
             + line("M42 66 C50 54 64 48 78 48", 2.5, "#F2C4D0")
             + c(70, 40, 8, "#F2C4D0") + c(79, 38, 6, "#F2C4D0")
             + line("M14 72 C24 70 36 70 48 70", 2.5, "#C9A27A"),
    "brick": p("M14 44 L64 44 L64 78 L14 78 Z", BRICK)
           + p("M14 44 L36 30 L86 30 L64 44 Z", BRICK_TOP)
           + p("M64 44 L86 30 L86 64 L64 78 Z", "#B06448")
           + line("M24 54 L30 54 M44 66 L52 66 M70 50 L74 48", 2.5, "#A0583E"),
    # --- unit 7: r-blends -------------------------------------------------------------------------
    "present": r(14, 44, 72, 50, RED, 4) + r(10, 32, 80, 16, RED, 4)
             + r(44, 32, 12, 62, GOLD, 0)
             + p("M50 32 C36 14 18 22 30 32 Z", GOLD) + p("M50 32 C64 14 82 22 70 32 Z", GOLD)
             + c(50, 31, 5, GOLD),
    "pretzel": "".join(colored_line(d, TOAST, 11) for d in [
                   "M50 54 C34 30 14 32 14 52 C14 72 34 82 50 82 C66 82 86 72 86 52 C86 32 66 30 50 54",
                   "M30 82 C38 70 46 60 50 54 C54 60 62 70 70 82"])
             + "".join(c(x, y, 1.8, WHITE, False) for x, y in
                       [(18, 46), (26, 38), (16, 60), (36, 80), (82, 46), (74, 38), (84, 60), (64, 80), (50, 82)]),
    "tray": p("M8 70 L92 70 L84 86 L16 86 Z", TAN)
          + r(4, 64, 92, 8, TAN, 3)
          + r(26, 38, 22, 26, BLUE, 3) + p("M48 44 C58 44 58 58 48 58", "none")
          + c(70, 58, 9, TOAST),
    "trumpet": "".join(colored_line(d, GOLD, 7) for d in ["M10 54 L62 54", "M24 54 C24 70 50 70 50 54"])
             + p("M60 46 C74 44 84 30 92 26 L92 82 C84 78 74 64 60 62 Z", GOLD)
             + "".join(r(x, 36, 6, 14, GOLD, 2) + c(x + 3, 34, 4, GOLD) for x in (30, 40, 50))
             + r(4, 50, 8, 8, GOLD, 2),
    # --- unit 8: s-blends -------------------------------------------------------------------------
    "snake": p("M14 86 C8 72 28 66 50 70 C74 74 92 70 88 58 C84 46 60 52 44 50 C28 48 20 38 30 30 "
               "C34 26 40 26 44 28 L48 36 C42 34 36 36 38 40 C42 44 54 42 66 42 C88 42 100 54 96 70 "
               "C92 86 70 86 50 82 C34 79 22 80 20 90 Z", GREEN)
           + c(46, 26, 11, GREEN)
           + c(42, 23, 2.4, "#222", False) + c(51, 23, 2.4, "#222", False) + smile(46, 30, 4)
           + c(30, 76, 3, "#5FA34C", False) + c(64, 77, 3, "#5FA34C", False) + c(80, 62, 3, "#5FA34C", False),
    "sponge": r(14, 34, 72, 46, GOLD, 8) + r(14, 26, 72, 14, GREEN, 6)
            + "".join(e(x, y, 4, 3, "#C9900E", 0, False) for x, y in
                      [(26, 50), (44, 56), (62, 48), (74, 64), (34, 68), (54, 70)])
            + c(84, 18, 5, LBLUE) + c(92, 26, 3, LBLUE),
    "swan": p("M0 70 L100 70 L100 100 L0 100 Z", LBLUE)
          + line("M8 82 C14 78 20 86 26 82 M60 88 C66 84 72 92 78 88", 2.5, WHITE)
          + p("M20 58 C20 74 40 78 62 76 C80 74 92 66 88 52 C80 60 70 58 60 54 C50 50 30 46 20 58 Z", WHITE)
          + colored_line("M64 58 C70 46 62 34 64 22 C66 14 74 12 78 18", WHITE, 7)
          + p("M80 16 L92 22 L80 24 Z", ORANGE) + c(74, 17, 1.8, "#222", False)
          + line("M36 62 C46 58 56 62 62 66", 2.5),
    "skate": line(GROUND, 3)
           + r(10, 70, 80, 8, GRAY, 3)
           + p("M18 70 L18 30 C18 20 46 20 46 30 L46 48 C62 50 80 54 84 64 L84 70 Z", RED)
           + line("M24 36 L40 36 M24 44 L40 44", 2.5, WHITE)
           + c(24, 84, 7, PURPLE) + c(50, 84, 7, PURPLE) + c(76, 84, 7, PURPLE),
    "stool": line(GROUND, 3)
           + colored_line("M30 40 L18 92 M70 40 L82 92 M50 42 L50 92", MBROWN, 6)
           + colored_line("M26 70 L74 70", MBROWN, 4)
           + e(50, 36, 36, 9, MBROWN) + e(50, 32, 36, 9, MBROWN),
    # --- batch 2, unit 9: teams at the end --------------------------------------------------------
    "ring": f'<path d="M22 64 a28 28 0 1 0 56 0 a28 28 0 1 0 -56 0 Z M30 64 a20 20 0 1 0 40 0 a20 20 0 1 0 -40 0 Z" '
            f'fill="{GOLD}" fill-rule="evenodd" {S}/>'
            + p("M36 30 L42 18 L58 18 L64 30 L50 42 Z", PURPLE)
            + line("M42 18 L46 30 L50 42 M58 18 L54 30 L50 42 M36 30 L64 30", 2)
            + line("M26 54 C28 46 32 42 36 40", 3, "#F6D27A"),
    "skunk": line(GROUND, 3)
           + p("M60 70 C70 66 74 44 70 28 C68 14 80 8 90 14 C98 22 96 42 90 56 C86 68 76 74 64 76 Z", SLATE)
           + nos(p("M78 16 C86 14 92 22 90 34 C88 46 84 58 78 66 C82 52 84 38 82 28 C82 22 80 18 78 16 Z", WHITE))
           + e(46, 70, 26, 16, SLATE)
           + colored_line("M32 82 L32 90 M60 82 L60 90", SLATE, 4)
           + c(24, 58, 14, SLATE)
           + nos(p("M24 44 C26 50 26 56 24 64 C22 56 22 50 24 44 Z", WHITE))
           + c(14, 48, 4, SLATE) + c(34, 48, 4, SLATE)
           + face_eyes(24, 57, 10, 2.4) + c(24, 64, 2, PINK, False) + smile(24, 66, 3),
    "pond": p("M0 46 L100 46 L100 100 L0 100 Z", GREEN)
          + e(50, 70, 42, 20, BLUE)
          + line("M28 66 C34 62 40 70 46 66 M58 78 C64 74 70 82 76 78", 2.5, LBLUE)
          + p("M60 64 C60 56 80 56 80 64 C80 70 60 72 60 64 Z M70 64 L80 62", "#5FA34C")
          + c(66, 60, 4, PINK)
          + colored_line("M10 46 L8 24 M16 48 L18 26", "#5FA34C", 3) + e(8, 22, 3, 6, BROWN) + e(18, 24, 3, 6, BROWN),
    "vest": p("M30 10 L40 10 C42 22 58 22 60 10 L70 10 L72 30 C80 34 84 40 84 50 L84 90 L16 90 L16 50 "
              "C16 40 20 34 28 30 Z", ORANGE)
          + line("M50 22 L50 90", 3) + line("M18 50 L48 50 M52 50 L82 50 M16 70 L48 70 M52 70 L84 70", 2.5, "#D9763E")
          + c(54, 32, 2.5, DARK, False),
    "stamp": c(50, 14, 10, MBROWN) + colored_line("M50 22 L50 40", MBROWN, 8)
           + r(26, 40, 48, 18, MBROWN, 4) + r(22, 58, 56, 10, RED, 2)
           + p("M10 74 L90 74 L94 96 L6 96 Z", LBLUE)
           + nos(star(50, 85, 9, RED)),
    # --- unit 10: word families --------------------------------------------------------------------
    # bat, pan, wig and bug were drawn first, then given to Bunnies Reading (its batch has them); replaced by:
    # "can" (a soup can) was replaced by "man" after merging Bunnies Reading, so "can" stays only the verb.
    "man": line(GROUND, 3)
           + colored_line("M42 70 L40 90 M58 70 L60 90", BLUE, 9)
           + e(38, 91, 7, 3.5, DARK) + e(62, 91, 7, 3.5, DARK)
           + colored_line("M30 44 L18 64 M70 44 L84 26", SKIN, 7)
           + p("M30 40 C30 34 40 32 50 32 C60 32 70 34 70 40 L66 72 L34 72 Z", GREEN)
           + e(35, 24, 3.5, 5, SKIN) + e(65, 24, 3.5, 5, SKIN) + c(50, 22, 15, SKIN)
           + p("M35 20 C35 2 65 2 65 20 C60 13 40 13 35 20 Z", BROWN)
           + p("M36 26 C38 46 62 46 64 26 C60 34 40 34 36 26 Z", BROWN)
           + c(44, 21, 2.2, "#222", False) + c(56, 21, 2.2, "#222", False)
           + line("M45 27 C48 29.5 52 29.5 55 27", 2),
    "jug": colored_line("M70 34 C88 34 90 64 72 68", BLUE, 5)
           + p("M38 16 L62 16 L64 26 C74 34 76 48 74 70 C74 86 68 92 50 92 C32 92 26 86 26 70 C24 48 26 34 36 26 Z", BLUE)
           + p("M26 66 C40 62 60 62 74 66 L74 70 C74 86 68 92 50 92 C32 92 26 86 26 70 Z", WHITE)
           + r(36, 8, 28, 10, RED, 3),
    "rake": colored_line("M80 4 L46 60", MBROWN, 6)
            + p("M20 66 L64 52 L68 60 L24 74 Z", GREEN)
            + "".join(colored_line(f"M{24 + i * 8.6} {72 - i * 2.8} L{20 + i * 8.6} {90 - i * 2.8}", GREEN, 3) for i in range(6))
            + p("M70 92 C74 82 86 82 90 88 C84 94 76 96 70 92 Z", ORANGE),
    "crow": line(GROUND, 3)
            + colored_line("M44 76 L42 90 M54 76 L56 90", GOLD, 3)
            + p("M86 46 L98 40 L94 58 Z", SLATE)
            + p("M28 46 C30 64 48 80 66 72 C80 66 90 56 88 46 C76 42 54 42 28 46 Z", SLATE)
            + p("M40 52 C52 48 70 50 80 56 C70 64 52 64 40 52 Z", "#6B7488")
            + c(30, 36, 14, SLATE)
            + p("M16 34 L2 40 L16 42 Z", GOLD) + c(26, 32, 2.6, "#222", False),
    "jar": r(26, 26, 48, 68, LBLUE, 10)
         + p("M28 46 L72 46 L72 84 C72 90 68 92 64 92 L36 92 C32 92 28 90 28 84 Z", RED)
         + r(22, 10, 56, 16, GOLD, 4) + line("M30 14 L30 22 M40 14 L40 22 M50 14 L50 22 M60 14 L60 22 M70 14 L70 22", 2)
         + line("M34 34 L34 40", 3, WHITE),
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
