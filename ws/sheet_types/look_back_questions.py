"""Owls Reading (R4-A, C, D): questions about the read on the page before.

The top of the page sends the child back to the reading page ("Look back at page 7"); then
multiple-choice questions (circle A, B or C) and written answers on lines. Questions about a
nonfiction read include its diagram or caption; questions about two texts include some that need
both. The answer key gives each letter with its option and a sample for each written answer.
"""

from __future__ import annotations

from ..longreads import check_read_sheet, head_item, planned_read, question_items
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

WRITE_LINES = 2


@register("look_back_questions")
class LookBackQuestions(SheetType):
    template = "look_back_questions.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        p, k = planned_read(ctx)
        if not isinstance(k, int):
            raise KeyError(f"page {ctx.spec.page} is planned as a reading page, not a questions page")
        head = head_item(p, k) | {"back_page": ctx.spec.page - 1}
        items, key = question_items(ctx, p.pages[k].questions, WRITE_LINES)
        return SheetContent(title=p.title, parent_tip=ctx.tip(self.name), items=[head, *items], answer_key=key)

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = [error(sheet, m) for m in check_read_sheet(sheet, WRITE_LINES)]
        if sheet.items and sheet.items[0].get("back_page") != sheet.page_number - 1:
            issues.append(error(sheet, "must send the child back to the page before"))
        return issues
