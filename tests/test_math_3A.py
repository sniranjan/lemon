"""Math 3A (Kittens math): syllabus shape, next_number and add_facts (golden output + checks)."""

import pytest

from ws import generate as gen
from ws import registry
from ws.sheet_types.add_facts import fact_shape
from ws.syllabus import load_level, resolve_page, sheet_id

MA3A = load_level("math", "3A")


def test_3A_shape():
    assert [s.code for s in MA3A.sections] == list("ABCDEF")
    assert [len(s.parts) for s in MA3A.sections] == [6, 1, 6, 3, 2, 2]
    assert all(s.public_name and s.standards for s in MA3A.sections)
    assert sheet_id(MA3A, MA3A.section("C"), 71) == "MA-3A-C-001"
    # §8 example: 3A-C part 2 is n + 1 with n ≤ 17
    r = resolve_page(MA3A, 85).rules
    assert (r["addend"], r["max_first"]) == (1, 17)
    assert resolve_page(MA3A, 130).rules["max_first"] == 999


@pytest.mark.parametrize("page", [1, 71, 181])   # next_number run, bridged +1, mixed +1/+2/+3
def test_golden_3A(page, out_dir, fixture_content, golden):
    (sheet, path), = gen.generate_pages(MA3A, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_whole_3A_passes_type_checks(fixture_content):
    plan = gen.build_plan(MA3A)
    for page in range(1, MA3A.pages + 1):
        sheet = gen.build_sheet(MA3A, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id


def test_bridge_pairs_and_answers(fixture_content):
    sheet = gen.build_sheet(MA3A, 71, gen.build_plan(MA3A))
    assert all(i["bridge"] and i["b"] == 1 for i in sheet.items)
    assert sheet.answer_key == [x for i in sheet.items for x in (i["a"] + 1, i["a"] + 1)]
    assert "→" not in sheet.title


def test_add_facts_verify_catches_mistakes(fixture_content):
    sheet = gen.build_sheet(MA3A, 85, gen.build_plan(MA3A))   # C part 2: n + 1, n ≤ 17
    check = registry.get("add_facts").verify
    assert check(sheet) == []
    bad_key = sheet.model_copy(update={"answer_key": [a + 1 for a in sheet.answer_key]})
    assert any("answer key" in i.message for i in check(bad_key))
    items = [dict(i) for i in sheet.items]
    items[-1] = {**items[-1], "a": 18}
    assert any("first number outside" in i.message for i in check(sheet.model_copy(update={"items": items})))
    items = [dict(i) for i in sheet.items]
    items[-1] = {**items[-1], "b": 2}
    assert any("second number" in i.message for i in check(sheet.model_copy(update={"items": items})))


def test_next_number_verify_catches_mistakes(fixture_content):
    sheet = gen.build_sheet(MA3A, 61, gen.build_plan(MA3A))   # B: up to 120
    check = registry.get("next_number").verify
    assert check(sheet) == []
    assert all(71 <= i["n"] <= 119 for i in sheet.items)
    bad_key = sheet.model_copy(update={"answer_key": [i["n"] for i in sheet.items]})
    assert any("answer key" in i.message for i in check(bad_key))
    items = [dict(i) for i in sheet.items]
    items[0] = {**items[0], "n": 120}
    assert any("outside" in i.message for i in check(sheet.model_copy(update={"items": items})))


def test_fact_shape_is_general():
    s = fact_shape({"op": "-", "second": [1, 2], "min_first": 0, "max_first": 3})
    assert (0, 1) not in s["facts"] and (3, 2) in s["facts"] and s["count"] == 10
    with pytest.raises(ValueError, match="bridge"):
        fact_shape({"addend": 2, "max_first": 9, "bridge": 2})
