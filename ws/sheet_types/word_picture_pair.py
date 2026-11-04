"""EN 7A-A: two big picture+word cards (the page's new words) and a "Say it again" strip."""

from __future__ import annotations

from ..content import vocab_by_word
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register


def card_items(words: list[str], kind: str) -> list[dict]:
    bank = vocab_by_word()
    return [{"kind": kind, "word": w, "picture": bank[w].picture} for w in words]


@register("word_picture_pair")
class WordPicturePair(SheetType):
    template = "word_picture_pair.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        return SheetContent(
            title="Look and say",
            parent_tip=ctx.rng.choice(ctx.banks["tips"][self.name]),
            items=card_items(entry.new_words, "card") + card_items(entry.review_words, "strip"),
            new_words=list(entry.new_words),
            review_words=list(entry.review_words),
        )

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = []
        cards = [i for i in sheet.items if i["kind"] == "card"]
        if [c["word"] for c in cards] != sheet.new_words or len(cards) != 2:
            issues.append(Issue(sheet_id=sheet.id, severity="error",
                                message=f"expected 2 cards showing the new words, got {[c['word'] for c in cards]}"))
        return issues
