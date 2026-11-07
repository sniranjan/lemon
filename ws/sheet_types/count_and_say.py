"""MA 6A-A/B: rows of N pictures with the numeral and number word; count aloud while pointing."""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import NUMBER_WORDS, error, new_numbers, page_rules, pick_numbers, pick_objects

ROWS = 3


def count_rows(ctx: GenContext, rows: int = ROWS) -> list[dict]:
    numbers = pick_numbers(ctx.rng, ctx.rules, rows)
    objects = pick_objects(ctx.rng, rows)
    return [{"kind": "count", "n": n, "object": o["name"], "picture": o["picture"], "word": NUMBER_WORDS[n]}
            for n, o in zip(numbers, objects)]


def check_counts(sheet: Sheet) -> list[Issue]:
    rules = page_rules(sheet)
    issues = []
    for item in sheet.items:
        if not rules["min"] <= item["n"] <= rules["max"]:
            issues.append(error(sheet, f"{item['n']} is outside this part's range {rules['min']}–{rules['max']}"))
    for n in new_numbers(rules):
        if n not in [i["n"] for i in sheet.items]:
            issues.append(error(sheet, f"the part's new number {n} is missing"))
    return issues


@register("count_and_say")
class CountAndSay(SheetType):
    template = "count_and_say.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        items = count_rows(ctx)
        return SheetContent(title="Count and say", parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[i["n"] for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = check_counts(sheet)
        for i in sheet.items:
            if i["word"] != NUMBER_WORDS[i["n"]]:
                issues.append(error(sheet, f"number word {i['word']!r} doesn't match {i['n']}"))
        return issues
