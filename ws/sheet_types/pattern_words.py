"""Puppies Reading, Word Patterns: picture + word with its spelling pattern left as gaps to fill.

A pattern bank at the top shows the part's letter teams (sh ch th wh, a_e i_e ..., ai ay ...). Each of
the four cards shows a picture and the word with the pattern's letters as empty boxes; on the first
`show_word_pages` pages of a part the whole word is printed beside it, with the pattern in bold.
The words come from the level plan (`ws.plan.plan_spelling`); the first card is the page's new word.
"""

from __future__ import annotations

from ..content import phonics
from ..models import Issue, Sheet
from ..spelling import gapped, pattern_letters, pattern_span
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules


def _rules(sheet: Sheet) -> dict:
    return page_rules(sheet)


@register("pattern_words")
class PatternWords(SheetType):
    template = "pattern_words.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        data = phonics()
        entry = ctx.plan.for_page(ctx.spec.page)
        part_start = next(p.pages[0] for p in _section_parts(ctx) if p.pages[0] <= ctx.spec.page <= p.pages[1])
        show = ctx.spec.page - part_start < ctx.rules.get("show_word_pages", 0)
        items: list[dict] = [{"kind": "bank", "patterns": [pattern_letters(data, c) for c in ctx.rules["patterns"]]}]
        for card in entry.extra["cards"]:
            span = pattern_span(card["word"], card["pattern"], data)
            items.append({"kind": "pattern", "word": card["word"], "picture": card["picture"],
                          "pattern": card["pattern"], "letters": gapped(card["word"], span), "show_word": show})
        return SheetContent(title="Fill in the letters" if not show else "Read it, then fill it in",
                            parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[i["word"] for i in items[1:]],
                            new_words=list(entry.new_words), review_words=list(entry.review_words))

    def verify(self, sheet: Sheet) -> list[Issue]:
        data = phonics()
        rules = _rules(sheet)
        issues = []
        cards = [i for i in sheet.items if i["kind"] == "pattern"]
        if len(cards) != rules["cards_per_sheet"]:
            issues.append(error(sheet, f"{len(cards)} cards; the section asks for {rules['cards_per_sheet']}"))
        for c in cards:
            w, code = c["word"], c["pattern"]
            if code not in rules["patterns"]:
                issues.append(error(sheet, f"{w!r} shows pattern {code!r}, not one of this part's {rules['patterns']}"))
            if code not in data["pattern_words"].get(w, []):
                issues.append(error(sheet, f"{w!r} is not listed with pattern {code!r} in content/phonics/"))
            span = pattern_span(w, code, data)
            if span is None:
                issues.append(error(sheet, f"pattern {code!r} doesn't occur in {w!r}"))
            elif c["letters"] != gapped(w, span):
                issues.append(error(sheet, f"gaps in {w!r} don't match the pattern {code!r}"))
            elif "".join(ch for ch, _ in c["letters"]) != w:
                issues.append(error(sheet, f"letters don't spell {w!r}"))
        if sheet.new_words and (not cards or cards[0]["word"] != sheet.new_words[0]):
            issues.append(error(sheet, "the new word is not the first card"))
        words = [c["word"] for c in cards]
        if len(set(words)) != len(words):
            issues.append(error(sheet, f"a word twice on one page: {words}"))
        if sheet.answer_key != words:
            issues.append(error(sheet, "answer key doesn't match the cards"))
        return issues


def _section_parts(ctx: GenContext):
    from ..syllabus import load_level

    return load_level(ctx.spec.subject, ctx.spec.level).section(ctx.spec.section).parts
