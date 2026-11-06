"""The coordinate plane in four quadrants (Pandas math, 6.NS.6b–c, 6.NS.8).

One grid from −R to R on both axes (drawn SVG, a line at every whole number). Items:
- `read`: a lettered point drawn on the grid; the child writes its coordinates.
- `plot`: a letter and coordinates; the child draws the point.
- `distance`: two points with the same x or the same y; the child finds how far apart they are.
Rules (merged level → section → part):
- `range`: R, the largest coordinate (default 6). `read`, `plot`, `distance`: how many of each.
- `axis_points`: how many `plot` points sit on an axis (one coordinate 0); the rest are inside a
  quadrant. Read points are always inside a quadrant, one in each quadrant first.
- `title`: the sheet title.
Every point stores its grid position in pixels (`px`, `py`) as well as its coordinates; the
template draws read points at that position and verify checks it against the coordinates, so
a point can't be drawn in the wrong place.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error
from ._rational import show

CELL = 38
TOP = 16          # room above the grid for the top label
MARGIN = 26        # room for the y-axis labels left of the grid
LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"   # no I or O: they look like 1 and 0


def origin(rng_r: int) -> tuple[int, int]:
    return MARGIN + rng_r * CELL, TOP + rng_r * CELL


def pixel(x: int, y: int, R: int) -> tuple[int, int]:
    ox, oy = origin(R)
    return ox + x * CELL, oy - y * CELL


def quadrant(x: int, y: int) -> int:
    if x == 0 or y == 0:
        return 0
    return {(True, True): 1, (False, True): 2, (False, False): 3, (True, False): 4}[(x > 0, y > 0)]


def coords(x: int, y: int) -> str:
    return f"({show(str(x))}, {show(str(y))})"


def answer_for(i: dict) -> str:
    if i["kind"] == "read":
        return f"{i['label']} {coords(i['x'], i['y'])}"
    if i["kind"] == "plot":
        return f"{i['label']} plotted at {coords(i['x'], i['y'])}"
    (x1, y1), (x2, y2) = i["p1"], i["p2"]
    return f"{abs(x1 - x2) + abs(y1 - y2)} units"


@register("coordinate_grid")
class CoordinateGrid(SheetType):
    template = "coordinate_grid.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        rng = ctx.rng
        R = r.get("range", 6)
        n_read, n_plot, n_dist = r["read"], r["plot"], r.get("distance", 0)
        used: set[tuple[int, int]] = set()

        def point(q: int) -> tuple[int, int]:
            while True:
                if q == 0:
                    v = rng.choice([k for k in range(-R, R + 1) if k])
                    x, y = (v, 0) if rng.random() < 0.5 else (0, v)
                else:
                    sx, sy = {1: (1, 1), 2: (-1, 1), 3: (-1, -1), 4: (1, -1)}[q]
                    x, y = sx * rng.randint(1, R), sy * rng.randint(1, R)
                near = any(abs(x - a) + abs(y - b) < 2 for a, b in used)
                if (x, y) not in used and not near:
                    used.add((x, y))
                    return x, y

        letters = iter(LETTERS)
        items = []
        quads = [1, 2, 3, 4]
        rng.shuffle(quads)
        for k in range(n_read):
            x, y = point(quads[k % 4] if k < 4 else rng.randint(1, 4))
            px, py = pixel(x, y, R)
            items.append({"kind": "read", "label": next(letters), "x": x, "y": y, "px": px, "py": py})
        rng.shuffle(quads)
        axis = r.get("axis_points", 0)
        plot_q = [0] * axis + [quads[k % 4] for k in range(n_plot - axis)]
        rng.shuffle(plot_q)
        for q in plot_q:
            x, y = point(q)
            px, py = pixel(x, y, R)
            items.append({"kind": "plot", "label": next(letters), "x": x, "y": y, "px": px, "py": py})
        pairs: set = set()
        while len([i for i in items if i["kind"] == "distance"]) < n_dist:
            same_x = len(pairs) % 2 == 0
            c = rng.choice([k for k in range(-R, R + 1) if k])
            a, b = rng.sample([k for k in range(-R, R + 1) if k], 2)
            if (a > 0) == (b > 0):
                continue   # across an axis: the distance needs both absolute values (6.NS.8)
            p1, p2 = ([c, a], [c, b]) if same_x else ([a, c], [b, c])
            if (tuple(p1), tuple(p2)) in pairs:
                continue
            pairs.add((tuple(p1), tuple(p2)))
            items.append({"kind": "distance", "p1": p1, "p2": p2})
        for n, i in enumerate(items, 1):
            i["n"] = n
            i["answer"] = answer_for(i)
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[i["answer"] for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        R = r.get("range", 6)
        items = sheet.items
        issues: list[Issue] = []
        if R != 6:
            issues.append(error(sheet, f"the template draws the grid from −6 to 6, not ±{R}"))
        kinds = [i.get("kind") for i in items]
        want = ["read"] * r["read"] + ["plot"] * r["plot"] + ["distance"] * r.get("distance", 0)
        if kinds != want:
            issues.append(error(sheet, f"items {kinds} should be {want}"))
        if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
            issues.append(error(sheet, "items are not numbered 1, 2, 3… in order"))
        points = [i for i in items if i.get("kind") in ("read", "plot")]
        labels = [i.get("label") for i in points]
        if labels != list(LETTERS[:len(points)]):
            issues.append(error(sheet, f"points are lettered {labels}, not A, B, C… in order"))
        spots = [(i["x"], i["y"]) for i in points]
        if len(set(spots)) != len(spots):
            issues.append(error(sheet, "two points are in the same place"))
        for i in points:
            label = f"point {i.get('label')} {coords(i['x'], i['y'])}"
            if not (-R <= i["x"] <= R and -R <= i["y"] <= R):
                issues.append(error(sheet, f"{label} is off the grid (−{R} to {R})"))
            if [i.get("px"), i.get("py")] != list(pixel(i["x"], i["y"], R)):
                issues.append(error(sheet, f"{label} is drawn at ({i.get('px')}, {i.get('py')}) px, "
                                           f"not at its coordinates {pixel(i['x'], i['y'], R)}"))
            if i["kind"] == "read" and quadrant(i["x"], i["y"]) == 0:
                issues.append(error(sheet, f"{label}: points to read sit inside a quadrant, not on an axis"))
            for j in points:
                if j is not i and abs(i["x"] - j["x"]) + abs(i["y"] - j["y"]) < 2:
                    issues.append(error(sheet, f"{label} is too close to point {j.get('label')}"))
        reads = [quadrant(i["x"], i["y"]) for i in points if i["kind"] == "read"]
        if set(reads[:4]) != set(range(1, min(len(reads), 4) + 1)) and len(reads) >= 4:
            issues.append(error(sheet, f"the first four points to read should cover all four quadrants, not {reads}"))
        plots = [quadrant(i["x"], i["y"]) for i in points if i["kind"] == "plot"]
        if plots.count(0) != r.get("axis_points", 0):
            issues.append(error(sheet, f"{plots.count(0)} plot points on an axis; this part has {r.get('axis_points', 0)}"))
        if len(plots) - plots.count(0) >= 4 and not {1, 2, 3, 4} <= set(plots):
            issues.append(error(sheet, "points to plot should reach all four quadrants"))
        for i in items:
            if i.get("kind") != "distance":
                continue
            (x1, y1), (x2, y2) = i["p1"], i["p2"]
            if not ((x1 == x2) != (y1 == y2)) or not all(-R <= v <= R for v in (x1, y1, x2, y2)):
                issues.append(error(sheet, f"distance {i.get('n')}: the two points must share exactly one coordinate"))
        for i in items:
            if i.get("answer") != answer_for(i):
                issues.append(error(sheet, f"item {i.get('n')}: answer {i.get('answer')} should be {answer_for(i)}"))
        if sheet.answer_key != [i.get("answer") for i in items]:
            issues.append(error(sheet, "answer key doesn't match the items"))
        return issues
