"""Two-page passages (Pandas Reading on, sheet type `passage_spread`): a reading page, then a
questions page about the same text.

A passage is longer than one page of questions can sit under, so each question set takes two
pages in a row: the left page is the passage (paragraphs numbered, so questions can say
"paragraph 3"), the right page is its questions. A Letter page holds about 300 words of grade 6
text at the 20px floor, so the end of a longer passage continues at the top of the questions page
(`split_text`, whole sentences, the same split every time). A passage has one or two question sets; the
second time the reading page says what to look for ("Read it again. Look for ...").

Content: `content/passages/<level>/<section>.yaml`, a list of passages, each with `id`, `title`,
`text` (paragraphs split by a blank line), `genre` (`nonfiction` or `story`; Whales Reading adds `speech`,
`essay` and `letter`, named on the page) and `pages`: the
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
MAX_VERSE = 60       # characters in one line of a poem: never wraps at 20px beside its line number
MAX_TEXT_TITLE = 34  # a paired text's title, on one line with its "Text 1" badge
LINES = {"write": 2, "paragraph": 5, "organizer": 3}
TWO_COLUMNS = 30     # choices this short (all four) sit in two columns, A B / C D
_PARAGRAPH_REF = re.compile(r"\bparagraphs? (\d+)(?: and (\d+))?", re.I)
_QUOTED = re.compile(r"[\"“]([^\"”]+)[\"”]")
_LINE_REF = re.compile(r"\blines? (\d+)(?:\s*(?:and|–|-|to)\s*(\d+))?", re.I)
_STANZA_REF = re.compile(r"\bstanza (\d+)", re.I)


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
    evidence: str | list[str]          # a list: one quote from each of two texts (Penguins Reading, genre paired)

    @model_validator(mode="after")
    def _fields_for_kind(self) -> SpreadQuestion:
        k = self.kind
        need = {"mc": {"choices"}, "quote": {"choices"}, "write": {"sample"},
                "paragraph": {"sample", "rubric"}, "organizer": {"heads", "samples"}}[k]
        optional = {"rubric"} if k == "write" else set()     # a short answer may carry a rubric too
        for f in ("choices", "sample", "samples", "heads", "rubric"):
            has = getattr(self, f) is not None
            if f in optional:
                continue
            if has != (f in need):
                raise ValueError(f"{k} question {self.ask!r}: {'needs' if f in need else 'has no'} {f}")
        if self.choices is not None and (len(self.choices) != 4 or len(set(self.choices)) != 4):
            raise ValueError(f"question {self.ask!r} needs 4 different choices")
        if self.heads is not None and (not 2 <= len(self.heads) <= 3 or len(self.samples) != len(self.heads)):
            raise ValueError(f"organizer {self.ask!r} needs 2–3 heads and one sample per head")
        return self

    @property
    def quotes(self) -> list[str]:
        return [self.evidence] if isinstance(self.evidence, str) else list(self.evidence)


class SpreadSet(_Strict):
    focus: str
    look_for: str | None = None
    questions: list[SpreadQuestion]


class SubText(_Strict):
    """One of two texts read side by side (genre `paired`): e.g. a story set in the past, then a
    historical account of the same time."""
    title: str
    kind: str                          # shown under the title: story, history, ...
    text: str

    @property
    def paragraphs(self) -> list[str]:
        return [" ".join(p.split()) for p in re.split(r"\n\s*\n", self.text.strip())]


class SpreadPassage(_Strict):
    id: str
    title: str
    # speech/essay/letter: Whales Reading rhetoric. Penguins Reading adds: argument (a made-up writer's case),
    # poem (stanzas split by a blank line, one line of verse per line, numbered on the page) and paired (two
    # `texts`, no `text`).
    genre: Literal["nonfiction", "story", "speech", "essay", "letter", "argument", "poem", "paired"]
    text: str | None = None
    texts: list[SubText] | None = None
    pages: list[SpreadSet]
    story: str | None = None     # a story told in installments (Lions Reading C): its name ...
    part: int | None = None      # ... and this installment's number, shown on the reading page

    @model_validator(mode="after")
    def _body(self) -> SpreadPassage:
        if (self.genre == "paired") != (self.texts is not None) or (self.text is None) == (self.texts is None):
            raise ValueError(f"passage {self.id}: genre paired has exactly two `texts`, every other genre one `text`")
        if self.texts is not None and len(self.texts) != 2:
            raise ValueError(f"passage {self.id}: a paired passage needs exactly two texts")
        return self

    @property
    def paragraphs(self) -> list[str]:
        if self.texts is not None:
            return [para for t in self.texts for para in t.paragraphs]
        return [" ".join(p.split()) for p in re.split(r"\n\s*\n", self.text.strip())]

    @property
    def full_text(self) -> str:
        """Everything the child reads, for evidence checks (both texts of a pair)."""
        if self.texts is not None:
            return "\n\n".join(t.text for t in self.texts)
        return self.text

    @property
    def stanzas(self) -> list[list[str]]:
        """A poem's stanzas, each a list of its lines (whitespace inside a line normalized)."""
        return [[" ".join(line.split()) for line in st.strip().splitlines() if line.strip()]
                for st in re.split(r"\n\s*\n", (self.text or "").strip())]

    @property
    def poem_lines(self) -> list[str]:
        return [line for st in self.stanzas for line in st]


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
    fk_lo, fk_hi = rules.get("fk_grade", [5.5, 7.5])
    if p.genre == "poem":
        # poems: counted in lines, no readability score (FK assumes prose sentences), must fit one page
        n = len(p.poem_lines)
        lo, hi = rules.get("poem_lines", [12, 28])
        if not lo <= n <= hi:
            out.append(f"passage {p.id}: {n} lines (needs {lo}–{hi})")
        if poem_page_lines(p) > READ_LINES:
            out.append(f"passage {p.id}: the poem takes {poem_page_lines(p)} lines (max {READ_LINES:g} on its page)")
        for line in p.poem_lines:
            if len(line) > MAX_VERSE:
                out.append(f"passage {p.id}: line {line!r} is longer than {MAX_VERSE} characters")
    elif p.genre == "paired":
        lo, hi = rules.get("text_words", [140, 175])
        for i, t in enumerate(p.texts, start=1):
            n = len(words(t.text))
            if not lo <= n <= hi:
                out.append(f"passage {p.id}: text {i} has {n} words (needs {lo}–{hi})")
            fk = fk_grade(t.text)
            if not fk_lo <= fk <= fk_hi:
                out.append(f"passage {p.id}: text {i} Flesch-Kincaid grade {fk} (needs {fk_lo}–{fk_hi})")
            if len(t.title) > MAX_TEXT_TITLE:
                out.append(f"passage {p.id}: text title {t.title!r} is longer than {MAX_TEXT_TITLE} characters")
        if paired_page_lines(p) > PAIRED_LINES:
            out.append(f"passage {p.id}: both texts take {paired_page_lines(p)} lines (max {PAIRED_LINES:g} on the reading page)")
    else:
        n = len(words(p.text))
        lo, hi = rules.get("passage_words", [320, 380])
        if not lo <= n <= hi:
            out.append(f"passage {p.id}: {n} words (needs {lo}–{hi})")
        fk = fk_grade(p.text)
        if not fk_lo <= fk <= fk_hi:
            out.append(f"passage {p.id}: Flesch-Kincaid grade {fk} (needs {fk_lo}–{fk_hi})")
    if len(p.title) > MAX_TITLE:
        out.append(f"passage {p.id}: title is {len(p.title)} characters (max {MAX_TITLE})")
    heads = [x for t in p.texts or [] for x in (t.title, t.kind)]
    texts = [p.title, p.full_text, *heads] + [t for s in p.pages for t in [s.look_for or ""] + [
        t for q in s.questions for t in [q.ask, q.sample or "", q.rubric or "", *(q.choices or []),
                                          *(q.samples or []), *(q.heads or [])]]]
    for w in british_words(" ".join(texts)):
        out.append(f"passage {p.id}: {w!r} is not American English")
    lo_sets, hi_sets = rules.get("sets_per_passage", [1, 2])
    if not lo_sets <= len(p.pages) <= hi_sets:
        out.append(f"passage {p.id}: has {len(p.pages)} question sets (needs {lo_sets}–{hi_sets})")
    if (p.story is None) != (p.part is None):
        out.append(f"passage {p.id}: an installment needs both story and part")
    if rules.get("needs_story") and p.story is None:
        out.append(f"passage {p.id}: this section's passages are installments of one story (story, part)")
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
        n_compare = rules.get("compare_questions")
        if n_compare and p.texts:
            both = sum(len(q.quotes) == 2 and in_text(q.quotes[0], p.texts[0].text)
                       and in_text(q.quotes[1], p.texts[1].text) for q in s.questions)
            if both < n_compare:
                out.append(f"{where}: {both} questions quote both texts (needs {n_compare})")
        units = round(page_units(s.questions) + passage_spill_units(p))
        if units > rules.get("page_units", 100):
            out.append(f"{where}: questions page takes {units} units with the passage's end "
                       f"(max {rules.get('page_units', 100)})")
        for q in s.questions:
            if len(q.ask) > MAX_ASK:
                out.append(f"{where}: question is {len(q.ask)} characters (max {MAX_ASK}): {q.ask!r}")
            for ev in q.quotes:
                if not in_text(ev, p.full_text):
                    out.append(f"{where}: evidence {ev!r} is not in the passage")
            if rules.get("rubrics") and q.kind in ("write", "paragraph") and not q.rubric:
                out.append(f"{where}: written answer {q.ask!r} needs a rubric for the answer key")
            if p.genre == "poem":
                out += [f"{where}: {m}" for m in line_ref_problems(p, q)]
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
                    if not in_text(c, p.full_text):
                        out.append(f"{where}: quote choice {c!r} is not in the passage")
                if not any(in_text(ev, q.choices[0]) or in_text(q.choices[0], ev) for ev in q.quotes):
                    out.append(f"{where}: a quote question's evidence must be its right choice")
            if q.kind == "paragraph":
                # Whales Reading analytical paragraphs: rules `paragraph_sentences`, `paragraph_quotes`
                # (how many quotes the sample needs) and `rubric_parts` (labels the rubric must name)
                s_lo, s_hi = rules.get("paragraph_sentences", [3, 4])
                n_sent = len(sentences(q.sample))
                if not s_lo <= n_sent <= s_hi:
                    out.append(f"{where}: paragraph sample has {n_sent} sentences (needs {s_lo}–{s_hi})")
                if rules.get("max_rubric") and len(q.rubric) > rules["max_rubric"]:
                    out.append(f"{where}: rubric is {len(q.rubric)} characters (max {rules['max_rubric']})")
                quoted = _QUOTED.findall(q.sample)
                if not quoted:
                    out.append(f"{where}: paragraph sample must quote the text in double quotes")
                elif len(quoted) < rules.get("paragraph_quotes", 1):
                    out.append(f"{where}: paragraph sample quotes the text {len(quoted)} time(s) "
                               f"(needs {rules['paragraph_quotes']})")
                for qt in quoted:
                    if p.genre == "poem":
                        qt = qt.replace(" / ", " ")      # a quote across two lines of a poem: "glittering / as if"
                    if not in_text(qt.strip(" ,."), p.full_text):
                        out.append(f"{where}: sample quotes {qt!r}, which is not in the passage")
                for part in rules.get("rubric_parts", []):
                    if f"{part}:" not in q.rubric:
                        out.append(f"{where}: the rubric must name '{part}:'")
            if q.kind == "organizer":
                for h in q.heads:
                    if len(h) > MAX_HEAD:
                        out.append(f"{where}: organizer head {h!r} is longer than {MAX_HEAD}")
                if "paragraph_quotes" in rules:
                    for qt in (m for v in q.samples for m in _QUOTED.findall(v)):
                        if not in_text(qt.strip(" ,."), p.full_text):
                            out.append(f"{where}: organizer sample quotes {qt!r}, which is not in the passage")
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
PAIRED_LINES = 29.0  # two texts on one reading page (no "continues" line; calibrated on rendered pages)


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


