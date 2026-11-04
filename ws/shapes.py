"""Simple closed outlines for coloring sheets, as SVG path data on a 100×100 grid.

These are drawn inline (outline only, no fill), so they live here rather than in
assets/pictures/, whose fill-lightness rule doesn't apply to them.
"""

SHAPES: dict[str, str] = {
    "circle": "M50 8 A42 42 0 1 1 49.9 8 Z",
    "square": "M12 12 H88 V88 H12 Z",
    "triangle": "M50 8 L92 88 H8 Z",
    "heart": "M50 88 C20 66 6 48 10 30 C14 12 38 8 50 28 C62 8 86 12 90 30 C94 48 80 66 50 88 Z",
    "star": "M50 6 L61 37 L94 38 L68 58 L77 90 L50 71 L23 90 L32 58 L6 38 L39 37 Z",
    "house": "M50 8 L92 44 H80 V90 H20 V44 H8 Z",
    "cloud": "M26 74 C8 74 6 52 22 48 C20 30 42 24 50 36 C56 20 82 24 80 44 C96 46 96 74 78 74 Z",
    "egg": "M50 6 C74 6 88 44 88 62 C88 82 72 94 50 94 C28 94 12 82 12 62 C12 44 26 6 50 6 Z",
}
