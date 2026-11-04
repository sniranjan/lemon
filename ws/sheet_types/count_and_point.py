"""MA 6A-B/C: rows of N pictures and 3 numerals; the child points to the one that shows how many."""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error
from .count_and_say import check_counts, count_rows


def choices_for(ctx: GenContext, answer: int, k: int) -> list[int]:
    lo, hi = ctx.rules["min"], ctx.rules["max"]
    # prefer near neighbors (harder to guess), fall back to anything in range
    near = [n for n in range(max(lo, answer - 2), min(hi, answer + 2) + 1) if n != answer]
    far = [n for n in range(lo, hi + 1) if n != answer and n not in near]
    ctx.rng.shuffle(near)
    ctx.rng.shuffle(far)
    return (near + far)[: k - 1]


@register("count_and_point")
class CountAndPoint(SheetType):
    template = "count_and_point.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        k = ctx.rules.get("choices", 3)
        items = count_rows(ctx)
        # the answer's position must not be the same on every row
        while True:
            positions = [ctx.rng.randrange(k) for _ in items]
            if len(set(positions)) > 1:
                break
        for item, pos in zip(items, positions):
            others = choices_for(ctx, item["n"], k)
            item["choices"] = others[:pos] + [item["n"]] + others[pos:]
        return SheetContent(title="Count and point", parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[i["n"] for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = check_counts(sheet)
        for i in sheet.items:
            c = i["choices"]
            if c.count(i["n"]) != 1 or len(set(c)) != len(c):
                issues.append(error(sheet, f"choices {c} must be distinct and include {i['n']} once"))
        if len({i["choices"].index(i["n"]) for i in sheet.items}) == 1:
            issues.append(error(sheet, "the answer is in the same position on every row"))
        return issues