def poem_page_lines(p: SpreadPassage) -> float:
    """Lines a poem takes on its reading page: one per line of verse, plus half a line between stanzas."""
    return len(p.poem_lines) + 0.5 * (len(p.stanzas) - 1)


def paired_page_lines(p: SpreadPassage) -> float:
    """Lines two texts take on one reading page: each title line (1.5) and its wrapped paragraphs."""
    return sum(1.5 + sum(wrap_lines(t) + PARA_GAP for t in sub.paragraphs) for sub in p.texts) + 0.5


def passage_spill_units(p: SpreadPassage) -> float:
    """A poem or a pair always fits its reading page, so nothing continues above the questions."""
    return 0.0 if p.genre in ("poem", "paired") else spill_units(p.paragraphs)


def line_ref_problems(p: SpreadPassage, q: SpreadQuestion) -> list[str]:
    """A poem question that names lines ("lines 3–4") or a stanza must find its evidence there."""
    out = []
    lines, stanzas = p.poem_lines, p.stanzas
    for m in _LINE_REF.finditer(q.ask):
        a = int(m.group(1))
        b = int(m.group(2) or a)
        if not 1 <= a <= b <= len(lines):
            out.append(f"{q.ask!r} names line {a}–{b}, the poem has {len(lines)}")
        elif not any(in_text(ev, " ".join(lines[a - 1:b])) for ev in q.quotes):
            out.append(f"evidence for {q.ask!r} is not in line(s) {a}–{b}")
    for m in _STANZA_REF.finditer(q.ask):
        n = int(m.group(1))
        if not 1 <= n <= len(stanzas):
            out.append(f"{q.ask!r} names stanza {n}, the poem has {len(stanzas)}")
        elif not any(in_text(ev, " ".join(stanzas[n - 1])) for ev in q.quotes):
            out.append(f"evidence for {q.ask!r} is not in stanza {n}")
    return out


