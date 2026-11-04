"""EN 7A-C: one big picture and 2–4 short sentences built from frames, using only known words.

Each sentence ends with a small picture of its word, so a child who can't read yet
can still "read" the line from the pictures.
"""

from __future__ import annotations

import re

from ..content import stories, vocab_by_word
from ..models import Issue, Sheet
from ..syllabus import level_rank
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

TOKEN = re.compile(r"[A-Za-z']+")


def article(word: str) -> str:
    return "an" if word[0] in "aeiou" else "a"


@register("word_story")
class WordStory(SheetType):
    template = "word_story.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        words = list(ctx.plan.for_page(ctx.spec.page).review_words)
        frames = ctx.rng.sample(stories()["frames"], len(words))
        bank = vocab_by_word()
        items = [{"kind": "picture", "word": words[0], "picture": bank[words[0]].picture}]
        for frame, w in zip(frames, words):
            before, after = frame.replace("{a}", article(w)).split("{w}")
            items.append({"kind": "sentence", "word": w, "picture": bank[w].picture,
                          "before": before, "after": after, "text": f"{before}{w}{after}"})
        return SheetContent(
            title="Read together",
            parent_tip=ctx.tip(self.name),
            items=items,
            review_words=words,
        )

    def verify(self, sheet: Sheet) -> list[Issue]:
        allowed = {w.lower() for w in stories()["allowed_words"]}
        known = {w for w, e in vocab_by_word().items() if level_rank(e.level) <= level_rank(sheet.level)}
        issues = []
        for s in (i for i in sheet.items if i["kind"] == "sentence"):
            unknown = [t for t in TOKEN.findall(s["text"]) if t.lower() not in allowed and t not in known]
            if unknown:
                issues.append(error(sheet, f"story uses unknown words {unknown}: {s['text']!r}"))
        if sheet.items[0]["word"] not in sheet.review_words:
            issues.append(error(sheet, "story picture is not one of the story words"))
        return issues
