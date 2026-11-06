"""EN 5A-B: a picture and its word split into onset + rime ("c" + "at"), said in two parts, then whole.

Cards come from the level plan (`ws.plan.plan_letters`): short-vowel words with different rimes, a
rhyming family on one page (cat, hat), or a new word with its family mates. The splits are the
hand-checked `rimes` lists in content/sounds/english.yaml.
"""

from __future__ import annotations

from ..content import sounds, vocab_by_word
from ..models import Issue, Sheet
from ..plan import rime_split
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

VOWELS = set("aeiou")


@register("sound_parts")
class SoundParts(SheetType):
    template = "sound_parts.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        splits, bank = rime_split(sounds()), vocab_by_word()
        family = entry.extra["layout"] == "family"
        items = [{"kind": "word", "word": w, "picture": bank[w].picture,
                  "onset": splits[w][0], "rime": splits[w][1], "new": w in entry.new_words}
                 for w in entry.extra["words"]]
        return SheetContent(title="Words that rhyme" if family else "Say the sounds",
                            parent_tip=ctx.tip("sound_parts_rhyme" if family else self.name), items=items,
                            new_words=list(entry.new_words), review_words=list(entry.review_words))

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = []
        splits = rime_split(sounds())
        if not 2 <= len(sheet.items) <= 3:
            issues.append(error(sheet, f"expected 2–3 cards, got {len(sheet.items)}"))
        for item in sheet.items:
            w, onset, rime = item["word"], item["onset"], item["rime"]
            if onset + rime != w or not onset:
                issues.append(error(sheet, f"{onset!r} + {rime!r} doesn't make {w!r}"))
            if splits.get(w) != (onset, rime):
                issues.append(error(sheet, f"{w!r} split isn't the hand-checked one in content/sounds/"))
            if rime[0] not in VOWELS or VOWELS & set(onset):
                issues.append(error(sheet, f"{w!r}: the rime must start at the vowel"))
        words = [i["word"] for i in sheet.items]
        if len(set(words)) != len(words):
            issues.append(error(sheet, f"the same word twice on one page: {words}"))
        if sheet.title == "Words that rhyme" and len({i["rime"] for i in sheet.items}) != 1:
            issues.append(error(sheet, "a rhyming page must use one rime"))
        return issues