# --- planner -------------------------------------------------------------------------------

def spread_queue(level: str, section: str) -> list[tuple[str, int]]:
    """(passage id, set) for each two-page spread of a section, in file order."""
    return [(p["id"], k) for p in load_passages(level, section) for k in range(len(p["pages"]))]


# --- pages ---------------------------------------------------------------------------------

def reading_split(p: SpreadPassage) -> tuple[list[dict], list[dict]]:
    """split_text for prose; a poem or a pair sits whole on its reading page (its own items carry it)."""
    if p.genre in ("poem", "paired"):
        return [], []
    return split_text(p.paragraphs)


def reading_extra(p: SpreadPassage) -> dict:
    """What a poem or pair's reading page shows: numbered lines in stanzas, or two titled texts."""
    if p.genre == "poem":
        n, stanzas = 0, []
        for st in p.stanzas:
            rows = []
            for line in st:
                n += 1
                rows.append({"n": n, "text": line})
            stanzas.append(rows)
        return {"stanzas": stanzas}
    if p.genre == "paired":
        return {"texts": [{"title": t.title, "type": t.kind,
                           "paragraphs": [{"n": i, "text": para, "cont": False}
                                          for i, para in enumerate(t.paragraphs, start=1)]}
                          for t in p.texts]}
    return {}


