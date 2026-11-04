"""MA 6A-D: dot patterns up to 10, each with its numeral."""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, pick_numbers

CARDS = 4

# Fixed, dice-like patterns on a 100×100 grid so each number always looks the same.
_COL = [25, 75]
PATTERNS: dict[int, list[tuple[int, int]]] = {
    1: [(50, 50)],
    2: [(25, 25), (75, 75)],
    3: [(20, 20), (50, 50), (80, 80)],
    4: [(25, 25), (75, 25), (25, 75), (75, 75)],
    5: [(22, 22), (78, 22), (50, 50), (22, 78), (78, 78)],
    6: [(x, y) for y in (18, 50, 82) for x in _COL],
    7: [(x, y) for y in (18, 50, 82) for x in (12, 88)] + [(50, 50)],   # wide columns keep the middle dot clear
    8: [(x, y) for y in (12, 37, 63, 88) for x in _COL],
    9: [(x, y) for y in (20, 50, 80) for x in (20, 50, 80)],
    10: [(x, y) for y in (10, 30, 50, 70, 90) for x in _COL],   # two columns of five, like 6 and 8
}


@register("dots_to_number")
class DotsToNumber(SheetType):
    template = "dots_to_number.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        numbers = pick_numbers(ctx.rng, ctx.rules, CARDS)
        items = [{"kind": "dots", "n": n, "dots": [list(p) for p in PATTERNS[n]]} for n in numbers]
        return SheetContent(title="Count the dots", parent_tip=ctx.tip(self.name), items=items,
                            answer_key=numbers)

    def verify(self, sheet: Sheet) -> list[Issue]:
        from .count_and_say import check_counts

        issues = check_counts(sheet)
        for i in sheet.items:
            if len(i["dots"]) != i["n"] or len({tuple(d) for d in i["dots"]}) != i["n"]:
                issues.append(error(sheet, f"{len(i['dots'])} dots shown for {i['n']}"))
        return issues
