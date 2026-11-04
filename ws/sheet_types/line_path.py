"""ZI-B/C (and later ZII): draw along a lane from a start dot to a small picture.

Lines always run left→right or top→bottom (diagonals top-left→bottom-right). Their length
grows across each part: `length_frac` [lo, hi] of the usable span, interpolated by the
page's progress through the part. Geometry is in the canvas's own pixel units.
"""

from __future__ import annotations

from ..content import line_targets
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

CANVAS_W, CANVAS_H = 704, 680
TARGET = 64            # end picture size
DISC = 44              # radius of the white disc the end picture sits on (centered on the line's end)
EDGE = 8               # clear space between the lane's rounded end and the canvas edge


def _fmt(*nums: float) -> str:
    return " ".join(f"{n:.1f}" for n in nums)


def _horizontal(y: float, x0: float, length: float, kind: str, humps: int, amp: float) -> tuple[str, tuple, tuple]:
    x1 = x0 + length
    if kind == "straight":
        return f"M{_fmt(x0, y)} L{_fmt(x1, y)}", (x0, y), (x1, y)
    # arc = one hump up; wave = `humps` half-waves alternating up and down
    seg = length / humps
    d = f"M{_fmt(x0, y)}"
    for i in range(humps):
        sign = -1 if (kind == "arc" or i % 2 == 0) else 1
        d += f" Q{_fmt(x0 + seg * (i + 0.5), y + sign * 2 * amp)} {_fmt(x0 + seg * (i + 1), y)}"
    return d, (x0, y), (x1, y)


@register("line_path")
class LinePath(SheetType):
    template = "line_path.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        n, lane = r["paths_per_sheet"], r["lane_px"]
        lo, hi = r["length_frac"]
        frac = lo + (hi - lo) * ctx.spec.progress
        kind = r["path"]
        # one direction per sheet, cycling through the allowed ones page by page
        directions = r.get("directions", ["horizontal"])
        direction = directions[(ctx.spec.page - 1) % len(directions)]
        targets = ctx.rng.sample(list(line_targets()), n)

        start = lane / 2 + 3 + EDGE          # the lane's rounded end must stay on the page
        paths = []
        if direction == "vertical":
            span = CANVAS_H - start - DISC - EDGE
            for i in range(n):
                x = CANVAS_W * (i + 0.5) / n
                y0, y1 = start, start + frac * span
                paths.append({"d": f"M{_fmt(x, y0)} L{_fmt(x, y1)}", "start": [x, y0], "end": [x, y1]})
        else:
            band = CANVAS_H / n
            span = CANVAS_W - start - DISC - EDGE
            length = frac * span
            for i in range(n):
                this_kind, humps = kind, r.get("humps", 1)
                if kind == "mixed_curves":
                    humps = ctx.rng.randint(*humps)
                    this_kind = "arc" if humps == 1 else "wave"
                amp = min(band * 0.22, 70)
                yc = band * (i + 0.5)
                if this_kind == "arc":
                    yc += amp / 2           # arc rises above its baseline; center the whole shape
                if direction == "diagonal":
                    drop = min(band * 0.5, length * 0.35)
                    y0 = yc - drop / 2
                    d = f"M{_fmt(start, y0)} L{_fmt(start + length, y0 + drop)}"
                    p0, p1 = (start, y0), (start + length, y0 + drop)
                else:
                    d, p0, p1 = _horizontal(yc, start, length, this_kind, humps, amp)
                paths.append({"d": d, "start": list(p0), "end": list(p1)})
        items = [{"kind": "path", **p, "target": t, "lane": lane, "direction": direction,
                  "disc": DISC, "size": TARGET} for p, t in zip(paths, targets)]
        return SheetContent(title="Draw the line", parent_tip=ctx.tip(self.name), items=items)

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = []
        for i in sheet.items:
            (x0, y0), (x1, y1) = i["start"], i["end"]
            if x1 < x0 or y1 < y0 or (x1, y1) == (x0, y0):
                issues.append(error(sheet, f"line runs the wrong way: {i['start']} → {i['end']}"))
            if not (DISC <= x1 <= CANVAS_W - DISC and DISC <= y1 <= CANVAS_H - DISC):
                issues.append(error(sheet, f"end picture at {i['end']} is outside the canvas"))
            if x0 < i["lane"] / 2 + 3 or y0 < i["lane"] / 2 + 3:
                issues.append(error(sheet, f"lane start {i['start']} is cut off by the page edge"))
        return issues
