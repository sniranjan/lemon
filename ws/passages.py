"""Reading passages and word builders for the passage levels (Foxes Reading on, planner `passages`).

Content (all original, hand-checked):
- `content/passages/<level>/<section>.yaml`: a list of passages. Each passage has an `id`, a `title`,
  the `text` (paragraphs split by a blank line), an optional `moral` (fables) and `pages`: one
  question set per page the passage serves. A question is multiple choice when it has `choices`
  (the first is right; the sheet shuffles them) and a written answer when it has a `sample`.
  Every question carries `evidence`: words copied exactly from the passage that back up the answer,
  so verify can check each question is answerable from the text.
- `content/wordparts/<level>.yaml`: `affixes` (un, re, ful, less, compound) and `words` to build,
  each with its `meaning`, a `sentence` with a blank (`___`) and a `foil`: a second built word that
  does not fit the sentence (the child picks between the two).

The planner gives every passage page one (passage, question set) in file order, and every word
builder page its words (least used first), so any page range builds the same sheets.
"""

from __future__ import annotations

import random
import re
from collections import Counter

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .content import level_passages as load_passages
from .content import wordparts
from .models import Level
from .plan import LevelPlan, PagePlan
from .readability import fk_grade, words

BLANK = "___"
MAX_ASK = 60       # characters: one line at 20px
MAX_CHOICE = 40    # characters: a choice never wraps
MAX_TITLE = 22     # characters: the title stays on one line in the header


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Question(_Strict):
    ask: str
    choices: list[str] | None = None    # multiple choice: the first is right
    sample: str | None = None           # written answer: a sample answer for the answer key
    starter: str | None = None          # the first words of a full-sentence answer (Say It in a Sentence)
    evidence: str                       # words copied exactly from the passage

    @model_validator(mode="after")
    def _one_kind(self) -> Question:
        if (self.choices is None) == (self.sample is None):
            raise ValueError(f"question {self.ask!r} needs either choices or a sample answer")
        if self.choices is not None and (len(self.choices) != 3 or len(set(self.choices)) != 3):
            raise ValueError(f"question {self.ask!r} needs 3 different choices")
        return self

    @property
    def kind(self) -> str:
        return "mc" if self.choices else "write"


class QuestionSet(_Strict):
    focus: str
    questions: list[Question]


class Passage(_Strict):
    id: str
    title: str
    text: str
    moral: str | None = None
    pages: list[QuestionSet]

    @property
    def paragraphs(self) -> list[str]:
        return [" ".join(p.split()) for p in re.split(r"\n\s*\n", self.text.strip())]


class WordPart(_Strict):
    built: str
    affix: str
    base: str | None = None             # prefix/suffix words: the known word
    parts: list[str] | None = None      # compound words: the two words
    meaning: str
    sentence: str
    foil: str
    pictures: list[str] = Field(default_factory=list)   # compound words: a picture for each part


def section_passages(level: str, section: str) -> list[Passage]:
    return [Passage.model_validate(p) for p in load_passages(level, section)]


def passage_by_id(level: str, section: str, pid: str) -> Passage:
    for p in section_passages(level, section):
        if p.id == pid:
            return p
    raise KeyError(f"no passage {pid!r} in content/passages/{level}/{section}.yaml")


def word_parts(level: str) -> list[WordPart]:
    return [WordPart.model_validate(w) for w in wordparts(level).get("words", [])]


def affixes(level: str) -> dict[str, dict]:
    return wordparts(level).get("affixes", {})


def first_and_second(w: WordPart) -> tuple[str, str]:
    """The two pieces as the child sees them: un + kind, care + ful, star + fish."""
    kind = affixes_kind(w)
    if kind == "compound":
        return w.parts[0], w.parts[1]
    return (w.affix, w.base) if kind == "prefix" else (w.base, w.affix)


def affixes_kind(w: WordPart) -> str:
    return "compound" if w.affix == "compound" else "prefix" if w.affix in ("un", "re") else "suffix"


# --- checks (shared by the sheet types' verify and the tests) ----------------------------------

# British spellings and words a US child or parent wouldn't use (CLAUDE.md §2).
BRITISH = frozenset("""
colour colours coloured colouring colourful favourite favourites neighbour neighbours neighbourhood behaviour
flavour flavours harbour honour humour labour rumour grey mum mummy realise realised organise organised
recognise recognised practise centre theatre metre tyre tyres kerb travelled travelling cancelled jumper
trousers biscuit biscuits nappy nappies pavement rubbish torch sweets lorry queue maths pyjamas aeroplane
fortnight learnt dreamt spelt programme mates telly cooker
""".split())


