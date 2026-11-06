"""Otters Reading (english R5): two-page spreads, clue words, figurative language, paragraph summaries."""

from collections import Counter

import pytest

from ws import generate as gen
from ws import registry
from ws.booklet import _answer_pages_by_line, _answer_rows
from ws.passages import (
    BRITISH, find_phrase, mark_segments, paragraph_problems, passage_problems, section_passages,
)
from ws.readability import words
from ws.render import min_child_px
from ws.sheet_types.figurative_language import KINDS, figure_problems, figures
from ws.syllabus import load_level, resolve_page
from ws.verify import banned_words

R5 = load_level("english", "R5")
SPREADS = "AC"


def _text(p) -> str:
    return " ".join([p.title, p.text, p.moral or ""] + [t for s in p.pages for q in s.questions
                                                        for t in [q.ask, q.sample or "", *(q.choices or [])]])


def test_level_shape():
    assert [s.code for s in R5.sections] == list("ABCDE")
    assert R5.public_name == "Otters" and all(s.public_name for s in R5.sections)
    assert len(R5.preview_pages) == 4
    assert min_child_px("R5", "english") == 20
    # two grades ahead (CLAUDE.md §15): every section is tagged with grade 5 standards
    for s in R5.sections:
        assert s.standards and all(".5." in c for c in s.standards), s.code
    for s in R5.sections:   # spreads need whole pairs: every section starts on an odd page with an even length
        assert s.pages[0] % 2 == 1 and (s.pages[1] - s.pages[0] + 1) % 2 == 0


# --- helpers ------------------------------------------------------------------------------

def test_find_phrase_and_marks():
    text = "A blanket of fog rolled in. The fog was thick, and the blanket was warm."
    assert find_phrase("a blanket of fog", text).start() == 0
    assert find_phrase("blanket", "blankets everywhere") is None
    assert find_phrase("the fog", "the\n  fog") is not None
    segs = mark_segments(["The bank by the river.", "The bank was open."], ["bank", "river"])
    assert segs == [[["The ", False], ["bank", True], [" by the ", False], ["river", True], [".", False]],
                    [["The bank was open.", False]]]


def test_paragraph_references():
    p = section_passages("R5", "A")[0]
    q = p.pages[0].questions[0]
    assert "paragraph 1" in q.ask and paragraph_problems(p, q) == []
    wrong = q.model_copy(update={"ask": "According to paragraph 3, what keeps most sea mammals warm?"})
    assert paragraph_problems(p, wrong)
    beyond = q.model_copy(update={"ask": "In paragraph 9, what happens?"})
    assert paragraph_problems(p, beyond)


# --- content ------------------------------------------------------------------------------

def _passages_with_rules(code):
    sec = R5.section(code)
    page = sec.pages[0]
    for p in section_passages("R5", code):
        rules = resolve_page(R5, page).rules
        yield p, rules
        page += rules["pages_per_passage"]


@pytest.mark.parametrize("code", "ABCDE")
def test_passages_follow_the_rules(code):
    sec = R5.section(code)
    ps = list(_passages_with_rules(code))
    pages = sum(r["pages_per_passage"] for _, r in ps)
    assert pages == sec.pages[1] - sec.pages[0] + 1
    for p, rules in ps:
        assert passage_problems(p, rules, code) == [], p.id
        assert banned_words(_text(p)) == [], p.id
        assert {w.lower() for w in words(_text(p))}.isdisjoint(BRITISH), p.id
        assert p.kind in ("story", "article"), p.id
        if code == "D":
            assert figure_problems(p, "R5", rules["kinds"]) == [], p.id
        if code == "E":
            assert len(p.paragraphs) == 3, p.id
        if "marks" in rules:
            for s in p.pages:
                assert rules["marks"][0] <= len(s.words) <= rules["marks"][1], p.id
        if code in SPREADS:
            assert len(p.pages) == 1 and len(p.pages[0].questions) == 5, p.id


def test_passage_ids_and_titles_are_unique():
    ps = [p for c in "ABCDE" for p in section_passages("R5", c)]
    assert len(ps) == 25 + 20 + 20 + 15 + 20
    assert len({p.id for p in ps}) == len(ps)
    assert len({p.title for p in ps}) == len(ps)
    themes = [p.moral for p in section_passages("R5", "C")]
    assert all(themes) and len(set(themes)) == len(themes)


def test_figurative_list_is_used_and_clean():
    table = figures("R5")
    used = Counter(w.lower() for p in section_passages("R5", "D") for s in p.pages for w in s.words)
    assert set(used) == {k.lower() for k in table}, "every listed phrase is used, and only listed phrases"
    assert max(used.values()) == 1, "each phrase is bold on one page only"
    for f in table.values():
        assert f.kind in KINDS and f.meaning and len(f.meaning) <= 44, f.phrase
        assert banned_words(f.phrase + " " + f.meaning) == [], f.phrase
    kinds = Counter(f.kind for f in table.values())
    assert kinds["simile"] >= 5 and kinds["metaphor"] >= 5 and kinds["idiom"] >= 5


# --- generated pages ----------------------------------------------------------------------

def test_every_page_is_planned_and_passes_its_checks():
    plan = gen.build_plan(R5)
    assert not plan.waiting and set(plan.pages) == set(range(1, 201))
    answers: dict[str, Counter] = {c: Counter() for c in "ABCDE"}
    for page in range(1, 201):
        sheet = gen.build_sheet(R5, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id
        role = sheet.items[0].get("role")
        if role == "read":
            assert sheet.answer_key is None and len(sheet.items) == 1
        else:
            assert sheet.answer_key
        answers[sheet.section].update(i["answer"] for i in sheet.items if i["kind"] == "mc")
    for code, c in answers.items():   # the right answer isn't always in the same place
        assert set(c) == set("ABC") and min(c.values()) >= sum(c.values()) // 5, (code, c)


def test_spreads_pair_a_reading_page_with_its_questions():
    plan = gen.build_plan(R5)
    for code in SPREADS:
        sec = R5.section(code)
        for page in range(sec.pages[0], sec.pages[1] + 1, 2):
            read, ask = plan.pages[page].extra, plan.pages[page + 1].extra
            assert (read["role"], ask["role"]) == ("read", "questions")
            assert read["passage"] == ask["passage"]
    sheet = gen.build_sheet(R5, 2, plan)
    assert sheet.items[0] == {"kind": "look_back", "role": "questions", "passage": "a01-sea-otter-coats", "set": 0,
                              "heading": "How Sea Otters Stay Warm", "read_page": 1, "text": "article"}


@pytest.mark.parametrize("page", [1, 2, 51, 131, 161])   # read_then_answer (both pages), clue_words, figurative, summary
def test_golden(page, out_dir, golden):
    (sheet, path), = gen.generate_pages(R5, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_answers_skip_reading_pages():
    plan = gen.build_plan(R5)
    sheets = [gen.build_sheet(R5, p, plan) for p in range(1, 51)]
    rows = _answer_rows([s for s in sheets if s.answer_key], by_line=True)
    assert [r["page"] for r in rows] == list(range(2, 51, 2))
    pages = _answer_pages_by_line(rows)
    assert sum(len(p) for p in pages) == 25
