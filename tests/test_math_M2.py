"""Cubs math (M2): syllabus shape, regrouping rules per part, and the checks of the four new sheet types."""

import pytest

from ws import generate as gen
from ws import registry
from ws.sheet_types.column_arithmetic import answer, regroups
from ws.sheet_types.place_value import number_name, parts
from ws.syllabus import load_level, resolve_page, sheet_id

M2 = load_level("math", "M2")


def _sheet(page):
    return gen.build_sheet(M2, page, gen.build_plan(M2))


def test_M2_shape():
    assert [s.code for s in M2.sections] == list("ABCDEFGH")
    assert all(s.public_name and s.standards for s in M2.sections)
    assert all(c.startswith("2.") for s in M2.sections[1:] for c in s.standards)
    assert len(M2.preview_pages) == 4
    assert sheet_id(M2, M2.section("D"), 71) == "MA-M2-D-001"
    assert M2.public_name == "Cubs"


def test_regroups_and_names():
    assert regroups("add", [47, 5]) == 1 and regroups("add", [42, 5]) == 0
    assert regroups("add", [17, 32, 18]) == 1
    assert regroups("sub", [52, 17]) == 1 and regroups("sub", [57, 12]) == 0
    assert regroups("sub", [402, 158]) == 2          # borrowing across a zero counts twice
    assert answer("sub", [402, 158]) == 244
    assert number_name(347) == "three hundred forty-seven" and number_name(14) == "fourteen"
    assert number_name(700) == "seven hundred" and parts(307) == [300, 7]


@pytest.mark.parametrize("first,last,regroup", [(71, 80, False), (81, 90, True), (91, 100, False),
                                                (101, 110, True), (131, 150, False), (151, 170, True),
                                                (171, 175, False), (176, 180, True), (181, 185, False),
                                                (186, 190, True)])
def test_regrouping_per_part(first, last, regroup, fixture_content):
    for page in range(first, last + 1):
        sheet = _sheet(page)
        rules = resolve_page(M2, page).rules
        for item in sheet.items:
            r = regroups(item["op"], item["numbers"])
            assert (r > 0) == regroup, (sheet.id, item)
            assert r <= 1 and answer(item["op"], item["numbers"]) >= 1
            assert item["boxes"] == regroup
            assert answer(item["op"], item["numbers"]) <= rules.get("max_answer", 10**6)


def test_column_verify_catches_errors(fixture_content):
    sheet = _sheet(85)   # adding ones, every problem carries
    check = registry.get("column_arithmetic").verify
    assert check(sheet) == []
    bad_key = sheet.model_copy(update={"answer_key": [a + 1 for a in sheet.answer_key]})
    assert any("answer key" in i.message for i in check(bad_key))
    items = [dict(i) for i in sheet.items]
    items[0]["numbers"] = [42, 5]   # no carry on a carrying page
    assert any("doesn't regroup" in i.message for i in check(sheet.model_copy(update={"items": items})))
    items[0]["numbers"] = [95, 9]   # answer over 99
    assert any("above 99" in i.message for i in check(sheet.model_copy(update={"items": items})))
    items = [dict(i) for i in sheet.items]
    items[0]["boxes"] = False
    assert any("boxes" in i.message for i in check(sheet.model_copy(update={"items": items})))
    sub = _sheet(165)
    items = [dict(i) for i in sub.items]
    items[0]["numbers"] = [30, 45]  # would be negative
    assert any("below 1" in i.message or "outside" in i.message
               for i in check(sub.model_copy(update={"items": items})))


def test_place_value_verify_catches_errors(fixture_content):
    check = registry.get("place_value").verify
    blocks = _sheet(25)
    assert check(blocks) == []
    items = [dict(i) for i in blocks.items]
    items[0]["places"] = [items[0]["places"][0], (items[0]["places"][1] + 1) % 10, items[0]["places"][2]]
    assert any("don't show" in i.message for i in check(blocks.model_copy(update={"items": items})))
    expanded = _sheet(36)
    assert check(expanded) == []
    items = [dict(i) for i in expanded.items]
    named = next(k for k, i in enumerate(items) if i["form"] == "name_to_number")
    items[named]["name"] = "ten"
    assert any("not the name" in i.message for i in check(expanded.model_copy(update={"items": items})))
    compare = _sheet(44)
    assert check(compare) == []
    flipped = ["<" if s == ">" else ">" if s == "<" else s for s in compare.answer_key]
    assert any("answer key" in i.message for i in check(compare.model_copy(update={"answer_key": flipped})))


def test_skip_count_and_story_verify(fixture_content):
    skip = _sheet(66)
    check = registry.get("skip_count").verify
    assert check(skip) == []
    items = [dict(i) for i in skip.items]
    items[0]["cells"] = [c + 1 for c in items[0]["cells"]]
    assert any("multiple" in i.message for i in check(skip.model_copy(update={"items": items})))
    story = _sheet(191)
    check = registry.get("math_story").verify
    assert check(story) == []
    items = [dict(i) for i in story.items]
    items[0]["a"] += 1   # text no longer matches
    assert check(story.model_copy(update={"items": items}))
