"""Two equations at once (Lions math, 8.EE.8a–c): simple 2×2 linear systems.

Each equation is stored as two lists of terms in x and y (`lhs`, `rhs`; a term is
`{"c": "3", "v": "x" | "y" | ""}`) plus its printed tokens. Tasks (rules `tasks`, cycled):
- `graph_read`: both lines drawn on a grid (y = mx + b); the child reads where they cross.
- `graph_draw`: both equations, an empty grid; the child draws the lines and reads the point.
- `substitution`: y = mx + b (or x = ky + c) with Ax + By = C.
- `elimination`: Ax + By = C twice; one letter cancels by adding or taking away, sometimes after
  multiplying one equation by 2 or 3.
- `inspect`: no solution (parallel lines) or infinitely many (the same line, scaled).
- `story`: a story from content/math/systems.yaml (8.EE.8c); the child writes two equations.
Rules: `problems`, `tasks`, `grid` (R), `solutions` [lo, hi] for x and y (not stories),
`max_number` (largest printed number, not stories). Every solution is whole. Verify re-prints every
equation, checks the solution in both, that it is the only one (or the stated none/all), that
drawn lines match their equations and pass through ≥ 3 grid points, and recomputes the stories.
"""

from __future__ import annotations

from fractions import Fraction

from ..content import system_stories
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._algebra import clip, floats, fstr, lattice, merge, show, side_tokens
from ._common import error

GRAPH = {"graph_read", "graph_draw"}
GRAPH_SLOPES = ["-3", "-2", "-1", "-1/2", "-1/3", "1/3", "1/2", "1", "2", "3", "0"]


def T(c, v: str = "") -> dict:
    return {"c": fstr(c), "v": v}


def eq(lhs: list[dict], rhs: list[dict]) -> dict:
    return {"lhs": lhs, "rhs": rhs, "tokens": merge(side_tokens(lhs) + [" = "] + side_tokens(rhs))}


def si(m, b) -> dict:
    """y = mx + b."""
    m, b = Fraction(m), Fraction(b)
    rhs = ([T(m, "x")] if m else []) + ([T(b)] if b or not m else [])
    return eq([T(1, "y")], rhs)


def std(A: int, B: int, C: int) -> dict:
    """Ax + By = C."""
    return eq([t for t in (T(A, "x") if A else None, T(B, "y") if B else None) if t], [T(C)])


def coeffs(e: dict) -> tuple[Fraction, Fraction, Fraction]:
    """(a, b, c) with the equation the same as a·x + b·y = c."""
    a = b = c = Fraction(0)
    for sign, side in ((1, e["lhs"]), (-1, e["rhs"])):
        for t in side:
            v = sign * Fraction(t["c"])
            if t["v"] == "x":
                a += v
            elif t["v"] == "y":
                b += v
            else:
                c -= v
    return a, b, c


def solve(e1: dict, e2: dict) -> tuple[Fraction, Fraction] | str:
    a1, b1, c1 = coeffs(e1)
    a2, b2, c2 = coeffs(e2)
    det = a1 * b2 - a2 * b1
    if det == 0:
        same = a1 * c2 == a2 * c1 and b1 * c2 == b2 * c1
        return "all" if same else "none"
    return (c1 * b2 - c2 * b1) / det, (a1 * c2 - a2 * c1) / det


def slope_intercept(e: dict) -> tuple[Fraction, Fraction]:
    a, b, c = coeffs(e)
    return -a / b, c / b


def numbers(e: dict) -> list[Fraction]:
    return [Fraction(t["c"]) for t in e["lhs"] + e["rhs"]]


def story_text(frame: dict, v: dict) -> str:
    return frame["text"].format(**v)


def story_values(frame: dict, x: int, y: int, p: int | None, q: int | None) -> dict:
    if frame["kind"] == "sum_value":
        return {"T": x + y, "V": p * x + q * y, "p": p, "q": q}
    return {"T": x + y, "D": x - y}


def answer(i: dict) -> str:
    if i["task"] == "story":
        n = i["names"]
        return f"{n[0]} {i['x']}, {n[1]} {i['y']}"
    s = solve(i["eq1"], i["eq2"])
    if s == "none":
        return "no solution (parallel lines)"
    if s == "all":
        return "infinitely many solutions (the same line)"
    return f"({show(s[0])}, {show(s[1])})"


