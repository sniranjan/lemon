"""Letter teams and rhymes (Kittens Reading): hand-checked tables in `content/phonics/english.yaml`.

`plan_phonics` plans the letter-team pages (rule `teams`) and rhyme pages (rule `rhyme_task`) of a
level, like `plan_phrases` does for phrase pages: every page is decided up front from the syllabus, the
word bank and the page's seed, so any page range gives the same sheets as a full run.

New words on letter-team pages are chosen by team, not by word-bank order: a page that brings a new word
takes the next unused word of this level (bank order) that the phonics file lists under one of the
page's teams. Pages with no such word yet stay out of the plan (verify warns until the word bank has them).
"""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Sequence

from .models import Level, VocabEntry
from .plan import LevelPlan, PagePlan
from .syllabus import level_rank, page_seed, resolve_page


# --- the tables ---------------------------------------------------------------------------

def team_spec(data: dict, team: str) -> dict:
    try:
        return data["letter_teams"][team]
    except KeyError:
        raise KeyError(f"letter team {team!r} is not in content/phonics/english.yaml") from None


def split_team(word: str, letters: str, where: str) -> list[str] | None:
    """[before, team, after], with the team at its place in the word (None if it isn't there)."""
    if where == "start":
        i = 0 if word.startswith(letters) else -1
    elif where == "end":
        i = len(word) - len(letters) if word.endswith(letters) else -1
    else:
        i = word.find(letters)
    if i < 0:
        return None
    return [word[:i], letters, word[i + len(letters):]]


def rhyme_group(data: dict, word: str) -> dict | None:
    for g in data.get("rhymes", []):
        if word in g["words"]:
            return g
    return None


def _vowels(s: str) -> set[int]:
    return {i for i, c in enumerate(s) if c in "aeiou"}


def shared_ending(a: str, b: str) -> str:
    """The spelled ending two rhyming words share, if it holds the whole vowel ("at" in cat/hat, "ear"
    in bear/pear); "" when the spelling differs (bear/chair, bed/bread)."""
    n = 0
    while n < min(len(a), len(b)) and a[-1 - n] == b[-1 - n]:
        n += 1
    end = a[len(a) - n:]
    if not end or end[0] not in "aeiou":
        return ""
    for w in (a, b):
        before = w[: len(w) - n]
        if before and before[-1] in "aeiou":   # the vowel team is cut in two (br-e-ad / b-ed)
            return ""
    return end


def usable(entry: VocabEntry) -> bool:
    """Words that can stand on a letter-team or rhyme row: pictured, and not a color word."""
    return bool(entry.picture) and not entry.needs_color


# --- planning -----------------------------------------------------------------------------

def plan_phonics(level: Level, bank: Sequence[VocabEntry], plan: LevelPlan, data: dict) -> LevelPlan:
    if not data or not any(resolve_page(level, p).rules.keys() & {"teams", "rhyme_task"}
                           for p in range(1, level.pages + 1)):
        return plan
    rank = level_rank(level.level)
    known = {w.word: w for w in bank if level_rank(w.level) < rank and usable(w)}
    this_level = [w for w in bank if w.level == level.level and usable(w)]
    min_seen = level.rules.get("min_exposures_per_word", 0)
    state = {"seen": Counter(), "uses": Counter(), "level_new": set(), "used_new": set(), "signatures": set()}

    for page in range(1, level.pages + 1):
        spec = resolve_page(level, page)
        rules = spec.rules
        if "teams" not in rules and "rhyme_task" not in rules:
            continue
        rng = random.Random(page_seed(level.subject, level.level, spec.section, page, plan.variant))
        if "teams" in rules:
            entry = _team_page(page, rules, data, known, this_level, state, min_seen, rng)
        else:
            entry = _rhyme_page(page, rules, data, known, state, rng)
        if entry is not None:
            plan.pages[page] = entry
    return plan


def _ties(rng: random.Random, words) -> dict[str, float]:
    return {w: rng.random() for w in sorted(words)}


