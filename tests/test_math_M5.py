"""Otters math (M5): long division by two-digit numbers, unlike fractions, fractions times fractions,
decimals (place value, columns, times and sharing), parentheses and volume."""

import copy
from decimal import Decimal
from fractions import Fraction

import pytest

from ws import generate as gen
from ws import registry
from ws.sheet_types import box_volume, decimal_ops, fraction_ops, order_of_operations
from ws.sheet_types._exact import dec_str, frac_str
from ws.sheet_types.decimal_place_value import answer as pv_answer
from ws.syllabus import load_level, resolve_page, sheet_id
from ws.verify import banned_words

M5 = load_level("math", "M5")


def check(sheet):
    return [i.message for i in registry.get(sheet.sheet_type).verify(sheet)]


def test_M5_shape():
    assert [s.code for s in M5.sections] == list("ABCDEF")
    assert [s.pages for s in M5.sections] == [(1, 40), (41, 90), (91, 120), (121, 160), (161, 190), (191, 200)]
    assert all(s.public_name and s.standards and s.source == "ours" for s in M5.sections)
    codes = {c for s in M5.sections for c in s.standards}
    assert {"5.NBT.6", "5.NF.1", "5.NF.4", "5.NBT.7", "5.OA.1", "5.MD.5"} <= codes
    assert all(c.startswith("5.") for c in codes)   # grade 5 work (content_grade 5)
    assert all(p.pages[1] - p.pages[0] == 9 for s in M5.sections for p in s.parts)   # 10-page parts
    assert M5.public_name == "Otters" and len(M5.preview_pages) == 4
    assert sheet_id(M5, M5.section("D"), 131) == "MA-M5-D-011"
    assert resolve_page(M5, 125).sheet_type == "decimal_place_value"
    assert [resolve_page(M5, p).sheet_type for p in (191, 192)] == ["order_of_operations", "box_volume"]
    assert banned_words("Otters M5 page") == ["m5"]


def test_exact_helpers():
    assert frac_str(Fraction(13, 12)) == "1 1/12" and frac_str(Fraction(6, 3)) == "2" and frac_str(Fraction(2, 4)) == "1/2"
    assert dec_str(Decimal("340.00")) == "340" and dec_str(Decimal("4.560")) == "4.56" and dec_str(Decimal(".5")) == "0.5"
    item = {"op": "add", "a": {"whole": 0, "num": 1, "den": 6}, "b": {"whole": 0, "num": 1, "den": 3}}
    assert fraction_ops.answer(item) == Fraction(1, 2) and fraction_ops.needs_simplify(item)
    assert decimal_ops.answer({"op": "÷", "a": "8.4", "b": "4"}) == Decimal("2.1")
    with pytest.raises(ValueError):
        decimal_ops.answer({"op": "÷", "a": "1", "b": "3"})
    assert pv_answer({"task": "value", "x": "6.284", "digit": 3}) == "0.08"
    assert pv_answer({"task": "round", "x": "3.96", "place": "tenth"}) == "4.0"
    assert order_of_operations.evaluate("[(3 + 5) × 2] − 4") == 12
    with pytest.raises(ValueError):
        order_of_operations.evaluate("3 − (5 − 5)")


