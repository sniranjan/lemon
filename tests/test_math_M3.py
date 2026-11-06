"""Foxes math (M3): 3-digit column adding and taking away, times and sharing facts, fractions on a
number line and story problems."""

import copy

import pytest

from ws import generate as gen
from ws import registry
from ws.sheet_types.column_arithmetic import across_zero, answer, regroups
from ws.sheet_types.story_problem import evaluate
from ws.syllabus import load_level, resolve_page, sheet_id
from ws.verify import banned_words

M3 = load_level("math", "M3")


def check(sheet):
    return [i.message for i in registry.get(sheet.sheet_type).verify(sheet)]


def test_M3_shape():
    assert [s.code for s in M3.sections] == list("ABCDEFG")
    assert [s.pages for s in M3.sections] == [(1, 30), (31, 60), (61, 90), (91, 140), (141, 170),
                                              (171, 190), (191, 200)]
    assert all(s.public_name and s.standards and s.source == "ours" for s in M3.sections)
    codes = {c for s in M3.sections for c in s.standards}
    assert {"3.NBT.2", "3.OA.1", "3.OA.7", "3.OA.6", "3.NF.1", "3.NF.2", "3.OA.3", "3.OA.8"} <= codes
    assert all(c.startswith("3.") for c in codes)   # grade 3 work (content_grade 3)
    assert M3.public_name == "Foxes" and len(M3.preview_pages) == 4
    assert sheet_id(M3, M3.section("E"), 141) == "MA-M3-E-001"
    assert resolve_page(M3, 105).rules["amounts"] == [7]
    assert banned_words("Foxes M3 page") == ["m3"]


def test_regroup_counting():
    assert regroups("add", [345, 123]) == 0
    assert regroups("add", [358, 125]) == 1     # ones carry
    assert regroups("add", [375, 152]) == 1     # tens carry
    assert regroups("add", [468, 357]) == 2
    assert regroups("sub", [532, 117]) == 1
    assert regroups("sub", [402, 168]) == 2 and across_zero("sub", [402, 168])
    assert not across_zero("sub", [452, 168])


def test_story_expressions():
    assert evaluate("a * b - d", {"a": 3, "b": 6, "d": 4}) == 14
    assert evaluate("c / b * 2", {"c": 12, "b": 3}) == 8
    assert evaluate("d < c", {"d": 3, "c": 4}) is True
    with pytest.raises(ValueError):
        evaluate("c / b", {"c": 7, "b": 2})
    with pytest.raises(ValueError):
        evaluate("__import__('os')", {})


