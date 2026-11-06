"""Level-wide schedule: what each page of a level will contain, decided up front.

Generators read their page's entry instead of looking at earlier output, so any page range
can be generated on its own and still match a full run. `plan_new_words` fills the
word-introduction sections (7A-A); later planners add review grids and stories.
"""

from __future__ import annotations

from collections import Counter
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


def level_exposures(subject: str, levels: Sequence[str], bank: Sequence[VocabEntry]) -> Counter[str]:
    """How many pages of each earlier level's plan (variant 1) show each word: new card, strip,
    grid or story. Built fresh, so the earlier level's own plan objects are never touched."""
    from .syllabus import load_level

    counts: Counter[str] = Counter()
    for code in levels:
        earlier = load_level(subject, code)
        plan = plan_review(earlier, plan_new_words(earlier, bank), bank)
        counts.update(w for p in plan.pages.values() for w in p.new_words + p.review_words)
    return counts


def plan_review(level: Level, plan: LevelPlan, bank: Sequence[VocabEntry] = ()) -> LevelPlan:
    """Plan review sections (grids and stories) on top of the word-introduction plan.

    Each page draws from words already introduced in the sections named by
    `review_from_sections` (default: every earlier section), choosing the words seen least
    so far (new + strip + earlier reviews), oldest first on ties. That is what lets every
    word reach `min_exposures_per_word` even when the strip missed it.
    `review_from_levels` pages (6A-A Word Hunt) review an earlier level's words instead, least
    seen in that level's own plan first, then word-bank order.
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
    prior: Counter[str] | None = None   # sightings in the reviewed earlier level(s), for `review_from_levels`
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
        from_levels = rules.get("review_from_levels")
        if from_levels:
            earlier = [w.word for w in bank if w.level in from_levels]
            if prior is None:
                prior = level_exposures(level.subject, from_levels, bank)
            for i, w in enumerate(earlier):
                intro.setdefault(w, (i - len(earlier), ""))   # before page 1, in bank order
                seen.setdefault(w, prior.get(w, 0))           # least seen in the earlier level first
            pool = earlier
        else:
            pool = [w for w, (p, sec) in intro.items() if p < page and (sources is None or sec in sources)]
        if len(pool) < n:
            continue   # not enough known words yet (word bank still growing)
        pool.sort(key=lambda w: (seen[w], intro[w][0]))
        chosen = pool[:n]
        for w in chosen:
            seen[w] += 1
        plan.pages[page] = PagePlan(page=page, review_words=chosen)
    return plan


def plan_phrases(level: Level, bank: Sequence[VocabEntry], plan: LevelPlan, data: dict) -> LevelPlan:
    """Plan phrase and sentence pages (6A-B/C): rule `phrase_groups` names the frame groups.

    Each page gets `phrases_per_sheet` phrases (`phrase_kind`: phrase | sentence) from the
    groups' frames, filled with known words: every word of earlier levels, plus this level's
    words introduced on this page or before. A page that introduces new words uses each of them
    in one phrase; pages the word bank can't fill yet stay out of the plan. Otherwise the
    planner prefers this level's new words until they have been seen `min_exposures_per_word`
    times, then phrases not used yet, words not already on the page, a different frame group for each
    phrase, words seen least so far, and frames used least, so words keep coming back and the sheets don't repeat. Ties are
    broken by the page's seed, so a variant gets different (equally good) phrases.
    """
    import random

    from .phrases import fillings, picture_size, pictures_for, render
    from .syllabus import level_rank, page_seed

    rank = level_rank(level.level)
    known: dict[str, VocabEntry] = {w.word: w for w in bank if level_rank(w.level) < rank}
    this_level = {w.word: w for w in bank if w.level == level.level}
    # sightings so far on other pages (grids, cards); phrase pages are counted as they are planned
    seen: Counter[str] = Counter(w for page, p in plan.pages.items() for w in p.new_words + p.review_words
                                 if not resolve_page(level, page).rules.get("phrase_groups"))
    text_uses: Counter[str] = Counter()
    frame_uses: Counter[str] = Counter()
    min_seen = level.rules.get("min_exposures_per_word", 0)
    level_new: set[str] = set()   # this level's words introduced so far: first in line until seen min_seen times

    for page in range(1, level.pages + 1):
        spec = resolve_page(level, page)
        rules = spec.rules
        groups = rules.get("phrase_groups")
        if not groups:
            continue
        entry = plan.pages.get(page)
        if rules.get("new_words_per_sheet", 0) and entry is None:
            continue   # the word bank can't introduce this page's new words yet
        entry = entry or PagePlan(page=page)
        for w in entry.new_words:
            known[w] = this_level[w]
            level_new.add(w)
        kind = rules.get("phrase_kind", "phrase")
        frame_bank = data["phrase_groups" if kind == "phrase" else "sentence_groups"]
        candidates = [(g, f, fill) for g in groups for f in frame_bank[g] for fill in fillings(f, data, known)]
        rng = random.Random(page_seed(level.subject, level.level, spec.section, page, plan.variant))
        todo = list(entry.new_words)
        on_page: list[str] = []
        frames_on_page: set[str] = set()
        groups_on_page: set[str] = set()
        phrases = []
        for _ in range(rules["phrases_per_sheet"]):
            def score(c):
                group, frame, fill = c
                words = list(fill.values())
                text = render(frame, fill, known, data)
                return (not any(w in todo for w in words) if todo else False,
                        # the new word's own picture is on its page ("I can hop", not "The bunny can hop.")
                        any(w in todo and this_level[w].picture and w not in pictures_for(fill, data)
                            for w in words),
                        -sum(1 for w in words if w in level_new and seen[w] < min_seen and w not in on_page),
                        text_uses[text],
                        any(w in on_page for w in words),
                        group in groups_on_page,
                        frame in frames_on_page,
                        sum(seen[w] for w in words) / len(words),
                        frame_uses[frame])
            if not candidates:
                raise ValueError(f"{level.level} page {page}: no phrase fits groups {groups} with the known words")
            shuffled = candidates[:]
            rng.shuffle(shuffled)
            group, frame, fill = min(shuffled, key=score)
            words = list(fill.values())
            text = render(frame, fill, known, data)
            phrase = {"frame": frame, "slots": dict(fill), "text": text,
                      "words": words, "pictures": pictures_for(fill, data)}
            if picture_size(fill):
                phrase["picture_size"] = picture_size(fill)
            phrases.append(phrase)
            text_uses[text] += 1
            frame_uses[frame] += 1
            frames_on_page.add(frame)
            groups_on_page.add(group)
            todo = [w for w in todo if w not in words]
            for w in words:
                seen[w] += 1
                on_page.append(w)
        if todo:
            raise ValueError(f"{level.level} page {page}: new word(s) {todo} fit no frame in groups {groups}; "
                             f"add a slot kind or frame for them in content/phrases/")
        review = [w for w in dict.fromkeys(on_page) if w not in entry.new_words]
        plan.pages[page] = PagePlan(page=page, new_words=list(entry.new_words), review_words=review,
                                    extra={"phrases": phrases})
    return plan


def plan_spelling(level: Level, bank: Sequence[VocabEntry], plan: LevelPlan, data: dict) -> LevelPlan:
    """Plan Puppies Reading (3A) pages from the hand-checked tables in content/phonics/english.yaml.

    Only levels with a `known_levels` rule use it. Each page's cards come from one table, chosen by
    the page's rules: `patterns` (Word Patterns), `endings` (Word Endings), `syllable_kinds` (Clap the
    Parts) or `sentence_words` (Copy a Sentence). A card's word must be pictured and known on that page:
    a word of the `known_levels`, or one of this level's words introduced on an earlier page (the
    page's own new word is always its first card). Among the rest the planner prefers variety on the
    page (different patterns, endings, spelling rules, syllable kinds), then this level's words, then
    words seen least, then word-bank order; the page's seed breaks ties, so a variant differs.
    Copy sentences are the `sentences:` of this level's words, each used as rarely as possible.
    """
    import random

    from .phonics import pattern_span, sentence_tokens, spelling_rule, syllable_table, tail
    from .syllabus import page_seed

    known_levels = level.rules.get("known_levels")
    if not known_levels:
        return plan
    entries = {w.word: w for w in bank}
    order = {w.word: i for i, w in enumerate(bank)}
    earlier = {w.word for w in bank if w.level in known_levels}
    mine = [w.word for w in bank if w.level == level.level]
    intro = {w: page for page, p in plan.pages.items() for w in p.new_words}
    seen: Counter[str] = Counter()
    text_uses: Counter[str] = Counter()
    syllables = syllable_table(data)
    used_sets: set[frozenset] = set()   # word sets of earlier pages: no page repeats another

    def usable(w: str, page: int) -> bool:
        e = entries.get(w)
        return bool(e and e.picture) and (w in earlier or (w in intro and intro[w] < page))

    def weight(w: str) -> tuple:
        # this level's words count as seen two fewer times, so they come back first
        return ((seen[w] - 2) if w in intro else seen[w], order.get(w, 0))

    for page in range(1, level.pages + 1):
        spec = resolve_page(level, page)
        rules = spec.rules
        kind = next((k for k in ("patterns", "endings", "syllable_kinds", "sentence_words") if k in rules), None)
        if kind is None:
            continue
        entry = plan.pages.get(page)
        if rules.get("new_words_per_sheet", 0) and entry is None:
            continue   # the word bank can't introduce this page's new word yet
        new = list(entry.new_words) if entry else []
        rng = random.Random(page_seed(level.subject, level.level, spec.section, page, plan.variant))
        cards: list[dict] = []

        def pick(options: list, key):
            options = options[:]
            rng.shuffle(options)
            word = (lambda o: o) if options and isinstance(options[0], str) else (lambda o: o[0])
            n = rules.get("cards_per_sheet") or rules["sentences_per_sheet"]
            if len(cards) == n - 1:   # the last card must not make a page seen before
                taken = frozenset(c["word"] for c in cards)
                fresh = [o for o in options if taken | {word(o)} not in used_sets]
                options = fresh or options
            return min(options, key=key) if options else None

        def need(n: int, what: str):
            if n:
                return
            raise ValueError(f"{level.level} page {page}: not enough known words for {what}")

        if kind == "patterns":
            codes = rules["patterns"]
            covered: set[str] = set()
            for w in new:
                code = next((c for c in data["pattern_words"].get(w, []) if c in codes), None)
                if code is None:
                    raise ValueError(f"{level.level} page {page}: new word {w!r} has none of the patterns {codes}")
                cards.append({"word": w, "picture": entries[w].picture, "pattern": code})
                covered.add(code)
            pool = [(w, c) for w, cs in data["pattern_words"].items() for c in cs
                    if c in codes and usable(w, page) and pattern_span(w, c, data)]
            while len(cards) < rules["cards_per_sheet"]:
                taken = {c["word"] for c in cards}
                options = [o for o in pool if o[0] not in taken]
                need(len(options), f"the patterns {codes}")
                w, code = pick(options, lambda o: (o[1] in covered, *weight(o[0])))
                cards.append({"word": w, "picture": entries[w].picture, "pattern": code})
                covered.add(code)
        elif kind == "endings":
            wanted = rules["endings"]
            pool = [(b, e, f) for b, forms in data["endings"].items() for e, f in (forms or {}).items()
                    if e in wanted and usable(b, page)]
            rules_on_page: set[tuple] = set()
            ends_on_page: list[str] = []
            while len(cards) < rules["cards_per_sheet"]:
                taken = {c["word"] for c in cards}
                options = [o for o in pool if o[0] not in taken]
                need(len(options), f"the endings {wanted}")
                b, e, f = pick(options, lambda o: (ends_on_page.count(o[1]),
                                                   (o[1], spelling_rule(*o)) in rules_on_page, *weight(o[0])))
                cards.append({"word": b, "picture": entries[b].picture, "ending": e, "form": f,
                              "tail": tail(b, e, f), "rule": spelling_rule(b, e, f)})
                rules_on_page.add((e, spelling_rule(b, e, f)))
                ends_on_page.append(e)
        elif kind == "syllable_kinds":
            kinds = rules["syllable_kinds"]
            pool = [w for w, (k, _) in syllables.items() if k in kinds and usable(w, page)]
            kinds_on_page: list[str] = []
            while len(cards) < rules["cards_per_sheet"]:
                taken = {c["word"] for c in cards}
                options = [w for w in pool if w not in taken]
                need(len(options), f"the syllable kinds {kinds}")
                w = pick(options, lambda w: (kinds_on_page.count(syllables[w][0]), *weight(w)))
                k, syls = syllables[w]
                cards.append({"word": w, "picture": entries[w].picture, "syllables": list(syls)})
                kinds_on_page.append(k)
        else:
            lo, hi = rules["sentence_words"]
            marks = rules.get("end_marks", ["."])
            pool = [(w, s) for w in mine if usable(w, page) for s in entries[w].sentences
                    if lo <= len(sentence_tokens(s)) <= hi and s[-1:] in marks]
            while len(cards) < rules["sentences_per_sheet"]:
                taken = {c["word"] for c in cards}
                options = [o for o in pool if o[0] not in taken]
                need(len(options), f"copy sentences of {lo}–{hi} words ending {marks}")
                w, s = pick(options, lambda o: (text_uses[o[1]], *weight(o[0])))
                cards.append({"word": w, "picture": entries[w].picture, "text": s})
                text_uses[s] += 1
        words = [c["word"] for c in cards]
        used_sets.add(frozenset(words))
        for w in words:
            seen[w] += 1
        review = [w for w in dict.fromkeys(words) if w not in new]
        plan.pages[page] = PagePlan(page=page, new_words=new, review_words=review, extra={"cards": cards})
    return plan
