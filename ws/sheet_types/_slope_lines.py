"""Slope and lines y = mx + b (Lions math, 8.EE.5–6, 8.F.1–4).

Every item is one line y = mx + b with m from the rules' `slopes` ("p/q" strings) and b whole in
`intercepts` (or any rational for `points`/`table`, where only the slope is asked). Tasks:
- `points`: two whole-number points; find the slope.        - `table`: an x/y table; find the slope.
- `read_slope`: a drawn line with two dots; find the slope.  - `read_mb`: y = mx + b; write m and b.
- `write_graph`: a drawn line; write its equation.           - `draw_line`: an equation; draw the line.
- `from_points`, `from_table`: write the equation from two points or a table.
- `compare` (8.F.2): line A as an equation, line B as a table; which has the greater rate of change?
- `is_function` (8.F.1): an x/y table; is y a function of x (no x with two different y-values)?
  They come in yes/no pairs on a page, in either order.
Rules: `mixes` (a list of task lists; pages cycle through them from the part's first page; a page
with graph tasks has 4 items, a points/read_mb page 8, other pages 6), `grid` (R: the grid runs
−R…R), `slopes`, `intercepts` [lo, hi], `points` [lo, hi] (coordinates in points and tables).
Drawn lines store their exact end points on the grid's edge (as floats for drawing) and the dots;
verify recomputes the ends (Fraction), checks every dot and table row is on the line, and that a
line to draw passes through at least 3 whole-number grid points.
"""

from __future__ import annotations

from fractions import Fraction

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent
from ._algebra import MINUS, clip, floats, fstr, lattice, line_tokens, show
from ._common import error, page_rules, part_offset

GRAPH = {"read_slope", "write_graph", "draw_line"}
EIGHT = {"points", "read_mb"}
EQUATION = {"write_graph", "from_points", "from_table"}


def per_page(mix: list[str]) -> int:
    if GRAPH & set(mix):
        return 4
    return 8 if set(mix) <= EIGHT else 6


def tasks_for(rules: dict, page_index: int) -> list[str]:
    mixes = rules["mixes"]
    mix = mixes[page_index % len(mixes)]
    return [mix[k % len(mix)] for k in range(per_page(mix))]


def eq_text(m, b) -> str:
    """y = (1/2)x − 3 for answer keys (a fraction slope in brackets so it reads clearly)."""
    m, b = Fraction(m), Fraction(b)
    if m == 0:
        return f"y = {show(b)}"
    mag = abs(m)
    coef = "" if mag == 1 else (str(mag) if mag.denominator == 1 else f"({mag})")
    out = f"y = {MINUS if m < 0 else ''}{coef}x"
    if b:
        out += f" {MINUS if b < 0 else '+'} {abs(b)}"
    return out


def answer(i: dict) -> str:
    t = i["task"]
    if t in ("points", "table", "read_slope"):
        return f"slope {show(i['m'])}"
    if t == "read_mb":
        return f"slope {show(i['m'])}, y-intercept {show(i['b'])}"
    if t == "is_function":
        return "yes" if function_ok(i["xs"], i["ys"]) else "no"
    if t == "compare":
        return "A" if Fraction(i["m"]) > Fraction(i["mB"]) else "B"
    if t == "draw_line":
        (x1, y1), (x2, y2) = i["through"]
        return f"line through ({show(x1)}, {show(y1)}) and ({show(x2)}, {show(y2)})"
    return eq_text(i["m"], i["b"])


def function_ok(xs: list[int], ys: list[int]) -> bool:
    """True when no x-value has two different y-values."""
    seen: dict[int, int] = {}
    return all(seen.setdefault(x, y) == y for x, y in zip(xs, ys))


def _line_ok(m: Fraction, b: Fraction, R: int) -> bool:
    return len(lattice(m, b, R)) >= 3


