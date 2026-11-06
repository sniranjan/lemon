"""Planning for the read-and-write sections (Cubs Reading, english 2A): picture puzzles, kinds of
words and read-aloud passages. Part of the level-wide plan (CLAUDE.md §5), so any page range gives the
same sheets as a full run.

Pages are picked up by their rules, not by level code:
- `puzzle: missing | crossword` (word_puzzle): words from `puzzle_words` in content/grammar/english.yaml.
- `word_kinds: pick | sort | fill` (word_sort): naming / doing / describing words from the hand-checked
  `kinds` lists, and fill-in sentences from `fill`.
- `passage_words: [lo, hi]` (read_aloud): passages from content/passages/english.yaml, in file order,
  each read on `passage_reads` pages in a row with different questions.

Words are chosen least seen first: this level's new words until they reach `min_exposures_per_word`, then
whatever has been shown least on this level's pages. Ties are broken by the page's seed, so a variant gets
different (equally good) pages.
"""

from __future__ import annotations

import random
import re
from collections import Counter
from collections.abc import Sequence

from .models import Level, VocabEntry
from .plan import LevelPlan, PagePlan
from .syllabus import level_rank, page_seed, resolve_page

KINDS = ("naming", "doing", "describing")
VOWELS = set("aeiou")
WORD = re.compile(r"[A-Za-z']+")


# --- helpers shared with the sheet types' verify ------------------------------------------------

def kind_of(word: str, grammar: dict) -> str | None:
    for kind in KINDS:
        if word in grammar["kinds"][kind]:
            return kind
    return None


def distractor_kinds(kind: str) -> list[str]:
    """Kinds the wrong fill-in choice may come from. A describing blank often sits before a noun
    ("a ___ hug"), where a naming word could read as right ("a bear hug"): only doing words there."""
    return ["doing"] if kind == "describing" else [k for k in KINDS if k != kind]


def sentences(text: str) -> list[str]:
    """Split a passage into sentences (a closing quote stays with its sentence)."""
    return [s for s in re.split(r'(?<=[.!?])"?\s+(?=["A-Z])', text.strip()) if s]


def word_count(text: str) -> int:
    return len(WORD.findall(text))


def forms(word: str) -> set[str]:
    """The word and its everyday inflections: skip → skips, skipped, skipping; carry → carries, carried."""
    out = {word, word + "s", word + "es", word + "ed", word + "ing", word + "d"}
    if word.endswith("y"):
        out |= {word[:-1] + "ies", word[:-1] + "ied"}
    if word.endswith("e"):
        out |= {word[:-1] + "ing"}
    if len(word) >= 3 and word[-1] not in "aeiouwxy" and word[-2] in "aeiou" and word[-3] not in "aeiou":
        out |= {word + word[-1] + "ed", word + word[-1] + "ing"}
    if word == "leaf":
        out.add("leaves")
    return out


def mentions(text: str, word: str) -> bool:
    tokens = {t.lower() for t in WORD.findall(text)}
    return bool(tokens & forms(word))


def in_text(phrase: str, text: str) -> bool:
    """`phrase` appears word for word in `text` (case-insensitive, whole words)."""
    return re.search(r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)", text.lower()) is not None


# --- the planner -----------------------------------------------------------------------------

class _Picker:
    """Least-seen choice with seeded ties."""

    def __init__(self, seen: Counter, level_words: set[str], min_seen: int, rng: random.Random):
        self.seen, self.level_words, self.min_seen, self.rng = seen, level_words, min_seen, rng

    def due(self, word: str) -> bool:
        """A new word of this level that hasn't reached its sightings yet."""
        return word in self.level_words and self.seen[word] < self.min_seen

    def order(self, words: Sequence[str]) -> list[str]:
        pool = list(dict.fromkeys(words))
        self.rng.shuffle(pool)
        return sorted(pool, key=lambda w: (not self.due(w), self.seen[w]))


