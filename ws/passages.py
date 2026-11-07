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
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .content import level_passages as load_passages
from .content import wordparts
from .models import Level
from .plan import LevelPlan, PagePlan
from .readability import fk_grade, words
from .spreads import spread_queue
from .sheet_types._common import page_rules

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
    # words or phrases printed in bold on this page (Otters Reading: clue words, figurative language);
    # each is copied exactly from the passage
    words: list[str] = Field(default_factory=list)


class Passage(_Strict):
    id: str
    title: str
    text: str
    moral: str | None = None
    kind: Literal["story", "article"] | None = None   # labels the reading card (Otters Reading on)
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
    max_ask, max_choice = rules.get("max_ask", MAX_ASK), rules.get("max_choice", MAX_CHOICE)
    max_title = rules.get("max_title", MAX_TITLE)
    n = len(words(p.text))
    lo, hi = rules.get("passage_words", [120, 150])
    if not lo <= n <= hi:
        out.append(f"passage {p.id}: {n} words (needs {lo}–{hi})")
    if len(p.title) > max_title:
        out.append(f"passage {p.id}: title is {len(p.title)} characters (max {max_title})")
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
    # a two-page spread (rule `spread`) has one question set: the reading page, then its questions page
    sets = rules.get("pages_per_passage", 2) // (2 if rules.get("spread") else 1)
    if len(p.pages) != sets:
        out.append(f"passage {p.id}: has {len(p.pages)} question sets (needs {sets})")
    for s in p.pages:
        if len(s.questions) != n_q:
            out.append(f"passage {p.id}: a page has {len(s.questions)} questions (needs {n_q})")
        writes = sum(q.kind == "write" for q in s.questions)
        if not n_write[0] <= writes <= n_write[1]:
            out.append(f"passage {p.id}: a page has {writes} written answers (needs {n_write[0]}–{n_write[1]})")
        for q in s.questions:
            if len(q.ask) > max_ask:
                out.append(f"passage {p.id}: question is {len(q.ask)} characters (max {max_ask}): {q.ask!r}")
            for c in q.choices or []:
                if len(c) > max_choice:
                    out.append(f"passage {p.id}: choice is {len(c)} characters (max {max_choice}): {c!r}")
            if " ".join(q.evidence.split()) not in flat:
                out.append(f"passage {p.id}: evidence {q.evidence!r} is not in the passage")
            if q.kind == "write" and rules.get("starters") is not None and not q.starter:
                out.append(f"passage {p.id}: every written question here needs a starter")
            if q.starter and not (q.sample or "").startswith(q.starter):
                out.append(f"passage {p.id}: sample answer doesn't start with its starter {q.starter!r}")
            out += [f"passage {p.id}: {m}" for m in paragraph_problems(p, q)]
        for w in s.words:
            if not find_phrase(w, p.text):
                out.append(f"passage {p.id}: bold word {w!r} is not in the passage")
    if section == "C" and not p.moral:
        out.append(f"passage {p.id}: a fable needs its moral")
    return out


_PARAGRAPH = re.compile(r"\bparagraphs? (\d)(?: and (\d))?\b", re.I)


def find_phrase(phrase: str, text: str) -> re.Match | None:
    """`phrase` as whole words in `text`, ignoring case and spacing (a line break may fall inside it)."""
    pattern = r"\s+".join(re.escape(w) for w in phrase.split())
    return re.search(r"(?<![\w'’-])" + pattern + r"(?![\w’-]|'\w)", text, re.I)