def _item(ctx: GenContext, task: str, want: bool | None = None) -> dict | None:
    r, rng = ctx.rules, ctx.rng
    R = r["grid"]
    m = Fraction(rng.choice(r["slopes"]))
    plo, phi = r["points"]
    item: dict = {"task": task, "m": fstr(m)}
    if task in ("points", "from_points"):
        x1, y1 = rng.randint(plo, phi), rng.randint(plo, phi)
        run = m.denominator * rng.choice([1, 1, 2]) * rng.choice([1, -1])
        x2, y2 = x1 + run, y1 + m * run
        if not (plo <= x2 <= phi and plo <= y2 <= phi):
            return None
        b = y1 - m * x1
        if task == "from_points" and (b.denominator > 1 or not r["intercepts"][0] <= b <= r["intercepts"][1]):
            return None
        item.update(b=fstr(b), p1=[x1, y1], p2=[x2, int(y2)])
        return item
    if task == "is_function":
        xs = rng.sample(range(-5, 6), 5)
        ys = [rng.randint(-9, 9) for _ in xs]
        if not want:   # one x-value comes back with a different y-value
            j, k = rng.sample(range(5), 2)
            xs[k] = xs[j]
            if ys[k] == ys[j]:
                ys[k] += rng.choice([-3, 3])
        return {"task": task, "xs": xs, "ys": ys, "function": bool(want)}
    if task == "compare":
        b = Fraction(rng.randint(*r["intercepts"]))
        m2 = Fraction(rng.choice(r["slopes"]))
        x0, step = rng.randint(-3, 1), m2.denominator
        b2 = Fraction(rng.randint(*r["intercepts"]))
        xs = [x0 + k * step for k in range(4)]
        ys = [m2 * x + b2 for x in xs]
        if m2 == m or any(v.denominator > 1 or abs(v) > 2 * phi for v in ys) or (m == 0 and b == 0):
            return None
        item.update(b=fstr(b), tokens=line_tokens(m, b), mB=fstr(m2), bB=fstr(b2), xs=xs, ys=[int(v) for v in ys])
        return item
    if task in ("table", "from_table"):
        step = m.denominator * rng.choice([1, 1, 2]) if m.denominator > 1 else rng.choice([1, 1, 2, 3])
        x0 = rng.randint(plo, phi)
        xs = [x0 + k * step for k in range(4)]
        b = Fraction(rng.randint(*r["intercepts"])) if task == "from_table" else \
            Fraction(rng.randint(plo, phi)) - m * x0
        ys = [m * x + b for x in xs]
        if any(not plo * 2 <= v <= phi * 2 or v.denominator > 1 for v in xs + ys):
            return None
        item.update(b=fstr(b), xs=xs, ys=[int(v) for v in ys])
        return item
    b = Fraction(rng.randint(*r["intercepts"]))
    if not _line_ok(m, b, R) or (m == 0 and b == 0):
        return None
    item["b"] = fstr(b)
    if task == "read_mb":
        item["tokens"] = line_tokens(m, b)
        return item
    pts = lattice(m, b, R)
    if task == "read_slope":
        a, c = sorted(rng.sample(range(len(pts)), 2))
        dots = [pts[a], pts[c]]
    elif task == "write_graph":
        other = [p for p in pts if p[0] != 0]
        dots = [[0, int(b)], rng.choice(other)]
    else:   # draw_line: the answer names the y-intercept and the next whole-number point
        dots = []
        item["tokens"] = line_tokens(m, b)
        nxt = [p for p in pts if p[0] > 0] or [p for p in pts if p[0] < 0]
        item["through"] = [[0, int(b)], nxt[0]]
    item.update(grid=R, dots=sorted(dots), ends=floats(clip(m, b, R)))
    return item


def _key(i: dict) -> tuple:
    return tuple(sorted((k, str(v)) for k, v in i.items() if k != "n"))


