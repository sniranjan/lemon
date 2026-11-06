"""Foxes Reading (english R3): passages with questions, word builders, full-sentence answers."""

from collections import Counter

import pytest

from ws import generate as gen
from ws import registry
from ws.booklet import _answer_pages_by_line, _answer_rows
from ws.passages import (
    BRITISH, affixes, passage_problems, section_passages, word_parts, wordpart_problems,
)
from ws.readability import fk_grade, sentences, syllables, words
from ws.render import min_child_px
from ws.syllabus import load_level, resolve_page
from ws.verify import banned_words

R3 = load_level("english", "R3")
PASSAGE_SECTIONS = "ACDE"


def test_level_shape():
    assert [s.code for s in R3.sections] == list("ABCDE")
    assert R3.public_name == "Foxes" and all(s.public_name for s in R3.sections)
    assert len(R3.preview_pages) == 4
    assert min_child_px("R3", "english") == 20
    # two grades ahead (CLAUDE.md §15): every section is tagged with grade 3 standards
    for s in R3.sections:
        assert s.standards and all(".3." in c for c in s.standards), s.code


# --- readability ------------------------------------------------------------------------

def test_readability_rules():
    assert sentences('"Wait!" said Mia. Mr. Grant waved. She ran.') == ['"Wait!" said Mia.', "Mr. Grant waved.", "She ran."]
    assert [syllables(w) for w in ["cat", "careful", "table", "jumped", "wanted", "boxes", "beautiful"]] == [1, 2, 2, 1, 2, 2, 4]
    assert words("didn't well-known") == ["didn't", "well-known"]
    assert fk_grade("The cat sat. The dog ran.") < 0 < fk_grade(
        "Grandmother carefully explained the interesting experiment to everyone in the classroom.")


# --- content ------------------------------------------------------------------------------

@pytest.mark.parametrize("code", PASSAGE_SECTIONS)
def test_passages_follow_the_rules(code):
    sec = R3.section(code)
    rules = resolve_page(R3, sec.pages[0]).rules
    ps = section_passages("R3", code)
    assert sum(len(p.pages) for p in ps) == sec.pages[1] - sec.pages[0] + 1
    for p in ps:
        assert passage_problems(p, rules, code) == [], p.id
        text = " ".join([p.title, p.text, p.moral or ""] + [t for s in p.pages for q in s.questions
                                                            for t in [q.ask, q.sample or "", *(q.choices or [])]])
        assert banned_words(text) == [], p.id
        assert {w.lower() for w in words(text)}.isdisjoint(BRITISH), p.id


def test_passage_ids_and_titles_are_unique():
    ps = [p for c in PASSAGE_SECTIONS for p in section_passages("R3", c)]
    assert len(ps) >= 70
    assert len({p.id for p in ps}) == len(ps)
    assert len({p.title for p in ps}) == len(ps)


def test_word_builders_are_hand_checked():
    pool = word_parts("R3")
    known = {w.built for w in pool}
    assert len(known) == len(pool)
    for w in pool:
        assert w.affix in affixes("R3")
        assert wordpart_problems(w, known) == [], w.built
        assert banned_words(w.sentence + " " + w.meaning) == []


# --- generated pages ----------------------------------------------------------------------

def test_every_page_is_planned_and_passes_its_checks():
    plan = gen.build_plan(R3)
    assert not plan.waiting and set(plan.pages) == set(range(1, 201))
    answers: dict[str, Counter] = {c: Counter() for c in "ACD"}
    built: Counter = Counter()
    for page in range(1, 201):
        sheet = gen.build_sheet(R3, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id
        assert sheet.answer_key
        if sheet.section in answers:
            answers[sheet.section].update(i["answer"] for i in sheet.items if i["kind"] == "mc")
        built.update(i["built"] for i in sheet.items if i["kind"] == "build")
    for code, c in answers.items():   # the right answer isn't always in the same place
        assert set(c) == set("ABC") and min(c.values()) >= sum(c.values()) // 5, (code, c)
    assert set(built) == {w.built for w in word_parts("R3")}, "every word builder is used"


@pytest.mark.parametrize("page", [1, 51, 85, 171])   # passage_questions, word_builder (un-, compound), full_sentence_answer
def test_golden(page, out_dir, golden):
    (sheet, path), = gen.generate_pages(R3, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_answer_pages_split_by_height():
    plan = gen.build_plan(R3)
    sheets = [gen.build_sheet(R3, p, plan) for p in range(1, 51)]
    rows = _answer_rows(sheets, by_line=True)
    assert all(r["lines"] for r in rows)
    pages = _answer_pages_by_line(rows)
    assert sum(len(p) for p in pages) == 50 and max(len(p) for p in pages) < 20
