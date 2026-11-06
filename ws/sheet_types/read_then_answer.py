"""Otters Reading (R5-A, C): a two-page spread for passages too long to share a page with questions.

The reading page holds the passage alone (about 300 words, numbered paragraphs, no answers); the next
page holds its 5 questions (circle A, B or C, and written answers on lines) and points back to the
reading page. A section uses it with the rule `spread`; the planner (`ws.passages.plan_passages`)
gives each passage two pages in a row, the reading page first. Content:
content/passages/<level>/<section>.yaml, one question set per passage.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..passages import build_spread_items, check_spread_sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

WRITE_LINES = 2


@register("read_then_answer")
class ReadThenAnswer(SheetType):
    template = "read_then_answer.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        title, items, key = build_spread_items(ctx, WRITE_LINES)
        return SheetContent(title=title, parent_tip=ctx.tip(self.name), items=items, answer_key=key)

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = [error(sheet, m) for m in check_spread_sheet(sheet, WRITE_LINES)]
        if sheet.items and sheet.items[0].get("role") == "questions" and not any(
                i["kind"] == "write" for i in sheet.items):
            issues.append(error(sheet, "a questions page needs at least one written answer"))
        return issues
