"""Percents (Pandas math, 6.RP.3c): a percent as a rate per 100, the percent of a number, and
finding the whole from a part and the percent.

Rules (merged level → section → part):
- `layout`: `grids` (hundred grids with some squares shaded; the child writes how many out of
  100 and the percent) or `facts` (rows of percent facts).
- `problems`: grids or facts a page (default 6 grids, 12 facts).
- `shaded` (grids): [lo, hi] squares shaded out of 100.
- `tasks` (facts): what the facts ask, cycling down the page: `of` (25% of 80 = ☐),
  `whole` (25% of ☐ = 20), `percent` (☐% of 80 = 20).
- `percents` (facts): the percents used. `whole`: [lo, hi] for the whole; `max_part`: largest part.
- `title`: the sheet title.
Every fact has a whole-number part and whole; verify recomputes p × whole ÷ 100 = part exactly.
Grids shade whole columns of ten first, then part of the next column, top to bottom.
"""

from __future__ import annotations

from fractions import Fraction

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

GRIDS, FACTS = 6, 12
MAX_TRIES = 5000


def fact_answer(f: dict) -> str:
    return {"of": str(f["part"]), "whole": str(f["whole"]), "percent": f"{f['p']}%"}[f["task"]]


def answers_for(item: dict) -> str:
    if item["kind"] == "grid":
        return f"{item['shaded']}/100 = {item['shaded']}%"
    return fact_answer(item)


@register("percent_problem")
class PercentProblem(SheetType):
    template = "percent_problem.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        items = []
        if r["layout"] == "grids":
            lo, hi = r["shaded"]
            for n, k in enumerate(ctx.rng.sample(range(lo, hi + 1), r.get("problems", GRIDS)), 1):
                items.append({"kind": "grid", "n": n, "shaded": k})
        else:
            seen = set()
            for n in range(1, r.get("problems", FACTS) + 1):
                task = r["tasks"][(n - 1) % len(r["tasks"])]
                for _ in range(MAX_TRIES):
                    p = ctx.rng.choice(r["percents"])
                    w = ctx.rng.randint(*r["whole"])
                    part = Fraction(p * w, 100)
                    if part.denominator == 1 and 0 < part <= r["max_part"] and (p, w) not in seen:
                        break
                else:
                    raise ValueError(f"percent_problem: no fact fits {r}")
                seen.add((p, w))
                items.append({"kind": "fact", "n": n, "task": task, "p": p, "whole": w, "part": int(part)})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[answers_for(i) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        items = sheet.items
        issues: list[Issue] = []
        grids = r["layout"] == "grids"
        count = r.get("problems", GRIDS if grids else FACTS)
        if len(items) != count:
            issues.append(error(sheet, f"{len(items)} problems; this part has {count}"))
        if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
            issues.append(error(sheet, "problems are not numbered 1, 2, 3… in order"))
        for idx, i in enumerate(items):
            label = f"problem {i.get('n')}"
            if grids:
                lo, hi = r["shaded"]
                if i.get("kind") != "grid" or not lo <= i.get("shaded", -1) <= hi:
                    issues.append(error(sheet, f"{label}: a grid needs {lo}–{hi} shaded squares"))
                continue
            task = r["tasks"][idx % len(r["tasks"])]
            if i.get("kind") != "fact" or i.get("task") != task:
                issues.append(error(sheet, f"{label}: should be a {task!r} fact"))
            p, w, part = i.get("p"), i.get("whole"), i.get("part")
            if p not in r["percents"] or not r["whole"][0] <= w <= r["whole"][1]:
                issues.append(error(sheet, f"{label}: {p}% of {w} is outside this part's numbers"))
            if Fraction(p * w, 100) != part:
                issues.append(error(sheet, f"{label}: {p}% of {w} is {Fraction(p * w, 100)}, not {part}"))
            if not isinstance(part, int) or not 0 < part <= r["max_part"]:
                issues.append(error(sheet, f"{label}: the part {part} must be a whole number 1–{r['max_part']}"))
        if not grids and len({(i.get("p"), i.get("whole")) for i in items}) != len(items):
            issues.append(error(sheet, "the same fact is on the page twice"))
        if grids and len({i.get("shaded") for i in items}) != len(items):
            issues.append(error(sheet, "two grids have the same number shaded"))
        if sheet.answer_key != [answers_for(i) for i in items]:
            issues.append(error(sheet, "answer key doesn't match the problems"))
        return issues
