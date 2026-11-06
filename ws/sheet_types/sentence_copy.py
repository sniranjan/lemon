"""Puppies Reading, Copy a Sentence: read a short sentence about a picture, then copy it on the
writing lines (capital letter first, end mark last).

The sentences are the `sentences:` of this level's words (content/vocab/english.yaml), chosen by the
level plan. Verify checks that each uses only known words, sight words and their regular endings
(content/phonics/english.yaml), uses its picture's word, and fits the part's length and end marks.
"""

from __future__ import annotations

from ..content import phonics, vocab_by_word
from ..models import Issue, Sheet
from ..phonics import check_sentence
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error
from .pattern_words import _rules


def known_words(level: str) -> set[str]:
    """The words a Puppies sentence may use: the `known_levels` and the level's own words."""
    from ..syllabus import load_level

    lvl = load_level("english", level)
    levels = set(lvl.rules.get("known_levels", [])) | {level}
    return {w for w, e in vocab_by_word().items() if e.level in levels}


@register("sentence_copy")
class SentenceCopy(SheetType):
    template = "sentence_copy.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        rows = ctx.rules.get("copy_rows", 2)
        items = [{"kind": "copy", "word": c["word"], "picture": c["picture"], "text": c["text"], "rows": rows}
                 for c in entry.extra["cards"]]
        return SheetContent(title="Read it and copy it", parent_tip=ctx.tip(self.name), items=items,
                            new_words=list(entry.new_words), review_words=list(entry.review_words))

    def verify(self, sheet: Sheet) -> list[Issue]:
        rules = _rules(sheet)
        data, bank = phonics(), vocab_by_word()
        words = known_words(sheet.level)
        issues = []
        cards = [i for i in sheet.items if i["kind"] == "copy"]
        if len(cards) != rules["sentences_per_sheet"]:
            issues.append(error(sheet, f"{len(cards)} sentences; the section asks for {rules['sentences_per_sheet']}"))
        for c in cards:
            entry = bank.get(c["word"])
            if entry is None or c["text"] not in entry.sentences:
                issues.append(error(sheet, f"{c['text']!r} is not one of {c['word']!r}'s sentences"))
            issues += [error(sheet, p) for p in check_sentence(c["text"], c["word"], data, words,
                                                               tuple(rules["sentence_words"]), rules.get("end_marks"))]
        texts = [c["text"] for c in cards]
        if len(set(texts)) != len(texts) or len({c["word"] for c in cards}) != len(cards):
            issues.append(error(sheet, f"the same word or sentence twice on one page: {texts}"))
        if sheet.answer_key:
            issues.append(error(sheet, "a copying page has no answer key"))
        return issues
