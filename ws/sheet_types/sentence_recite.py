"""EN 6A-C: a picture and one short sentence ("The dog can run."), said three times.

Each block has three circles; the child colors one each time he says the sentence. The
sentences come from the level plan and use only words he knows (see phrase_card).
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error
from .phrase_card import check_phrase_items, phrase_items


@register("sentence_recite")
class SentenceRecite(SheetType):
    template = "sentence_recite.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        items, new, review = phrase_items(ctx, "sentence")
        for item in items:
            item["times"] = ctx.rules.get("recite_times", 3)
        return SheetContent(title="Say it three times", parent_tip=ctx.tip(self.name), items=items,
                            new_words=new, review_words=review)

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = check_phrase_items(sheet, "sentence", "max_sentence_words")
        for item in sheet.items:
            if not item["text"].endswith(".") or not item["text"][0].isupper():
                issues.append(error(sheet, f"not a complete sentence: {item['text']!r}"))
        return issues
