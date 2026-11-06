"""Right triangles and the Pythagorean theorem (Lions math, 8.G.6–8).

Tasks (rules `mixes`: lists of tasks; pages cycle through them from the part's first page):
- `hypotenuse`: a drawn right triangle with legs `a` (across) and `b` (up); find c.
- `leg`: the hypotenuse c and the leg a are labeled; find b.
- `is_right`: three side lengths; is it a right triangle? (the converse; half are, half aren't).
- `distance`: two whole-number points on a grid (not in a line across or up); how far apart?
Rules: `triples` (true: every answer is whole, from Pythagorean triples and their multiples;
false: answers are square roots, written √n ≈ to one decimal), `max_side` (the longest side), `grid`
(R for distance grids). Triangles are drawn from `a` and `b` only (scaled, square corner marked),
so the picture always matches the numbers; verify recomputes a² + b² = c² with whole numbers and
rounds roots exactly (half up).
"""

from __future__ import annotations

from math import isqrt

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._algebra import is_square, root_one_decimal
from ._common import error

GRAPH = {"distance"}
MAX_RATIO = 3.5   # a drawn triangle's long leg is at most 3.5 times its short leg, so it stays readable


def triples(max_side: int) -> list[tuple[int, int, int]]:
    return [(a, b, isqrt(a * a + b * b)) for a in range(3, max_side) for b in range(a + 1, max_side)
            if is_square(a * a + b * b) and isqrt(a * a + b * b) <= max_side]


def root_text(n: int) -> str:
    return str(isqrt(n)) if is_square(n) else f"√{n} ≈ {root_one_decimal(n)}"


def answer(i: dict) -> str:
    t = i["task"]
    if t == "hypotenuse":
        return f"c = {root_text(i['a'] ** 2 + i['b'] ** 2)}"
    if t == "leg":
        return f"b = {root_text(i['c'] ** 2 - i['a'] ** 2)}"
    if t == "is_right":
        x, y, z = sorted(i["sides"])
        return "yes" if x * x + y * y == z * z else "no"
    (x1, y1), (x2, y2) = i["p1"], i["p2"]
    return f"{root_text((x2 - x1) ** 2 + (y2 - y1) ** 2)} units"


def per_page(mix: list[str]) -> int:
    return 4 if GRAPH & set(mix) else 6


def tasks_for(rules: dict, page_index: int) -> list[str]:
    mix = rules["mixes"][page_index % len(rules["mixes"])]
    return [mix[k % len(mix)] for k in range(per_page(mix))]


def _page_index(subject: str, level: str, page: int) -> int:
    from ..syllabus import load_level

    sec = load_level(subject, level).section_for_page(page)
    part = sec.part_for_page(page)
    return page - (part.pages if part else sec.pages)[0]


def _item(ctx: GenContext, task: str, right: bool = True) -> dict | None:
    r, rng = ctx.rules, ctx.rng
    top, whole = r["max_side"], r["triples"]
    flip = rng.random() < 0.5
    if task == "distance":
        R = r["grid"]
        p1 = [rng.randint(-R + 1, R - 1), rng.randint(-R + 1, R - 1)]
        p2 = [rng.randint(-R + 1, R - 1), rng.randint(-R + 1, R - 1)]
        dx, dy = abs(p2[0] - p1[0]), abs(p2[1] - p1[1])
        n = dx * dx + dy * dy
        if dx < 2 or dy < 2 or is_square(n) != whole:
            return None
        return {"task": task, "grid": R, "p1": sorted([p1, p2])[0], "p2": sorted([p1, p2])[1]}
    if whole:
        a, b, c = rng.choice(triples(top))
        if rng.random() < 0.5:
            a, b = b, a
    else:
        a, b = rng.randint(2, 12), rng.randint(2, 12)
        c = None
    if (task == "hypotenuse" or (whole and task == "leg")) and not _shape_ok(a, b, None):
        return None
    if task == "hypotenuse":
        if not whole and (is_square(a * a + b * b) or a * a + b * b > top * top):
            return None
        return {"task": task, "a": a, "b": b, "flip": flip}
    if task == "leg":
        if whole:
            return {"task": task, "a": a, "c": c, "b": b, "flip": flip}
        c = rng.randint(max(a, b) + 1, top)
        if is_square(c * c - a * a) or not _shape_ok(a, None, c):
            return None
        return {"task": task, "a": a, "c": c, "flip": flip}
    if task == "is_right":
        if right:
            return {"task": task, "sides": sorted([a, b, c])}
        x, y, z = sorted([a, b, c])
        z += rng.choice([-1, 1])
        if x * x + y * y == z * z or z <= y:
            return None
        return {"task": task, "sides": [x, y, z]}
    raise ValueError(f"pythagorean: unknown task {task!r}")


