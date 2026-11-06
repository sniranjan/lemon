"""Pandas Reading (english R6): two-page passages (reading page, then questions page)."""

from collections import Counter

import pytest

from ws import generate as gen
from ws import registry
from ws.passages import BRITISH
from ws.readability import words
from ws.render import min_child_px
from ws.spreads import (
    SpreadQuestion, in_text, section_spreads, split_text, spread_problems, wrap_lines,
)
from ws.syllabus import load_level, resolve_page
from ws.verify import banned_words

R6 = load_level("english", "R6")


def _texts(p) -> str:
    return " ".join([p.title, p.text] + [t for s in p.pages for t in [s.look_for or ""] + [
        t for q in s.questions for t in [q.ask, q.sample or "", q.rubric or "", *(q.choices or []),
                                          *(q.samples or []), *(q.heads or [])]]])


def test_level_shape():
    assert [s.code for s in R6.sections] == list("ABCDE")
    assert R6.public_name == "Pandas" and all(s.public_name for s in R6.sections)
    assert len(R6.preview_pages) == 4
    assert min_child_px("R6", "english") == 20
    # two grades ahead (CLAUDE.md §15): every section is tagged with grade 6 standards
    for s in R6.sections:
        assert s.standards and all(".6." in c for c in s.standards), s.code
        assert s.sheet_types == ["passage_spread"]
        assert (s.pages[1] - s.pages[0] + 1) % 2 == 0, "a section is whole spreads"


@pytest.mark.parametrize("code", "ABCDE")
def test_passages_follow_the_rules(code):
    sec = R6.section(code)
    rules = resolve_page(R6, sec.pages[0]).rules
    ps = section_spreads("R6", code)
    assert sum(len(p.pages) for p in ps) * 2 == sec.pages[1] - sec.pages[0] + 1
    for p in ps:
        assert spread_problems(p, rules) == [], p.id
        assert banned_words(_texts(p)) == [], p.id
        assert {w.lower() for w in words(_texts(p))}.isdisjoint(BRITISH), p.id


def test_passage_ids_and_titles_are_unique():
    ps = [p for c in "ABCDE" for p in section_spreads("R6", c)]
    assert len({p.id for p in ps}) == len(ps)
    assert len({p.title for p in ps}) == len(ps)


def test_question_schema():
    with pytest.raises(ValueError):
        SpreadQuestion(kind="mc", ask="?", choices=["a", "b", "c"], evidence="x")
    with pytest.raises(ValueError):
        SpreadQuestion(kind="paragraph", ask="?", sample="s", evidence="x")   # no rubric
    with pytest.raises(ValueError):
        SpreadQuestion(kind="organizer", ask="?", heads=["Cause"], samples=["a"], evidence="x")
    assert in_text("It’s “here”", 'Yes. It\'s "here" now.')


def test_split_keeps_every_word_in_order():
    for c in "ABCDE":
        for p in section_spreads("R6", c):
            first, rest = split_text(p.paragraphs)
            assert first and not first[0]["cont"]
            joined = " ".join(x["text"] for x in first + rest)
            assert joined.split() == " ".join(p.paragraphs).split(), p.id
            assert [x["n"] for x in first + rest if x["n"]] == list(range(1, len(p.paragraphs) + 1))
    assert wrap_lines("a " * 10) == 1 and wrap_lines("word " * 40) == 3


def test_every_page_is_planned_and_passes_its_checks():
    plan = gen.build_plan(R6)
    assert not plan.waiting and set(plan.pages) == set(range(1, 201))
    answers: Counter = Counter()
    for page in range(1, 201):
        sheet = gen.build_sheet(R6, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id
        side = sheet.items[0]["side"]
        assert side == ("read" if page % 2 else "questions")
        if side == "read":
            assert sheet.answer_key is None
        else:
            assert sheet.answer_key and plan.pages[page].extra["passage"] == plan.pages[page - 1].extra["passage"]
            answers.update(i["answer"] for i in sheet.items if i["kind"] in ("mc", "quote"))
    assert set(answers) == set("ABCD") and min(answers.values()) >= sum(answers.values()) // 7, answers


@pytest.mark.parametrize("page", [1, 2, 172])   # reading page, questions page, written answers page
def test_golden(page, out_dir, golden):
    (sheet, path), = gen.generate_pages(R6, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_tips_fit_one_line():
    """A one-line tip leaves the reading page its full height (64 characters at 17px)."""
    from ws.content import tips

    t = tips("english")
    for s in R6.sections:
        for tip in s.rules["tips"]["passage_spread"]:
            assert len(tip) <= 64, tip
    for tip in t["passage_spread"] + t["passage_spread_read"]:
        assert len(tip) <= 64, tip