def british_words(text: str) -> list[str]:
    return sorted({w.lower() for w in words(text)} & BRITISH)


def passage_problems(p: Passage, rules: dict, section: str) -> list[str]:
    """Content rules for one passage: length, readability, spelling, answerable questions."""
    out = []
    n = len(words(p.text))
    lo, hi = rules.get("passage_words", [120, 150])
    if not lo <= n <= hi:
        out.append(f"passage {p.id}: {n} words (needs {lo}–{hi})")
    if len(p.title) > MAX_TITLE:
        out.append(f"passage {p.id}: title is {len(p.title)} characters (max {MAX_TITLE})")
    fk_lo, fk_hi = rules.get("fk_grade", [2.5, 4.5])
    fk = fk_grade(p.text)
    if not fk_lo <= fk <= fk_hi:
        out.append(f"passage {p.id}: Flesch-Kincaid grade {fk} (needs {fk_lo}–{fk_hi})")
    texts = [p.title, p.text, p.moral or ""] + [t for s in p.pages for q in s.questions
                                                for t in [q.ask, q.sample or "", q.starter or "", *(q.choices or [])]]
    for w in british_words(" ".join(texts)):
        out.append(f"passage {p.id}: {w!r} is not American English")
    flat = " ".join(p.text.split())
    n_q = rules.get("questions_per_page", 3)
    n_write = rules.get("written_answers", [1, 1])
    if len(p.pages) != rules.get("pages_per_passage", 2):
        out.append(f"passage {p.id}: serves {len(p.pages)} pages (needs {rules.get('pages_per_passage', 2)})")
    for s in p.pages:
        if len(s.questions) != n_q:
            out.append(f"passage {p.id}: a page has {len(s.questions)} questions (needs {n_q})")
        writes = sum(q.kind == "write" for q in s.questions)
        if not n_write[0] <= writes <= n_write[1]:
            out.append(f"passage {p.id}: a page has {writes} written answers (needs {n_write[0]}–{n_write[1]})")
        for q in s.questions:
            if len(q.ask) > MAX_ASK:
                out.append(f"passage {p.id}: question is {len(q.ask)} characters (max {MAX_ASK}): {q.ask!r}")
            for c in q.choices or []:
                if len(c) > MAX_CHOICE:
                    out.append(f"passage {p.id}: choice is {len(c)} characters (max {MAX_CHOICE}): {c!r}")
            if " ".join(q.evidence.split()) not in flat:
                out.append(f"passage {p.id}: evidence {q.evidence!r} is not in the passage")
            if q.kind == "write" and rules.get("starters") is not None and not q.starter:
                out.append(f"passage {p.id}: every written question here needs a starter")
            if q.starter and not (q.sample or "").startswith(q.starter):
                out.append(f"passage {p.id}: sample answer doesn't start with its starter {q.starter!r}")
    if section == "C" and not p.moral:
        out.append(f"passage {p.id}: a fable needs its moral")
    return out


def wordpart_problems(w: WordPart, known: set[str]) -> list[str]:
    out = []
    kind = affixes_kind(w)
    if kind == "compound":
        if not w.parts or len(w.parts) != 2 or "".join(w.parts) != w.built:
            out.append(f"{w.built}: compound parts {w.parts} don't spell it")
    elif kind == "prefix":
        if w.built != w.affix + w.base:
            out.append(f"{w.built}: {w.affix} + {w.base} doesn't spell it")
    elif w.built != w.base + w.affix:
        out.append(f"{w.built}: {w.base} + {w.affix} doesn't spell it")
    if w.sentence.count(BLANK) != 1:
        out.append(f"{w.built}: the sentence needs exactly one blank ({BLANK})")
    if w.foil == w.built or (w.foil not in known and w.foil != w.base):
        out.append(f"{w.built}: foil {w.foil!r} must be its base word or another built word")
    return out


# --- planner -------------------------------------------------------------------------------

