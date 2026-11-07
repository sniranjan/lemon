"""Otters Reading (R5-D): a short passage with its similes, metaphors, idioms, adages or proverbs in bold.

The child says what each one really means, names its kind, and explains why the writer used it.
Every bold phrase must be in the hand-checked list content/figurative/<level>.yaml (phrase, kind,
meaning), with a kind the part allows (rule `kinds`). A multiple-choice question that quotes a
phrase and asks what it means must have that phrase's listed meaning as its right answer; one that
asks what kind it is must have its listed kind. Content: content/passages/<level>/D.yaml.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict

from ..content import figurative
from ..models import Issue, Sheet
from ..passages import Passage, build_passage_items, check_passage_sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules
from .clue_words import marks_problems

WRITE_LINES = 2
KINDS = ("simile", "metaphor", "idiom", "adage", "proverb", "personification", "hyperbole")


class Figure(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phrase: str      # exactly as it appears in the passage
    kind: str
    meaning: str     # what it really means: the right answer of a "what does it mean?" question


def figures(level: str) -> dict[str, Figure]:
    return {f["phrase"]: Figure.model_validate(f) for f in figurative(level)}


def figure_problems(p: Passage, level: str, kinds: list[str]) -> list[str]:
    """Every bold phrase is listed with an allowed kind; meaning and kind questions match the list."""
    table = figures(level)
    out = []
    for s in p.pages:
        for w in s.words:
            f = table.get(w)
            if f is None:
                out.append(f"passage {p.id}: {w!r} is not in content/figurative/{level}.yaml")
                continue
            if f.kind not in kinds:
                out.append(f"passage {p.id}: {w!r} is a {f.kind}, not one of {kinds} in this part")
        for q in s.questions:
            quoted = [w for w in s.words if f'"{w}"' in q.ask and w in table]
            if not q.choices or len(quoted) != 1:
                continue
            f = table[quoted[0]]
            if re.search(r"\bkind\b|\bsimile or\b|\bmetaphor or\b|\bidiom or\b", q.ask):
                if q.choices[0] != f.kind or not set(q.choices) <= set(KINDS):
                    out.append(f"passage {p.id}: {q.ask!r} must answer {f.kind!r} from the kinds list")
            elif re.search(r"\bmeans?\b", q.ask) and q.choices[0] != f.meaning:
                out.append(f"passage {p.id}: {q.ask!r} must answer the listed meaning {f.meaning!r}")
    return out


@register("figurative_language")
class FigurativeLanguage(SheetType):
    template = "figurative_language.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        title, items, key = build_passage_items(ctx, WRITE_LINES, marks=True)
        return SheetContent(title=title, parent_tip=ctx.tip(self.name), items=items, answer_key=key)

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..passages import passage_by_id
        rules = page_rules(sheet)
        msgs = check_passage_sheet(sheet, WRITE_LINES) + marks_problems(sheet, rules)
        if not msgs:
            p = passage_by_id(sheet.level, rules["passages"], sheet.items[0]["passage"])
            msgs += figure_problems(p, sheet.level, rules.get("kinds", list(KINDS)))
        return [error(sheet, m) for m in msgs]
