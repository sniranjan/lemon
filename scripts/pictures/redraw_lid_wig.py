import sys
from pathlib import Path
O = 'stroke="#222" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"'
def svg(*p): return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">' + "".join(p) + "</svg>\n"
def line(d, color, w):
    return (f'<path d="{d}" fill="none" stroke="#222" stroke-width="{w+6}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
def blob(circles, fill):
    """Union of circles with one outer outline: thick dark strokes first, plain fills on top."""
    a = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#222" stroke="#222" stroke-width="6"/>' for x, y, r in circles)
    b = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>' for x, y, r in circles)
    return a + b

GREY, DARK, HI, POT = "#A0A4AA", "#7F8A9E", "#C4C7CC", "#E87878"

def lid():
    pot = (line("M23 83 L13 82 M77 83 L87 82", "#444444", 3)
           + f'<path d="M23 81 L77 81 L75 91 C74 96 71 97 66 97 L34 97 C29 97 26 96 25 91 Z" fill="{POT}" {O}/>'
           + f'<ellipse cx="50" cy="81" rx="28" ry="5" fill="#444444" {O}/>')
    g = ('<g transform="rotate(-10 50 50)">'
         f'<path d="M9 58 C9 68 91 68 91 58 L91 54 L9 54 Z" fill="{DARK}" {O}/>'
         f'<path d="M9 54 C9 28 91 28 91 54 C91 62 9 62 9 54 Z" fill="{GREY}" {O}/>'
         f'<path d="M20 46 C26 39 36 36 46 35" fill="none" stroke="{HI}" stroke-width="4" stroke-linecap="round"/>'
         f'<path d="M45 36 C45 30 47 29 50 29 C53 29 55 30 55 36 Z" fill="#444444" {O}/>'
         f'<ellipse cx="50" cy="26" rx="14" ry="6" fill="#444444" {O}/>'
         '</g>')
    return svg(pot, g)

def wig():
    WIG = "#F0935A"
    stand = (f'<rect x="30" y="89" width="40" height="8" rx="3" fill="{DARK}" {O}/>'
             + line("M50 76 L50 89", DARK, 6))
    back = blob([(50, 22, 14), (34, 26, 13), (66, 26, 13), (24, 40, 12), (76, 40, 12),
                 (21, 54, 12), (79, 54, 12), (24, 68, 11), (76, 68, 11), (36, 72, 9), (64, 72, 9),
                 (50, 40, 20)], WIG)
    head = f'<ellipse cx="50" cy="56" rx="15" ry="19" fill="#D9C7B0" {O}/>'
    bangs = blob([(36, 38, 9), (50, 35, 10), (64, 38, 9)], WIG)
    loops = []
    for x, y in [(50, 19), (34, 24), (66, 24), (23, 39), (77, 39), (20, 54), (80, 54), (24, 68), (76, 68),
                 (37, 37), (51, 34), (63, 37)]:
        loops.append(f'<path d="M{x-4} {y+3} C{x-6} {y-4} {x+5} {y-5} {x+4} {y+1} C{x+3} {y+5} {x-2} {y+4} {x-1} {y}" '
                     'fill="none" stroke="#222" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
    return svg(stand, back, head, bangs, *loops)

out = Path(sys.argv[1])
(out / "lid.svg").write_text(lid()); (out / "wig.svg").write_text(wig())
