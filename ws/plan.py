"""Level-wide schedule: what each page of a level will contain, decided up front.

Generators read their page's entry instead of looking at earlier output, so any page range
can be generated on its own and still match a full run. `plan_new_words` fills the
word-introduction sections (7A-A); later planners add review grids and stories.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field

from .models import Level, VocabEntry
from .syllabus import resolve_page


class PagePlan(BaseModel):
    page: int
    new_words: list[str] = Field(default_factory=list)
    review_words: list[str] = Field(default_factory=list)   # strip / grid / story words
    numbers: list[int] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class LevelPlan(BaseModel):
    subject: str
    level: str
    variant: int = 1
    pages: dict[int, PagePlan] = Field(default_factory=dict)

    def for_page(self, page: int) -> PagePlan:
        try:
            return self.pages[page]
        except KeyError:
            raise KeyError(f"{self.level} page {page} isn't planned yet: the word bank doesn't have "
                           f"enough words for it; add words to content/vocab/") from None


def plan_new_words(level: Level, bank: Sequence[VocabEntry], variant: int = 1) -> LevelPlan:
    """Plan the sections that introduce words (rule `new_words_per_sheet` > 0).

    Words are introduced in word-bank order, `new_words_per_sheet` per page, each exactly
    once. Where the section has a `say_it_again` rule, each page from the 4th on gets a strip
    of words introduced `sheets_back` = [lo, hi] pages earlier, preferring the words the strip
    has shown least so far (then the oldest). Pages the bank can't fill yet are left out of
    the plan. Review grids and stories (7A-B/C) are planned with their sheet types.
    """
    plan = LevelPlan(subject=level.subject, level=level.level, variant=variant)
    words = [w.word for w in bank if w.level == level.level]
    next_word = 0
    new_on: dict[int, list[str]] = {}
    strip_count: dict[str, int] = {}

    for page in range(1, level.pages + 1):
        rules = resolve_page(level, page).rules
        n = rules.get("new_words_per_sheet", 0)
        if not n:
            continue
        if next_word + n > len(words):
            break   # bank exhausted: later pages need more words first
        new = words[next_word : next_word + n]
        next_word += n
        new_on[page] = new
        entry = PagePlan(page=page, new_words=new)

        strip = rules.get("say_it_again")
        if strip:
            lo, hi = strip["sheets_back"]
            candidates = [w for back in range(hi, lo - 1, -1) for w in new_on.get(page - back, [])]
            # oldest first, then least-shown first (sort is stable)
            candidates.sort(key=lambda w: strip_count.get(w, 0))
            chosen = candidates[: strip["count"]]
            if len(chosen) == strip["count"]:
                entry.review_words = chosen
                for w in chosen:
                    strip_count[w] = strip_count.get(w, 0) + 1
        plan.pages[page] = entry
    return plan


def plan_review(level: Level, plan: LevelPlan) -> LevelPlan:
    """Plan review sections (grids and stories) on top of the word-introduction plan.

    Each page draws from words already introduced in the sections named by
    `review_from_sections` (default: every earlier section), choosing the words seen least
    so far (new + strip + earlier reviews), oldest first on ties. That is what lets every
    word reach `min_exposures_per_word` even when the strip missed it.
    Grid pages take `words_per_sheet` words; story pages one word per sentence, with the
    sentence count cycling through `sentences_per_story` = [lo, hi] (2, 3, 4, 3, 2, ...).
    """
    seen: dict[str, int] = {}
    intro: dict[str, tuple[int, str]] = {}   # word -> (page, section) where it was new
    for page, entry in sorted(plan.pages.items()):
        for w in entry.new_words:
            seen[w] = seen.get(w, 0) + 1
            intro[w] = (page, resolve_page(level, page).section)
        for w in entry.review_words:
            seen[w] = seen.get(w, 0) + 1

    story_index = 0
    for page in range(1, level.pages + 1):
        spec = resolve_page(level, page)
        rules = spec.rules
        if rules.get("new_words_per_sheet", 0) or page in plan.pages:
            continue
        if "words_per_sheet" in rules:
            n = rules["words_per_sheet"]
        elif "sentences_per_story" in rules:
            lo, hi = rules["sentences_per_story"]
            cycle = list(range(lo, hi + 1)) + list(range(hi - 1, lo, -1))
            n = cycle[story_index % len(cycle)]
            story_index += 1
        else:
            continue
        sources = rules.get("review_from_sections")
        pool = [w for w, (p, sec) in intro.items() if p < page and (sources is None or sec in sources)]
        if len(pool) < n:
            continue   # not enough known words yet (word bank still growing)
        pool.sort(key=lambda w: (seen[w], intro[w][0]))
        chosen = pool[:n]
        for w in chosen:
            seen[w] += 1
        plan.pages[page] = PagePlan(page=page, review_words=chosen)
    return plan
