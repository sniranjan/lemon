"""Otters Reading (R5-E): a passage of 3 numbered paragraphs, summed up one paragraph at a time.

On a passage's first page the child picks the best one-sentence summary of two paragraphs (circle A,
B or C) and writes one for the third; on its second page they write summaries themselves and pick
the best summary of the whole passage. Every question names its paragraph ("paragraph 2") or the
whole passage, and its evidence must come from that paragraph (ws.passages.paragraph_problems).
Content: content/passages/<level>/E.yaml.
"""

from __future__ import annotations

import re

from ..models import Issue, Sheet
from ..passages import build_passage_items, check_passage_sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

WRITE_LINES = 2
_TARGET = re.compile(r"\bparagraph \d\b|\bwhole (passage|article|story)\b", re.I)


@register("paragraph_summary")
class ParagraphSummary(SheetType):
    template = "paragraph_summary.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        title, items, key = build_passage_items(ctx, WRITE_LINES, numbered=True)
        return SheetContent(title=title, parent_tip=ctx.tip(self.name), items=items, answer_key=key)

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        rules = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        msgs = check_passage_sheet(sheet, WRITE_LINES)
        head = sheet.items[0] if sheet.items else {}
        n = rules.get("paragraphs", 3)
        if len(head.get("paragraphs", [])) != n:
            msgs.append(f"the passage needs exactly {n} paragraphs")
        if not head.get("numbered"):
            msgs.append("paragraphs must be numbered")
        for q in sheet.items[1:]:
            if not _TARGET.search(q["ask"]):
                msgs.append(f"question {q['n']} must name a paragraph or the whole passage")
        return [error(sheet, m) for m in msgs]