def build_spread_items(ctx) -> tuple[str, list[dict], list[str] | None]:
    """(title, items, answer key) for one page of a spread: the reading page or its questions page."""
    entry = ctx.plan.for_page(ctx.spec.page).extra
    p = spread_by_id(ctx.spec.level, ctx.rules["passages"], entry["passage"])
    k = entry["set"]
    s = p.pages[k]
    first, rest = reading_split(p)
    if entry["side"] == "read":
        head = {"kind": "passage", "passage": p.id, "set": k, "side": "read", "genre": p.genre,
                "again": k > 0, "look_for": s.look_for if k > 0 else None,
                "paragraphs": first, "turn": bool(rest)}
        head.update(reading_extra(p))
        if p.story:   # an installment (Lions Reading C): only then, so other levels' items are unchanged
            head.update(story=p.story, part=p.part)
        return p.title, [head], None
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
        if head["paragraphs"] != reading_split(p)[0] or any(head.get(f) != v for f, v in reading_extra(p).items()):
            out.append(f"passage text on the sheet doesn't match {p.id}")
        if (head.get("story"), head.get("part")) != (p.story, p.part):
            out.append(f"story and part on the sheet don't match {p.id}")
        if len(sheet.items) != 1 or sheet.answer_key:
            out.append("a reading page holds only the passage")
        return out
    if head.get("continued") != reading_split(p)[1]:
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
