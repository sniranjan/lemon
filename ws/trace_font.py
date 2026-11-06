"""The trace font: dotted lowercase letters for a child to trace with a pencil.

Andika (our page font) only has outlines; a dashed outline gives two rails, which is hard to trace.
So each letter here is a single centerline in Andika's ball-and-stick shapes (one-storey a and g),
drawn as round dots over a light gray band, on writing lines. Letters are SVG paths, not text.

Units: a letter cell is 150 high: y=0 top line, 50 middle line, 100 base line, 150 the bottom of
descenders (g, j, p, q, y). Widths vary per letter.
"""

from __future__ import annotations

import struct
from functools import lru_cache
from pathlib import Path

from markupsafe import Markup

# letter -> (width, [stroke paths in the order they are written])
GLYPHS: dict[str, tuple[int, list[str]]] = {
    "a": (50, ["M50,75 A25,25 0 1 0 0,75 A25,25 0 1 0 50,75", "M50,50 L50,100"]),
    "b": (50, ["M0,0 L0,100", "M0,75 A25,25 0 1 1 50,75 A25,25 0 1 1 0,75"]),
    "c": (48, ["M46,62 A25,25 0 1 0 46,88"]),
    "d": (50, ["M50,75 A25,25 0 1 0 0,75 A25,25 0 1 0 50,75", "M50,0 L50,100"]),
    "e": (50, ["M1,75 L50,75 A25,25 0 1 0 45,90"]),
    "f": (44, ["M44,8 C40,2 35,0 31,0 C22,0 18,6 18,16 L18,100", "M3,48 L38,48"]),
    "g": (50, ["M50,75 A25,25 0 1 0 0,75 A25,25 0 1 0 50,75", "M50,50 L50,128 C50,152 12,155 3,138"]),
    "h": (50, ["M0,0 L0,100", "M0,74 C0,56 10,50 25,50 C40,50 50,56 50,74 L50,100"]),
    "i": (12, ["M6,50 L6,100", "M6,28 L6,28.5"]),
    "j": (32, ["M30,50 L30,128 C30,150 10,152 2,140", "M30,28 L30,28.5"]),
    "k": (46, ["M0,0 L0,100", "M42,50 L2,78", "M14,70 L46,100"]),
    "l": (12, ["M6,0 L6,100"]),
    "m": (72, ["M0,50 L0,100", "M0,72 C0,56 6,50 18,50 C30,50 36,56 36,72 L36,100",
               "M36,72 C36,56 42,50 54,50 C66,50 72,56 72,72 L72,100"]),
    "n": (50, ["M0,50 L0,100", "M0,74 C0,56 10,50 25,50 C40,50 50,56 50,74 L50,100"]),
    "o": (50, ["M25,50 A25,25 0 1 0 25,100 A25,25 0 1 0 25,50"]),
    "p": (50, ["M0,50 L0,150", "M0,75 A25,25 0 1 1 50,75 A25,25 0 1 1 0,75"]),
    "q": (50, ["M50,75 A25,25 0 1 0 0,75 A25,25 0 1 0 50,75", "M50,50 L50,150"]),
    "r": (44, ["M0,50 L0,100", "M0,74 C0,58 12,50 26,50 C34,50 40,53 44,58"]),
    "s": (48, ["M44,58 C40,52 33,50 25,50 C14,50 6,55 6,63 C6,72 16,74 25,75 "
               "C36,76 46,79 46,88 C46,96 37,100 25,100 C14,100 6,97 2,91"]),
    "t": (38, ["M18,14 L18,100", "M2,50 L36,50"]),
    "u": (50, ["M0,50 L0,76 C0,94 10,100 25,100 C40,100 50,94 50,76", "M50,50 L50,100"]),
    "v": (48, ["M0,50 L24,100 L48,50"]),
    "w": (72, ["M0,50 L17,100 L36,58 L55,100 L72,50"]),
    "x": (46, ["M0,50 L46,100", "M46,50 L0,100"]),
    "y": (48, ["M0,50 L24,100", "M48,50 L0,150"]),
    "z": (48, ["M2,50 L46,50 L2,100 L48,100"]),
}

CELL_H = 150
GAP = 36          # between letters in a word
REPEAT_GAP = 46   # between copies of a letter in a practice row


def has_glyph(ch: str) -> bool:
    return ch in GLYPHS


def missing_glyphs(text: str) -> list[str]:
    return sorted({ch for ch in text if ch != " " and ch not in GLYPHS})


def text_width(text: str, gap: int = GAP) -> int:
    widths = [GLYPHS[ch][0] for ch in text]
    return sum(widths) + gap * (len(widths) - 1)