def _team_page(page, rules, data, known, this_level, state, min_seen, rng) -> PagePlan | None:
    teams = rules["teams"]
    rows_wanted = rules["rows_per_sheet"]
    per_team = rules.get("team_rows", rows_wanted)
    seen, uses = state["seen"], state["uses"]
    lists = {t: team_spec(data, t)["words"] for t in teams}

    new: list[str] = []
    n_new = rules.get("new_words_per_sheet", 0)
    if n_new:
        fits = [e.word for e in this_level if e.word not in state["used_new"]
                and any(e.word in lists[t] for t in teams)]
        if len(fits) < n_new:
            return None   # the word bank has no new word with this page's team yet
        new = fits[:n_new]
        state["used_new"].update(new)
        state["level_new"].update(new)
        for w in new:
            known[w] = next(e for e in this_level if e.word == w)

    avail = {t: [w for w in lists[t] if w in known] for t in teams}
    tie = _ties(rng, {w for ws in avail.values() for w in ws})
    team_tie = _ties(rng, teams)

    def key(w):   # this level's new words until seen enough, then the least seen
        return (not (w in state["level_new"] and seen[w] < min_seen), seen[w], tie[w])

    rows: list[tuple[str, str]] = [(next(t for t in teams if w in lists[t]), w) for w in new]
    on_page = set(new)
    # this level's words not yet seen enough come back first, whatever their team (each new word must
    # reach `min_exposures_per_word` within its unit)
    due = sorted({w for t in teams for w in avail[t] if w in state["level_new"] and seen[w] < min_seen
                  and w not in on_page}, key=key)
    for w in due[: rows_wanted - len(rows)]:
        rows.append((next(t for t in teams if w in avail[t]), w))
        on_page.add(w)
    first = [t for t, _ in rows]
    order = first + sorted((t for t in teams if t not in first and avail[t]), key=lambda t: (uses[t], team_tie[t]))
    cap = per_team
    while len(rows) < rows_wanted:
        added = False
        for t in order:
            count = sum(1 for r, _ in rows if r == t)
            while count < cap and len(rows) < rows_wanted:
                options = [w for w in avail[t] if w not in on_page]
                if not options:
                    break
                w = min(options, key=key)
                rows.append((t, w))
                on_page.add(w)
                count += 1
                added = True
        if not added:
            if cap >= rows_wanted:
                raise ValueError(f"page {page}: teams {teams} have only {len(on_page)} words he knows; "
                                 f"{rows_wanted} are needed")
            cap += 1

    # never the same set of words twice: swap the last row for its next best word
    task = rules.get("team_task", "trace")
    sig = (task, frozenset(w for _, w in rows))
    if sig in state["signatures"]:
        t, w = rows[-1]
        options = sorted((x for x in avail[t] if x not in on_page), key=key)
        if options and w not in new:
            rows[-1] = (t, options[0])
            sig = (task, frozenset(w for _, w in rows))
    state["signatures"].add(sig)

    # rows of one team stay together (word families come in pairs); groups and rows are shuffled
    groups: dict[str, list[str]] = {}
    for t, w in rows:
        groups.setdefault(t, []).append(w)
    group_list = list(groups.items())
    rng.shuffle(group_list)
    ordered = []
    for t, ws in group_list:
        rng.shuffle(ws)
        ordered += [{"team": t, "word": w} for w in ws]
    for row in ordered:
        seen[row["word"]] += 1
        uses[row["team"]] += 1
    return PagePlan(page=page, new_words=new, review_words=[r["word"] for r in ordered if r["word"] not in new],
                    extra={"rows": ordered})


def _rhyme_page(page, rules, data, known, state, rng) -> PagePlan:
    task = rules["rhyme_task"]
    rows_wanted = rules["rows_per_sheet"]
    k = rules.get("choices", 2)
    seen, uses = state["seen"], state["uses"]
    groups = [dict(g, words=[w for w in g["words"] if w in known]) for g in data["rhymes"]]
    groups = [g for g in groups if len(g["words"]) >= 2]
    tie = _ties(rng, {w for g in groups for w in g["words"]})
    group_tie = _ties(rng, [g["sound"] for g in groups])
    on_page: set[str] = set()
    sounds_on_page: set[str] = set()

    def pick_words(g, n):
        options = sorted((w for w in g["words"] if w not in on_page), key=lambda w: (seen[w], tie[w]))
        return options[:n]

    def best_group(candidates):
        return min(candidates, key=lambda g: (uses["rhyme:" + g["sound"]], group_tie[g["sound"]]))

    rows = []
    for _ in range(rows_wanted):
        g = best_group([g for g in groups if g["sound"] not in sounds_on_page and len(pick_words(g, 2)) == 2])
        sounds_on_page.add(g["sound"])
        uses["rhyme:" + g["sound"]] += 1
        a, b = pick_words(g, 2)
        on_page.update((a, b))
        if task == "pair":
            rows.append({"words": [a, b]})
            continue
        others = []
        for _ in range(k - 1 if task == "pick" else 1):
            d = best_group([o for o in groups if o["vowel"] != g["vowel"] and o["sound"] not in sounds_on_page
                            and pick_words(o, 1)])
            sounds_on_page.add(d["sound"])
            w = pick_words(d, 1)[0]
            on_page.add(w)
            others.append(w)
        if task == "pick":   # "cat": which one rhymes, hat or sun?
            pos = rng.randrange(k)
            rows.append({"prompt": a, "choices": others[:pos] + [b] + others[pos:], "answer": b})
        else:                # odd one out: cat, hat, sun
            pos = rng.randrange(3)
            pair = [a, b]
            rows.append({"choices": pair[:pos] + others + pair[pos:], "answer": others[0]})
    if task != "pair" and len(rows) > 1:
        positions = [r["choices"].index(r["answer"]) for r in rows]
        if len(set(positions)) == 1:   # the answer is never in the same place on every row
            r = rows[-1]
            c = r["choices"]
            i = positions[-1]
            j = (i + 1) % len(c)
            c[i], c[j] = c[j], c[i]
    words = [w for r in rows for w in ([r["prompt"]] if "prompt" in r else []) + r.get("choices", r.get("words", []))]
    for w in words:
        seen[w] += 1
    return PagePlan(page=page, review_words=list(dict.fromkeys(words)), extra={"rows": rows})
