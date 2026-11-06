"""Bunnies Reading (5A) word batch 1 pictures (23 words, approved 2026-11-06 by the orchestrator under the
user's delegation) in the house style, plus a redrawn "hat" (a wide-brim straw sun hat, so it no longer
looks like a cap).

Run: uv run python scripts/pictures/draw_5A_batch1.py <out_dir> [slug ...]
A record only: the SVGs in assets/pictures/ are the source of truth (STATUS.md, picture workflow).
Helpers come from draw_7A_batch5.py.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draw_7A_batch5 import (BARK, BLUE, BROWN, DARK, DBLUE, DGREEN, GOLD, GRAY, GREEN, LBLUE, LGRAY,  # noqa: E402
                            MBROWN, ORANGE, PEACH, PINK, PURPLE, RED, S, SKIN, SLATE, TAN, TOAST, WHEAT,
                            WHITE, c, colored_line, e, eyes, heart, line, p, r, rot)

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else None
ONLY = set(sys.argv[2:])
STRAW = "#D9B46A"


def web():
    cx, cy = 50, 54
    ends = [(cx + 42 * math.cos(t), cy + 42 * math.sin(t)) for t in [i * math.pi / 4 + math.pi / 8 for i in range(8)]]
    out = "".join(line(f"M{cx} {cy} L{x:.1f} {y:.1f}", 3, SLATE) for x, y in ends)
    for k in (0.35, 0.68, 1.0):
        pts = [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in ends]
        out += line("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z", 3, SLATE)
    return out


PICS = {
    "queen": p("M28 50 C24 30 36 24 50 24 C64 24 76 30 72 50 L76 78 L24 78 Z", BROWN)
           + p("M12 100 C14 82 30 74 50 74 C70 74 86 82 88 100 Z", PURPLE)
           + p("M42 66 L58 66 L58 78 C54 82 46 82 42 78 Z", SKIN)
           + e(50, 50, 18, 21, SKIN)
           + p("M32 44 C34 32 42 30 50 34 C58 30 66 32 68 44 C60 38 40 38 32 44 Z", BROWN)
           + eyes(52, 43, 57, 2.6)
           + line("M44 60 C47 63 53 63 56 60", 2.5)
           + p("M30 32 L30 12 L40 22 L50 8 L60 22 L70 12 L70 32 Z", GOLD)
           + c(50, 22, 3.5, RED) + c(38, 27, 2.5, BLUE) + c(62, 27, 2.5, BLUE),
    "quilt": p("M10 20 L90 20 L90 84 L10 84 Z", BLUE)
           + "".join(r(10 + 20 * i, 20 + 16 * j, 20, 16, [BLUE, PEACH, GREEN, PINK][(i + j) % 4])
                     for i in range(4) for j in range(4))
           + line("M14 24 L86 24 L86 80 L14 80 Z", 1.5, WHITE)
           + p("M70 84 L90 84 L90 66 Z", PURPLE),
    "zipper": p("M14 6 L48 6 L48 54 L30 96 L14 96 Z", BLUE) + p("M86 6 L52 6 L52 54 L70 96 L86 96 Z", BLUE)
            + "".join(r(44 if k % 2 else 50, 8 + 6 * k, 6, 4, GRAY, 1) for k in range(8))
            + "".join(r(44 - 2.6 * k, 58 + 6 * k, 5, 4, GRAY, 1) + r(51 + 2.6 * k, 58 + 6 * k, 5, 4, GRAY, 1) for k in range(6))
            + r(42, 50, 16, 10, SLATE, 3) + r(45, 60, 10, 22, GRAY, 4) + e(50, 76, 3, 3, BLUE),
    "bat": rot(-40, 50, 46,
               p("M12 43 L50 42 C66 40 80 37 90 37 C97 37 97 55 90 55 C80 55 66 52 50 50 L12 49 Z", TAN)
               + e(10, 46, 3.5, 7, MBROWN)
               + r(14, 41, 22, 10, RED, 3))
          + c(76, 80, 11, WHITE) + line("M69 72 C73 77 73 83 69 88 M83 72 C79 77 79 83 83 88", 2, RED),
    "pen": rot(-35, 50, 50,
               r(14, 42, 52, 16, BLUE, 3) + p("M66 42 L86 50 L66 58 Z", WHEAT) + p("M80 47.6 L90 50 L80 52.4 Z", DARK)
               + r(8, 40, 14, 20, DBLUE, 3) + line("M10 38 L30 38", 4, GRAY)),
    "pin": colored_line("M80 36 L26 36", GRAY, 6)
           + colored_line("M26 36 C8 36 8 64 24 64 C34 64 34 50 24 50 C16 50 16 60 26 62 L72 42", GRAY, 6)
           + p("M66 26 L88 26 C96 26 96 46 88 46 L66 46 Z", GRAY)
           + line("M72 32 L86 32", 2.5, WHITE),
    "mop": colored_line("M74 6 L50 62", MBROWN, 6)
         + "".join(colored_line(f"M{x} 66 C{x - 3} 76 {x + 3} 84 {x - 2 + (x % 7) / 2} 94", GRAY, 5)
                   for x in (30, 38, 46, 54, 62, 70))
         + r(28, 58, 46, 10, BLUE, 4),
    "bug": line("M30 46 L14 38 M28 60 L10 60 M30 74 L14 84 M70 46 L86 38 M72 60 L90 60 M70 74 L86 84", 4)
           + line("M44 22 L36 8 M56 22 L64 8", 3)
           + e(50, 60, 24, 28, GREEN) + line("M50 36 L50 88", 3)
           + c(40, 52, 4, DGREEN) + c(60, 52, 4, DGREEN) + c(42, 72, 4, DGREEN) + c(58, 72, 4, DGREEN)
           + c(50, 28, 11, GREEN) + eyes(26, 45, 55, 2.4) + line("M46 32 C48 34 52 34 54 32", 2),
    "mat": line("M14 30 L10 24 M24 30 L22 24 M34 30 L34 24 M66 30 L66 24 M76 30 L78 24 M86 30 L90 24 "
                "M14 76 L10 82 M24 76 L22 82 M34 76 L34 82 M66 76 L66 82 M76 76 L78 82 M86 76 L90 82", 3)
         + r(8, 30, 84, 46, RED, 6)
         + r(8, 40, 84, 8, ORANGE) + r(8, 58, 84, 8, ORANGE) + p("M8 30 L92 30 L92 76 L8 76 Z", "none"),
    "net": colored_line("M42 50 L8 94", MBROWN, 6)
           + p("M40 34 C40 64 54 84 68 84 C82 84 90 62 88 34 Z", LBLUE)
           + line("M48 36 C50 60 58 78 66 82 M60 36 C60 58 64 76 70 82 M74 36 C74 56 74 72 74 82 "
                  "M44 50 L88 50 M48 64 L86 64 M56 76 L82 76", 1.8, WHITE)
           + e(64, 34, 25, 10, "none") + colored_line("M39 34 C39 26 89 26 89 34 C89 42 39 42 39 34", GRAY, 4),
    "bun": e(50, 74, 40, 10, WHEAT) + p("M12 72 C12 38 30 26 50 26 C70 26 88 38 88 72 C70 78 30 78 12 72 Z", TOAST)
           + "".join(e(x, y, 2.6, 1.6, WHITE, a) for x, y, a in
                     [(36, 40, -20), (50, 36, 0), (64, 42, 20), (42, 52, -10), (58, 54, 15), (28, 56, -30), (72, 58, 30)])
           + line("M26 46 C32 38 40 34 46 33", 3, "#E8BC84"),
    "top": line("M8 92 L92 92", 3) + line("M10 52 L18 52 M8 62 L16 62 M84 52 L92 52 M86 62 L94 62", 3, GRAY)
           + r(44, 10, 12, 18, BLUE, 3)
           + p("M18 40 C18 26 82 26 82 40 L52 88 L48 88 Z", RED)
           + p("M20 46 L80 46 L72 58 L28 58 Z", ORANGE) + p("M18 40 C18 26 82 26 82 40 L52 88 L48 88 Z", "none"),
    "mug": colored_line("M70 42 C90 42 90 74 70 74", BLUE, 6)
           + r(20, 28, 52, 62, BLUE, 8) + heart(46, 58, 11, RED),
    "pan": colored_line("M70 52 L96 36", BARK, 8)
           + e(40, 58, 36, 30, GRAY) + e(40, 58, 28, 22, SLATE)
           + line("M24 48 C28 42 34 40 40 39", 3, LGRAY),
    "jet": line("M2 40 L18 40 M4 48 L16 48 M6 56 L14 56", 3, GRAY)
           + p("M40 52 L58 52 L42 86 L32 86 Z", DBLUE)
           + p("M18 46 C20 38 30 36 40 36 L82 38 C92 40 96 46 96 50 C96 54 92 58 82 58 L28 58 C22 58 18 54 18 46 Z", LBLUE)
           + p("M18 46 L12 20 L22 20 L36 38 Z", DBLUE)
           + "".join(c(x, 44, 2.6, DARK, False) for x in (48, 56, 64, 72))
           + p("M84 40 C90 41 94 45 95 48 L84 48 Z", DARK)
           + p("M46 46 L64 46 L50 22 L42 22 Z", DBLUE),
    "wig": r(38, 88, 24, 8, GRAY, 3) + colored_line("M50 80 L50 88", GRAY, 6)
           + e(50, 60, 17, 21, GRAY)
           + "".join(c(x, y, 9, col) for (x, y), col in zip(
               [(26, 74), (74, 74), (22, 60), (78, 60), (22, 45), (78, 45), (28, 31), (72, 31), (40, 23), (60, 23),
                (50, 20), (36, 38), (50, 34), (64, 38)],
               [PINK, BLUE, ORANGE, GREEN, PURPLE, PINK, BLUE, ORANGE, GREEN, PURPLE, PINK, ORANGE, BLUE, GREEN])),
    "log": line("M4 82 L96 82", 3)
           + p("M16 40 L80 40 L80 74 L16 74 C8 74 8 40 16 40 Z", MBROWN)
           + line("M24 48 L50 48 M30 58 L62 58 M22 66 L44 66", 2.5, BARK)
           + e(80, 57, 13, 17, WHEAT) + e(80, 57, 8, 11, "none") + e(80, 57, 3, 5, "none")
           + colored_line("M44 40 L40 26", MBROWN, 5) + e(36, 20, 7, 4, GREEN, -30),
    "nut": rot(-35, 50, 52,
               p("M50 12 C68 12 72 30 65 42 C61 50 61 54 65 62 C73 76 65 92 50 92 C35 92 27 76 35 62 "
                 "C39 54 39 50 35 42 C28 30 32 12 50 12 Z", STRAW)
               + line("M42 24 L46 26 M54 22 L58 25 M40 34 L44 35 M56 34 L60 33 M40 70 L44 72 M56 70 L60 68 "
                      "M44 82 L48 80 M54 80 L58 82", 2.5, MBROWN)),
    "map": p("M8 22 L36 14 L36 82 L8 90 Z", WHEAT) + p("M36 14 L64 22 L64 90 L36 82 Z", TAN)
           + p("M64 22 L92 14 L92 82 L64 90 Z", WHEAT)
           + p("M14 34 C20 28 30 30 30 38 C30 46 18 46 14 40 Z", GREEN) + p("M70 60 C76 54 86 56 86 64 C84 72 72 72 70 66 Z", GREEN)
           + line("M18 70 C28 60 40 66 46 56 C52 46 62 52 68 42 C72 36 76 34 80 30", 3, RED).replace('stroke-linecap="round"', 'stroke-dasharray="5 5" stroke-linecap="round"')
           + line("M76 24 L86 34 M86 24 L76 34", 4, RED),
    "web": colored_line("M6 8 L94 8", MBROWN, 5) + line("M34 13 L42 16 M66 13 L58 16", 3, SLATE) + web(),
    "lid": e(50, 30, 10, 6, BARK) + colored_line("M50 34 L50 38", BARK, 6)
           + p("M10 72 C14 50 30 38 50 38 C70 38 86 50 90 72 Z", GRAY)
           + r(6, 70, 88, 9, SLATE, 4) + line("M24 58 C30 50 38 46 46 45", 3, LGRAY),
    "jam": r(26, 36, 48, 56, RED, 9) + r(34, 52, 32, 24, WHITE, 3)
           + c(50, 66, 6, RED) + p("M46 58 L50 61 L54 58 L50 55 Z", GREEN)
           + p("M22 30 L78 30 L80 40 L20 40 Z", BLUE) + p("M26 20 L74 20 L76 30 L24 30 Z", BLUE)
           + line("M30 24 L36 36 M44 24 L48 36 M56 24 L58 36 M68 24 L66 36", 2, WHITE),
    "tub": e(18, 46, 6, 8, GRAY) + e(82, 46, 6, 8, GRAY)
           + p("M14 40 L86 40 L78 88 L22 88 Z", GRAY)
           + e(50, 40, 36, 8, LBLUE)
           + c(38, 32, 5, WHITE) + c(48, 28, 6, WHITE) + c(60, 31, 5, WHITE)
           + line("M18 60 L82 60 M20 74 L80 74", 2.5, SLATE),
    # --- redraw: hat is a wide-brim straw sun hat (the old one read as a cap) -------------------------
    "hat": e(50, 66, 46, 14, STRAW) + p("M26 64 C26 36 36 26 50 26 C64 26 74 36 74 64 C64 68 36 68 26 64 Z", STRAW)
           + p("M27 52 C36 56 64 56 73 52 L74 62 C64 66 36 66 26 62 Z", RED)
           + line("M34 40 C38 34 44 32 48 32", 2.5, "#F0D9A0") + line("M14 70 C30 76 70 76 86 70", 2, MBROWN),
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
