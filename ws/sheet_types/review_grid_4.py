"""EN 7A-B: four known pictures + words in a 2×2 grid for a "find it" game."""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, word_items


@register("review_grid_4")
class ReviewGrid4(SheetType):
    template = "review_grid_4.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        words = list(ctx.plan.for_page(ctx.spec.page).review_words)
        ctx.rng.shuffle(words)
        return SheetContent(
            title="Find it",
            parent_tip=ctx.tip(self.name),
            items=word_items(words, "grid"),
            review_words=words,
        )

    def verify(self, sheet: Sheet) -> list[Issue]:
        words = [i["word"] for i in sheet.items]
        if len(words) != 4 or len(set(words)) != 4:
            return [error(sheet, f"expected 4 different words, got {words}")]
        if sheet.new_words:
            return [error(sheet, f"review sheet introduces new words {sheet.new_words}")]
        return []
