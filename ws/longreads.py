"""Long reads for Owls Reading (english R4, planner `long_reads`): chapter stories, word detective,
nonfiction with text features, two texts on one topic, and first summaries.

Content (all original, hand-checked): `content/passages/<level>/<section>.yaml`, a list of reads.
A read has an `id`, a `title`, a `kind` (story or article) and either
- `text`: paragraphs split by a blank line; a paragraph starting with `## ` is a heading, or
- `texts`: two short texts on one topic (`title`, `text`, optional `kind`), read side by side.
Optional: `story` + `chapter` (chapter stories), `figure` (a simple diagram drawn from data: steps,
a cycle, a table, a bar chart or a time line, with a title and a caption).
`pages` holds one question set per page that asks about it. A question is multiple choice
(`choices`, the first is right; the sheet shuffles them) or written (`sample` answer, optional
`starter`). Every question carries `evidence`: words copied exactly from the read (paragraphs,
headings, figure or caption), a list when it draws on both texts. A set may name `targets`: the
words the page shows in bold (Word Detective).

Layouts (section rules):
- `spread: true`: a read takes two pages: the reading page (`long_read_page`) and, after it, its
  questions (`look_back_questions`). The read has exactly one question set.
- otherwise a read serves `pages_per_passage` pages, each with the text and one question set on the
  same page (`word_detective`, `big_idea_summary`).

Readability is measured on body text only (headings, captions and figures are not sentences), and
on each of two texts separately.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from .content import level_passages
from .models import Level
from .passages import BRITISH, LETTERS, MAX_ASK, MAX_CHOICE
from .plan import LevelPlan, PagePlan
from .readability import fk_grade, words

MAX_TITLE = 22          # characters: the header title stays on one line at 28px
MAX_STEP = 26           # characters in one diagram box
HEADING = "## "


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LRQuestion(_Strict):
    ask: str
    choices: list[str] | None = None
    sample: str | None = None
    starter: str | None = None
    evidence: str | list[str]

    @model_validator(mode="after")
    def _one_kind(self) -> LRQuestion:
        if (self.choices is None) == (self.sample is None):
            raise ValueError(f"question {self.ask!r} needs either choices or a sample answer")
        if self.choices is not None and (len(self.choices) != 3 or len(set(self.choices)) != 3):
            raise ValueError(f"question {self.ask!r} needs 3 different choices")
        return self

    @property
    def kind(self) -> str:
        return "mc" if self.choices else "write"

    @property
    def quotes(self) -> list[str]:
        return [self.evidence] if isinstance(self.evidence, str) else list(self.evidence)


class LRSet(_Strict):
    focus: str
    targets: list[str] = []
    questions: list[LRQuestion]


class Figure(_Strict):
    kind: Literal["steps", "cycle", "table", "bars", "timeline"]
    title: str
    caption: str
    items: list[str] | None = None            # steps, cycle
    columns: list[str] | None = None          # table
    rows: list[list[str]] | None = None       # table: cells; bars: [label, number]; timeline: [when, what]
    unit: str | None = None                   # bars: what the numbers count

    @model_validator(mode="after")
    def _shape(self) -> Figure:
        if self.kind in ("steps", "cycle"):
            if not self.items or not 3 <= len(self.items) <= 5:
                raise ValueError(f"figure {self.title!r}: {self.kind} needs 3–5 items")
        else:
            if not self.rows or not 2 <= len(self.rows) <= 5:
                raise ValueError(f"figure {self.title!r}: {self.kind} needs 2–5 rows")
            width = len(self.columns) if self.kind == "table" and self.columns else 2
            if any(len(r) != width for r in self.rows):
                raise ValueError(f"figure {self.title!r}: every row needs {width} cells")
            if self.kind == "table" and not self.columns:
                raise ValueError(f"figure {self.title!r}: a table needs columns")
            if self.kind == "bars":
                if not self.unit or any(not re.fullmatch(r"\d+", r[1]) for r in self.rows):
                    raise ValueError(f"figure {self.title!r}: bars need a unit and whole numbers")
        return self

    def strings(self) -> list[str]:
        return [self.title, self.caption, *(self.items or []), *(self.columns or []),
                *(c for r in self.rows or [] for c in r), self.unit or ""]


class SubText(_Strict):
    title: str
    text: str
    kind: str = "article"      # article, journal, letter, interview, story: shown under the title


class LongRead(_Strict):
    id: str
    title: str
    kind: Literal["story", "article"] = "story"
    story: str | None = None
    chapter: int | None = None
    text: str | None = None
    texts: list[SubText] | None = None
    figure: Figure | None = None
    pages: list[LRSet]

    @model_validator(mode="after")
    def _body(self) -> LongRead:
        if (self.text is None) == (self.texts is None):
            raise ValueError(f"read {self.id}: give either text or texts")
        if self.texts is not None and len(self.texts) != 2:
            raise ValueError(f"read {self.id}: texts must be exactly two")
        if (self.story is None) != (self.chapter is None):
            raise ValueError(f"read {self.id}: a chapter needs both story and chapter")
        return self

    @property
    def blocks(self) -> list[dict]:
        """The text as the sheet shows it: headings and paragraphs, whitespace normalized."""
        return _blocks(self.text or "")

    @property
    def body_texts(self) -> list[str]:
        """Plain body text for readability: one string per text (headings left out)."""
        if self.texts:
            return [" ".join(b["p"] for b in _blocks(t.text) if "p" in b) for t in self.texts]
        return ["\n\n".join(b["p"] for b in self.blocks if "p" in b)]

    def all_strings(self) -> list[str]:
        out = [self.title, self.story or ""]
        out += [b.get("p") or b.get("h") for b in self.blocks]
        for t in self.texts or []:
            out += [t.title, t.kind] + [b.get("p") or b.get("h") for b in _blocks(t.text)]
        if self.figure:
            out += self.figure.strings()
        return out


def _blocks(text: str) -> list[dict]:
    out = []
    for para in re.split(r"\n\s*\n", text.strip()):
        para = " ".join(para.split())
        if para.startswith(HEADING):
            out.append({"h": para[len(HEADING):]})
        elif para:
            out.append({"p": para})
    return out


def section_reads(level: str, section: str) -> list[LongRead]:
    return [LongRead.model_validate(p) for p in level_passages(level, section)]


def read_by_id(level: str, section: str, rid: str) -> LongRead:
    for p in section_reads(level, section):
        if p.id == rid:
            return p
    raise KeyError(f"no read {rid!r} in content/passages/{level}/{section}.yaml")


# --- content checks -----------------------------------------------------------------------

def _flat(s: str) -> str:
    return " ".join(s.split())


def read_problems(p: LongRead, rules: dict) -> list[str]:
    """Content rules for one read: length, readability, spelling, layout limits, answerable questions."""
    out = []
    lo, hi = rules.get("passage_words", [130, 160])
    fk_lo, fk_hi = rules.get("fk_grade", [3.5, 5.5])
    for body in p.body_texts:
        n = len(words(body))
        if not lo <= n <= hi:
            out.append(f"read {p.id}: {n} words (needs {lo}–{hi})")
        fk = fk_grade(body)
        if not fk_lo <= fk <= fk_hi:
            out.append(f"read {p.id}: Flesch-Kincaid grade {fk} (needs {fk_lo}–{fk_hi})")
    if len(p.title) > MAX_TITLE:
        out.append(f"read {p.id}: title is {len(p.title)} characters (max {MAX_TITLE})")
    for t in p.texts or []:
        if len(t.title) > 34:
            out.append(f"read {p.id}: text title {t.title!r} is longer than 34 characters")
    need = rules.get("needs")
    if need == "chapter" and p.chapter is None:
        out.append(f"read {p.id}: a chapter story needs story and chapter")
    if need == "figure":
        if not p.figure:
            out.append(f"read {p.id}: needs a figure (diagram, table, chart or time line)")
        heads = sum("h" in b for b in p.blocks)
        if heads < 2:
            out.append(f"read {p.id}: needs at least 2 headings (has {heads})")
    if need == "two_texts" and not p.texts:
        out.append(f"read {p.id}: needs two texts")
    if p.figure:
        f = p.figure
        for s in (f.items or []):
            if len(s) > MAX_STEP:
                out.append(f"read {p.id}: figure box {s!r} is longer than {MAX_STEP} characters")
        if f.kind in ("table", "timeline", "bars"):
            for r in f.rows:
                if sum(len(c) for c in r) > 52:
                    out.append(f"read {p.id}: figure row {r} is too long for one line")
        if len(f.caption) > 120:
            out.append(f"read {p.id}: caption is longer than 120 characters")
    texts = p.all_strings() + [t for s in p.pages for q in s.questions
                               for t in [q.ask, q.sample or "", q.starter or "", *(q.choices or [])]]
    for w in sorted({w.lower() for w in words(" ".join(texts))} & BRITISH):
        out.append(f"read {p.id}: {w!r} is not American English")
    corpus = [_flat(s) for s in p.all_strings()]
    per_text = [" ".join(_flat(b.get("p") or b.get("h")) for b in _blocks(t.text)) for t in p.texts or []]
    n_q = rules.get("questions_per_page", 3)
    n_write = rules.get("written_answers", [1, 1])
    want_sets = 1 if rules.get("spread") else rules.get("pages_per_passage", 2)
    if len(p.pages) != want_sets:
        out.append(f"read {p.id}: has {len(p.pages)} question sets (needs {want_sets})")
    body = " ".join(corpus)
    for s in p.pages:
        if len(s.questions) != n_q:
            out.append(f"read {p.id}: a page has {len(s.questions)} questions (needs {n_q})")
        writes = sum(q.kind == "write" for q in s.questions)
        if not n_write[0] <= writes <= n_write[1]:
            out.append(f"read {p.id}: a page has {writes} written answers (needs {n_write[0]}–{n_write[1]})")
        long_mc = sum(any(len(c) > MAX_CHOICE for c in q.choices or []) for q in s.questions)
        if long_mc > rules.get("long_choice_questions", n_q):
            out.append(f"read {p.id}: {long_mc} questions have choices over {MAX_CHOICE} characters "
                       f"(max {rules['long_choice_questions']} a page)")
        n_targets = rules.get("targets")
        if n_targets is not None:
            if len(s.targets) != n_targets:
                out.append(f"read {p.id}: a page needs {n_targets} bold words, has {len(s.targets)}")
            for t in s.targets:
                if not re.search(rf"\b{re.escape(t)}\b", body):
                    out.append(f"read {p.id}: bold word {t!r} is not in the text")
                if not any(t in q.ask for q in s.questions):
                    out.append(f"read {p.id}: no question asks about {t!r}")
        if rules.get("needs") == "figure" and p.figure:
            fig = [_flat(x) for x in p.figure.strings()]
            if not any(_flat(e) in x for q in s.questions for e in q.quotes for x in fig):
                out.append(f"read {p.id}: no question uses the figure or its caption")
        if rules.get("needs") == "two_texts":
            both = sum(len(q.quotes) == 2 and _flat(q.quotes[0]) in per_text[0] and _flat(q.quotes[1]) in per_text[1]
                       for q in s.questions)
            if both < rules.get("compare_questions", 2):
                out.append(f"read {p.id}: {both} questions use both texts (needs {rules.get('compare_questions', 2)})")
        for q in s.questions:
            if len(q.ask) > MAX_ASK:
                out.append(f"read {p.id}: question is {len(q.ask)} characters (max {MAX_ASK}): {q.ask!r}")
            for c in q.choices or []:
                if len(c) > rules.get("max_choice", MAX_CHOICE):
                    out.append(f"read {p.id}: choice is {len(c)} characters (max {rules.get('max_choice', MAX_CHOICE)}): {c!r}")
            for e in q.quotes:
                if not any(_flat(e) in c for c in corpus):
                    out.append(f"read {p.id}: evidence {e!r} is not in the read")
            if q.starter and not (q.sample or "").startswith(q.starter):
                out.append(f"read {p.id}: sample answer doesn't start with its starter {q.starter!r}")
            if q.kind == "write" and rules.get("starters") and not q.starter:
                out.append(f"read {p.id}: every written question here needs a starter")
    return out


# --- planner -------------------------------------------------------------------------------

def plan_long_reads(level: Level, variant: int = 1) -> LevelPlan:
    """Every page of a long-read level, planned up front, reads in file order.

    `spread` sections: the read on one page, its questions on the next (the read's first page is
    always an odd page of its part, so the pairs never slip). Other sections: one page per
    question set, the text printed again on each.
    """
    from .syllabus import resolve_page

    plan = LevelPlan(subject=level.subject, level=level.level, variant=variant)
    queues: dict[str, list[tuple[str, int]]] = {}
    for page in range(1, level.pages + 1):
        spec = resolve_page(level, page)
        rules = spec.rules
        code = rules.get("reads")
        if code is None:
            continue
        if code not in queues:
            reads = section_reads(level.level, code)
            if rules.get("spread"):
                queues[code] = [(p.id, k) for p in reads for k in ("read", 0)]
            else:
                queues[code] = [(p.id, k) for p in reads for k in range(len(p.pages))]
        if not queues[code]:
            plan.waiting[page] = f"content/passages/{level.level}/{code}.yaml needs more reads"
            continue
        rid, k = queues[code].pop(0)
        plan.pages[page] = PagePlan(page=page, extra={"read": rid, "set": k})
    return plan


# --- building pages --------------------------------------------------------------------------

def head_item(p: LongRead, k, targets: list[str] | None = None) -> dict:
    item = {"kind": "read", "read": p.id, "set": k, "again": isinstance(k, int) and k > 0,
            "type": p.kind, "heading": p.title, "blocks": p.blocks}
    if p.story:
        item["story"], item["chapter"] = p.story, p.chapter
    if p.texts:
        item["texts"] = [{"title": t.title, "type": t.kind, "blocks": _blocks(t.text)} for t in p.texts]
    if p.figure:
        f = p.figure.model_dump(exclude_none=True)
        if f["kind"] == "bars":
            top = max(int(r[1]) for r in f["rows"])
            f["widths"] = [round(100 * int(r[1]) / top) for r in f["rows"]]
        item["figure"] = f
    if targets:
        item["targets"] = list(targets)
    return item


def question_items(ctx, qs: list[LRQuestion], lines: int) -> tuple[list[dict], list[str]]:
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
            item = {"kind": "write", "n": n, "ask": q.ask, "lines": lines}
            if q.starter and starters:
                item["starter"] = q.starter
            items.append(item)
            key.append(f"{n}. Sample: {q.sample}")
    return items, key


def planned_read(ctx) -> tuple[LongRead, object]:
    entry = ctx.plan.for_page(ctx.spec.page).extra
    return read_by_id(ctx.spec.level, ctx.rules["reads"], entry["read"]), entry["set"]


def check_read_sheet(sheet, lines: int | None) -> list[str]:
    """What a long-read page must hold: its planned read, its questions in order, a matching key.
    `lines` None: a reading page (no questions)."""
    from .generate import build_plan
    from .syllabus import load_level, resolve_page

    level = load_level(sheet.subject, sheet.level)
    rules = resolve_page(level, sheet.page_number).rules
    head = sheet.items[0] if sheet.items else {}
    if head.get("kind") != "read":
        return ["the first item must be the read"]
    try:
        p = read_by_id(sheet.level, rules["reads"], head["read"])
    except KeyError as e:
        return [e.args[0]]
    out = read_problems(p, rules)
    planned = build_plan(level, sheet.variant).pages.get(sheet.page_number)
    if planned is None or planned.extra != {"read": head["read"], "set": head["set"]}:
        out.append("read doesn't match the level plan")
    if head["blocks"] != p.blocks or head["heading"] != p.title or sheet.title != p.title:
        out.append(f"text on the sheet doesn't match {p.id}")
    if lines is None:
        if head["set"] != "read" or len(sheet.items) != 1 or sheet.answer_key:
            out.append("a reading page holds the read only")
        return out
    k = head["set"]
    if not isinstance(k, int) or not 0 <= k < len(p.pages):
        return out + [f"no question set {k!r} in {p.id}"]
    qs = p.pages[k].questions
    if head.get("targets", []) != p.pages[k].targets:
        out.append("bold words don't match the question set")
    asked = sheet.items[1:]
    if [i.get("ask") for i in asked] != [q.ask for q in qs]:
        return out + [f"questions on the sheet don't match {p.id} set {k + 1}"]
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
            if item["kind"] != "write" or item["lines"] != lines:
                out.append(f"question {n}: needs {lines} writing lines")
            key.append(f"{n}. Sample: {q.sample}")
    if sheet.answer_key != key:
        out.append("answer key doesn't match the questions")
    return out



def split_targets(text: str, targets: list[str]) -> list[tuple[str, bool]]:
    """Text cut into (piece, bold) runs so a template can bold the target words (whole words only)."""
    if not targets:
        return [(text, False)]
    pat = re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(targets, key=len, reverse=True)) + r")\b")
    out, at = [], 0
    for m in pat.finditer(text):
        if m.start() > at:
            out.append((text[at:m.start()], False))
        out.append((m.group(0), True))
        at = m.end()
    if at < len(text):
        out.append((text[at:], False))
    return out