def _nz(rng, lo, hi) -> int:
    while True:
        v = rng.randint(lo, hi)
        if v:
            return v


def _item(ctx: GenContext, task: str) -> dict | None:
    r, rng = ctx.rules, ctx.rng
    R, (lo, hi) = r["grid"], r["solutions"]
    x, y = rng.randint(lo, hi), rng.randint(lo, hi)
    if task in GRAPH:
        m1, m2 = (Fraction(s) for s in rng.sample(GRAPH_SLOPES, 2))
        lines = []
        for m in (m1, m2):
            b = y - m * x
            if b.denominator > 1 or abs(b) > R - 1 or len(lattice(m, b, R)) < 3:
                return None
            lines.append((m, b))
        e1, e2 = si(*lines[0]), si(*lines[1])
        return {"task": task, "x": x, "y": y, "eq1": e1, "eq2": e2, "grid": R,
                "ends": [floats(clip(m, b, R)) for m, b in lines]}
    if task == "substitution":
        A, B = _nz(rng, -5, 5), _nz(rng, -5, 5)
        if rng.random() < 0.7:
            m, b = _nz(rng, -4, 4), rng.randint(-9, 9)
            if A + B * m == 0 or y != m * x + b:
                b = y - m * x
            e1 = si(m, b)
        else:
            k, c = _nz(rng, -4, 4), 0
            c = x - k * y
            e1 = eq([T(1, "x")], [T(k, "y")] + ([T(c)] if c else []))
        e2 = std(A, B, A * x + B * y)
        if rng.random() < 0.5:
            e1, e2 = e2, e1
        return {"task": task, "x": x, "y": y, "eq1": e1, "eq2": e2}
    if task == "elimination":
        A1, B1 = _nz(rng, -6, 6), _nz(rng, -6, 6)
        k = rng.choice([1, -1, -1, 2, -2, 3])
        if rng.random() < 0.5:   # y cancels after multiplying the first equation by k
            A2, B2 = _nz(rng, -6, 6), -k * B1
        else:
            A2, B2 = -k * A1, _nz(rng, -6, 6)
        e1, e2 = std(A1, B1, A1 * x + B1 * y), std(A2, B2, A2 * x + B2 * y)
        if A1 * B2 - A2 * B1 == 0:
            return None
        return {"task": task, "x": x, "y": y, "eq1": e1, "eq2": e2}
    if task == "inspect":
        if rng.random() < 0.5:   # parallel lines in slope-intercept form, or same slope in standard form
            m = Fraction(_nz(rng, -4, 4))
            b1, b2 = rng.sample(range(-9, 10), 2)
            e1, e2 = si(m, b1), si(m, b2)
            if rng.random() < 0.5:
                A, B = _nz(rng, -5, 5), _nz(rng, -5, 5)
                C1, C2 = rng.sample(range(-20, 21), 2)
                k = rng.choice([1, 2, 3])
                e1, e2 = std(A, B, C1), std(k * A, k * B, k * C2)
                if C1 == C2:
                    return None
        else:   # the same line twice
            A, B, k = _nz(rng, -5, 5), _nz(rng, -5, 5), rng.choice([2, 3, -2])
            C = A * x + B * y
            e1, e2 = std(A, B, C), std(k * A, k * B, k * C)
        return {"task": task, "eq1": e1, "eq2": e2}
    if task == "story":
        frame = rng.choice(system_stories())
        x, y = rng.randint(*frame["x"]), rng.randint(*frame["y"])
        p = rng.choice(frame["p"]) if frame["kind"] == "sum_value" else None
        q = rng.choice(frame["q"]) if frame["kind"] == "sum_value" else None
        if frame["kind"] == "sum_diff" and x <= y:
            return None
        v = story_values(frame, x, y, p, q)
        return {"task": task, "frame": frame["id"], "x": x, "y": y, "values": v,
                "names": frame["names"], "text": story_text(frame, v)}
    raise ValueError(f"linear_system: unknown task {task!r}")


def _ok(item: dict, r: dict) -> bool:
    if item["task"] == "story":
        return True
    nums = numbers(item["eq1"]) + numbers(item["eq2"])
    return all(abs(v) <= r["max_number"] for v in nums)