# one golden per layout: column adding, column taking away, skip-count bridge, arrays,
# times backwards (pairs), times families, unit fractions, fill the labels, story problems
@pytest.mark.parametrize("page", [1, 11, 31, 32, 141, 144, 171, 181, 191])
def test_golden(page, out_dir, fixture_content, golden):
    (sheet, path), = gen.generate_pages(M3, [page])
    assert check(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_whole_level_passes_and_keeps_to_the_parts(fixture_content):
    plan = gen.build_plan(M3)
    layouts = set()
    for page in range(1, M3.pages + 1):
        sheet = gen.build_sheet(M3, page, plan)
        assert check(sheet) == [], (sheet.id, check(sheet))
        r = resolve_page(M3, page).rules
        if sheet.sheet_type == "column_arithmetic":
            assert len(sheet.items) == 9
            assert all(1 <= answer(p["op"], p["numbers"]) <= 999 for p in sheet.items)
            assert all(regroups(p["op"], p["numbers"]) in r["regroup_counts"] for p in sheet.items)
        if sheet.sheet_type == "fact_drill":
            layouts.add(sheet.items[0]["layout"])
            facts = [f for i in sheet.items if i["kind"] != "track" for f in i.get("facts", [i])]
            assert all(f["c"] <= 100 and (f["a"] <= 100) for f in facts)
            if page <= 140:
                assert {f["op"] for f in facts} == {"*"}
        if sheet.sheet_type == "fraction_line":
            assert sorted(i["den"] for i in sheet.items) == [2, 3, 4, 6, 8]
        if sheet.sheet_type == "story_problem":
            assert sorted(i["steps"] for i in sheet.items) == [1, 1, 2]
            assert not banned_words(" ".join(i["text"] for i in sheet.items))
    assert layouts == {"skip", "arrays", "horizontal", "vertical", "pairs", "families"}


def test_verify_catches_bad_columns(fixture_content):
    plan = gen.build_plan(M3)
    sheet = gen.build_sheet(M3, 11, plan)   # taking away, 1–2 trades, one through a zero
    assert check(sheet) == []

    def broken(numbers):
        bad = copy.deepcopy(sheet)
        bad.items[0]["numbers"] = numbers
        bad.answer_key[0] = answer("sub", numbers)
        return check(bad)

    assert any("regroup" in m for m in broken([987, 123]))          # no trade on a trading page
    assert any("below" in m for m in broken([210, 420]))
    assert any("outside" in m for m in broken([150, 120]))
    no_zero = copy.deepcopy(sheet)
    for q in no_zero.items:
        if across_zero(q["op"], q["numbers"]):
            q["numbers"][0] += 10
    no_zero.answer_key = [answer(q["op"], q["numbers"]) for q in no_zero.items]
    assert any("through a zero" in m for m in check(no_zero))
    bad_key = sheet.model_copy(update={"answer_key": [x + 1 for x in sheet.answer_key]})
    assert any("answer key" in m for m in check(bad_key))


def test_verify_catches_bad_times_facts(fixture_content):
    plan = gen.build_plan(M3)
    skip = gen.build_sheet(M3, 31, plan)
    bad = copy.deepcopy(skip)
    bad.items[0]["cells"][3] += 1
    assert any("track" in m for m in check(bad))
    bad = copy.deepcopy(skip)
    bad.items[1].update(c=bad.items[1]["c"] + 2)
    assert any("is wrong" in m for m in check(bad))

    arrays = gen.build_sheet(M3, 32, plan)
    bad = copy.deepcopy(arrays)
    bad.items[0]["rows"] += 1
    assert any("rows of" in m for m in check(bad))

    pairs = gen.build_sheet(M3, 141, plan)
    bad = copy.deepcopy(pairs)
    bad.items[0]["facts"][0].update(a=bad.items[0]["facts"][0]["a"] + 1)
    assert any("sharing fact" in m for m in check(bad))

    sharing = gen.build_sheet(M3, 143, plan)   # horizontal sharing facts
    bad = copy.deepcopy(sharing)
    bad.items[0].update(a=bad.items[0]["a"] + 1)
    assert any("even" in m or "is wrong" in m for m in check(bad))


def test_verify_catches_bad_fraction_lines(fixture_content):
    plan = gen.build_plan(M3)
    unit = gen.build_sheet(M3, 171, plan)
    named = next(i for i in unit.items if i["task"] == "name")
    bad = copy.deepcopy(unit)
    next(i for i in bad.items if i["n"] == named["n"])["num"] = 2
    assert any("unit fraction" in m for m in check(bad))
    bad = copy.deepcopy(unit)
    bad.items[0]["ticks"] = bad.items[0]["ticks"][:-1]
    assert any("ticks" in m for m in check(bad))
    bad = copy.deepcopy(unit)
    bad.items[0]["den"] = 5
    assert any("5 parts" in m for m in check(bad))
    bad_key = unit.model_copy(update={"answer_key": list(reversed(unit.answer_key))})
    assert any("answer key" in m for m in check(bad_key))


def test_verify_catches_bad_stories(fixture_content):
    plan = gen.build_plan(M3)
    sheet = gen.build_sheet(M3, 191, plan)
    bad = copy.deepcopy(sheet)
    bad.items[0]["answer"] += 1
    assert any("answer" in m for m in check(bad))
    bad = copy.deepcopy(sheet)
    bad.items[0]["text"] = bad.items[0]["text"].replace(".", "!", 1)
    assert any("text doesn't match" in m for m in check(bad))
    two = next(i for i in sheet.items if i["steps"] == 2)
    bad = copy.deepcopy(sheet)
    item = next(i for i in bad.items if i["n"] == two["n"])
    item["frame"] = next(i for i in sheet.items if i["steps"] == 1)["frame"]
    msgs = check(bad)
    assert any("twice" in m for m in msgs) and any("two-step" in m for m in msgs)
