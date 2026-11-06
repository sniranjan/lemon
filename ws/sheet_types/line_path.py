"""Pencil paths (ZI-B/C, ZII-A…D): draw along a lane from a start dot to a small picture or shape.

Lines always run left→right or top→bottom (diagonals top-left→bottom-right), and never turn
back: zigzags and corners may go up or down while moving right, but never left. Their length
grows across each part: `length_frac` [lo, hi] of the usable span, interpolated by the page's
progress through the part. Geometry is in the canvas's own pixel units.

Rules (all optional except `path`, `paths_per_sheet`, `lane_px`, `length_frac`):
- `path`: straight | arc | wave | mixed_curves (ZI), zigzag | steps | bumps | s_curve | mixed (ZII)
- `kinds`: for `path: mixed`, the kinds each lane picks from
- `humps` (arc/wave), `turns` (zigzag corners), `steps` (stair steps), `bumps`, `bends` (s_curve):
  an int or an [lo, hi] range picked per lane
- `start_marker`: dot (ZI) | shape (a small shape on a disc, the same shape at the end) |
  picture (a story pair from content/pencil/line_stories.yaml). Every lane still starts at a dot.
"""

from __future__ import annotations

import math
import re

from ..content import line_stories, line_targets
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ..shapes import SHAPES
from ._common import error

CANVAS_W, CANVAS_H = 704, 680
TARGET = 64            # end picture size
DISC = 44              # radius of the white disc the end picture sits on (centered on the line's end)
EDGE = 8               # clear space between the lane's rounded end and the canvas edge
DOT = 11               # start dot radius
SHAPE = 56             # shape drawn inside a disc (start/end shape markers)
GAP = 10               # clear space between neighboring lanes and discs
MARKER_SHAPES = ("circle", "square", "triangle", "heart", "star", "house", "moon", "kite")
CORNER_KINDS = ("steps", "bumps", "s_curve")
# ZII sheet titles and parent-tip keys (content/tips/pencil.yaml: line_path_<style>)
TITLES = {"shape": "Shape to shape", "picture": "Off they go",
          "zigzag": "Zigzag lines", "corners": "Corners and curves"}


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


# --- ZII lane shapes, built along the flow (u) and across it (v), then mapped to x/y ----------

def _segments(kind: str, u0: float, vc: float, length: float, count: int, amp: float) -> list[tuple]:
    """Lane geometry as (command, points...) in (u, v); u only ever grows."""
    if kind == "straight":
        return [("M", (u0, vc)), ("L", (u0 + length, vc))]
    if kind in ("arc", "wave"):
        seg, v = length / count, vc + (amp / 2 if kind == "arc" else 0)
        out = [("M", (u0, v))]
        for i in range(count):
            sign = -1 if (kind == "arc" or i % 2 == 0) else 1
            out.append(("Q", (u0 + seg * (i + 0.5), v + sign * 2 * amp), (u0 + seg * (i + 1), v)))
        return out
    if kind == "zigzag":            # `count` sharp corners, alternating above and below the center
        du = length / (count + 1)
        pts = [(u0 + du * j, vc + (-amp if j % 2 else amp)) for j in range(1, count + 1)]
        return [("M", (u0, vc)), *(("L", p) for p in pts), ("L", (u0 + length, vc))]
    if kind == "steps":             # a staircase: along, across, along … (`count` steps)
        du, dv = length / (count + 1), 2 * amp / count
        out, v = [("M", (u0, vc - amp))], vc - amp
        for j in range(1, count + 1):
            out += [("L", (u0 + du * j, v)), ("L", (u0 + du * j, v + dv))]
            v += dv
        return out + [("L", (u0 + length, v))]
    if kind == "bumps":             # square bumps: along, up, along, down … (`count` bumps)
        du = length / (2 * count + 1)
        out, v = [("M", (u0, vc + amp))], vc + amp
        for j in range(1, 2 * count + 1):
            out.append(("L", (u0 + du * j, v)))
            v = vc - amp if v > vc else vc + amp
            out.append(("L", (u0 + du * j, v)))
        return out + [("L", (u0 + length, v))]
    if kind == "s_curve":           # smooth S bends from one side to the other (`count` bends)
        du = length / count
        out, v = [("M", (u0, vc - amp))], vc - amp
        for j in range(count):
            a, nv = u0 + du * j, (vc + amp if v < vc else vc - amp)
            out.append(("C", (a + du / 2, v), (a + du / 2, nv), (a + du, nv)))
            v = nv
        return out
    raise ValueError(f"unknown line path kind {kind!r}")