class Lines:
    """A mode of `coordinate_grid` (rules `mode`); coordinate_grid.py dispatches here."""

    name = "coordinate_grid"
    template = "coordinate_grid_lines.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, spec = ctx.rules, ctx.spec
        tasks = tasks_for(r, part_offset(spec.subject, spec.level, spec.page))
        items: list[dict] = []
        first_yes = ctx.rng.random() < 0.5 if "is_function" in tasks else True
        for k, task in enumerate(tasks):
            want = (tasks[:k].count("is_function") % 2 == 0) == first_yes
            for _ in range(5000):
                item = _item(ctx, task, want)
                if item and _key(item) not in {_key(i) for i in items} and \
                        all("m" not in item or (item["m"], item["b"]) != (i.get("m"), i.get("b")) for i in items):
                    break
            else:
                raise ValueError(f"slope_graph: no {task} item fits the rules")
            items.append({"n": k + 1, **item})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[answer(i) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        issues: list[Issue] = []
        R = r["grid"]
        plo, phi = r["points"]
        want = tasks_for(r, part_offset(sheet.subject, sheet.level, sheet.page_number))
        if [i["task"] for i in sheet.items] != want:
            issues.append(error(sheet, f"tasks {[i['task'] for i in sheet.items]} should be {want}"))
        funcs = []
        for i in sheet.items:
            t, label = i["task"], f"item {i.get('n')} ({i['task']})"
            if t == "is_function":
                ok = function_ok(i["xs"], i["ys"])
                funcs.append(ok)
                if ok != i["function"] or len(i["xs"]) != 5 or not all(-5 <= v <= 5 for v in i["xs"]):
                    issues.append(error(sheet, f"{label}: the table doesn't match its yes/no"))
                if not ok and len(set(i["xs"])) != 4:
                    issues.append(error(sheet, f"{label}: exactly one x-value should repeat"))
                continue
            m, b = Fraction(i["m"]), Fraction(i["b"])
            if t == "compare":
                m2, b2 = Fraction(i["mB"]), Fraction(i["bB"])
                if m2 == m or i["mB"] not in r["slopes"]:
                    issues.append(error(sheet, f"{label}: the two rates must differ"))
                if any(y != m2 * x + b2 for x, y in zip(i["xs"], i["ys"])):
                    issues.append(error(sheet, f"{label}: table B isn't one line"))
            if i["m"] not in r["slopes"]:
                issues.append(error(sheet, f"{label}: slope {i['m']} isn't one of this part's slopes"))
            if t not in ("points", "table") and (b.denominator > 1 or not r["intercepts"][0] <= b <= r["intercepts"][1]):
                issues.append(error(sheet, f"{label}: y-intercept {i['b']} should be whole, in {r['intercepts']}"))
            if t in GRAPH | {"read_mb"} and m == 0 and b == 0:
                issues.append(error(sheet, f"{label}: y = 0 is the x-axis itself"))
            if t in ("points", "from_points"):
                (x1, y1), (x2, y2) = i["p1"], i["p2"]
                if x1 == x2 or Fraction(y2 - y1, x2 - x1) != m or y1 != m * x1 + b:
                    issues.append(error(sheet, f"{label}: the points don't have slope {i['m']}"))
                if not all(plo <= v <= phi for v in (x1, y1, x2, y2)):
                    issues.append(error(sheet, f"{label}: a point is outside {plo}…{phi}"))
            if t in ("table", "from_table"):
                xs, ys = i["xs"], i["ys"]
                steps = {xs[k + 1] - xs[k] for k in range(len(xs) - 1)}
                if len(xs) != 4 or len(steps) != 1 or steps.pop() <= 0:
                    issues.append(error(sheet, f"{label}: table x-values should go up in equal steps"))
                if any(y != m * x + b for x, y in zip(xs, ys)):
                    issues.append(error(sheet, f"{label}: a table row isn't on y = {i['m']}x + {i['b']}"))
            if t in GRAPH:
                if i.get("grid") != R or i["ends"] != floats(clip(m, b, R)):
                    issues.append(error(sheet, f"{label}: the drawn line doesn't match y = {i['m']}x + {i['b']}"))
                pts = lattice(m, b, R)
                if len(pts) < 3:
                    issues.append(error(sheet, f"{label}: the line passes fewer than 3 grid points"))
                for d in i["dots"] + i.get("through", []):
                    if d not in pts:
                        issues.append(error(sheet, f"{label}: point {d} isn't on the line inside the grid"))
                if t == "read_slope" and len(i["dots"]) != 2:
                    issues.append(error(sheet, f"{label}: needs two dots to count rise and run"))
                if t == "write_graph" and [0, int(b)] not in i["dots"]:
                    issues.append(error(sheet, f"{label}: the y-intercept should be marked"))
            if t in ("read_mb", "draw_line", "compare") and i["tokens"] != line_tokens(m, b):
                issues.append(error(sheet, f"{label}: the printed equation isn't y = {i['m']}x + {i['b']}"))
        if any(funcs[k] == funcs[k + 1] for k in range(0, len(funcs) - 1, 2)):
            issues.append(error(sheet, f"function tables should come in yes/no pairs (got {funcs})"))
        lines = [(i["m"], i["b"]) for i in sheet.items if "m" in i]
        if len(set(lines)) != len(lines):
            issues.append(error(sheet, "the same line is on the page twice"))
        expected = [answer(i) for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the items {expected}"))
        return issues
