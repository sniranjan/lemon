"""Owls Reading (R4-E, The Big Idea): first summaries of stories (RL.4.2) and articles (RI.4.2).

A ~150-word read, two multiple-choice questions (the big idea, the best summary, a key detail, a
detail too small for a summary), then the big idea written in one sentence in a box with a short
reminder of what goes in it (story: who, what they wanted or did, how it ended; article: the topic
and the most important point). In part 1 the first words of the sentence are printed.
"""

from __future__ import annotations

from ..longreads import check_read_sheet, head_item, planned_read, question_items
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

WRITE_LINES = 2


@register("big_idea_summary")
class BigIdeaSummary(SheetType):
    template = "big_idea_summary.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        p, k = planned_read(ctx)
        items, key = question_items(ctx, p.pages[k].questions, WRITE_LINES)
        return SheetContent(title=p.title, parent_tip=ctx.tip(self.name), items=[head_item(p, k), *items],
                            answer_key=key)

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        issues = [error(sheet, m) for m in check_read_sheet(sheet, WRITE_LINES)]
        qs = sheet.items[1:]
        if not qs or qs[-1]["kind"] != "write":
            issues.append(error(sheet, "the last question is the one-sentence big idea"))
        starters = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules.get("starters", False)
        if qs and qs[-1]["kind"] == "write" and bool(qs[-1].get("starter")) != bool(starters):
            issues.append(error(sheet, "sentence starters belong in part 1 only"))
        return issues
