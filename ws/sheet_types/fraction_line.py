"""Fractions on a number line (Foxes math, 3.NF.1–2): the line from 0 to 1 cut into equal parts.

Each item is one number line from 0 to 1 split into `den` equal parts (ticks 0, 1, …, den), with
one task (rules, merged level → section → part):
- `name`: a dot sits on tick `num`; the child writes the fraction num/den in the box.
- `mark`: the fraction num/den is printed; the child draws a dot on its tick.
- `fill`: every tick is labeled (0, 1/den, 2/den, …, 1) except `blanks`, which the child writes.
`denominators`: the parts a line may have (grade 3 uses 2, 3, 4, 6 and 8 only).
`unit_only`: every fraction has numerator 1 (named, marked or filled), as in the first part.
`tasks`: the tasks a page mixes. `lines`: number lines per page (default 5).
When a page has as many lines as denominators, each denominator is on it exactly once.

Only whole numbers are stored (ticks, numerators); the template turns them into pixel positions,
so verify can check every mark exactly. One answer per line: "num/den", "dot on 3/4" for a mark,
"1/6 and 5/6" for the empty labels of a fill line.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

LINES = 5
GRADE3_DENOMINATORS = {2, 3, 4, 6, 8}
FILL_BLANKS = 2


def answers_for(item: dict) -> list[str]:
    den = item["den"]
    if item["task"] == "fill":
        return [" and ".join(f"{k}/{den}" for k in item["blanks"])]
    frac = f"{item['num']}/{den}"
    return [f"dot on {frac}"] if item["task"] == "mark" else [frac]


@register("fraction_line")
class FractionLine(SheetType):
    template = "fraction_line.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        lines = r.get("lines", LINES)
        dens = list(r["denominators"])
        ctx.rng.shuffle(dens)
        dens = [dens[i % len(dens)] for i in range(lines)]
        tasks = [r["tasks"][i % len(r["tasks"])] for i in range(lines)]
        ctx.rng.shuffle(tasks)
        items = []
        for n, (den, task) in enumerate(zip(dens, tasks), 1):
            item = {"kind": "line", "n": n, "task": task, "den": den, "ticks": list(range(den + 1))}
            if task == "fill":
                inner = [1] if r.get("unit_only") else list(range(1, den))
                k = min(FILL_BLANKS, len(inner))
                item["blanks"] = sorted(ctx.rng.sample(inner, k))
            else:
                item["num"] = 1 if r.get("unit_only") else ctx.rng.randint(1, den - 1)
            items.append(item)
        answers = [a for i in items for a in answers_for(i)]
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items, answer_key=answers)

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues: list[Issue] = []
        items = sheet.items
        lines = r.get("lines", LINES)
        if len(items) != lines:
            issues.append(error(sheet, f"{len(items)} number lines; this part has {lines}"))
        if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
            issues.append(error(sheet, "number lines are not numbered 1, 2, 3… in order"))
        for i in items:
            den, task = i["den"], i["task"]
            label = f"line {i.get('n')} ({task}, {den} parts)"
            if den not in r["denominators"] or den not in GRADE3_DENOMINATORS:
                issues.append(error(sheet, f"{label}: {den} parts isn't used here ({r['denominators']})"))
            if task not in r["tasks"]:
                issues.append(error(sheet, f"{label}: task {task!r} isn't used in this part"))
            if i.get("ticks") != list(range(den + 1)):
                issues.append(error(sheet, f"{label}: ticks should be 0…{den}, evenly spaced from 0 to 1"))
            if task == "fill":
                b = i.get("blanks", [])
                if not b or b != sorted(set(b)) or not all(1 <= k < den for k in b):
                    issues.append(error(sheet, f"{label}: empty labels must be inside ticks, between 0 and 1"))
                if r.get("unit_only") and b != [1]:
                    issues.append(error(sheet, f"{label}: this part only uses unit fractions"))
            else:
                num = i.get("num")
                if not isinstance(num, int) or not 1 <= num < den:
                    issues.append(error(sheet, f"{label}: {num}/{den} isn't on a tick between 0 and 1"))
                elif r.get("unit_only") and num != 1:
                    issues.append(error(sheet, f"{label}: {num}/{den} isn't a unit fraction"))
        dens = [i["den"] for i in items]
        if len(items) >= len(r["denominators"]) and set(dens) != set(r["denominators"]):
            issues.append(error(sheet, f"denominators {sorted(set(dens))}; every page needs {r['denominators']}"))
        if len(items) <= len(r["denominators"]) and len(set(dens)) != len(dens):
            issues.append(error(sheet, "two lines have the same number of parts"))
        for t in r["tasks"]:
            if len(items) >= len(r["tasks"]) and not any(i["task"] == t for i in items):
                issues.append(error(sheet, f"no {t!r} line on the page"))
        expected = [a for i in items for a in answers_for(i)]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the lines {expected}"))
        return issues