def svg(text: str, scale: float, *, gap: int = GAP, solid: int = 0, width_px: float | None = None) -> Markup:
    """Dotted `text` on writing lines, `scale` px per unit (x-height = 50 * scale px).

    The first `solid` letters are drawn solid (a model to copy). `width_px` stretches the writing
    lines to that width (the letters stay left-aligned).
    """
    missing = missing_glyphs(text)
    if missing:
        raise KeyError(f"the trace font has no {missing}")
    pad = 8   # units around the letters, so round caps aren't clipped
    w_units = text_width(text, gap) + 2 * pad
    if width_px:
        w_units = max(w_units, width_px / scale)
    h_units = CELL_H + 2 * pad
    band = 12 / scale if scale < 1.2 else 15 / scale     # light gray band under the dots
    dot = max(3.6, 3.0 * scale) / scale                   # dot diameter
    step = dot * 2.3                                      # dot spacing
    line = 1.6 / scale
    parts = [
        f'<svg class="trace" width="{w_units * scale:.0f}" height="{h_units * scale:.0f}" '
        f'viewBox="{-pad} {-pad} {w_units:.1f} {h_units}" aria-hidden="true">',
        f'<g stroke-width="{line:.2f}">'
        f'<line x1="{-pad}" y1="0" x2="{w_units - pad:.1f}" y2="0" stroke="#b9b9be"/>'
        f'<line x1="{-pad}" y1="50" x2="{w_units - pad:.1f}" y2="50" stroke="#b9b9be" '
        f'stroke-dasharray="{6 / scale:.2f} {5 / scale:.2f}"/>'
        f'<line x1="{-pad}" y1="100" x2="{w_units - pad:.1f}" y2="100" stroke="#6b6b70" '
        f'stroke-width="{2.4 / scale:.2f}"/></g>',
    ]
    x = 0
    for i, ch in enumerate(text):
        width, strokes = GLYPHS[ch]
        d = " ".join(strokes)
        if i < solid:
            parts.append(f'<path transform="translate({x},0)" d="{d}" fill="none" stroke="#1d1d1f" '
                         f'stroke-width="{band * 0.62:.2f}" stroke-linecap="round" stroke-linejoin="round"/>')
        else:
            parts.append(f'<g transform="translate({x},0)" fill="none" stroke-linecap="round" stroke-linejoin="round">'
                         f'<path d="{d}" stroke="#e1e1e4" stroke-width="{band:.2f}"/>'
                         f'<path d="{d}" stroke="#2b2b30" stroke-width="{dot:.2f}" '
                         f'stroke-dasharray="0 {step:.2f}"/></g>')
        x += width + gap
    parts.append("</svg>")
    return Markup("".join(parts))


def row(letter: str, scale: float, width_px: float, *, solid: int = 0, max_n: int = 7) -> Markup:
    """As many copies of `letter` as fit in `width_px` (at most `max_n`), on one set of writing lines."""
    width = GLYPHS[letter][0]
    n = int((width_px / scale - 16 + REPEAT_GAP) // (width + REPEAT_GAP))
    return svg(letter * max(1, min(n, max_n)), scale, gap=REPEAT_GAP, solid=solid, width_px=width_px)


# --- Andika: which characters it can print (the solid letters next to the traced ones) ----------

_ANDIKA = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "Andika-Regular.ttf"


@lru_cache(maxsize=None)
def andika_chars() -> frozenset[int]:
    """Code points in Andika's cmap (format 4 subtable), read with struct: no font library needed."""
    data = _ANDIKA.read_bytes()
    num_tables = struct.unpack(">H", data[4:6])[0]
    cmap = None
    for i in range(num_tables):
        tag, _, offset, _ = struct.unpack(">4sIII", data[12 + 16 * i: 28 + 16 * i])
        if tag == b"cmap":
            cmap = offset
    if cmap is None:
        raise ValueError("Andika has no cmap table")
    chars: set[int] = set()
    n = struct.unpack(">H", data[cmap + 2: cmap + 4])[0]
    for i in range(n):
        _, _, off = struct.unpack(">HHI", data[cmap + 4 + 8 * i: cmap + 12 + 8 * i])
        sub = cmap + off
        if struct.unpack(">H", data[sub: sub + 2])[0] != 4:
            continue
        segs = struct.unpack(">H", data[sub + 6: sub + 8])[0] // 2
        ends = struct.unpack(f">{segs}H", data[sub + 14: sub + 14 + 2 * segs])
        starts = struct.unpack(f">{segs}H", data[sub + 16 + 2 * segs: sub + 16 + 4 * segs])
        for s, e in zip(starts, ends):
            if s != 0xFFFF:
                chars.update(range(s, e + 1))
    return frozenset(chars)


def andika_has(text: str) -> bool:
    return all(ord(ch) in andika_chars() for ch in text)
