"""Owls Reading (english R4): chapter stories, word detective, true facts, two texts, the big idea."""

from collections import Counter

import pytest

from ws import generate as gen
from ws import registry
from ws.longreads import LongRead, read_problems, section_reads, split_targets
from ws.passages import BRITISH
from ws.readability import words
from ws.render import min_child_px
from ws.syllabus import load_level, resolve_page
from ws.verify import banned_words

R4 = load_level("english", "R4")
SPREAD = "ACD"


def test_level_shape():
    assert [s.code for s in R4.sections] == list("ABCDE")
    assert R4.public_name == "Owls" and all(s.public_name for s in R4.sections)
    assert len(R4.preview_pages) == 4
    assert min_child_px("R4", "english") == 20
    # two grades ahead (CLAUDE.md §15): every section is tagged with grade 4 standards
    for s in R4.sections:
        assert s.standards and all(".4." in c for c in s.standards), s.code
    # a spread section starts on a reading page and has whole pairs, so read/questions never slip
    for code in SPREAD:
        lo, hi = R4.section(code).pages
        assert (hi - lo + 1) % 2 == 0
        assert resolve_page(R4, lo).sheet_type == "long_read_page"
        assert resolve_page(R4, lo + 1).sheet_type == "look_back_questions"


def test_split_targets_bolds_whole_words_only():
    assert split_targets("A timid cat, timidly.", ["timid"]) == [("A ", False), ("timid", True), (" cat, timidly.", False)]
    assert split_targets("No targets here.", []) == [("No targets here.", False)]


def test_figure_and_read_shapes_are_validated():
    with pytest.raises(ValueError):
        LongRead.model_validate({"id": "x", "title": "X", "pages": []})          # no text
    with pytest.raises(ValueError):
        LongRead.model_validate({"id": "x", "title": "X", "text": "Hi.", "pages": [],
                                 "figure": {"kind": "bars", "title": "T", "caption": "C",
                                            "rows": [["a", "three"], ["b", "4"]], "unit": "feet"}})


# --- content ------------------------------------------------------------------------------

@pytest.mark.parametrize("code", "ABCDE")
def test_reads_follow_the_rules(code):
    sec = R4.section(code)
    rules = resolve_page(R4, sec.pages[0]).rules
    reads = section_reads("R4", code)
    per = 2 if rules.get("spread") else None
    assert sum(per or len(p.pages) for p in reads) == sec.pages[1] - sec.pages[0] + 1
    page = sec.pages[0]
    for p in reads:
        assert read_problems(p, resolve_page(R4, page).rules) == [], p.id   # part rules (starters) by page
        page += per or len(p.pages)
        text = " ".join(p.all_strings() + [t for s in p.pages for q in s.questions
                                           for t in [q.ask, q.sample or "", q.starter or "", *(q.choices or [])]])
        assert banned_words(text) == [], p.id
        assert {w.lower() for w in words(text)}.isdisjoint(BRITISH), p.id


def test_read_ids_and_titles_are_unique():
    reads = [p for c in "ABCDE" for p in section_reads("R4", c)]
    assert len({p.id for p in reads}) == len(reads)
    assert len({p.title for p in reads}) == len(reads)


def test_chapter_stories_run_in_order():
    by_story: dict[str, list[int]] = {}
    for p in section_reads("R4", "A"):
        by_story.setdefault(p.story, []).append(p.chapter)
    assert len(by_story) >= 3
    for story, chapters in by_story.items():
        assert chapters == list(range(1, len(chapters) + 1)), story


def test_word_detective_words_are_all_different():
    targets = [t for p in section_reads("R4", "B") for s in p.pages for t in s.targets]
    assert len(targets) == len(set(targets)) == 80


# --- generated pages ----------------------------------------------------------------------

def test_every_page_is_planned_and_passes_its_checks():
    plan = gen.build_plan(R4)
    assert not plan.waiting and set(plan.pages) == set(range(1, 201))
    answers: dict[str, Counter] = {c: Counter() for c in "ABCDE"}
    for page in range(1, 201):
        sheet = gen.build_sheet(R4, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id
        if sheet.sheet_type == "long_read_page":
            assert not sheet.answer_key and len(sheet.items) == 1
            nxt = gen.build_sheet(R4, page + 1, plan)
            assert nxt.sheet_type == "look_back_questions" and nxt.items[0]["read"] == sheet.items[0]["read"]
        else:
            assert sheet.answer_key
        answers[sheet.section].update(i["answer"] for i in sheet.items if i["kind"] == "mc")
    for code, c in answers.items():   # the right answer isn't always in the same place
        assert set(c) == set("ABC") and min(c.values()) >= sum(c.values()) // 5, (code, c)


@pytest.mark.parametrize("page", [1, 2, 61, 101, 141, 171])
def test_golden(page, out_dir, golden):
    (sheet, path), = gen.generate_pages(R4, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")
