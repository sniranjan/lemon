"""Penguins Reading (english R7): spreads of articles, arguments, poems and paired texts, plus word roots."""

from collections import Counter

import pytest

from ws import generate as gen
from ws import registry
from ws.content import tips
from ws.passages import BRITISH
from ws.readability import words
from ws.render import min_child_px
from ws.roots import explain_problems, explained_on, level_roots, root_problems
from ws.spreads import SpreadPassage, SpreadQuestion, page_units, passage_spill_units, section_spreads, spread_problems
from ws.syllabus import load_level, resolve_page
from ws.verify import banned_words

R7 = load_level("english", "R7")
SPREADS = "ABDE"


def _texts(p) -> str:
    return " ".join([p.title, p.full_text, *[x for t in p.texts or [] for x in (t.title, t.kind)]] + [
        t for s in p.pages for q in s.questions
        for t in [q.ask, q.sample or "", q.rubric or "", *(q.choices or [])]])


def test_level_shape():
    assert [s.code for s in R7.sections] == list("ABCDE")
    assert R7.public_name == "Penguins" and all(s.public_name for s in R7.sections)
    assert len(R7.preview_pages) == 4
    assert min_child_px("R7", "english") == 20
    # two grades ahead (CLAUDE.md §15): every section is tagged with grade 7 standards
    for s in R7.sections:
        assert s.standards and all(".7." in c for c in s.standards), s.code
    for c in SPREADS:
        s = R7.section(c)
        assert s.sheet_types == ["passage_spread"] and (s.pages[1] - s.pages[0] + 1) % 2 == 0
    assert R7.section("C").sheet_types == ["word_roots"]


@pytest.mark.parametrize("code", SPREADS)
def test_passages_follow_the_rules(code):
    sec = R7.section(code)
    rules = resolve_page(R7, sec.pages[0]).rules
    ps = section_spreads("R7", code)
    assert len(ps) * 2 == sec.pages[1] - sec.pages[0] + 1
    for p in ps:
        assert spread_problems(p, rules) == [], p.id
        assert banned_words(_texts(p)) == [], p.id
        assert {w.lower() for w in words(_texts(p))}.isdisjoint(BRITISH), p.id
        assert round(page_units(p.pages[0].questions) + passage_spill_units(p)) <= rules["page_units"], p.id
        # every written answer has a one-line rubric for the answer key
        assert all(q.rubric for q in p.pages[0].questions if q.kind in ("write", "paragraph")), p.id


def test_paired_texts_compare_both():
    for p in section_spreads("R7", "E"):
        assert p.genre == "paired" and [t.kind for t in p.texts] == ["story", "history"], p.id
        both = [q for q in p.pages[0].questions if len(q.quotes) == 2]
        assert len(both) >= 2, p.id


def test_ids_and_titles_are_unique():
    ps = [p for c in SPREADS for p in section_spreads("R7", c)]
    assert len({p.id for p in ps}) == len(ps)
    assert len({p.title for p in ps}) == len(ps)


def test_schema_extensions():
    # a short answer may carry a rubric (Penguins); Pandas' paragraph answers still need one
    assert SpreadQuestion(kind="write", ask="?", sample="s", rubric="r", evidence="x").rubric == "r"
    with pytest.raises(ValueError):
        SpreadQuestion(kind="paragraph", ask="?", sample="s", evidence="x")
    q = SpreadQuestion(kind="mc", ask="?", choices=list("abcd"), evidence=["one", "two"])
    assert q.quotes == ["one", "two"]
    with pytest.raises(ValueError):    # a pair needs two texts and no `text`
        SpreadPassage(id="x", title="x", genre="paired", text="t", pages=[])
    poem = SpreadPassage(id="p", title="P", genre="poem", text="one\n  two\n\nthree\n", pages=[])
    assert poem.stanzas == [["one", "two"], ["three"]] and poem.poem_lines == ["one", "two", "three"]


def test_roots_are_hand_checked():
    roots = level_roots("R7")
    assert len(roots) == 40
    assert [r.origin for r in roots] == ["Latin", "Greek"] * 20 or Counter(r.origin for r in roots)["Greek"] >= 15
    for r in roots:
        assert root_problems(r) == [], r.root
    assert explain_problems("R7") == []
    assert sum(explained_on("R7", r.root) is not None for r in roots) == 30
    every = [w.word for r in roots for w in r.words] + [r.explain.word for r in roots if r.explain]
    assert len(every) == len(set(every)), "a word belongs to one root only"
    text = " ".join(x for r in roots for x in [r.meaning, *(w.meaning for w in r.words),
                                               *(s.text for s in r.sentences),
                                               *([r.explain.sample, r.explain.rubric] if r.explain else [])])
    assert banned_words(text) == []
    assert {w.lower() for w in words(text)}.isdisjoint(BRITISH)


def test_every_page_is_planned_and_passes_its_checks():
    plan = gen.build_plan(R7)
    assert not plan.waiting and set(plan.pages) == set(range(1, 201))
    answers: Counter = Counter()
    for page in range(1, 201):
        sheet = gen.build_sheet(R7, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id
        if sheet.sheet_type == "word_roots":
            assert sheet.answer_key
            continue
        side = sheet.items[0]["side"]
        assert side == ("read" if page % 2 else "questions")
        if side == "questions":
            answers.update(i["answer"] for i in sheet.items if i["kind"] in ("mc", "quote"))
    assert set(answers) == set("ABCD") and min(answers.values()) >= sum(answers.values()) // 7, answers


def test_tips_fit_one_line():
    """A one-line tip leaves the reading page its full height (64 characters at 17px)."""
    for s in R7.sections:
        for name, ts in s.rules.get("tips", {}).items():
            for tip in ts:
                assert len(tip) <= 64, tip
    for tip in tips("english")["word_roots"]:
        assert len(tip) <= 64, tip


@pytest.mark.parametrize("page", [1, 2, 52, 101, 121, 131, 132, 161, 162])
def test_golden(page, out_dir, golden):
    (sheet, path), = gen.generate_pages(R7, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")
