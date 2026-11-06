"""Write the line (Whales math, F-LE.A.2, F-IF.B.6, A-CED.A.2): write y = mx + b from a table, from two
points, or from a situation.

Each item stores the slope `m` and intercept `b` (whole numbers) and what is shown: `xs` and `ys` for a
table, `p1`/`p2` for two points, or a situation frame (`story`: id, start, slope) from
content/math/algebra_stories.yaml with its filled-in `text`. The answer is canonical: 'y = 3x − 2',
'h = 2w + 4' (the frame's letters). Verify recomputes every table value and point from m and b,
fills the story in again, and checks the ranges.

Rules (merged level → section → part):
- `kinds`: cycled for `items` (default 5): table, points, situation. Situations run across the page.
- `slope`: [lo, hi] whole slopes (never 0); `intercept`: [lo, hi] for b.
"""

from __future__ import annotations

from ..algebra import Poly, pretty
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._algebra_stories import algebra_stories, frame
from ._common import error

ITEMS = 5


def rhs(m: int, b: int, x: str = "x") -> str:
    return Poly({((x, 1),): m, (): b}).text()


def story_text(story: dict) -> str:
    return frame("linear", story["id"])["text"].format(start=story["start"], slope=abs(story["slope"]))


def answer_for(i: dict) -> str:
    if i["kind"] == "situation":
        f = frame("linear", i["story"]["id"])
        return f"{f['y']} = {pretty(rhs(i['m'], i['b'], f['x']))}"
    return f"y = {pretty(rhs(i['m'], i['b']))}"


def choose(kind: str, rng, r: dict) -> dict:
    lo, hi = r.get("slope", [-5, 5])
    blo, bhi = r.get("intercept", [-9, 9])
    m = rng.choice([k for k in range(lo, hi + 1) if k])
    b = rng.randint(blo, bhi)
    if kind == "table":
        step = rng.choice([1, 1, 2])
        x0 = rng.randint(-2, 1) if step == 1 else rng.choice([0, -2])
        xs = [x0 + step * k for k in range(4)]
        return {"m": m, "b": b, "xs": xs, "ys": [m * x + b for x in xs]}
    if kind == "points":
        x1, x2 = sorted(rng.sample([-4, -3, -2, -1, 1, 2, 3, 4, 5], 2))
        return {"m": m, "b": b, "p1": [x1, m * x1 + b], "p2": [x2, m * x2 + b]}
    if kind == "situation":
        f = rng.choice(algebra_stories()["linear"])
        start, slope = rng.randint(*f["start"]), rng.randint(*f["slope"])
        story = {"id": f["id"], "start": start, "slope": slope}
        return {"m": slope, "b": start, "story": story, "text": story_text(story)}
    raise ValueError(f"unknown slope_intercept kind {kind!r}")


@register("slope_intercept")
class SlopeIntercept(SheetType):
    template = "slope_intercept.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        items, seen = [], set()
        for n in range(1, r.get("items", ITEMS) + 1):
            kind = r["kinds"][(n - 1) % len(r["kinds"])]
            for _ in range(200):
                d = choose(kind, ctx.rng, r)
                key = (d["m"], d["b"])
                if key not in seen:
                    break
            seen.add(key)
            item = {"n": n, "kind": kind, **d}
            item["answer"] = answer_for(item)
            items.append(item)
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[f"{i['n']}) {i['answer']}" for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues: list[Issue] = []
        if len(sheet.items) != r.get("items", ITEMS):
            issues.append(error(sheet, f"{len(sheet.items)} problems; this part has {r.get('items', ITEMS)}"))
        lo, hi = r.get("slope", [-5, 5])
        blo, bhi = r.get("intercept", [-9, 9])
        for k, i in enumerate(sheet.items):
            label = f"problem {i.get('n')} ({i.get('kind')})"
            m, b = i["m"], i["b"]
            if i.get("n") != k + 1 or i["kind"] != r["kinds"][k % len(r["kinds"])]:
                issues.append(error(sheet, f"{label}: numbering or kind doesn't follow the part"))
            if i["kind"] == "situation":
                f = frame("linear", i["story"]["id"])
                s = i["story"]
                if (s["slope"], s["start"]) != (m, b) or not f["slope"][0] <= m <= f["slope"][1] \
                        or not f["start"][0] <= b <= f["start"][1] or i.get("text") != story_text(s):
                    issues.append(error(sheet, f"{label}: the story doesn't match its numbers"))
                if "a" in (f["x"], f["y"]):
                    issues.append(error(sheet, f"{label}: the letter a is never a variable here"))
            else:
                if m == 0 or not lo <= m <= hi or not blo <= b <= bhi:
                    issues.append(error(sheet, f"{label}: slope {m} or intercept {b} is outside the part"))
            if i["kind"] == "table":
                xs = i["xs"]
                steps = {q - p for p, q in zip(xs, xs[1:])}
                if len(xs) != 4 or len(steps) != 1 or i["ys"] != [m * x + b for x in xs]:
                    issues.append(error(sheet, f"{label}: the table isn't evenly spaced on y = {m}x + {b}"))
            if i["kind"] == "points":
                (x1, y1), (x2, y2) = i["p1"], i["p2"]
                if x1 == x2 or y1 != m * x1 + b or y2 != m * x2 + b or 0 in (x1, x2):
                    issues.append(error(sheet, f"{label}: the points aren't on the line (or one gives b away)"))
            if i.get("answer") != answer_for(i):
                issues.append(error(sheet, f"{label}: answer {i.get('answer')} should be {answer_for(i)}"))
        keys = [(i["m"], i["b"]) for i in sheet.items]
        if len(set(keys)) != len(keys):
            issues.append(error(sheet, "the same line is on the page twice"))
        if sheet.answer_key != [f"{i['n']}) {i['answer']}" for i in sheet.items]:
            issues.append(error(sheet, "answer key doesn't match the problems"))
        return issues
