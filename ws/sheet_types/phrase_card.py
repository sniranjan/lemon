"""EN 6A-B: three cards of picture + short phrase ("a red apple", "mom and dad") to say aloud.

The phrases come from the level plan (`ws.plan.plan_phrases`), so any page range gives the
same sheets. Every word is one the child already knows, or the page's new word.
"""

from __future__ import annotations

import re

from ..content import phrases, vocab_by_word
from ..models import Issue, Sheet
from ..phrases import check_phrase
from ..registry import GenContext, SheetContent, SheetType, register
from ..syllabus import level_rank
from ._common import error, page_rules

_SPLIT = re.compile(r"([A-Za-z']+)")


def phrase_items(ctx: GenContext, kind: str) -> tuple[list[dict], list[str], list[str]]:
    entry = ctx.plan.for_page(ctx.spec.page)
    items = []
    for p in entry.extra["phrases"]:
        content = set(p["words"])
        # the text in runs, with the slot words marked so the template can make them bold
        runs = [[t, t.lower() in content] for t in _SPLIT.split(p["text"]) if t]
        items.append({"kind": kind, "text": p["text"], "runs": runs, "frame": p["frame"], "slots": p["slots"],
                      "word": p["pictures"][0] if p["pictures"] else p["words"][0],
                      "words": p["words"], "pictures": p["pictures"]})
        if p.get("picture_size"):
            items[-1]["picture_size"] = p["picture_size"]
    return items, list(entry.new_words), list(entry.review_words)


def check_phrase_items(sheet: Sheet, kind: str, limit_rule: str) -> list[Issue]:
    rules = page_rules(sheet)
    rank = level_rank(sheet.level)
    known = {w: e for w, e in vocab_by_word().items() if level_rank(e.level) <= rank}
    issues = []
    items = [i for i in sheet.items if i["kind"] == kind]
    if len(items) != rules["phrases_per_sheet"]:
        issues.append(error(sheet, f"expected {rules['phrases_per_sheet']} {kind}s, got {len(items)}"))
    for item in items:
        issues += [error(sheet, p) for p in check_phrase(item, phrases(), known, rules.get(limit_rule))]
        if not item["pictures"]:
            issues.append(error(sheet, f"{kind} {item['text']!r} has no picture"))
    texts = [i["text"] for i in items]
    if len(set(texts)) != len(texts):
        issues.append(error(sheet, f"the same {kind} twice on one page: {texts}"))
    on_page = {w for i in items for w in i["words"]}
    missing = [w for w in sheet.new_words if w not in on_page]
    if missing:
        issues.append(error(sheet, f"new word(s) {missing} are not used on the page"))
    bank = vocab_by_word()
    pictured = {p for i in items for p in i["pictures"]}
    unpictured = [w for w in sheet.new_words if w in bank and bank[w].picture and w not in pictured]
    if unpictured:
        issues.append(error(sheet, f"new word(s) {unpictured} are used but their picture isn't shown"))
    return issues


@register("phrase_card")
class PhraseCard(SheetType):
    template = "phrase_card.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        items, new, review = phrase_items(ctx, "phrase")
        return SheetContent(title="Say the words", parent_tip=ctx.tip(self.name), items=items,
                            new_words=new, review_words=review)

    def verify(self, sheet: Sheet) -> list[Issue]:
        return check_phrase_items(sheet, "phrase", "max_phrase_words")
