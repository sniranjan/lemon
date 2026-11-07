"""Greek and Latin word roots (Penguins Reading section C, rule `roots`, sheet type `word_roots`).

Content (hand-checked): `content/wordroots/<level>.yaml`, a list of `roots`, in teaching order. Each root has
- `root`: as printed (`spect`, `chron`), `origin` (Latin or Greek) and `meaning` ("look, see");
- `words`: 4 grade-level words built on it, each with a short `meaning` (the first is the card's example;
  the second and third are matched on the root's teaching page; the fourth on its review page);
- `sentences`: 2 sentences with one blank (`___`): the first for word 2 or 3 (teaching page), the second for
  word 4 (review page);
- `explain`: a fifth word the child hasn't seen on the page, with a `sample` answer and a `rubric`
  ("Use the root to explain what ... means"). Only the roots that are explained have one (see below).

Pages (planned up front, so any page range builds the same sheets): part 1 (`roots_per_page: 2`) takes
two roots a page in file order and explains one of them (the first on the part's odd pages, the second on
the even ones); part 2 (`review: true`, `roots_per_page: 4`) reviews four roots a page in the same order, with
their fourth words, the second sentences of the two already explained, and the explanation of the first root
that wasn't (so 30 of the 40 roots carry an `explain`: one a page).
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

from .content import CONTENT_DIR
from .models import Level
from .plan import LevelPlan, PagePlan

BLANK = "___"
LETTERS = "ABCD"
MAX_MEANING = 44      # characters: a matching meaning stays on one line at 20px
MAX_SENTENCE = 70     # characters: a fill-in sentence (with its blank line) takes at most two lines at 20px


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RootWord(_Strict):
    word: str
    meaning: str


class RootSentence(_Strict):
    word: str
    text: str


class Explain(_Strict):
    word: str
    sample: str
    rubric: str


class Root(_Strict):
    root: str
    origin: Literal["Latin", "Greek"]
    meaning: str
    words: list[RootWord]
    sentences: list[RootSentence]
    explain: Explain | None = None

    @model_validator(mode="after")
    def _shape(self) -> Root:
        if len(self.words) != 4 or len({w.word for w in self.words}) != 4:
            raise ValueError(f"root {self.root}: needs 4 different words")
        if len(self.sentences) != 2:
            raise ValueError(f"root {self.root}: needs 2 sentences")
        return self


@lru_cache(maxsize=None)
def _load(level: str) -> tuple[dict, ...]:
    path = CONTENT_DIR / "wordroots" / f"{level}.yaml"
    return tuple((yaml.safe_load(path.read_text()) or {}).get("roots", [])) if path.exists() else ()


def level_roots(level: str) -> list[Root]:
    return [Root.model_validate(r) for r in _load(level)]


def root_by_name(level: str, name: str) -> Root:
    for r in level_roots(level):
        if r.root == name:
            return r
    raise KeyError(f"no root {name!r} in content/wordroots/{level}.yaml")


def _contains_root(word: str, root: str) -> bool:
    """The root's letters appear in the word (roots with two spellings list both: `ped, pod`)."""
    return any(f.strip() in word.lower() for f in root.split(","))


def root_problems(r: Root) -> list[str]:
    """Content rules for one root: every word carries it, sentences have one blank and the right word."""
    out = []
    for w in [*r.words, *([r.explain] if r.explain else [])]:
        if not _contains_root(w.word, r.root):
            out.append(f"root {r.root}: {w.word!r} doesn't contain the root")
    for w in r.words:
        if len(w.meaning) > MAX_MEANING:
            out.append(f"root {r.root}: meaning of {w.word!r} is longer than {MAX_MEANING} characters")
    names = [w.word for w in r.words]
    if r.explain and r.explain.word in names:
        out.append(f"root {r.root}: the explain word must not be one of its 4 words")
    if r.sentences[0].word not in names[1:3]:
        out.append(f"root {r.root}: sentence 1 must use word 2 or 3")
    if r.sentences[1].word != names[3]:
        out.append(f"root {r.root}: sentence 2 must use word 4")
    for s in r.sentences:
        if s.text.count(BLANK) != 1:
            out.append(f"root {r.root}: sentence {s.text!r} needs exactly one blank")
        if len(s.text) > MAX_SENTENCE:
            out.append(f"root {r.root}: sentence {s.text!r} is longer than {MAX_SENTENCE} characters")
        if re.search(rf"\b{re.escape(s.word)}\b", s.text, re.I):
            out.append(f"root {r.root}: sentence {s.text!r} gives its answer away")
    if r.explain and (not r.explain.sample.strip() or not r.explain.rubric.strip()):
        out.append(f"root {r.root}: explain needs a sample and a rubric")
    return out


