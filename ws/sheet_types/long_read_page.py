"""Owls Reading (R4-A, C, D): a long read alone on its page; its questions follow on the next page.

A chapter of a longer story (~250 words), a nonfiction article with headings and a simple diagram
(steps, a cycle, a table, a bar chart or a time line, with a caption), or two short texts on one topic.
The child reads it (twice is better) and ticks the boxes at the bottom; `look_back_questions` asks
about it on the next page. Which read a page gets comes from the level plan (`ws.longreads`).
"""

from __future__ import annotations

from ..longreads import check_read_sheet, head_item, planned_read
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error


@register("long_read_page")
class LongReadPage(SheetType):
    template = "long_read_page.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        p, k = planned_read(ctx)
        if k != "read":
            raise KeyError(f"page {ctx.spec.page} is planned as a questions page, not a reading page")
        return SheetContent(title=p.title, parent_tip=ctx.tip(self.name), items=[head_item(p, k)])

    def verify(self, sheet: Sheet) -> list[Issue]:
        return [error(sheet, m) for m in check_read_sheet(sheet, None)]
