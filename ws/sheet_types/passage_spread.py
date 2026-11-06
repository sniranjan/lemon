"""Pandas Reading (R6): a two-page spread per question set: the passage, then its questions.

The reading page holds the passage alone (320–380 words, paragraphs numbered); the next page holds
3–4 questions about it: multiple choice (A–D), "which sentence best supports" quotes from the text,
short written answers, 3–4-sentence answers with evidence, and labeled organizer boxes (Cause /
Effect). A passage serves one or two spreads; the second reading page says what to look for. The
answer key (questions page only) gives each letter with its option, sample answers, and a short
"full answer" rubric for the 3–4-sentence answers. Content and checks: ws/spreads.py.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ..spreads import build_spread_items, check_spread_sheet
from ._common import error


@register("passage_spread")
class PassageSpread(SheetType):
    template = "passage_spread.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        title, items, key = build_spread_items(ctx)
        # the reading page and the questions page have their own tips (the reading tip is one line)
        tip = ctx.tip("passage_spread_read" if items[0]["side"] == "read" else self.name)
        return SheetContent(title=title, parent_tip=tip, items=items, answer_key=key)

    def verify(self, sheet: Sheet) -> list[Issue]:
        return [error(sheet, m) for m in check_spread_sheet(sheet)]
