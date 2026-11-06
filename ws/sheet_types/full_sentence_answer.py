"""Foxes Reading (R3-E): a passage and 3 questions answered in full sentences on lines.

The child turns the question into the start of the answer ("Why did Ben smile?" -> "Ben smiled
because ..."). In part 1 the first words of each answer (`starter`) are printed on the line; in
part 2 they aren't. The answer key has a full-sentence sample answer for each question.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..passages import build_passage_items, check_passage_sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

WRITE_LINES = 2


@register("full_sentence_answer")
class FullSentenceAnswer(SheetType):
    template = "full_sentence_answer.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        title, items, key = build_passage_items(ctx, WRITE_LINES)
        return SheetContent(title=title, parent_tip=ctx.tip(self.name), items=items, answer_key=key)

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        issues = [error(sheet, m) for m in check_passage_sheet(sheet, WRITE_LINES)]
        starters = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules.get("starters", True)
        qs = sheet.items[1:]
        if len(qs) != 3 or any(q["kind"] != "write" for q in qs):
            issues.append(error(sheet, "needs exactly 3 written questions"))
        if starters and not all(q.get("starter") for q in qs):
            issues.append(error(sheet, "every question needs a sentence starter in this part"))
        if not starters and any(q.get("starter") for q in qs):
            issues.append(error(sheet, "no sentence starters in this part"))
        return issues
