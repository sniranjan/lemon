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
    # pages the word bank can't fill yet -> why (verify warns about them); used by plan_letters
    waiting: dict[int, str] = Field(default_factory=dict)

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
        if not n or "teams" in rules:   # letter-team pages pick new words by team (ws/phonics.py)
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
        for earlier in range(1, page):   # words this level brought on other kinds of page (letter teams)
            for w in plan.pages[earlier].new_words if earlier in plan.pages else ():
                known.setdefault(w, this_level[w])
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
        for index in range(rules["phrases_per_sheet"]):
            # `level_word_first` (Kittens): the page's first sentence uses one of this level's own words
            want_level_word = rules.get("level_word_first") and index == 0

            def score(c):
                group, frame, fill = c
                words = list(fill.values())
                text = render(frame, fill, known, data)
                return (not any(w in todo for w in words) if todo else False,
                        # the new word's own picture is on its page ("I can hop", not "The bunny can hop.")
                        any(w in todo and this_level[w].picture and w not in pictures_for(fill, data)
                            for w in words),
                        -sum(1 for w in words if w in level_new and seen[w] < min_seen and w not in on_page),
                        bool(want_level_word) and not any(w in this_level for w in words),
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


# --- letters and sounds (5A: rule `planner: letters`) ---------------------------------------------

def rime_split(data: dict) -> dict[str, tuple[str, str]]:
    """word -> (onset, rime) from the hand-checked `rimes` lists in content/sounds/."""
    return {w: (w[: -len(rime)], rime) for rime, words in data.get("rimes", {}).items() for w in words}


def plan_letters(level: Level, bank: Sequence[VocabEntry], data: dict, variant: int = 1) -> LevelPlan:
    """Plan a letters-and-sounds level page by page from the syllabus rules and content/sounds/.

    - letter_trace, rule `letters`: `pages_per_letter` pages per letter (step 1, 2, …), then review
      pages of `review_rows` letters (the part's letters reviewed least first, then earlier ones).
      Rule `review_sets` instead lists the letters of each page (Letter Pairs).
    - sound_parts: `vowels` pages show `cards_per_sheet` onset + rime words with those short vowels,
      different rimes where possible; `families` pages one rhyming family each; `introduce` pages
      bring the next word of this level that has a rime, with its family mates.
    - word_trace: `trace_words` words from `word_set` (short | known | this_level).
    Words are picked least seen first (then list order), so every word keeps coming back. A word of
    this level is new on the first page that shows it. Pages the word bank can't fill yet go in
    `plan.waiting` with the reason.
    """
    from .syllabus import level_rank, page_seed

    usable = {w.word: w for w in bank
              if level_rank(w.level) <= level_rank(level.level) and w.picture and not w.needs_color}
    this_level = [w.word for w in bank if w.level == level.level and w.word in usable]
    this_level_set = set(this_level)
    splits = {w: s for w, s in rime_split(data).items() if w in usable}
    order = {w.word: i for i, w in enumerate(bank)}
    min_seen = level.rules.get("min_exposures_per_word", 0)
    seen: Counter[str] = Counter()
    reviewed: Counter[str] = Counter()     # letters on review rows
    family_uses: Counter[str] = Counter()
    introduced: set[str] = set()
    letters_done: list[str] = []           # letters whose own pages are planned, in teaching order
    prev: set[str] = set()                 # words on the page before
    combos: set[tuple] = set()             # (sheet type, words) already used: no page repeats another
    plan = LevelPlan(subject=level.subject, level=level.level, variant=variant)

    def ready(w: str) -> bool:
        """Earlier levels' words, and this level's words once introduced."""
        return w not in this_level_set or w in introduced

    def letter_words(letter: str) -> list[str]:
        """Words for a letter: known words with its first sound; if fewer than two, this level's new
        words with that sound (they are introduced there: queen for q); else words with the sound inside."""
        starts = [w for w in data["letter_words"].get(letter, []) if w in usable]
        known = [w for w in starts if ready(w)]
        if len(known) >= 2:
            return known
        if len(starts) >= 2:
            return starts
        inside = [w for w in data.get("letter_inside", {}).get(letter, []) if w in usable and ready(w)]
        return known + [w for w in inside if w not in known]

    def least_seen(words: list[str], n: int, avoid: set[str] = frozenset()) -> list[str]:
        pool = [w for w in dict.fromkeys(words) if w not in avoid]
        pool.sort(key=lambda w: (seen[w], words.index(w)))
        return pool[:max(n, 0)]

    for page in range(1, level.pages + 1):
        spec = resolve_page(level, page)
        section = level.section(spec.section)
        rules = spec.rules
        part = section.part_for_page(page)
        offset = page - (part.pages[0] if part else section.pages[0])
        extra: dict[str, Any] = {}
        why = None

        def rank(w: str, page: int = page) -> tuple:
            # least seen, not on the page before, then a fixed shuffle (different for each page and variant)
            return seen[w], w in prev, page_seed(level.subject, level.level, w, page, variant)

        def not_again(words: list[str], ranked: list[str], kind: str = spec.sheet_type) -> list[str]:
            """Swap the last word for the next candidate while this set of words was already a page."""
            spare = [w for w in ranked if w not in words]
            while (kind, frozenset(words)) in combos and spare:
                words = words[:-1] + [spare.pop(0)]
            return words

        if spec.sheet_type == "letter_trace" and "review_sets" in rules:
            letters = rules["review_sets"][page - section.pages[0]]
            rows, used = [], set()
            for letter in letters:
                pick = least_seen(letter_words(letter), 1, used)
                if not pick:
                    why = f"letter {letter} has no approved word yet"
                    break
                used.add(pick[0])
                rows.append({"letter": letter, "word": pick[0]})
            extra = {"layout": "rows", "upper": bool(rules.get("show_upper")), "rows": rows}

        elif spec.sheet_type == "letter_trace":
            letters, per = rules["letters"], rules.get("pages_per_letter", 2)
            if offset < per * len(letters):
                letter, step = letters[offset // per], offset % per + 1
                words = letter_words(letter)
                if len(words) < 2:
                    why = f"letter {letter} needs two approved words (has {len(words)})"
                else:
                    extra = {"layout": "letter", "letter": letter, "step": step, "words": least_seen(words, 2)}
                    if letter not in letters_done:
                        letters_done.append(letter)
            else:
                mine = [x for x in letters if x in letters_done]
                earlier = [x for x in letters_done if x not in letters]
                pool = sorted(mine, key=lambda x: (reviewed[x], mine.index(x))) + \
                    sorted(earlier, key=lambda x: (reviewed[x], earlier.index(x)))
                rows, used = [], set()
                for letter in pool[: rules.get("review_rows", 3)]:
                    pick = least_seen(letter_words(letter), 1, used)
                    used.add(pick[0])
                    rows.append({"letter": letter, "word": pick[0]})
                    reviewed[letter] += 1
                extra = {"layout": "rows", "upper": False, "rows": rows}

        elif spec.sheet_type == "sound_parts":
            n = rules.get("cards_per_sheet", 3)
            if rules.get("families"):
                fams: dict[str, list[str]] = {}
                for w, (_, rime) in splits.items():
                    if not ready(w):
                        continue
                    fams.setdefault(rime, []).append(w)
                fams = {r: ws for r, ws in fams.items() if len(ws) >= 2}
                names = list(fams)
                rime = min(names, key=lambda r: (family_uses[r], names.index(r)))
                family_uses[rime] += 1
                words = sorted(least_seen(fams[rime], n), key=fams[rime].index)
                extra = {"layout": "family", "rime": rime, "words": words}
            else:
                vowels = rules["vowels"]
                pool = [w for w, (_, rime) in splits.items() if rime[0] in vowels and ready(w)]
                words = []
                if rules.get("introduce"):
                    fresh = [w for w in this_level if w in splits and w not in introduced]
                    if not fresh:
                        why = "needs a new short-vowel word (none approved yet)"
                    else:
                        new = fresh[0]
                        rime = splits[new][1]
                        mates = [w for w in pool if splits[w][1] == rime and w != new]
                        due = [w for w in this_level if w in introduced and seen[w] < min_seen and w in pool]
                        words = [new] + least_seen(mates, n - 1)
                        words += least_seen(due, n - len(words), set(words))
                        others = sorted([w for w in pool if w not in words],
                                        key=lambda w: (splits[w][1][0] != rime[0], seen[w], order[w]))
                        words += others[: n - len(words)]
                else:
                    # least seen first, with a different rime on each card where possible
                    ranked = sorted(pool, key=rank)
                    for w in ranked:
                        if len(words) < n and splits[w][1] not in {splits[x][1] for x in words}:
                            words.append(w)
                    words += [w for w in ranked if w not in words][: n - len(words)]
                    words = not_again(words, ranked)
                if not why and len(words) < n:
                    why = f"only {len(words)} approved words with short {'/'.join(vowels)}"
                extra = {"layout": "cards", "words": words}

        elif spec.sheet_type == "word_trace":
            n, lo, hi = rules.get("trace_words", 3), rules.get("min_letters", 1), rules.get("max_letters", 99)
            kind = rules["word_set"]
            if kind == "short":
                pool = [w for w in splits if ready(w)]
            elif kind == "this_level":
                pool = [w for w in this_level if w in introduced]
            else:
                pool = [w for w in usable if w.isalpha() and w.islower()
                        and (w not in this_level or w in introduced)]
            pool = [w for w in pool if lo <= len(w) <= hi]
            pool.sort(key=rank)
            words = not_again(pool[:n], pool)
            if len(words) < n:
                why = ("needs this level's new words (none approved yet)" if kind == "this_level"
                       else f"only {len(words)} approved words fit")
            extra = {"words": words}
        else:
            continue

        if why:
            plan.waiting[page] = why
            continue
        shown = extra.get("words") or [r["word"] for r in extra.get("rows", [])]
        new = [w for w in shown if w in this_level and w not in introduced]
        introduced.update(new)
        seen.update(shown)
        prev = set(shown)
        combos.add((spec.sheet_type, frozenset(shown)))
        plan.pages[page] = PagePlan(page=page, new_words=new, review_words=[w for w in shown if w not in new],
                                    extra=extra)
    return plan
