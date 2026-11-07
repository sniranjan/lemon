"""Lions Reading (english R8): two-page spreads (Pandas' passage_spread) for close reading, arguments,
a story in installments and evidence-based paragraph answers."""

from collections import Counter

import pytest

from ws import generate as gen
from ws import registry
from ws.passages import BRITISH
from ws.readability import fk_grade, sentences, words
from ws.render import min_child_px
from ws.spreads import section_spreads, spread_problems
from ws.syllabus import load_level, resolve_page
from ws.verify import banned_words

R8 = load_level("english", "R8")


def _texts(p) -> str:
    return " ".join([p.title, p.text, p.story or ""] + [t for s in p.pages for t in [s.look_for or ""] + [
        t for q in s.questions for t in [q.ask, q.sample or "", q.rubric or "", *(q.choices or []),
                                          *(q.samples or []), *(q.heads or [])]]])


def _section_pages(code: str):
    """(first page, rules) for each passage of a section, in file order."""
    page = R8.section(code).pages[0]
    for p in section_spreads("R8", code):
        yield p, resolve_page(R8, page).rules
        page += 2 * len(p.pages)


def test_level_shape():
    assert [s.code for s in R8.sections] == list("ABCD")
    assert R8.public_name == "Lions" and all(s.public_name for s in R8.sections)
    assert len(R8.preview_pages) == 4
    assert min_child_px("R8", "english") == 20
    for s in R8.sections:   # two grades ahead (CLAUDE.md §15): grade 8 standards only
        assert s.standards and all(".8." in c for c in s.standards), s.code
        assert s.sheet_types == ["passage_spread"]
        assert (s.pages[1] - s.pages[0] + 1) % 2 == 0, "a section is whole spreads"


@pytest.mark.parametrize("code", "ABCD")
def test_passages_follow_the_rules(code):
    sec = R8.section(code)
    ps = section_spreads("R8", code)
    assert sum(len(p.pages) for p in ps) * 2 == sec.pages[1] - sec.pages[0] + 1
    for p, rules in _section_pages(code):
        assert spread_problems(p, rules) == [], p.id
        assert 7.5 <= fk_grade(p.text) <= 9.5, p.id
        assert banned_words(_texts(p)) == [], p.id
        assert {w.lower() for w in words(_texts(p))}.isdisjoint(BRITISH), p.id


def test_paragraph_answers_are_grade_8_models():
    """Explain Why: every set has one paragraph answer, 4–5 sentences with a quote, and a one-line rubric;
    part 1 plans it in Claim / Evidence / Reasoning boxes first."""
    for p, rules in _section_pages("D"):
        for s in p.pages:
            paras = [q for q in s.questions if q.kind == "paragraph"]
            assert len(paras) == 1 and s.questions[-1].kind == "paragraph", p.id
            assert 4 <= len(sentences(paras[0].sample)) <= 5 and '"' in paras[0].sample, p.id
            assert len(paras[0].rubric) <= 120, p.id


def test_the_story_runs_in_order():
    parts = section_spreads("R8", "C")
    assert {p.story for p in parts} == {"The Tower Clock"}
    assert [p.part for p in parts] == list(range(1, len(parts) + 1))
    assert all(p.genre == "story" for p in parts)


def test_arguments_plant_irrelevant_evidence():
    """Weighing Arguments: most arguments ask which sentence is not relevant evidence (RI.8.8)."""
    asks = [q.ask.lower() for p in section_spreads("R8", "B") for s in p.pages for q in s.questions
            if q.kind == "quote"]
    assert sum("not" in a and "relevant" in a for a in asks) >= 8


def test_ids_and_titles_are_unique():
    ps = [p for c in "ABCD" for p in section_spreads("R8", c)]
    assert len({p.id for p in ps}) == len(ps)
    assert len({p.title for p in ps}) == len(ps)


def test_every_page_is_planned_and_passes_its_checks():
    plan = gen.build_plan(R8)
    assert not plan.waiting and set(plan.pages) == set(range(1, 201))
    answers: Counter = Counter()
    for page in range(1, 201):
        sheet = gen.build_sheet(R8, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id
        side = sheet.items[0]["side"]
        assert side == ("read" if page % 2 else "questions")
        if side == "read":
            assert sheet.answer_key is None
            assert ("story" in sheet.items[0]) == (sheet.section == "C")
        else:
            answers.update(i["answer"] for i in sheet.items if i["kind"] in ("mc", "quote"))
    assert set(answers) == set("ABCD") and min(answers.values()) >= sum(answers.values()) // 7, answers


@pytest.mark.parametrize("page", [1, 2, 101, 152])   # excerpt + questions, a story part, plan-then-write
def test_golden(page, out_dir, golden):
    (sheet, path), = gen.generate_pages(R8, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_tips_fit_one_line():
    """A one-line tip leaves the reading page its full height (64 characters at 17px)."""
    for s in R8.sections:
        for key in ("passage_spread", "passage_spread_read"):
            for tip in s.rules["tips"][key]:
                assert len(tip) <= 64, tip
