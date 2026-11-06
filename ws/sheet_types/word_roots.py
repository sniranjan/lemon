"""Penguins Reading (R7-C): Greek and Latin roots as clues to word meaning (L.7.4b).

Each page shows its root cards (root, Latin or Greek, what it means, an example word), then: match four
words to their meanings (write the letter), fill two blanks from the word box, and use a root to explain a
word that isn't on the page (written, with a sample answer and a one-line rubric in the key). Review pages
show four roots and their fourth words. Content and planning: ws/roots.py, content/wordroots/<level>.yaml.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ..roots import build_root_items, check_root_sheet
from ._common import error


@register("word_roots")
class WordRoots(SheetType):
    template = "word_roots.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        title, items, key = build_root_items(ctx)
        return SheetContent(title=title, parent_tip=ctx.tip(self.name), items=items, answer_key=key)

    def verify(self, sheet: Sheet) -> list[Issue]:
        return [error(sheet, m) for m in check_root_sheet(sheet)]
