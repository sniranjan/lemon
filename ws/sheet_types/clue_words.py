"""Otters Reading (R5-B): a short passage with 2–3 words in bold, and questions about what they mean.

Part 1: the child works out a word's meaning from the clues around it (a definition, a synonym or
an opposite, an example, a cause and effect). Part 2: words with more than one meaning (homographs);
the child picks the meaning the passage uses and writes a sentence with another meaning. The bold
words are each question set's `words` (copied exactly from the passage); every bold word is asked
about. A passage serves two pages with different bold words. Content: content/passages/<level>/B.yaml.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..passages import build_passage_items, check_passage_sheet, find_phrase
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules

WRITE_LINES = 2


def marks_problems(sheet: Sheet, rules: dict) -> list[str]:
    """Bold words: as many as the rule `marks` allows, and every one of them asked about."""
    head = sheet.items[0] if sheet.items else {}
    marks = head.get("marks", [])
    lo, hi = rules.get("marks", [2, 3])
    out = []
    if not lo <= len(marks) <= hi:
        out.append(f"{len(marks)} bold words (needs {lo}–{hi})")
    asks = " ".join(i["ask"] for i in sheet.items[1:])
    for m in marks:
        if not find_phrase(m, asks):
            out.append(f"bold word {m!r} isn't asked about")
    return out


@register("clue_words")
class ClueWords(SheetType):
    template = "clue_words.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        title, items, key = build_passage_items(ctx, WRITE_LINES, marks=True)
        return SheetContent(title=title, parent_tip=ctx.tip(self.name), items=items, answer_key=key)

    def verify(self, sheet: Sheet) -> list[Issue]:
        rules = page_rules(sheet)
        msgs = check_passage_sheet(sheet, WRITE_LINES) + marks_problems(sheet, rules)
        return [error(sheet, m) for m in msgs]
