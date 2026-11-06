"""Puppies Reading, Word Endings: add an ending to a known word, or take it off again.

Each of the four cards shows the word's picture (twice for "one and more": cat, cats), then
`add`: "jump + ing = ____" or `take_off`: "jumping − ing = ____", with a box to write the answer in.
Forms come from the hand-checked `endings` table in content/phonics/english.yaml; verify re-derives
each one from the spelling rules (double the last letter, drop the final e, add es).
"""

from __future__ import annotations

from ..content import phonics
from ..models import Issue, Sheet
from ..phonics import by_rule, spelling_rule, tail
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error
from .pattern_words import _rules

TITLES = {"add": "Add the ending", "take_off": "Take off the ending"}


@register("word_endings")
class WordEndings(SheetType):
    template = "word_endings.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        mode = ctx.rules["ending_mode"]
        items = []
        for c in entry.extra["cards"]:
            items.append({"kind": "ending", "mode": mode, "word": c["word"], "picture": c["picture"],
                          "ending": c["ending"], "form": c["form"], "tail": c["tail"],
                          "copies": 2 if c["ending"] == "plural" else 1})
        answers = [i["form"] if mode == "add" else i["word"] for i in items]
        return SheetContent(title=TITLES[mode], parent_tip=ctx.tip(self.name), items=items, answer_key=answers,
                            new_words=list(entry.new_words), review_words=list(entry.review_words))

    def verify(self, sheet: Sheet) -> list[Issue]:
        data = phonics()
        rules = _rules(sheet)
        irregular = data.get("irregular") or {}
        issues = []
        cards = [i for i in sheet.items if i["kind"] == "ending"]
        if len(cards) != rules["cards_per_sheet"]:
            issues.append(error(sheet, f"{len(cards)} cards; the section asks for {rules['cards_per_sheet']}"))
        for c in cards:
            base, ending, form = c["word"], c["ending"], c["form"]
            if ending not in rules["endings"]:
                issues.append(error(sheet, f"{base!r}: ending {ending!r} is not one of this part's {rules['endings']}"))
            listed = (data["endings"].get(base) or {}).get(ending)
            if listed != form:
                issues.append(error(sheet, f"{base} + {ending} = {form!r} is not in the hand-checked endings table"))
            expected = (irregular.get(base) or {}).get(ending) or by_rule(base, ending)
            if form != expected:
                issues.append(error(sheet, f"{base} + {ending}: {form!r} breaks the spelling rules ({expected!r})"))
            if c["tail"] != tail(base, ending, form):
                issues.append(error(sheet, f"{base}: shows the ending {c['tail']!r}, should be {tail(base, ending, form)!r}"))
            if c["mode"] != rules["ending_mode"]:
                issues.append(error(sheet, f"{base}: mode {c['mode']!r}, the part asks for {rules['ending_mode']!r}"))
            if c["copies"] != (2 if ending == "plural" else 1):
                issues.append(error(sheet, f"{base}: a plural shows its picture twice, a verb once"))
        words = [c["word"] for c in cards]
        if len(set(words)) != len(words):
            issues.append(error(sheet, f"a word twice on one page: {words}"))
        want = [c["form"] if rules["ending_mode"] == "add" else c["word"] for c in cards]
        if sheet.answer_key != want:
            issues.append(error(sheet, "answer key doesn't match the cards"))
        if len({spelling_rule(c["word"], c["ending"], c["form"]) for c in cards}) < 2 and len(cards) > 1:
            issues.append(Issue(sheet_id=sheet.id, severity="warning",
                                message="every card follows the same spelling rule"))
        return issues
