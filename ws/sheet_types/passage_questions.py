"""Foxes Reading (R3-A, C, D): an original passage, then 3–4 questions about it.

Multiple-choice questions (circle A, B or C) and short written answers on lines. Which passage and
question set a page gets comes from the level plan (`ws.passages.plan_passages`); a passage serves
two pages with different questions. The answer key gives each letter with its option, and a
sample answer for each written question. Content: content/passages/<level>/<section>.yaml.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..passages import build_passage_items, check_passage_sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

WRITE_LINES = 2


@register("passage_questions")
class PassageQuestions(SheetType):
    template = "passage_questions.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        title, items, key = build_passage_items(ctx, WRITE_LINES)
        return SheetContent(title=title, parent_tip=ctx.tip(self.name), items=items, answer_key=key)

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = [error(sheet, m) for m in check_passage_sheet(sheet, WRITE_LINES)]
        if not any(i["kind"] == "write" for i in sheet.items):
            issues.append(error(sheet, "a passage page needs at least one written answer"))
        return issues