def explained_on(level: str, name: str) -> str | None:
    """Where a root's explain question is: "teach" (its teaching page), "review" or None (not explained)."""
    i = [r.root for r in level_roots(level)].index(name)
    if i % 2 == (i // 2) % 2:
        return "teach"
    return "review" if i % 4 == 1 else None


def explain_problems(level: str) -> list[str]:
    """Exactly the roots that are explained somewhere carry an `explain`."""
    out = []
    for r in level_roots(level):
        where = explained_on(level, r.root)
        if where and not r.explain:
            out.append(f"root {r.root}: needs an explain word (explained on its {where} page)")
        if not where and r.explain:
            out.append(f"root {r.root}: has an explain word that no page uses")
    return out


# --- planner -------------------------------------------------------------------------------

def plan_roots(level: Level, plan: LevelPlan) -> None:
    """Fill in the word-roots pages of `plan` (sections with rule `roots`)."""
    from .syllabus import resolve_page

    names = [r.root for r in level_roots(level.level)]
    for sec in level.sections:
        spec0 = resolve_page(level, sec.pages[0])
        if not spec0.rules.get("roots"):
            continue
        taught = 0      # roots handed out on teaching pages so far
        reviewed = 0
        for page in range(sec.pages[0], sec.pages[1] + 1):
            spec = resolve_page(level, page)
            n = spec.rules.get("roots_per_page", 2)
            if spec.rules.get("review"):
                group = names[reviewed:reviewed + n]
                reviewed += n
            else:
                group = names[taught:taught + n]
                taught += n
            if len(group) < n:
                plan.waiting[page] = f"content/wordroots/{level.level}.yaml needs more roots"
                continue
            plan.pages[page] = PagePlan(page=page, extra={"roots": group, "review": bool(spec.rules.get("review"))})


# --- pages ---------------------------------------------------------------------------------

def build_root_items(ctx) -> tuple[str, list[dict], list[str]]:
    """(title, items, answer key) for one word-roots page."""
    entry = ctx.plan.for_page(ctx.spec.page).extra
    roots = [root_by_name(ctx.spec.level, n) for n in entry["roots"]]
    review = entry["review"]
    cards = [{"root": r.root, "origin": r.origin, "meaning": r.meaning,
              "example": None if review else r.words[0].word} for r in roots]
    if review:
        match = [r.words[3] for r in roots]
        fills = [r.sentences[1] for r in roots if explained_on(ctx.spec.level, r.root) == "teach"]
        explains = [r for r in roots if explained_on(ctx.spec.level, r.root) == "review"]
    else:
        match = [w for r in roots for w in r.words[1:3]]
        fills = [r.sentences[0] for r in roots]
        explains = [r for r in roots if explained_on(ctx.spec.level, r.root) == "teach"]
    order = list(range(len(match)))
    ctx.rng.shuffle(order)
    meanings = [match[i].meaning for i in order]
    answers = [LETTERS[order.index(i)] for i in range(len(match))]
    bank = sorted(w.word for w in match)
    key = ["1. " + " · ".join(f"{w.word} {a}" for w, a in zip(match, answers))]
    items: list[dict] = [{"kind": "roots", "roots": cards, "review": review},
                         {"kind": "match", "n": 1, "words": [w.word for w in match], "meanings": meanings,
                          "answers": answers}]
    sents = []
    for s in fills:
        before, after = s.text.split(BLANK)
        sents.append({"before": before, "after": after, "answer": s.word})
    items.append({"kind": "fill", "n": 2, "bank": bank, "sentences": sents})
    key.append("2. " + " · ".join(s.word for s in fills))
    for r in explains:
        items.append({"kind": "explain", "n": 3, "root": r.root, "meaning": r.meaning,
                      "explain_word": r.explain.word, "lines": 2})
        key.append(f"3. Sample: {r.explain.sample} Full answer: {r.explain.rubric}")
    title = "Root Review" if review else "Roots: " + " and ".join(r.root.split(",")[0] for r in roots)
    return title, items, key


def check_root_sheet(sheet) -> list[str]:
    """A word-roots page holds its planned roots, matching that pairs each word with its meaning, and a key
    that agrees with the content file."""
    from .generate import build_plan
    from .syllabus import load_level

    level = load_level(sheet.subject, sheet.level)
    head = sheet.items[0] if sheet.items else {}
    if head.get("kind") != "roots":
        return ["the first item must be the root cards"]
    planned = build_plan(level, sheet.variant).pages.get(sheet.page_number)
    names = [c["root"] for c in head["roots"]]
    if planned is None or planned.extra != {"roots": names, "review": head["review"]}:
        return ["roots don't match the level plan"]
    out = []
    try:
        roots = [root_by_name(sheet.level, n) for n in names]
    except KeyError as e:
        return [e.args[0]]
    for r in roots:
        out += root_problems(r)
    words = {w.word: w.meaning for r in roots for w in r.words}
    match = next((i for i in sheet.items if i["kind"] == "match"), None)
    if not match:
        return out + ["needs a matching task"]
    for w, a in zip(match["words"], match["answers"]):
        if match["meanings"][LETTERS.index(a)] != words.get(w):
            out.append(f"matching: {w!r} isn't paired with its meaning")
    if sorted(match["meanings"]) != sorted(words[w] for w in match["words"]):
        out.append("matching meanings don't match the words")
    fill = next((i for i in sheet.items if i["kind"] == "fill"), None)
    if not fill or any(s["answer"] not in fill["bank"] for s in fill["sentences"]):
        out.append("every blank's answer must be in the word bank")
    if fill and sorted(fill["bank"]) != sorted(match["words"]):
        out.append("the word bank must be the matched words")
    explains = [i for i in sheet.items if i["kind"] == "explain"]
    if len(explains) != 1:
        out.append("needs exactly one explain question")
    roots_by = {r.root: r for r in roots}
    for e in explains:
        r = roots_by.get(e["root"])
        if r is None or not r.explain or e["explain_word"] != r.explain.word or e["meaning"] != r.meaning:
            out.append(f"explain question for {e['root']!r} doesn't match the content file")
    seen = sorted(s["answer"] for s in fill["sentences"]) if fill else []
    if len(seen) != len(set(seen)):
        out.append("two blanks have the same answer")
    sentences = {s.text: s.word for r in roots for s in r.sentences}
    for s in fill["sentences"] if fill else []:
        if sentences.get(s["before"] + BLANK + s["after"]) != s["answer"]:
            out.append(f"blank {s['before']!r}… doesn't match its sentence in the content file")
    key = ["1. " + " · ".join(f"{w} {a}" for w, a in zip(match["words"], match["answers"]))]
    key.append("2. " + " · ".join(s["answer"] for s in fill["sentences"]) if fill else "2. ")
    key += [f"3. Sample: {roots_by[e['root']].explain.sample} Full answer: {roots_by[e['root']].explain.rubric}"
            for e in explains if roots_by.get(e["root"]) and roots_by[e["root"]].explain]
    if sheet.answer_key != key:
        out.append("answer key doesn't match the page")
    return out