def plan_reading(level: Level, bank: Sequence[VocabEntry], plan: LevelPlan, grammar: dict,
                 passages: dict) -> LevelPlan:
    """Fill puzzle, word-kind and passage pages into the plan (new words are already planned)."""
    rank = level_rank(level.level)
    known: list[str] = [w.word for w in bank if level_rank(w.level) < rank]
    level_words = {w.word for w in bank if w.level == level.level}
    min_seen = level.rules.get("min_exposures_per_word", 0)
    seen: Counter[str] = Counter()
    puzzle_use: Counter[str] = Counter()
    fill_use: Counter[str] = Counter()
    passage_page = 0

    for page in range(1, level.pages + 1):
        spec = resolve_page(level, page)
        rules = spec.rules
        if not ({"puzzle", "word_kinds", "passage_words"} & set(rules)):
            continue
        entry = plan.pages.get(page)
        if rules.get("new_words_per_sheet", 0) and entry is None:
            continue   # the word bank can't introduce this page's new word yet
        new = list(entry.new_words) if entry else []
        known += [w for w in new if w not in known]
        rng = random.Random(page_seed(level.subject, level.level, spec.section, page, plan.variant))
        pick = _Picker(seen, level_words, min_seen, rng)
        extra: dict = {}
        if "puzzle" in rules:
            extra["puzzles"] = _puzzles(rules, grammar, set(known), puzzle_use, rng)
            shown = [w for p in extra["puzzles"] for w in p["words"]]
        elif "word_kinds" in rules:
            extra, shown = _word_kinds(rules, grammar, known, new, pick, fill_use, page)
        else:
            extra["passage"], shown = _passage(rules, passages, passage_page, rng, level.level, page)
            passage_page += 1
        for w in dict.fromkeys(shown):
            seen[w] += 1
        for w in new:
            if w not in shown:
                raise ValueError(f"{level.level} page {page}: new word {w!r} isn't used on its page")
        review = [w for w in dict.fromkeys(shown) if w not in new]
        plan.pages[page] = PagePlan(page=page, new_words=new, review_words=review, extra=extra)
    return plan


# --- picture puzzles ---------------------------------------------------------------------------

def _puzzle_pool(rules: dict, grammar: dict, known: set[str]) -> list[str]:
    lo, hi = rules["word_length"]
    return [w for w in grammar["puzzle_words"] if w in known and lo <= len(w) <= hi]


def blank_positions(word: str, rules: dict, rng: random.Random) -> list[int]:
    blanks = rules["blanks"]
    if blanks == "all_but_first":
        return list(range(1, len(word)))
    if rules.get("blank_letters") == "vowels":
        # a sounded vowel: never a silent final e ("nos_" for nose), the first letter only if it's the only vowel
        vowels = [i for i, ch in enumerate(word) if ch in VOWELS and not (ch == "e" and i == len(word) - 1)]
        options = [i for i in vowels if i > 0] or vowels
    else:
        options = list(range(1, len(word)))
    return sorted(rng.sample(options, blanks))


def _puzzles(rules: dict, grammar: dict, known: set[str], use: Counter, rng: random.Random) -> list[dict]:
    pool = _puzzle_pool(rules, grammar, known)
    rng.shuffle(pool)
    pool.sort(key=lambda w: use[w])
    out = []
    if rules["puzzle"] == "missing":
        for w in pool[: rules["puzzle_items"]]:
            out.append({"words": [w], "blanks": blank_positions(w, rules, rng)})
            use[w] += 1
        return out
    on_page: set[str] = set()
    for _ in range(rules["puzzle_items"]):
        layout = None
        for across in [w for w in pool if w not in on_page]:
            downs = [d for d in pool if d not in on_page and d != across and set(d) & set(across)]
            downs.sort(key=lambda d: use[d])
            for down in downs:
                crossings = [(i, j) for i, a in enumerate(across) for j, d in enumerate(down) if a == d]
                if crossings:
                    i, j = rng.choice(crossings)
                    layout = {"words": [across, down], "across_row": j, "down_col": i}
                    break
            if layout:
                break
        if layout is None:
            raise ValueError("no two puzzle words cross; add puzzle_words")
        out.append(layout)
        for w in layout["words"]:
            use[w] += 1
            on_page.add(w)
        pool.sort(key=lambda w: use[w])
    return out


def crossword_grid(across: str, down: str, across_row: int, down_col: int, given: list[str]) -> list[list]:
    """Rows of cells: None (no square) or {"ch": letter, "given": bool}."""
    grid: list[list] = [[None] * len(across) for _ in down]
    for i, ch in enumerate(across):
        grid[across_row][i] = {"ch": ch, "given": ("first" in given and i == 0)}
    for j, ch in enumerate(down):
        cell = grid[j][down_col]
        first = "first" in given and j == 0
        if cell is None:
            grid[j][down_col] = {"ch": ch, "given": first}
        else:
            cell["given"] = cell["given"] or first or "shared" in given
    return grid