def paragraph_problems(p: Passage, q: Question) -> list[str]:
    """A question that names a paragraph ("In paragraph 2, ...") must find its evidence there."""
    m = _PARAGRAPH.search(q.ask)
    if not m:
        return []
    paras = p.paragraphs
    nums = [int(g) for g in m.groups() if g]
    if any(not 1 <= n <= len(paras) for n in nums):
        return [f"question {q.ask!r} names a paragraph the passage doesn't have ({len(paras)})"]
    ev = " ".join(q.evidence.split())
    if not any(ev in paras[n - 1] for n in nums):
        return [f"evidence for {q.ask!r} is not in paragraph {' or '.join(map(str, nums))}"]
    return []


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
        if "passages" in rules and rules.get("spread") and spec.sheet_type == "passage_spread":
            # two-page spreads (Pandas Reading on, ws/spreads.py): a reading page, then its questions page.
            # Otters Reading also uses `spread` with its own read_then_answer pages (handled below).
            code = rules["passages"]
            first = (page - level.section(spec.section).pages[0]) % 2 == 0
            if first:
                if code not in queues:
                    queues[code] = spread_queue(level.level, code)
                if not queues[code]:
                    plan.waiting[page] = f"content/passages/{level.level}/{code}.yaml needs more passages"
                    continue
                pid, k = queues[code].pop(0)
                plan.pages[page] = PagePlan(page=page, extra={"passage": pid, "set": k, "side": "read"})
            elif page - 1 in plan.pages:
                plan.pages[page] = PagePlan(page=page, extra={**plan.pages[page - 1].extra, "side": "questions"})
            else:
                plan.waiting[page] = f"content/passages/{level.level}/{code}.yaml needs more passages"
        elif "passages" in rules:
            code = rules["passages"]
            if code not in queues:
                # a spread (rule `spread`): every question set takes two pages, reading then questions
                roles = ["read", "questions"] if rules.get("spread") else [None]
                queues[code] = [(p.id, k, r) for p in section_passages(level.level, code)
                                for k in range(len(p.pages)) for r in roles]
            if not queues[code]:
                plan.waiting[page] = f"content/passages/{level.level}/{code}.yaml needs more passages"
                continue
            pid, k, role = queues[code].pop(0)
            extra = {"passage": pid, "set": k} if role is None else {"passage": pid, "set": k, "role": role}
            plan.pages[page] = PagePlan(page=page, extra=extra)
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
    if any(resolve_page(level, s.pages[0]).rules.get("roots") for s in level.sections):
        from .roots import plan_roots       # Penguins Reading: Greek and Latin roots (ws/roots.py)
        plan_roots(level, plan)
    return plan


# --- passage pages (shared by passage_questions and full_sentence_answer) -------------------

LETTERS = "ABC"


def mark_segments(paragraphs: list[str], marks: list[str]) -> list[list[list]]:
    """Each paragraph as [text, bold] pieces, with the first appearance of every mark in bold."""
    spans: list[tuple[int, int, int]] = []           # (paragraph, start, end)
    for m in marks:
        for i, para in enumerate(paragraphs):
            hit = find_phrase(m, para)
            if hit:
                spans.append((i, hit.start(), hit.end()))
                break
    out = []
    for i, para in enumerate(paragraphs):
        pieces, at = [], 0
        for _, a, b in sorted(s for s in spans if s[0] == i):
            if a < at:
                continue                               # overlapping marks: keep the first
            if a > at:
                pieces.append([para[at:a], False])
            pieces.append([para[a:b], True])
            at = b
        if at < len(para):
            pieces.append([para[at:], False])
        out.append(pieces)
    return out


def question_items(ctx, qs: list[Question], write_lines: int) -> tuple[list[dict], list[str]]:
    """Numbered question items and their answer key, choices shuffled with the page's RNG."""
    items, key = [], []
    starters = ctx.rules.get("starters", True)
    for n, q in enumerate(qs, start=1):
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
    return items, key


def build_passage_items(ctx, write_lines: int, *, marks: bool = False,
                        numbered: bool = False) -> tuple[str, list[dict], list[str]]:
    """(title, items, answer key) for one passage page: the passage, then its numbered questions.

    Multiple-choice options are shuffled with the page's RNG; the key gives the letter and the
    right option. Written answers get `write_lines` lines and a sample answer in the key.
    `marks`: the question set's `words` print in bold (the passage item gets `segments`);
    `numbered`: paragraph numbers in the margin, for questions that name a paragraph.
    """
    entry = ctx.plan.for_page(ctx.spec.page).extra
    p = passage_by_id(ctx.spec.level, ctx.rules["passages"], entry["passage"])
    k = entry["set"]
    head = {"kind": "passage", "passage": p.id, "set": k, "again": k > 0,
            "heading": p.title, "paragraphs": p.paragraphs}
    if p.kind:
        head["text"] = p.kind
    if numbered:
        head["numbered"] = True
    if marks:
        head["marks"] = list(p.pages[k].words)
        head["segments"] = mark_segments(p.paragraphs, p.pages[k].words)
    qitems, key = question_items(ctx, p.pages[k].questions, write_lines)
    return p.title, [head, *qitems], key


