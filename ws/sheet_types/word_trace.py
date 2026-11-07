"""EN 5A-D: three pictures, each with its word to read and then trace in dotted letters.

Words come from the level plan (`ws.plan.plan_letters`): short-vowel words, then picture words
he knows, then this level's new words.
"""

from __future__ import annotations

from ..content import vocab_by_word
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ..trace_font import andika_has, missing_glyphs
from ._common import error, page_rules


@register("word_trace")
class WordTrace(SheetType):
    template = "word_trace.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        bank = vocab_by_word()
        items = [{"kind": "word", "word": w, "picture": bank[w].picture} for w in entry.extra["words"]]
        return SheetContent(title="Trace the words", parent_tip=ctx.tip(self.name), items=items,
                            new_words=list(entry.new_words), review_words=list(entry.review_words))

    def verify(self, sheet: Sheet) -> list[Issue]:
        rules = page_rules(sheet)
        issues = []
        if len(sheet.items) != rules.get("trace_words", 3):
            issues.append(error(sheet, f"expected {rules.get('trace_words', 3)} words, got {len(sheet.items)}"))
        for item in sheet.items:
            w = item["word"]
            if missing_glyphs(w):
                issues.append(error(sheet, f"the trace font has no {missing_glyphs(w)} (in {w!r})"))
            if not andika_has(w):
                issues.append(error(sheet, f"Andika can't print {w!r}"))
            if not rules.get("min_letters", 1) <= len(w) <= rules.get("max_letters", 99):
                issues.append(error(sheet, f"{w!r} has {len(w)} letters, outside this part's range"))
        words = [i["word"] for i in sheet.items]
        if len(set(words)) != len(words):
            issues.append(error(sheet, f"the same word twice on one page: {words}"))
        return issues