def _emit(segs: list[tuple], vertical: bool) -> tuple[str, list, list]:
    xy = (lambda p: (p[1], p[0])) if vertical else (lambda p: p)
    parts = [cmd + " ".join(_fmt(*xy(p)) for p in pts) for cmd, *pts in segs]
    ends = [[round(c, 1) for c in xy(p)] for p in (segs[0][1], segs[-1][-1])]   # as printed in `d`
    return " ".join(parts), ends[0], ends[1]


def _count(ctx: GenContext, kind: str):
    key = {"zigzag": "turns", "steps": "steps", "bumps": "bumps", "s_curve": "bends"}.get(kind, "humps")
    n = ctx.rules.get(key, 1)
    return ctx.rng.randint(*n) if isinstance(n, list) else n


# --- path sampling (used by verify) -----------------------------------------------------------

_TOKEN = re.compile(r"[MLQC]|-?\d+(?:\.\d+)?")


def sample_path(d: str, step: float = 4.0) -> list[tuple[float, float]]:
    """Points along an SVG path of absolute M/L/Q/C commands, about `step` px apart (≥ 50 per segment)."""
    tokens, pts, cur, i = _TOKEN.findall(d), [], None, 0
    need = {"M": 1, "L": 1, "Q": 2, "C": 3}
    while i < len(tokens):
        cmd = tokens[i]
        ctrl = [(float(tokens[i + 1 + 2 * k]), float(tokens[i + 2 + 2 * k])) for k in range(need[cmd])]
        i += 1 + 2 * need[cmd]
        if cmd == "M":
            cur = ctrl[0]
            pts.append(cur)
            continue
        poly = [cur, *ctrl]
        chord = sum(math.dist(a, b) for a, b in zip(poly, poly[1:]))
        n = max(50, math.ceil(chord / step))
        for k in range(1, n + 1):
            t = k / n
            if cmd == "L":
                p = (cur[0] + (ctrl[0][0] - cur[0]) * t, cur[1] + (ctrl[0][1] - cur[1]) * t)
            elif cmd == "Q":
                (ax, ay), (bx, by), (cx, cy) = poly
                p = ((1 - t) ** 2 * ax + 2 * (1 - t) * t * bx + t * t * cx,
                     (1 - t) ** 2 * ay + 2 * (1 - t) * t * by + t * t * cy)
            else:
                (ax, ay), (bx, by), (cx, cy), (ex, ey) = poly
                w = ((1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3)
                p = (w[0] * ax + w[1] * bx + w[2] * cx + w[3] * ex, w[0] * ay + w[1] * by + w[2] * cy + w[3] * ey)
            pts.append(p)
        cur = ctrl[-1]
    return pts


def _dot_after_disc(d: str, start: list) -> list:
    """The start dot sits on the lane just outside the start disc."""
    for p in sample_path(d, step=1.0):
        if math.dist(p, start) >= DISC + DOT + 6:
            return [round(p[0], 1), round(p[1], 1)]
    raise ValueError("lane is too short to leave the start disc")


@register("line_path")
class LinePath(SheetType):
    template = "line_path.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        if r.get("start_marker", "dot") != "dot" or r["path"] not in ("straight", "arc", "wave", "mixed_curves"):
            return self._generate_zii(ctx)
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

    def _generate_zii(self, ctx: GenContext) -> SheetContent:
        """ZII: start shapes/pictures on discs, zigzags, corners and S-curves, vertical curves."""
        r = ctx.rules
        n, lane, marker = r["paths_per_sheet"], r["lane_px"], r.get("start_marker", "dot")
        lo, hi = r["length_frac"]
        frac = lo + (hi - lo) * ctx.spec.progress
        directions = r.get("directions", ["horizontal"])
        direction = directions[(ctx.spec.page - 1) % len(directions)]
        vertical = direction == "vertical"
        if marker == "shape":
            ends = [{"shape": s, "shape_path": SHAPES[s]} for s in ctx.rng.sample(MARKER_SHAPES, n)]
        elif marker == "picture":
            ends = [{"picture": a, "target": b} for a, b in ctx.rng.sample(list(line_stories()), n)]
        else:
            ends = [{"target": t} for t in ctx.rng.sample(list(line_targets()), n)]

        run, across = (CANVAS_H, CANVAS_W) if vertical else (CANVAS_W, CANVAS_H)
        u0 = (DISC if marker != "dot" else lane / 2 + 3) + EDGE
        length = frac * (run - u0 - DISC - EDGE)
        band = across / n
        # square bumps on a top→bottom lane would be flat strokes going left: those lanes use steps
        kinds = [k for k in r.get("kinds", []) if not (vertical and k == "bumps")] or ["steps"]
        items = []
        for i, end in enumerate(ends):
            kind = ctx.rng.choice(kinds) if r["path"] == "mixed" else r["path"]
            if vertical and kind == "bumps":
                kind = "steps"
            count = _count(ctx, kind)
            amp = min(band * (0.25 if kind in CORNER_KINDS else 0.22), 100 if kind in CORNER_KINDS else 70)
            d, p0, p1 = _emit(_segments(kind, u0, band * (i + 0.5), length, count, amp), vertical)
            item = {"kind": "path", "d": d, "start": p0, "end": p1, **end, "lane": lane,
                    "direction": direction, "disc": DISC, "size": TARGET, "path_kind": kind,
                    "join": "miter" if kind in ("steps", "bumps") else "round"}
            if marker != "dot":
                item["dot"] = _dot_after_disc(d, p0)
            items.append(item)
        style = marker if marker != "dot" else (
            "zigzag" if all(i["path_kind"] == "zigzag" for i in items) else "corners")
        return SheetContent(title=TITLES[style], parent_tip=ctx.tip(f"line_path_{style}"), items=items)

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = []
        sampled = []
        for i in sheet.items:
            (x0, y0), (x1, y1) = i["start"], i["end"]
            along = (x1 - x0) if i["direction"] != "vertical" else (y1 - y0)
            if along <= 0 or (i["direction"] == "diagonal" and y1 < y0):
                issues.append(error(sheet, f"line runs the wrong way: {i['start']} → {i['end']}"))
            for cx, cy in [i["end"]] + ([i["start"]] if "dot" in i else []):
                if not (DISC + EDGE <= cx <= CANVAS_W - DISC - EDGE and DISC + EDGE <= cy <= CANVAS_H - DISC - EDGE):
                    issues.append(error(sheet, f"disc at {[cx, cy]} is too close to the page edge"))
            if "dot" not in i and (x0 < i["lane"] / 2 + 3 or y0 < i["lane"] / 2 + 3):
                issues.append(error(sheet, f"lane start {i['start']} is cut off by the page edge"))
            if "shape" in i and i["shape"] not in SHAPES:
                issues.append(error(sheet, f"unknown shape {i['shape']!r}"))
            pts = sample_path(i["d"])
            issues += self._check_monotonic(sheet, i, pts)
            half = i["lane"] / 2 + 3
            if min(min(x, y, CANVAS_W - x, CANVAS_H - y) for x, y in pts) < half + EDGE - 0.05:
                issues.append(error(sheet, f"lane {i['d'][:24]}… comes too close to the page edge"))
            discs = [i["end"]] + ([i["start"]] if "dot" in i else [])
            sampled.append((i, pts, discs))
        issues += self._check_spacing(sheet, sampled)
        return issues

    @staticmethod
    def _check_monotonic(sheet: Sheet, item: dict, pts: list) -> list[Issue]:
        """The whole lane must keep moving right (or down): never back, not even inside a zigzag."""
        axes = {"horizontal": (0,), "diagonal": (0, 1), "vertical": (1,)}[item["direction"]]
        for a in axes:
            for p, q in zip(pts, pts[1:]):
                if q[a] < p[a] - 1e-6:
                    way = "left" if a == 0 else "up"
                    return [error(sheet, f"lane turns back ({way}) at {[round(p[0], 1), round(p[1], 1)]}")]
        if item["direction"] == "vertical":       # a flat stroke to the left reads as going back
            for p, q in zip(pts, pts[1:]):
                if q[0] < p[0] - 1e-6 and abs(q[1] - p[1]) < 1e-6:
                    return [error(sheet, f"lane runs flat to the left at {[round(p[0], 1), round(p[1], 1)]}")]
        return []

    @staticmethod
    def _check_spacing(sheet: Sheet, sampled: list) -> list[Issue]:
        """Lanes and discs on one sheet keep clear of each other."""
        issues = []
        for a in range(len(sampled)):
            for b in range(a + 1, len(sampled)):
                (ia, pa, da), (ib, pb, db) = sampled[a], sampled[b]
                ha, hb = ia["lane"] / 2 + 3, ib["lane"] / 2 + 3
                bbox = lambda pts, pad: (min(p[0] for p in pts) - pad, min(p[1] for p in pts) - pad,
                                         max(p[0] for p in pts) + pad, max(p[1] for p in pts) + pad)
                A, B = bbox(pa + da, DISC + GAP), bbox(pb + db, DISC + GAP)
                if A[2] < B[0] or B[2] < A[0] or A[3] < B[1] or B[3] < A[1]:
                    continue
                lane_gap = min(math.dist(p, q) for p in pa[::2] for q in pb[::2]) - ha - hb
                disc_gap = min([math.dist(c, q) - DISC - hb for c in da for q in pb]
                               + [math.dist(c, p) - DISC - ha for c in db for p in pa]
                               + [math.dist(c, e) - 2 * DISC for c in da for e in db])
                if min(lane_gap, disc_gap) < GAP:
                    issues.append(error(sheet, f"lanes {a + 1} and {b + 1} are too close together"))
        return issues
