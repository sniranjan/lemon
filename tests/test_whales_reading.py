"""Whales Reading (english R9): grade 9 two-page passages (Pandas' passage_spread), rhetoric texts and
analytical paragraphs with a claim, two quotes and an explanation."""

from collections import Counter

import pytest

from ws import generate as gen
from ws import registry
from ws.passages import BRITISH
from ws.readability import fk_grade, words
from ws.render import min_child_px
from ws.spreads import section_spreads, spread_problems
from ws.syllabus import load_level, resolve_page
from ws.verify import banned_words

R9 = load_level("english", "R9")


def _texts(p) -> str:
    return " ".join([p.title, p.text] + [t for s in p.pages for t in [s.look_for or ""] + [
        t for q in s.questions for t in [q.ask, q.sample or "", q.rubric or "", *(q.choices or []),
                                          *(q.samples or []), *(q.heads or [])]]])


def test_level_shape():
    assert [s.code for s in R9.sections] == list("ABCD")
    assert R9.public_name == "Whales" and all(s.public_name for s in R9.sections)
    assert len(R9.preview_pages) == 4
    assert min_child_px("R9", "english") == 20
    # two grades ahead of age 12 (CLAUDE.md §15): every section is tagged with grade 9–10 standards
    for s in R9.sections:
        assert s.standards and all(".9-10." in c for c in s.standards), s.code
        assert s.sheet_types == ["passage_spread"]
        assert (s.pages[1] - s.pages[0] + 1) % 2 == 0, "a section is whole spreads"


@pytest.mark.parametrize("code", "ABCD")
def test_passages_follow_the_rules(code):
    """Each question set is checked with the rules of the page it lands on (section D has two parts)."""
    sec = R9.section(code)
    ps = section_spreads("R9", code)
    assert sum(len(p.pages) for p in ps) * 2 == sec.pages[1] - sec.pages[0] + 1
    page = sec.pages[0]
    for p in ps:
        assert 8.5 <= fk_grade(p.text) <= 10.5, p.id
        for k in range(len(p.pages)):
            probs = spread_problems(p, resolve_page(R9, page).rules)
            assert [m for m in probs if f"set {k + 1}:" in m or " set " not in m] == [], (p.id, k)
            page += 2
        assert banned_words(_texts(p)) == [], p.id
        assert {w.lower() for w in words(_texts(p))}.isdisjoint(BRITISH), p.id


def test_passage_ids_and_titles_are_unique():
    ps = [p for c in "ABCD" for p in section_spreads("R9", c)]
    assert len({p.id for p in ps}) == len(ps) == len({p.title for p in ps})


def test_analytical_paragraph_rules():
    """Section D: 5–7 sentences, two exact quotes, a rubric naming claim, evidence and explanation."""
    p = section_spreads("R9", "D")[0]
    rules = resolve_page(R9, 151).rules
    assert spread_problems(p, rules) == []
    q = p.pages[0].questions[1]
    short = p.model_copy(deep=True)
    short.pages[0].questions[1] = q.model_copy(update={"sample": ". ".join(q.sample.split(". ")[:2]),
                                                       "rubric": "a claim and a quote"})
    msgs = " ".join(spread_problems(short, rules))
    assert "needs 5–7" in msgs and "needs 2" in msgs and "'Claim:'" in msgs
    # the defaults (Pandas Reading) are unchanged: 3–4 sentences, one quote, any rubric
    assert "needs 3–4" in " ".join(spread_problems(p, {k: v for k, v in rules.items()
                                                       if k not in ("paragraph_sentences", "paragraph_quotes",
                                                                    "rubric_parts")}))


def test_every_page_is_planned_and_passes_its_checks():
    plan = gen.build_plan(R9)
    assert not plan.waiting and set(plan.pages) == set(range(1, 201))
    answers: Counter = Counter()
    kinds: Counter = Counter()
    for page in range(1, 201):
        sheet = gen.build_sheet(R9, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id
        side = sheet.items[0]["side"]
        assert side == ("read" if page % 2 else "questions")
        if side == "questions":
            answers.update(i["answer"] for i in sheet.items if i["kind"] in ("mc", "quote"))
            kinds.update(i["kind"] for i in sheet.items[1:])
            if page > 150:
                assert [i["kind"] for i in sheet.items[1:]] == (["organizer", "paragraph"] if page <= 170
                                                                else ["quote", "paragraph"]), sheet.id
                assert sheet.items[2]["lines"] == 9
    assert set(answers) == set("ABCD") and min(answers.values()) >= sum(answers.values()) // 7, answers
    assert kinds["paragraph"] >= 50


@pytest.mark.parametrize("page", [1, 2, 102, 152, 172])
def test_golden(page, out_dir, golden):
    (sheet, path), = gen.generate_pages(R9, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_tips_fit_one_line():
    """A one-line tip leaves the reading page its full height (64 characters at 17px)."""
    for s in R9.sections:
        for kind in ("passage_spread", "passage_spread_read"):
            for tip in s.rules["tips"].get(kind, []):
                assert len(tip) <= 64, tip
