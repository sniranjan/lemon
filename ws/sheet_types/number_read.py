"""MA 6A-C: numerals in boxes to read aloud, each with that many small pictures under it."""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from .count_and_say import check_counts, count_rows

CARDS = 4


@register("number_read")
class NumberRead(SheetType):
    template = "number_read.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        items = count_rows(ctx, CARDS)
        return SheetContent(title="Read the numbers", parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[i["n"] for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        return check_counts(sheet)
