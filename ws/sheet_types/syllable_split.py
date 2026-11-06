"""Puppies Reading, Clap the Parts: clap a word, then write one syllable in each box (`boxes`), or
circle how many claps it has (`count`: 1, 2 or 3).

Splits come from the hand-checked `syllables` table in content/phonics/english.yaml. Verify checks
that the syllables spell the word, each has a vowel (RF.1.3d), and the count matches its group.
"""

from __future__ import annotations

from ..content import phonics
from ..models import Issue, Sheet
from ..spelling import check_syllables, syllable_table
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error
from .pattern_words import _rules

CHOICES = [1, 2, 3]


@register("syllable_split")
class SyllableSplit(SheetType):
    template = "syllable_split.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        mode = ctx.rules["syllable_mode"]
        items = [{"kind": "syllables", "mode": mode, "word": c["word"], "picture": c["picture"],
                  "syllables": c["syllables"], "choices": CHOICES if mode == "count" else []}
                 for c in entry.extra["cards"]]
        answers = ["-".join(i["syllables"]) if mode == "boxes" else len(i["syllables"]) for i in items]
        title = "Clap and count" if mode == "count" else "Clap and split"
        return SheetContent(title=title, parent_tip=ctx.tip(self.name), items=items, answer_key=answers,
                            new_words=list(entry.new_words), review_words=list(entry.review_words))

    def verify(self, sheet: Sheet) -> list[Issue]:
        rules = _rules(sheet)
        table = syllable_table(phonics())
        issues = []
        cards = [i for i in sheet.items if i["kind"] == "syllables"]
        if len(cards) != rules["cards_per_sheet"]:
            issues.append(error(sheet, f"{len(cards)} cards; the section asks for {rules['cards_per_sheet']}"))
        for c in cards:
            w = c["word"]
            if w not in table:
                issues.append(error(sheet, f"{w!r} is not in the hand-checked syllables table"))
                continue
            kind, syls = table[w]
            if c["syllables"] != syls:
                issues.append(error(sheet, f"{w!r} is split {c['syllables']}, the table says {syls}"))
            if kind not in rules["syllable_kinds"]:
                issues.append(error(sheet, f"{w!r} is a {kind} word, not one of this part's {rules['syllable_kinds']}"))
            issues += [error(sheet, p) for p in check_syllables(w, syls, kind)]
            if c["mode"] == "count" and len(syls) not in c["choices"]:
                issues.append(error(sheet, f"{w!r}: the answer {len(syls)} is not one of the choices"))
        words = [c["word"] for c in cards]
        if len(set(words)) != len(words):
            issues.append(error(sheet, f"a word twice on one page: {words}"))
        if rules["syllable_mode"] == "count" and len({len(c["syllables"]) for c in cards}) < 2:
            issues.append(error(sheet, "every word has the same number of claps; mix them"))
        return issues
