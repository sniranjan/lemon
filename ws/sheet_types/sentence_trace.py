"""Kittens Reading, Trace a Sentence: a picture and a short sentence of known words ("The dog can run."),
read together, then traced in gray letters on writing lines.

The sentences come from the level plan (`ws.plan.plan_phrases`, the same frames and truth rules as the
sentences of the level before), so every word is one he knows and the sentence matches its picture.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error
from .phrase_card import check_phrase_items, phrase_items


LINE_CHARS = 20     # a longer sentence is traced on two writing lines
TRACE_PX = (44, 64)  # trace letters: as big as fits the line, never smaller than 44px


def trace_lines(text: str) -> list[str]:
    """One writing line, or two split near the middle at a space."""
    if len(text) <= LINE_CHARS:
        return [text]
    words = text.split()
    best = min(range(1, len(words)), key=lambda i: max(len(" ".join(words[:i])), len(" ".join(words[i:]))))
    return [" ".join(words[:best]), " ".join(words[best:])]


def trace_size(lines: list[str]) -> int:
    return max(TRACE_PX[0], min(TRACE_PX[1], 1180 // max(len(l) for l in lines)))


@register("sentence_trace")
class SentenceTrace(SheetType):
    template = "sentence_trace.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        items, new, review = phrase_items(ctx, "sentence")
        for item in items:
            item["trace_lines"] = trace_lines(item["text"])
            item["trace_size"] = trace_size(item["trace_lines"])
        return SheetContent(title="Read it, then trace it", parent_tip=ctx.tip(self.name), items=items,
                            new_words=new, review_words=review)

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = check_phrase_items(sheet, "sentence", "max_sentence_words")
        for item in sheet.items:
            t = item["text"]
            if item.get("trace_lines") != trace_lines(t):
                issues.append(error(sheet, f"trace lines don't spell the sentence: {t!r}"))
            if not (t[0].isupper() and t.endswith(".")) or "  " in t:
                issues.append(error(sheet, f"not a complete sentence to trace: {t!r}"))
        return issues