def build_spread_items(ctx, write_lines: int) -> tuple[str, list[dict], list[str] | None]:
    """One page of a two-page spread (rule `spread`): the reading page (the passage alone, numbered
    paragraphs, no answers) or the questions page that follows it (no passage; it points back)."""
    entry = ctx.plan.for_page(ctx.spec.page).extra
    p = passage_by_id(ctx.spec.level, ctx.rules["passages"], entry["passage"])
    k = entry["set"]
    if entry["role"] == "read":
        return p.title, [{"kind": "passage", "role": "read", "passage": p.id, "set": k, "heading": p.title,
                          "paragraphs": p.paragraphs, "numbered": True, "text": p.kind or "passage"}], None
    qitems, key = question_items(ctx, p.pages[k].questions, write_lines)
    head = {"kind": "look_back", "role": "questions", "passage": p.id, "set": k, "heading": p.title,
            "read_page": ctx.spec.page - 1, "text": p.kind or "passage"}
    return p.title, [head, *qitems], key


def _check_questions(sheet, asked: list[dict], qs: list[Question], write_lines: int, label: str) -> list[str]:
    out = []
    if [i["ask"] for i in asked] != [q.ask for q in qs]:
        return [f"questions on the sheet don't match {label}"]
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


def check_passage_sheet(sheet, write_lines: int) -> list[str]:
    """What a passage page must hold: its planned passage, its questions in order, a matching key."""
    rules = page_rules(sheet)
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
    if "segments" in head and (head["marks"] != p.pages[head["set"]].words
                               or head["segments"] != mark_segments(p.paragraphs, head["marks"])):
        out.append(f"bold words on the sheet don't match {p.id} set {head['set'] + 1}")
    qs = p.pages[head["set"]].questions
    return out + _check_questions(sheet, sheet.items[1:], qs, write_lines, f"{p.id} set {head['set'] + 1}")


def check_spread_sheet(sheet, write_lines: int) -> list[str]:
    """A spread page: the right passage for its place in the section (reading pages on the section's
    odd pages, 1st, 3rd, ...; each questions page right after its reading page), and on a questions
    page the questions and key of that passage."""
    from .syllabus import load_level, resolve_page

    level = load_level(sheet.subject, sheet.level)
    rules = resolve_page(level, sheet.page_number).rules
    if not rules.get("spread"):
        return ["this section isn't set up for two-page spreads (rule `spread`)"]
    head = sheet.items[0] if sheet.items else {}
    try:
        p = passage_by_id(sheet.level, rules["passages"], head.get("passage", ""))
    except KeyError as e:
        return [e.args[0]]
    out = passage_problems(p, rules, rules["passages"])
    offset = sheet.page_number - level.section(sheet.section).pages[0]
    order = [q.id for q in section_passages(sheet.level, rules["passages"])]
    role = "read" if offset % 2 == 0 else "questions"
    if head.get("role") != role or order.index(p.id) != offset // 2 or head.get("set") != 0:
        out.append(f"page {sheet.page_number} should be the {role} page of {order[offset // 2]}")
        return out
    if head["heading"] != p.title or sheet.title != p.title:
        out.append(f"title on the sheet doesn't match {p.id}")
    if role == "read":
        if head.get("kind") != "passage" or head["paragraphs"] != p.paragraphs or not head.get("numbered"):
            out.append(f"passage text on the sheet doesn't match {p.id}")
        if len(sheet.items) != 1 or sheet.answer_key:
            out.append("a reading page holds only the passage (its questions are on the next page)")
        return out
    if head.get("kind") != "look_back" or head.get("read_page") != sheet.page_number - 1:
        out.append("a questions page must point back to the reading page before it")
    return out + _check_questions(sheet, sheet.items[1:], p.pages[0].questions, write_lines, f"{p.id}")