# one golden per sheet type and layout: dividing by tens, four-digit long division, unlike fractions,
# mixed numbers, whole times fraction, area model, place value, decimal columns (with and without the
# printed point), moving the point, decimal by decimal, parentheses, volume
@pytest.mark.parametrize("page", [1, 31, 41, 81, 91, 101, 121, 131, 151, 161, 181, 191, 192])
def test_golden(page, out_dir, fixture_content, golden):
    (sheet, path), = gen.generate_pages(M5, [page])
    assert check(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_whole_level_passes(fixture_content):
    plan = gen.build_plan(M5)
    for page in range(1, M5.pages + 1):
        sheet = gen.build_sheet(M5, page, plan)
        assert check(sheet) == [], (sheet.id, check(sheet))
        # answers never carry anything that reads like an internal code (R5 is a banned word)
        assert not banned_words(", ".join(map(str, sheet.answer_key))), sheet.answer_key
        if sheet.sheet_type == "long_division_2digit":
            for i, a in zip(sheet.items, sheet.answer_key):
                q, r = divmod(i["dividend"], i["divisor"])
                assert a == (f"{q} R {r}" if r else str(q))
        if sheet.sheet_type == "fraction_ops":
            for a in sheet.answer_key:   # simplest form, mixed numbers when over 1
                whole, _, frac = a.rpartition(" ") if " " in a else ("", "", a)
                if "/" in frac:
                    n, d = map(int, frac.split("/"))
                    assert 0 < n < d and Fraction(n, d).denominator == d


def test_verify_catches_bad_long_division(fixture_content):
    plan = gen.build_plan(M5)
    sheet = gen.build_sheet(M5, 31, plan)
    bad = copy.deepcopy(sheet)
    bad.items[0]["divisor"] = 7
    assert any("divisor" in m for m in check(bad))
    bad = copy.deepcopy(sheet)
    bad.items[0]["dividend"] = 123
    assert any("digits" in m for m in check(bad))
    bad = sheet.model_copy(update={"answer_key": ["1"] + sheet.answer_key[1:]})
    assert any("answer key" in m for m in check(bad))
    no_zero = copy.deepcopy(sheet)
    for i in no_zero.items:
        i["dividend"], i["divisor"] = 1554, 42   # 37, no zero (and repeats)
    assert any("0 inside" in m for m in check(no_zero))


def test_verify_catches_bad_fractions(fixture_content):
    plan = gen.build_plan(M5)
    sheet = gen.build_sheet(M5, 41, plan)   # adding, one denominator goes into the other
    bad = copy.deepcopy(sheet)
    bad.items[0]["b"] = dict(bad.items[0]["a"])
    assert any("unlike" in m or "twice" in m for m in check(bad))
    bad = copy.deepcopy(sheet)
    bad.items[0]["a"] = {"whole": 0, "num": 2, "den": 4}
    assert any("simplest" in m for m in check(bad))
    bad = copy.deepcopy(sheet)
    bad.items[0]["a"], bad.items[0]["b"] = {"whole": 0, "num": 1, "den": 4}, {"whole": 0, "num": 1, "den": 6}
    assert any("goes into" in m for m in check(bad))
    sub = gen.build_sheet(M5, 51, plan)
    bad = copy.deepcopy(sub)
    bad.items[0]["a"], bad.items[0]["b"] = bad.items[0]["b"], bad.items[0]["a"]
    assert any("more than 0" in m for m in check(bad))
    mul = gen.build_sheet(M5, 91, plan)
    bad = mul.model_copy(update={"answer_key": list(reversed(mul.answer_key))})
    assert any("answer key" in m for m in check(bad)) or mul.answer_key == list(reversed(mul.answer_key))


def test_verify_catches_bad_decimals(fixture_content):
    plan = gen.build_plan(M5)
    col = gen.build_sheet(M5, 141, plan)   # taking away, one from a whole number
    bad = copy.deepcopy(col)
    for i in bad.items:
        i["a"] = i["a"] + ".5" if "." not in i["a"] else i["a"]
    assert check(bad)
    bad = copy.deepcopy(col)
    bad.items[0]["cols"] = [1, 1]
    assert any("columns" in m for m in check(bad))
    facts = gen.build_sheet(M5, 161, plan)
    bad = copy.deepcopy(facts)
    bad.items[0]["b"] = "7"
    assert any("10, 100 or 1000" in m for m in check(bad))
    bad = copy.deepcopy(facts)
    bad.answer_key[0] = bad.answer_key[0] + "1"
    assert any("answer key" in m for m in check(bad))
    pv = gen.build_sheet(M5, 121, plan)
    bad = copy.deepcopy(pv)
    rounding = next(i for i in bad.items if i["task"] == "round")
    rounding["x"] = "3.5"
    assert any("thousandths" in m for m in check(bad))


def test_verify_catches_bad_parentheses_and_volume(fixture_content):
    plan = gen.build_plan(M5)
    ops = gen.build_sheet(M5, 191, plan)
    bad = copy.deepcopy(ops)
    bad.items[0]["expr"] = "(2 × 3) + 4"
    assert any("don't change" in m for m in check(bad))
    bad = copy.deepcopy(ops)
    bad.items[0]["expr"] = "(9 − 9) × 4"
    assert check(bad)
    vol = gen.build_sheet(M5, 192, plan)
    bad = copy.deepcopy(vol)
    base = next(i for i in bad.items if i["task"] == "base")
    base["base"] += 1
    assert any("base area" in m for m in check(bad))
    bad = copy.deepcopy(vol)
    two = next(i for i in bad.items if i["task"] == "two_boxes")
    two["dims"][1][1] += 1
    assert any("share a width" in m for m in check(bad))
    assert box_volume.volume({"dims": [[2, 3, 4], [1, 1, 1]]}) == 25
