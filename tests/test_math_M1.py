"""Puppies math (M1): adding and taking-away facts within 20, the fact_drill sheet type."""

import copy

import pytest

from ws import generate as gen
from ws import registry
from ws.syllabus import load_level, resolve_page, sheet_id

M1 = load_level("math", "M1")
CHECK = registry.get("fact_drill").verify


def test_M1_shape():
    assert [s.code for s in M1.sections] == list("ABCDEFGHIJ")
    assert all(s.public_name and s.standards for s in M1.sections)
    assert "2.OA.2" in {c for s in M1.sections for c in s.standards}
    assert sheet_id(M1, M1.section("F"), 111) == "MA-M1-F-001"
    assert len(M1.preview_pages) == 4
    assert resolve_page(M1, 85).rules["amounts"] == [9]


# one golden per layout: bridge (count on), horizontal, vertical, bridge (count back),
# missing numbers, fact families
@pytest.mark.parametrize("page", [1, 11, 12, 111, 181, 191])
def test_golden(page, out_dir, fixture_content, golden):
    (sheet, path), = gen.generate_pages(M1, [page])
    assert CHECK(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_whole_level_passes_and_keeps_to_the_parts(fixture_content):
    plan = gen.build_plan(M1)
    layouts = set()
    for page in range(1, M1.pages + 1):
        sheet = gen.build_sheet(M1, page, plan)
        assert CHECK(sheet) == [], sheet.id
        layouts.add(sheet.items[0]["layout"])
        facts = [f for i in sheet.items for f in i.get("facts", [i])]
        assert all(0 <= f["c"] <= 20 for f in facts)
        assert all(f[f["blank"]] == a for f, a in zip(facts, sheet.answer_key))
        if page <= 110:
            assert {f["op"] for f in facts} == {"+"}
        elif page <= 170:
            assert {f["op"] for f in facts} == {"-"}
    assert layouts == {"horizontal", "vertical", "bridge", "families"}


def test_first_page_of_each_part_uses_its_first_layout(fixture_content):
    plan = gen.build_plan(M1)
    assert gen.build_sheet(M1, 1, plan).items[0]["layout"] == "bridge"
    assert gen.build_sheet(M1, 111, plan).items[0]["layout"] == "bridge"
    assert gen.build_sheet(M1, 121, plan).items[0]["layout"] == "bridge"
    assert gen.build_sheet(M1, 21, plan).items[0]["layout"] == "horizontal"


def test_verify_catches_bad_facts(fixture_content):
    plan = gen.build_plan(M1)
    sheet = gen.build_sheet(M1, 131, plan)   # taking away 4 and 5, from 5–15
    assert CHECK(sheet) == []

    def broken(**change):
        bad = copy.deepcopy(sheet)
        bad.items[0].update(change)
        return [i.message for i in CHECK(bad)]

    a, b = sheet.items[0]["a"], sheet.items[0]["b"]
    assert any("is wrong" in m for m in broken(c=a - b + 1))
    assert any("below zero" in m for m in broken(a=2, b=4, c=-2))
    assert any("amount" in m for m in broken(b=7, c=a - 7))
    assert any("sign" in m for m in broken(op="+", c=a + b))
    bad_key = sheet.model_copy(update={"answer_key": [x + 1 for x in sheet.answer_key]})
    assert any("answer key" in i.message for i in CHECK(bad_key))
    dup = copy.deepcopy(sheet)
    dup.items[1].update({k: dup.items[0][k] for k in ("a", "op", "b", "c", "blank")})
    assert any("twice" in i.message for i in CHECK(dup))


def test_verify_catches_bad_sums_tracks_and_families(fixture_content):
    plan = gen.build_plan(M1)
    adding = gen.build_sheet(M1, 11, plan)   # +4, sums to 20
    bad = copy.deepcopy(adding)
    bad.items[0].update({"a": 17, "b": 4, "c": 21})
    assert any("above 20" in i.message for i in CHECK(bad))

    bridge = gen.build_sheet(M1, 111, plan)
    bad = copy.deepcopy(bridge)
    bad.items[0]["track"] = bad.items[0]["track"][1:]
    assert any("track" in i.message for i in CHECK(bad))

    fams = gen.build_sheet(M1, 191, plan)
    bad = copy.deepcopy(fams)
    bad.items[0]["facts"][2].update({"a": bad.items[0]["facts"][2]["a"] + 1})
    msgs = [i.message for i in CHECK(bad)]
    assert any("four facts" in m for m in msgs) and any("is wrong" in m for m in msgs)
