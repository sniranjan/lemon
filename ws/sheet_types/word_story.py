"""EN 7A-C: one big picture and 2–4 short sentences built from frames, using only known words.

Each sentence ends with a small picture of its word, so a child who can't read yet
can still "read" the line from the pictures.
"""

from __future__ import annotations

import re

from ..content import phrases, stories, vocab_by_word
from ..models import Issue, Sheet
from ..syllabus import level_rank
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

TOKEN = re.compile(r"[A-Za-z']+")


def article(entry) -> str:
    if entry.mass:
        return "some"
    return "an" if entry.word[0] in "aeiou" else "a"


def pick_frames(rng, words: list, story_data: dict) -> list[str]:
    """One frame per word, from its category's frames (or the defaults), no frame twice if avoidable.
    Plural nouns (`plural` in content/phrases/english.yaml) never go in "... is ..." frames."""
    plural = set(phrases().get("plural", []))
    used: set[str] = set()
    chosen = []
    for entry in words:
        options = story_data.get("frames_by_category", {}).get(entry.category) or story_data["frames"]
        if entry.word in plural:
            options = [f for f in options if " is " not in f] or options
        fresh = [f for f in options if f not in used] or options
        frame = rng.choice(fresh)
        used.add(frame)
        chosen.append(frame)
    return chosen


@register("word_story")
class WordStory(SheetType):
    template = "word_story.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        words = list(ctx.plan.for_page(ctx.spec.page).review_words)
        bank = vocab_by_word()
        frames = pick_frames(ctx.rng, [bank[w] for w in words], stories())
        items = [{"kind": "picture", "word": words[0], "picture": bank[words[0]].picture}]
        for frame, w in zip(frames, words):
            before, after = frame.replace("{a}", article(bank[w])).split("{w}")
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