def _key(i: dict) -> str:
    return str(sorted((k, str(v)) for k, v in i.items() if k != "n"))


@register("linear_system")
class LinearSystem(SheetType):
    template = "linear_system.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        tasks = [r["tasks"][k % len(r["tasks"])] for k in range(r["problems"])]
        items: list[dict] = []
        for k, task in enumerate(tasks):
            for _ in range(5000):
                item = _item(ctx, task)
                if item and _ok(item, r) and _key(item) not in {_key(i) for i in items} and \
                        (task == "story" or all((item.get("x"), item.get("y")) != (i.get("x"), i.get("y"))
                                                or task == "inspect" for i in items)):
                    break
            else:
                raise ValueError(f"linear_system: no {task} problem fits the rules")
            items.append({"n": k + 1, **item})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[answer(i) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues: list[Issue] = []
        R, (lo, hi) = r["grid"], r["solutions"]
        want = [r["tasks"][k % len(r["tasks"])] for k in range(r["problems"])]
        if [i["task"] for i in sheet.items] != want:
            issues.append(error(sheet, f"tasks {[i['task'] for i in sheet.items]} should be {want}"))
        frames = {f["id"]: f for f in system_stories()}
        for i in sheet.items:
            t, label = i["task"], f"problem {i.get('n')} ({i['task']})"
            if t == "story":
                f = frames.get(i["frame"])
                if f is None:
                    issues.append(error(sheet, f"{label}: unknown story {i['frame']!r}"))
                    continue
                v = story_values(f, i["x"], i["y"], i["values"].get("p"), i["values"].get("q"))
                if i["values"] != v or i["text"] != story_text(f, v) or i["names"] != f["names"]:
                    issues.append(error(sheet, f"{label}: the story's numbers don't match its answer"))
                if not (f["x"][0] <= i["x"] <= f["x"][1] and f["y"][0] <= i["y"] <= f["y"][1]):
                    issues.append(error(sheet, f"{label}: answer outside the story's ranges"))
                if f["kind"] == "sum_value" and (v["p"] not in f["p"] or v["q"] not in f["q"]):
                    issues.append(error(sheet, f"{label}: prices/sizes not from the story frame"))
                if f["kind"] == "sum_diff" and i["x"] <= i["y"]:
                    issues.append(error(sheet, f"{label}: the first answer should be the bigger one"))
                continue
            for e in (i["eq1"], i["eq2"]):
                if e["tokens"] != merge(side_tokens(e["lhs"]) + [" = "] + side_tokens(e["rhs"])):
                    issues.append(error(sheet, f"{label}: a printed equation doesn't match its terms"))
            if not _ok(i, r):
                issues.append(error(sheet, f"{label}: a number is bigger than {r['max_number']}"))
            s = solve(i["eq1"], i["eq2"])
            if t == "inspect":
                if s not in ("none", "all"):
                    issues.append(error(sheet, f"{label}: should have no solution or every solution, has {s}"))
                continue
            if isinstance(s, str) or s != (i["x"], i["y"]):
                issues.append(error(sheet, f"{label}: the solution isn't ({i['x']}, {i['y']}) (got {s})"))
            if not (lo <= i["x"] <= hi and lo <= i["y"] <= hi):
                issues.append(error(sheet, f"{label}: ({i['x']}, {i['y']}) is outside {lo}…{hi}"))
            if t in GRAPH:
                if i.get("grid") != R:
                    issues.append(error(sheet, f"{label}: grid size {i.get('grid')} isn't {R}"))
                for e, ends in zip((i["eq1"], i["eq2"]), i["ends"]):
                    if [tt["v"] for tt in e["lhs"]] != ["y"] or e["lhs"][0]["c"] != "1":
                        issues.append(error(sheet, f"{label}: graph equations should be y = mx + b"))
                        continue
                    m, b = slope_intercept(e)
                    if ends != floats(clip(m, b, R)) or len(lattice(m, b, R)) < 3:
                        issues.append(error(sheet, f"{label}: a drawn line doesn't match its equation"))
                    if [i["x"], i["y"]] not in lattice(m, b, R):
                        issues.append(error(sheet, f"{label}: the crossing point isn't on the grid"))
        expected = [answer(i) for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the problems {expected}"))
        return issues
