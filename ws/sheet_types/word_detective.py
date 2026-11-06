"""Owls Reading (R4-B, Word Detective): work out a word's meaning from clues in the text (L.4.4a).

A ~150-word read with this page's two target words in bold; the child picks each word's meaning
(circle A, B or C) and writes down the clue words that helped (a definition, an example, a
restatement or an opposite nearby). Each read serves two pages with different bold words.
"""

from __future__ import annotations

from ..longreads import check_read_sheet, head_item, planned_read, question_items
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

WRITE_LINES = 2


@register("word_detective")
class WordDetective(SheetType):
    template = "word_detective.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        p, k = planned_read(ctx)
        qs = p.pages[k]
        items, key = question_items(ctx, qs.questions, WRITE_LINES)
        return SheetContent(title=p.title, parent_tip=ctx.tip(self.name),
                            items=[head_item(p, k, qs.targets), *items], answer_key=key)

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = [error(sheet, m) for m in check_read_sheet(sheet, WRITE_LINES)]
        if not sheet.items or not sheet.items[0].get("targets"):
            issues.append(error(sheet, "a Word Detective page needs bold words"))
        return issues
