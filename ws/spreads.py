"""Two-page passages (Pandas Reading on, sheet type `passage_spread`): a reading page, then a
questions page about the same text.

A passage is longer than one page of questions can sit under, so each question set takes two
pages in a row: the left page is the passage (paragraphs numbered, so questions can say
"paragraph 3"), the right page is its questions. A Letter page holds about 300 words of grade 6
text at the 20px floor, so the end of a longer passage continues at the top of the questions page
(`split_text`, whole sentences, the same split every time). A passage has one or two question sets; the
second time the reading page says what to look for ("Read it again. Look for ...").

Content: `content/passages/<level>/<section>.yaml`, a list of passages, each with `id`, `title`,
`text` (paragraphs split by a blank line), `genre` (`nonfiction` or `story`) and `pages`: the
question sets. A set has a `focus`, an optional `look_for` (the second reading's prompt) and its
`questions`. Question kinds:

- `mc`: 4 `choices`, the first is right (the sheet shuffles them).
- `quote`: "Which sentence best supports ...?": 4 `choices` copied exactly from the text, the
  first is right. Verify finds every choice in the passage.
- `write`: a short written answer on 2 lines, with a `sample`.
- `paragraph`: 3–4 sentences with evidence on 5 lines, with a `sample` (3–4 sentences that quote
  the text in double quotes) and a `rubric` (what a full answer has), both for the answer key.
- `organizer`: 2–3 labeled boxes (`heads`, e.g. Cause / Effect) with one `samples` entry each.

Every question carries `evidence`: words copied exactly from the passage that back up the answer.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from .content import level_passages as load_passages
from .readability import fk_grade, sentences, words

LETTERS = "ABCD"
MAX_TITLE = 24       # characters: the passage title stays on one line in the header
MAX_ASK = 120        # characters: two lines at 20px
MAX_CHOICE = 70      # characters: one line at 20px (mc)
MAX_QUOTE = 130      # characters: two lines at 20px (quote choices)
MAX_HEAD = 18        # organizer box label
MAX_LOOK_FOR = 46    # "Read again: <look_for>" sits on the card border, one line
LINES = {"write": 2, "paragraph": 5, "organizer": 3}
TWO_COLUMNS = 30     # choices this short (all four) sit in two columns, A B / C D
_PARAGRAPH_REF = re.compile(r"\bparagraphs? (\d+)(?: and (\d+))?", re.I)
_QUOTED = re.compile(r"[\"“]([^\"”]+)[\"”]")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SpreadQuestion(_Strict):
    kind: Literal["mc", "quote", "write", "paragraph", "organizer"]
    ask: str
    choices: list[str] | None = None
    sample: str | None = None
    samples: list[str] | None = None
    heads: list[str] | None = None
    rubric: str | None = None
    evidence: str

    @model_validator(mode="after")
    def _fields_for_kind(self) -> SpreadQuestion:
        k = self.kind
        need = {"mc": {"choices"}, "quote": {"choices"}, "write": {"sample"},
                "paragraph": {"sample", "rubric"}, "organizer": {"heads", "samples"}}[k]
        for f in ("choices", "sample", "samples", "heads", "rubric"):
            has = getattr(self, f) is not None
            if has != (f in need):
                raise ValueError(f"{k} question {self.ask!r}: {'needs' if f in need else 'has no'} {f}")
        if self.choices is not None and (len(self.choices) != 4 or len(set(self.choices)) != 4):
            raise ValueError(f"question {self.ask!r} needs 4 different choices")
        if self.heads is not None and (not 2 <= len(self.heads) <= 3 or len(self.samples) != len(self.heads)):
            raise ValueError(f"organizer {self.ask!r} needs 2–3 heads and one sample per head")
        return self


class SpreadSet(_Strict):
    focus: str
    look_for: str | None = None
    questions: list[SpreadQuestion]


class SpreadPassage(_Strict):
    id: str
    title: str
    genre: Literal["nonfiction", "story"]
    text: str
    pages: list[SpreadSet]

    @property
    def paragraphs(self) -> list[str]:
        return [" ".join(p.split()) for p in re.split(r"\n\s*\n", self.text.strip())]


def section_spreads(level: str, section: str) -> list[SpreadPassage]:
    return [SpreadPassage.model_validate(p) for p in load_passages(level, section)]


def spread_by_id(level: str, section: str, pid: str) -> SpreadPassage:
    for p in section_spreads(level, section):
        if p.id == pid:
            return p
    raise KeyError(f"no passage {pid!r} in content/passages/{level}/{section}.yaml")


def _flat(text: str) -> str:
    return " ".join(text.replace("’", "'").replace("“", '"').replace("”", '"').split())


def in_text(quote: str, text: str) -> bool:
    return _flat(quote) in _flat(text)


def spread_problems(p: SpreadPassage, rules: dict) -> list[str]:
    """Content rules for one two-page passage: length, readability, spelling, answerable questions."""
    from .passages import british_words

    out = []
    n = len(words(p.text))
    lo, hi = rules.get("passage_words", [320, 380])
    if not lo <= n <= hi:
        out.append(f"passage {p.id}: {n} words (needs {lo}–{hi})")
    if len(p.title) > MAX_TITLE:
        out.append(f"passage {p.id}: title is {len(p.title)} characters (max {MAX_TITLE})")
    fk_lo, fk_hi = rules.get("fk_grade", [5.5, 7.5])
    fk = fk_grade(p.text)
    if not fk_lo <= fk <= fk_hi:
        out.append(f"passage {p.id}: Flesch-Kincaid grade {fk} (needs {fk_lo}–{fk_hi})")
    texts = [p.title, p.text] + [t for s in p.pages for t in [s.look_for or ""] + [
        t for q in s.questions for t in [q.ask, q.sample or "", q.rubric or "", *(q.choices or []),
                                          *(q.samples or []), *(q.heads or [])]]]
    for w in british_words(" ".join(texts)):
        out.append(f"passage {p.id}: {w!r} is not American English")
    lo_sets, hi_sets = rules.get("sets_per_passage", [1, 2])
    if not lo_sets <= len(p.pages) <= hi_sets:
        out.append(f"passage {p.id}: has {len(p.pages)} question sets (needs {lo_sets}–{hi_sets})")
    genres = rules.get("genres")
    if genres and p.genre not in genres:
        out.append(f"passage {p.id}: genre {p.genre} isn't one of {genres}")
    n_paras = len(p.paragraphs)
    q_lo, q_hi = rules.get("questions_per_page", [3, 4])
    kinds_needed = rules.get("kinds_per_page", {})
    for k, s in enumerate(p.pages):
        where = f"passage {p.id} set {k + 1}"
        if k > 0 and not s.look_for:
            out.append(f"{where}: a second reading needs a look_for prompt")
        if s.look_for and len(s.look_for) > MAX_LOOK_FOR:
            out.append(f"{where}: look_for is {len(s.look_for)} characters (max {MAX_LOOK_FOR})")
        if not q_lo <= len(s.questions) <= q_hi:
            out.append(f"{where}: {len(s.questions)} questions (needs {q_lo}–{q_hi})")
        kinds = [q.kind for q in s.questions]
        if not any(kd in ("write", "paragraph", "organizer") for kd in kinds):
            out.append(f"{where}: needs at least one written answer")
        for kd, (mn, mx) in kinds_needed.items():
            if not mn <= kinds.count(kd) <= mx:
                out.append(f"{where}: {kinds.count(kd)} {kd} questions (needs {mn}–{mx})")
        units = round(page_units(s.questions) + spill_units(p.paragraphs))
        if units > rules.get("page_units", 100):
            out.append(f"{where}: questions page takes {units} units with the passage's end "
                       f"(max {rules.get('page_units', 100)})")
        for q in s.questions:
            if len(q.ask) > MAX_ASK:
                out.append(f"{where}: question is {len(q.ask)} characters (max {MAX_ASK}): {q.ask!r}")
            if not in_text(q.evidence, p.text):
                out.append(f"{where}: evidence {q.evidence!r} is not in the passage")
            for m in _PARAGRAPH_REF.finditer(q.ask):
                for g in m.groups():
                    if g and not 1 <= int(g) <= n_paras:
                        out.append(f"{where}: {q.ask!r} names paragraph {g}, the text has {n_paras}")
            if q.kind == "mc":
                for c in q.choices:
                    if len(c) > MAX_CHOICE:
                        out.append(f"{where}: choice is {len(c)} characters (max {MAX_CHOICE}): {c!r}")
            if q.kind == "quote":
                for c in q.choices:
                    if len(c) > MAX_QUOTE:
                        out.append(f"{where}: quote is {len(c)} characters (max {MAX_QUOTE}): {c!r}")
                    if not in_text(c, p.text):
                        out.append(f"{where}: quote choice {c!r} is not in the passage")
                if not in_text(q.evidence, q.choices[0]) and not in_text(q.choices[0], q.evidence):
                    out.append(f"{where}: a quote question's evidence must be its right choice")
            if q.kind == "paragraph":
                n_sent = len(sentences(q.sample))
                if not 3 <= n_sent <= 4:
                    out.append(f"{where}: paragraph sample has {n_sent} sentences (needs 3–4)")
                quoted = _QUOTED.findall(q.sample)
                if not quoted:
                    out.append(f"{where}: paragraph sample must quote the text in double quotes")
                for qt in quoted:
                    if not in_text(qt.strip(" ,."), p.text):
                        out.append(f"{where}: sample quotes {qt!r}, which is not in the passage")
            if q.kind == "organizer":
                for h in q.heads:
                    if len(h) > MAX_HEAD:
                        out.append(f"{where}: organizer head {h!r} is longer than {MAX_HEAD}")
    return out


# --- page budget ---------------------------------------------------------------------------
# Rough heights on the questions page (one unit ~ 6px of the ~770px body): verify's layout check
# is the real test; this lets the content check catch an overfull set before anything renders.

def _ask_lines(ask: str) -> int:
    return 1 if len(ask) <= 58 else 2


def write_lines(kind: str, rules: dict) -> int:
    """Writing lines for a written answer; a section can give 3–4-sentence answers more (`paragraph_lines`)."""
    return rules.get("paragraph_lines", LINES[kind]) if kind == "paragraph" else LINES[kind]


def two_columns(q: SpreadQuestion) -> bool:
    return q.kind in ("mc", "quote") and all(len(c) + 2 * (q.kind == "quote") <= TWO_COLUMNS for c in q.choices)


def question_units(q: SpreadQuestion) -> int:
    ask = 5 * _ask_lines(q.ask) + 2
    if two_columns(q):
        return ask + 2 * 5 + 2
    if q.kind == "mc":
        return ask + 4 * 5 + 2
    if q.kind == "quote":
        return ask + sum(5 if len(c) <= 58 else 9 for c in q.choices) + 2
    return ask + 6 * LINES[q.kind] + (4 if q.kind == "organizer" else 0) + 2


def page_units(qs: list[SpreadQuestion]) -> int:
    return sum(question_units(q) for q in qs)


# --- splitting a passage over the spread ----------------------------------------------------
# Calibrated on rendered pages (Andika 20px, line height 1.27, 668px wide): a line holds 68–73
# characters, the reading page about 28 lines. The estimate is cautious (70 characters a line,
# 27 lines with paragraph gaps), so the reading page never overflows; verify's layout check is the
# real test.

CHARS_PER_LINE = 70
READ_LINES = 27.0
PARA_GAP = 0.25      # the space between paragraphs, in lines
LINE_UNITS = 3.6     # one line of passage text on the questions page, in page units


def wrap_lines(text: str, width: int = CHARS_PER_LINE) -> int:
    lines, cur = 1, 0
    for w in text.split():
        add = len(w) if cur == 0 else len(w) + 1
        if cur + add > width and cur:
            lines, cur = lines + 1, len(w)
        else:
            cur += add
    return lines


def split_text(paragraphs: list[str]) -> tuple[list[dict], list[dict]]:
    """(reading page, questions page) paragraphs: [{"n": 3, "text": ..., "cont": False}, ...].

    Paragraphs fill the reading page in order; the one that doesn't fit is split at a sentence
    end (its second half, `cont`, carries no number); the rest go to the top of the questions page.
    A split leaves room for the "turn the page" line on the reading page.
    """
    total = sum(wrap_lines(t) + PARA_GAP for t in paragraphs)
    budget = READ_LINES if total <= READ_LINES else READ_LINES - 1
    first: list[dict] = []
    rest: list[dict] = []
    used = 0.0
    for n, para in enumerate(paragraphs, start=1):
        if rest:
            rest.append({"n": n, "text": para, "cont": False})
            continue
        lines = wrap_lines(para)
        if used + lines <= budget:
            first.append({"n": n, "text": para, "cont": False})
            used += lines + PARA_GAP
            continue
        take: list[str] = []
        sents = sentences(para)
        for sent in sents:
            if used + wrap_lines(" ".join(take + [sent])) <= budget:
                take.append(sent)
            else:
                break
        if take:
            first.append({"n": n, "text": " ".join(take), "cont": False})
            rest.append({"n": None, "text": " ".join(sents[len(take):]), "cont": True})
        else:
            rest.append({"n": n, "text": para, "cont": False})
    return first, rest


def spill_units(paragraphs: list[str]) -> float:
    """How much of the questions page the end of the passage takes (0 when it all fits on page one)."""
    _, rest = split_text(paragraphs)
    if not rest:
        return 0.0
    return 6 + sum(wrap_lines(r["text"], CHARS_PER_LINE + 4) * LINE_UNITS + 1 for r in rest)


# --- planner -------------------------------------------------------------------------------

def spread_queue(level: str, section: str) -> list[tuple[str, int]]:
    """(passage id, set) for each two-page spread of a section, in file order."""
    return [(p["id"], k) for p in load_passages(level, section) for k in range(len(p["pages"]))]


# --- pages ---------------------------------------------------------------------------------

def build_spread_items(ctx) -> tuple[str, list[dict], list[str] | None]:
    """(title, items, answer key) for one page of a spread: the reading page or its questions page."""
    entry = ctx.plan.for_page(ctx.spec.page).extra
    p = spread_by_id(ctx.spec.level, ctx.rules["passages"], entry["passage"])
    k = entry["set"]
    s = p.pages[k]
    first, rest = split_text(p.paragraphs)
    if entry["side"] == "read":
        return p.title, [{"kind": "passage", "passage": p.id, "set": k, "side": "read", "genre": p.genre,
                          "again": k > 0, "look_for": s.look_for if k > 0 else None,
                          "paragraphs": first, "turn": bool(rest)}], None
    items: list[dict] = [{"kind": "questions", "passage": p.id, "set": k, "side": "questions",
                          "genre": p.genre, "page_before": ctx.spec.page - 1, "continued": rest}]
    key = []
    for n, q in enumerate(s.questions, start=1):
        item: dict = {"kind": q.kind, "n": n, "ask": q.ask}
        if q.kind in ("mc", "quote"):
            order = list(range(4))
            ctx.rng.shuffle(order)
            right = LETTERS[order.index(0)]
            item.update(choices=[q.choices[i] for i in order], answer=right, columns=2 if two_columns(q) else 1)
            key.append(f"{n}. {right} ({q.choices[0]})")
        elif q.kind == "organizer":
            item.update(heads=list(q.heads), lines=LINES["organizer"])
            key.append(f"{n}. " + " · ".join(f"{h}: {v}" for h, v in zip(q.heads, q.samples)))
        else:
            item["lines"] = write_lines(q.kind, ctx.rules)
            key.append(f"{n}. Sample: {q.sample}" + (f" Full answer: {q.rubric}" if q.rubric else ""))
        items.append(item)
    return p.title, items, key


def check_spread_sheet(sheet) -> list[str]:
    """What a spread page must hold: its planned passage (or questions), in order, with a matching key."""
    from .syllabus import load_level, resolve_page

    level = load_level(sheet.subject, sheet.level)
    rules = resolve_page(level, sheet.page_number).rules
    head = sheet.items[0] if sheet.items else {}
    if head.get("side") not in ("read", "questions"):
        return ["the first item must be the passage or the questions heading"]
    try:
        p = spread_by_id(sheet.level, rules["passages"], head["passage"])
    except KeyError as e:
        return [e.args[0]]
    out = spread_problems(p, rules)
    sec = level.section(sheet.section)
    first = (sheet.page_number - sec.pages[0]) % 2 == 0
    if first != (head["side"] == "read"):
        out.append(f"page {sheet.page_number}: the reading page must come first in each spread")
    if sheet.title != p.title:
        out.append(f"title doesn't match passage {p.id}")
    if head["side"] == "read":
        if head["paragraphs"] != split_text(p.paragraphs)[0]:
            out.append(f"passage text on the sheet doesn't match {p.id}")
        if len(sheet.items) != 1 or sheet.answer_key:
            out.append("a reading page holds only the passage")
        return out
    if head.get("continued") != split_text(p.paragraphs)[1]:
        out.append(f"the end of passage {p.id} on the questions page doesn't match the text")
    qs = p.pages[head["set"]].questions
    asked = sheet.items[1:]
    if [i["ask"] for i in asked] != [q.ask for q in qs]:
        out.append(f"questions on the sheet don't match {p.id} set {head['set'] + 1}")
        return out
    key = []
    for n, (item, q) in enumerate(zip(asked, qs), start=1):
        if item["n"] != n or item["kind"] != q.kind:
            out.append(f"question {item['n']}: out of order or the wrong kind")
            continue
        if q.kind in ("mc", "quote"):
            if sorted(item["choices"]) != sorted(q.choices):
                out.append(f"question {n}: choices don't match the content file")
                continue
            if item["columns"] != (2 if two_columns(q) else 1):
                out.append(f"question {n}: choices should be in {2 if two_columns(q) else 1} column(s)")
            if item["choices"][LETTERS.index(item["answer"])] != q.choices[0]:
                out.append(f"question {n}: answer {item['answer']} isn't the right choice")
            key.append(f"{n}. {item['answer']} ({q.choices[0]})")
        elif q.kind == "organizer":
            if item["heads"] != q.heads or item["lines"] != LINES["organizer"]:
                out.append(f"question {n}: organizer boxes don't match the content file")
            key.append(f"{n}. " + " · ".join(f"{h}: {v}" for h, v in zip(q.heads, q.samples)))
        else:
            if item["lines"] != write_lines(q.kind, rules):
                out.append(f"question {n}: needs {write_lines(q.kind, rules)} writing lines")
            key.append(f"{n}. Sample: {q.sample}" + (f" Full answer: {q.rubric}" if q.rubric else ""))
    if sheet.answer_key != key:
        out.append("answer key doesn't match the questions")
    return out
