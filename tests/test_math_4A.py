"""Math 4A (Bunnies Math): syllabus shape, number_trace / number_write goldens and checks."""

import pytest

from ws import generate as gen
from ws import registry
from ws.render import min_child_px
from ws.sheet_types.number_trace import font_chars
from ws.syllabus import load_level, resolve_page, sheet_id

MA4A = load_level("math", "4A")


def test_4A_shape():
    assert [s.code for s in MA4A.sections] == list("ABCDE")
    assert [len(s.parts) for s in MA4A.sections] == [4, 6, 2, 2, 6]
    assert all(s.public_name and s.standards for s in MA4A.sections)
    assert MA4A.public_name == "Bunnies"
    assert sheet_id(MA4A, MA4A.section("B"), 41) == "MA-4A-B-001"
    assert resolve_page(MA4A, 200).rules["max"] == 50
    assert min_child_px("4A", "math") == 28


def test_trace_font_has_every_digit():
    assert set("0123456789") <= font_chars()


@pytest.mark.parametrize("page", [3, 35, 75, 95, 145, 195])
def test_golden(page, out_dir, fixture_content, golden):
    (sheet, path), = gen.generate_pages(MA4A, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_whole_level_passes_type_checks(fixture_content):
    plan = gen.build_plan(MA4A)
    for page in range(1, MA4A.pages + 1):
        sheet = gen.build_sheet(MA4A, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id
        r = resolve_page(MA4A, page).rules
        if sheet.sheet_type == "number_trace":
            assert sheet.answer_key is None
            if page <= 10:
                assert {i["n"] for i in sheet.items} == {1, 2, 3}
        else:
            assert sheet.answer_key


def test_number_trace_verify_catches_bad_rows(fixture_content):
    sheet = gen.build_sheet(MA4A, 25, gen.build_plan(MA4A))   # part 3: 1–7, new 6 and 7
    check = registry.get("number_trace").verify
    assert check(sheet) == []
    items = [{**i, "n": 9} if i["n"] in (6, 7) else i for i in sheet.items]
    msgs = [i.message for i in check(sheet.model_copy(update={"items": items}))]
    assert any("outside" in m for m in msgs) and any("new numbers" in m for m in msgs)


def test_number_write_verify_catches_bad_blocks(fixture_content):
    plan = gen.build_plan(MA4A)
    check = registry.get("number_write").verify
    copy, fill = gen.build_sheet(MA4A, 105, plan), gen.build_sheet(MA4A, 175, plan)
    assert check(copy) == [] and check(fill) == []
    bad_key = fill.model_copy(update={"answer_key": [a + 1 for a in fill.answer_key]})
    assert any("answer key" in i.message for i in check(bad_key))
    items = [dict(t) for t in copy.items]
    items[0] = {**items[0], "numbers": [n + 40 for n in items[0]["numbers"]]}
    assert any("outside" in i.message for i in check(copy.model_copy(update={"items": items})))
    items = [dict(t) for t in fill.items]
    items[0] = {**items[0], "gaps": [0] + items[0]["gaps"][1:]}
    assert any("first box" in i.message for i in check(fill.model_copy(update={"items": items})))
    items[0] = {**fill.items[0], "gaps": [2, 3, 4, 7]}
    assert any("one after another" in i.message for i in check(fill.model_copy(update={"items": items})))


def test_no_duplicate_sheets(fixture_content):
    plan, seen = gen.build_plan(MA4A), set()
    for s in MA4A.sections:
        for sheet in gen.build_section(MA4A, s.code, s.pages[1], plan).values():
            key = repr(sheet.items)
            assert key not in seen, sheet.id
            seen.add(key)


def test_worst_case_pages_render_cleanly(out_dir, fixture_content):
    pytest.importorskip("playwright")
    from ws.render import render_pngs

    made = gen.generate_pages(MA4A, [31, 40, 41, 80, 100, 101, 120, 200])
    for r in render_pngs([p for _, p in made], min_child=28):
        assert r.problems == [], (r.html.name, r.problems)