def _shape_ok(a: int, b: int | None, c: int | None) -> bool:
    b2 = b * b if b is not None else c * c - a * a
    lo, hi = sorted([a * a, b2])
    return hi <= MAX_RATIO ** 2 * lo


def _key(i: dict) -> str:
    return str(sorted((k, str(v)) for k, v in i.items() if k not in ("n", "flip")))


@register("pythagorean")
class Pythagorean(SheetType):
    template = "pythagorean.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, spec = ctx.rules, ctx.spec
        tasks = tasks_for(r, _page_index(spec.subject, spec.level, spec.page))
        items: list[dict] = []
        first_yes = ctx.rng.random() < 0.5   # the right-triangle tests come in yes/no pairs, either order
        for k, task in enumerate(tasks):
            for _ in range(5000):
                item = _item(ctx, task, (tasks[:k].count("is_right") % 2 == 0) == first_yes)
                if item and _key(item) not in {_key(i) for i in items}:
                    break
            else:
                raise ValueError(f"pythagorean: no {task} problem fits the rules")
            items.append({"n": k + 1, **item})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[answer(i) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues: list[Issue] = []
        want = tasks_for(r, _page_index(sheet.subject, sheet.level, sheet.page_number))
        if [i["task"] for i in sheet.items] != want:
            issues.append(error(sheet, f"tasks {[i['task'] for i in sheet.items]} should be {want}"))
        top, whole = r["max_side"], r["triples"]
        rights = []
        for i in sheet.items:
            t, label = i["task"], f"problem {i.get('n')} ({i['task']})"
            if t == "is_right":
                x, y, z = i["sides"]
                if not (0 < x <= y < z <= top + 1) or i["sides"] != sorted(i["sides"]):
                    issues.append(error(sheet, f"{label}: sides {i['sides']} should be in order, longest ≤ {top + 1}"))
                rights.append(x * x + y * y == z * z)
                continue
            if t == "distance":
                (x1, y1), (x2, y2) = i["p1"], i["p2"]
                R = r["grid"]
                if i.get("grid") != R or not all(-R < v < R for v in (x1, y1, x2, y2)):
                    issues.append(error(sheet, f"{label}: a point is off the grid"))
                if abs(x2 - x1) < 2 or abs(y2 - y1) < 2:
                    issues.append(error(sheet, f"{label}: the points should make a real triangle"))
                n = (x2 - x1) ** 2 + (y2 - y1) ** 2
            elif t == "hypotenuse":
                n = i["a"] ** 2 + i["b"] ** 2
                if not _shape_ok(i["a"], i["b"], None):
                    issues.append(error(sheet, f"{label}: the triangle is too thin to read"))
            else:
                n = i["c"] ** 2 - i["a"] ** 2
                if i["c"] <= i["a"] or ("b" in i and i["b"] ** 2 != n):
                    issues.append(error(sheet, f"{label}: the sides don't make a right triangle"))
                if i["c"] > i["a"] and not _shape_ok(i["a"], None, i["c"]):
                    issues.append(error(sheet, f"{label}: the triangle is too thin to read"))
                if i["c"] > top:
                    issues.append(error(sheet, f"{label}: hypotenuse {i['c']} is over {top}"))
            if whole and not is_square(n):
                issues.append(error(sheet, f"{label}: the answer √{n} isn't whole on a whole-number page"))
            if not whole and is_square(n):
                issues.append(error(sheet, f"{label}: the answer {isqrt(n)} is whole on a square-root page"))
            if t != "distance" and isqrt(n) > top:
                issues.append(error(sheet, f"{label}: a side is longer than {top}"))
        if any(rights[k] == rights[k + 1] for k in range(0, len(rights) - 1, 2)):
            issues.append(error(sheet, f"right-triangle tests should come in yes/no pairs (got {rights})"))
        keys = [_key(i) for i in sheet.items]
        if len(set(keys)) != len(keys):
            issues.append(error(sheet, "the same problem is on the page twice"))
        expected = [answer(i) for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the problems {expected}"))
        return issues

