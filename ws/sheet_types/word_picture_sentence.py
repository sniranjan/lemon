"""EN 7A-A: two cards of picture + word + a short sentence read aloud together, plus the strip.

The sentence is read *to* the child, so it may use words he hasn't met yet; only its
length is limited (`max_sentence_words`).
"""

from __future__ import annotations

from ..content import vocab_by_word
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, word_items


@register("word_picture_sentence")
class WordPictureSentence(SheetType):
    template = "word_picture_sentence.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        bank = vocab_by_word()
        cards = word_items(entry.new_words, "card")
        for card in cards:
            sentences = bank[card["word"]].sentences
            if not sentences:
                raise KeyError(f"word {card['word']!r} has no sentences in the word bank")
            card["sentence"] = ctx.rng.choice(sentences)
        return SheetContent(
            title="Say and listen",
            parent_tip=ctx.tip(self.name),
            items=cards + word_items(entry.review_words, "strip"),
            new_words=list(entry.new_words),
            review_words=list(entry.review_words),
        )

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        limit = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules["max_sentence_words"]
        issues = []
        for c in (i for i in sheet.items if i["kind"] == "card"):
            if c["word"].lower() not in c["sentence"].lower():
                issues.append(error(sheet, f"sentence for {c['word']!r} doesn't use the word: {c['sentence']!r}"))
            if len(c["sentence"].split()) > limit:
                issues.append(error(sheet, f"sentence longer than {limit} words: {c['sentence']!r}"))
        return issues
