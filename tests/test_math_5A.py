"""Math 5A (Ducklings math): syllabus shape, part ranges and the number_sequence / ten-frame checks."""

from ws import generate as gen
from ws import registry
from ws.syllabus import load_level, resolve_page, sheet_id

MA5A = load_level("math", "5A")


def test_5A_shape():
    assert [s.code for s in MA5A.sections] == list("ABCDE")
    assert [len(s.parts) for s in MA5A.sections] == [10, 3, 3, 3, 2]
    assert all(s.public_name and s.standards for s in MA5A.sections)
    assert sheet_id(MA5A, MA5A.section("B"), 101) == "MA-5A-B-001"
    assert resolve_page(MA5A, 100).rules["show"] == "ten_frames"
    assert resolve_page(MA5A, 200).rules == {**resolve_page(MA5A, 200).rules, "show": "rods", "max": 100}


def test_5A_parts_and_sequences(fixture_content):
    plan = gen.build_plan(MA5A)
    first = [gen.build_sheet(MA5A, p, plan) for p in range(1, 11)]
    assert all({11, 12} <= {i["n"] for i in s.items} for s in first)   # both new numbers on every page
    assert max(i["n"] for s in first for i in s.items) <= 12
    seq = gen.build_sheet(MA5A, 171, plan)   # D part 2: up to 50, 3 gaps, a track reaches 46+
    assert seq.answer_key == [t["cells"][g] for t in seq.items for g in t["gaps"]]
    assert max(t["cells"][-1] for t in seq.items) >= 46
    assert all(t["cells"][-1] <= 50 and 0 not in t["gaps"] for t in seq.items)


def test_number_sequence_verify_catches_bad_tracks(fixture_content):
    sheet = gen.build_sheet(MA5A, 131, gen.build_plan(MA5A))
    check = registry.get("number_sequence").verify
    assert check(sheet) == []
    bad_key = sheet.model_copy(update={"answer_key": [a + 1 for a in sheet.answer_key]})
    assert any("answer key" in i.message for i in check(bad_key))
    items = [dict(t) for t in sheet.items]
    items[0] = {**items[0], "cells": [c + 30 for c in items[0]["cells"]]}
    assert any("outside" in i.message for i in check(sheet.model_copy(update={"items": items})))
    items[0] = {**sheet.items[0], "cells": sheet.items[0]["cells"][::-1]}
    assert any("counting up" in i.message for i in check(sheet.model_copy(update={"items": items})))


def test_ten_frames_verify(fixture_content):
    sheet = gen.build_sheet(MA5A, 95, gen.build_plan(MA5A))
    check = registry.get("number_read").verify
    assert check(sheet) == []
    items = [dict(i) for i in sheet.items]
    items[0]["frames"] = items[0]["frames"][:-1] + [items[0]["frames"][-1] - 1] if items[0]["ones"] else [10, 9]
    assert any("ten-frames" in i.message for i in check(sheet.model_copy(update={"items": items})))
