"""EN 7A-C: one big picture and 2–4 short sentences built from frames, using only known words.

Each sentence ends with a small picture of its word, so a child who can't read yet
can still "read" the line from the pictures.
"""

from __future__ import annotations

import re

from ..content import phrases, stories, vocab_by_word
from ..phrases import ownable
from ..models import Issue, Sheet
from ..syllabus import level_rank
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

TOKEN = re.compile(r"[A-Za-z']+")


def article(entry) -> str:
    if entry.mass:
        return "some"
    return "an" if entry.word[0] in "aeiou" else "a"


OWNS = re.compile(r"\b(my|have)\b")


def frame_options(entry, story_data: dict, phrase_data: dict) -> list[str]:
    """The frames that say something true about this word (see content/stories/english.yaml):
    its own frames, else its category's, else the defaults; "my" / "I have" only for things a child
    can have; no "I can" for what a 3-year-old can't do; plural nouns never in "... is ...";
    "the sun", never "a sun"."""
    own = story_data.get("frames_by_word", {}).get(entry.word)   # hand-written for this word: "I wash my hand."
    options = own or story_data.get("frames_by_category", {}).get(entry.category) or story_data["frames"]
    keep = []
    for f in options:
        if (OWNS.search(f) and not own and entry.category not in story_data.get("my_categories", [])
                and entry.word not in ownable(phrase_data)):
            continue
        if f.startswith("I can {w}") and entry.word in phrase_data.get("child_cannot", []):
            continue
        if " is " in f and entry.word in phrase_data.get("plural", []):
            continue
        if "{a}" in f and entry.word in phrase_data.get("the_only", []):
            continue
        keep.append(f)
    if not keep:
        raise ValueError(f"no story frame fits {entry.word!r}; add frames for it in content/stories/english.yaml")
    return keep


def story_sentences(entry, story_data: dict, phrase_data: dict) -> list[str]:
    """Every sentence a story may say about this word."""
    return [f.replace("{a}", article(entry)).replace("{w}", entry.word)
            for f in frame_options(entry, story_data, phrase_data)]


def pick_frames(rng, words: list, story_data: dict) -> list[str]:
    """One frame per word from `frame_options`, no frame twice if avoidable."""
    phrase_data = phrases()
    used: set[str] = set()
    chosen = []
    for entry in words:
        options = frame_options(entry, story_data, phrase_data)
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
        bank, story_data, phrase_data = vocab_by_word(), stories(), phrases()
        issues = []
        for s in (i for i in sheet.items if i["kind"] == "sentence"):
            entry = bank.get(s["word"])
            if entry is not None and s["text"] not in story_sentences(entry, story_data, phrase_data):
                issues.append(error(sheet, f"story sentence doesn't fit {s['word']!r}: {s['text']!r}"))
            unknown = [t for t in TOKEN.findall(s["text"]) if t.lower() not in allowed and t not in known]
            if unknown:
                issues.append(error(sheet, f"story uses unknown words {unknown}: {s['text']!r}"))
        if sheet.items[0]["word"] not in sheet.review_words:
            issues.append(error(sheet, "story picture is not one of the story words"))
        return issues