def plan_passages(level: Level, variant: int = 1) -> LevelPlan:
    """Every page of a passage level, planned up front.

    Passage pages (rule `passages: <section>`): the section's passages in file order, one question
    set per page. Word builder pages (`affixes: [...]`): `builds` words a page from the part's
    affixes, the least used first (ties broken by the page seed), one word per affix where the
    part mixes several. Pages the content doesn't cover yet wait (verify warns).
    """
    from .syllabus import page_seed, resolve_page

    plan = LevelPlan(subject=level.subject, level=level.level, variant=variant)
    queues: dict[str, list[tuple[str, int]]] = {}
    used: Counter[str] = Counter()
    pool = word_parts(level.level)
    for page in range(1, level.pages + 1):
        spec = resolve_page(level, page)
        rules = spec.rules
        if "passages" in rules:
            code = rules["passages"]
            if code not in queues:
                queues[code] = [(p.id, k) for p in section_passages(level.level, code) for k in range(len(p.pages))]
            if not queues[code]:
                plan.waiting[page] = f"content/passages/{level.level}/{code}.yaml needs more passages"
                continue
            pid, k = queues[code].pop(0)
            plan.pages[page] = PagePlan(page=page, extra={"passage": pid, "set": k})
        elif "affixes" in rules:
            rng = random.Random(page_seed(level.subject, level.level, spec.section, page, variant))
            n = rules.get("builds", 4)
            chosen: list[str] = []
            groups = rules["affixes"]
            for i in range(n):
                allowed = [groups[i % len(groups)]] if len(groups) > 1 else groups
                cands = [w.built for w in pool if w.affix in allowed and w.built not in chosen]
                if not cands:
                    break
                rng.shuffle(cands)
                cands.sort(key=lambda b: used[b])
                chosen.append(cands[0])
            if len(chosen) < n:
                plan.waiting[page] = f"content/wordparts/{level.level}.yaml needs more {'/'.join(groups)} words"
                continue
            used.update(chosen)
            plan.pages[page] = PagePlan(page=page, extra={"builds": chosen})
    return plan


# --- passage pages (shared by passage_questions and full_sentence_answer) -------------------

LETTERS = "ABC"


def build_passage_items(ctx, write_lines: int) -> tuple[str, list[dict], list[str]]:
    """(title, items, answer key) for one passage page: the passage, then its numbered questions.

    Multiple-choice options are shuffled with the page's RNG; the key gives the letter and the
    right option. Written answers get `write_lines` lines and a sample answer in the key.
    """
    entry = ctx.plan.for_page(ctx.spec.page).extra
    p = passage_by_id(ctx.spec.level, ctx.rules["passages"], entry["passage"])
    k = entry["set"]
    items: list[dict] = [{"kind": "passage", "passage": p.id, "set": k, "again": k > 0,
                          "heading": p.title, "paragraphs": p.paragraphs}]
    key = []
    starters = ctx.rules.get("starters", True)
    for n, q in enumerate(p.pages[k].questions, start=1):
        if q.kind == "mc":
            order = list(range(3))
            ctx.rng.shuffle(order)
            right = LETTERS[order.index(0)]
            items.append({"kind": "mc", "n": n, "ask": q.ask, "choices": [q.choices[i] for i in order],
                          "answer": right})
            key.append(f"{n}. {right} ({q.choices[0]})")
        else:
            item = {"kind": "write", "n": n, "ask": q.ask, "lines": write_lines}
            if q.starter and starters:
                item["starter"] = q.starter
            items.append(item)
            key.append(f"{n}. Sample: {q.sample}")
    return p.title, items, key


def check_passage_sheet(sheet, write_lines: int) -> list[str]:
    """What a passage page must hold: its planned passage, its questions in order, a matching key."""
    from .syllabus import load_level, resolve_page

    rules = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
    head = sheet.items[0] if sheet.items else {}
    if head.get("kind") != "passage":
        return ["the first item must be the passage"]
    try:
        p = passage_by_id(sheet.level, rules["passages"], head["passage"])
    except KeyError as e:
        return [e.args[0]]
    out = passage_problems(p, rules, rules["passages"])
    if head["paragraphs"] != p.paragraphs or head["heading"] != p.title or sheet.title != p.title:
        out.append(f"passage text on the sheet doesn't match {p.id}")
    qs = p.pages[head["set"]].questions
    asked = sheet.items[1:]
    if [i["ask"] for i in asked] != [q.ask for q in qs]:
        out.append(f"questions on the sheet don't match {p.id} set {head['set'] + 1}")
        return out
    key = []
    for n, (item, q) in enumerate(zip(asked, qs), start=1):
        if item["n"] != n:
            out.append(f"question {item['n']} is out of order")
        if q.kind == "mc":
            if item["kind"] != "mc" or sorted(item["choices"]) != sorted(q.choices):
                out.append(f"question {n}: choices don't match the content file")
                continue
            if item["choices"][LETTERS.index(item["answer"])] != q.choices[0]:
                out.append(f"question {n}: answer {item['answer']} isn't the right choice")
            key.append(f"{n}. {item['answer']} ({q.choices[0]})")
        else:
            if item["kind"] != "write" or item["lines"] != write_lines:
                out.append(f"question {n}: needs {write_lines} writing lines")
            key.append(f"{n}. Sample: {q.sample}")
    if sheet.answer_key != key:
        out.append("answer key doesn't match the questions")
    return out