# --- kinds of words ------------------------------------------------------------------------------

def _known_of(kind: str, grammar: dict, known: list[str]) -> list[str]:
    k = set(known)
    return [w for w in grammar["kinds"][kind] if w in k]


def _word_kinds(rules: dict, grammar: dict, known: list[str], new: list[str], pick: _Picker,
                fill_use: Counter, page: int) -> tuple[dict, list[str]]:
    layout = rules["word_kinds"]
    for w in new:
        if kind_of(w, grammar) is None:
            raise ValueError(f"new word {w!r} has no kind in content/grammar/english.yaml")
    on_page: list[str] = list(new)
    shown: list[str] = []

    def take(kinds: Sequence[str], exclude=()) -> str:
        pool = [w for kind in kinds for w in _known_of(kind, grammar, known) if w not in exclude]
        fresh = [w for w in pool if w not in on_page]
        word = pick.order(fresh or pool)[0]
        on_page.append(word)
        return word

    if layout == "pick":
        target = rules["target"]
        others = [k for k in KINDS if k != target]
        rows = []
        for r in range(rules["rows"]):
            if r == 0 and new:
                if kind_of(new[0], grammar) != target:
                    raise ValueError(f"page {page}: new word {new[0]!r} is not a {target} word")
                answer = new[0]
            else:
                answer = take([target])
            row = [answer, take(others), take(others)]
            pick.rng.shuffle(row)
            rows.append({"words": row, "answer": answer})
        pick.rng.shuffle(rows)
        shown = [w for r in rows for w in r["words"]]
        return {"rows": rows, "target": target}, shown

    if layout == "sort":
        words = list(new)
        for kind in KINDS:
            have = sum(1 for w in words if kind_of(w, grammar) == kind)
            for _ in range(rules["sort_words"] // len(KINDS) - have):
                words.append(take([kind]))
        pick.rng.shuffle(words)
        return {"sort": [{"word": w, "kind": kind_of(w, grammar)} for w in words]}, words

    if layout == "fill":
        target = rules["target"]
        n = rules["fill_sentences"]
        kinds = [target] * n if target != "mixed" else [KINDS[(page + i) % len(KINDS)] for i in range(n)]
        items = []
        for kind in kinds:
            k = set(known)
            options = [s for s in grammar["fill"][kind] if s["answer"] in k
                       and s["answer"] not in on_page and s["text"] not in [i["text"] for i in items]]
            if not options:
                raise ValueError(f"page {page}: no fill-in {kind} sentence left with known words")
            pick.rng.shuffle(options)
            sentence = min(options, key=lambda s: (not pick.due(s["answer"]), fill_use[s["text"]],
                                                   pick.seen[s["answer"]]))
            answer = sentence["answer"]
            on_page.append(answer)
            other = take(distractor_kinds(kind), exclude=[answer])
            choices = [answer, other]
            pick.rng.shuffle(choices)
            fill_use[sentence["text"]] += 1
            items.append({"text": sentence["text"], "answer": answer, "kind": kind, "choices": choices})
        shown = [w for i in items for w in i["choices"]]
        return {"fill": items}, shown

    raise ValueError(f"unknown word_kinds layout {layout!r}")


# --- read-aloud passages ---------------------------------------------------------------------------

def _passage(rules: dict, data: dict, index: int, rng: random.Random, level: str, page: int) -> tuple[dict, list[str]]:
    reads = rules.get("passage_reads", 1)
    passages = data["passages"]
    n_passage, read = divmod(index, reads)
    if n_passage >= len(passages):
        raise KeyError(f"{level} page {page} needs passage {n_passage + 1}, but content/passages/ has "
                       f"{len(passages)}; write more passages")
    p = passages[n_passage]
    n = rules["questions_per_sheet"]
    qs = p["questions"][read * n:(read + 1) * n]
    if len(qs) < n:
        raise ValueError(f"passage {p['id']!r} needs {n * reads} questions for {reads} readings, has "
                         f"{len(p['questions'])}")
    questions = []
    for q in qs:
        choices = [q["a"], *q["wrong"][: rules.get("choices", 3) - 1]]
        rng.shuffle(choices)
        questions.append({"q": q["q"], "answer": q["a"], "choices": choices})
    return {"id": p["id"], "read": read + 1, "reads": reads, "questions": questions}, list(p.get("words", []))
