"""Owls math (M4): four-digit column adding and taking away, long multiplication, long division,
factors and multiples, fraction bars."""

import copy

import pytest

from ws import generate as gen
from ws import registry
from ws.sheet_types.column_arithmetic import answer as column_answer
from ws.sheet_types.column_arithmetic import regroups
from ws.sheet_types.division_house import start, zero_inside
from ws.sheet_types.factor_pairs import factor_pairs, is_prime
from ws.sheet_types.long_multiplication import carries, partials
from ws.syllabus import load_level, resolve_page, sheet_id
from ws.verify import banned_words

M4 = load_level("math", "M4")


def check(sheet):
    return [i.message for i in registry.get(sheet.sheet_type).verify(sheet)]


def test_M4_shape():
    assert [s.code for s in M4.sections] == list("ABCDEF")
    assert [s.pages for s in M4.sections] == [(1, 20), (21, 60), (61, 100), (101, 150), (151, 170), (171, 200)]
    assert [s.public_name for s in M4.sections] == ["Warm-up", "Multiply by One Digit", "Two-by-Two",
                                                    "Long Division", "Factors and Multiples", "Fraction Friends"]
    assert all(s.standards and s.source == "ours" for s in M4.sections)
    codes = {c for s in M4.sections for c in s.standards}
    assert {"4.NBT.4", "4.NBT.5", "4.NBT.6", "4.OA.4", "4.NF.1", "4.NF.3"} <= codes
    assert all(c.startswith("4.") for c in codes)   # grade 4 work (content_grade 4)
    for s in M4.sections:   # 10-page parts
        assert all(p.pages[1] - p.pages[0] + 1 == 10 for p in s.parts)
    assert M4.public_name == "Owls" and len(M4.preview_pages) == 4
    assert sheet_id(M4, M4.section("D"), 101) == "MA-M4-D-001"
    assert resolve_page(M4, 95).rules["zero_shown"] is False
    assert banned_words("Owls M4 page") == ["m4"]


def test_helpers():
    assert partials("expanded", 47, 6) == [42, 240]
    assert partials("partials", 34, 23) == [102, 680]
    assert carries(47, 6) == [4, 2]
    assert start(156, 4) == 1 and start(832, 4) == 0
    assert zero_inside(208) and zero_inside(280) and not zero_inside(123)
    assert factor_pairs(24) == [[1, 24], [2, 12], [3, 8], [4, 6]]
    assert is_prime(97) and not is_prime(91) and not is_prime(1)
    assert regroups("sub", [5402, 1168]) == 2


# one golden per layout: four-digit adding, multiply in parts, carry layout, times tens, two-by-two,
# division (even, remainders, four digits), factor pairs, primes, fraction bars, equivalence, add/take away
@pytest.mark.parametrize("page", [1, 21, 41, 61, 81, 101, 131, 141, 151, 161, 171, 181, 191])
def test_golden(page, out_dir, fixture_content, golden):
    (sheet, path), = gen.generate_pages(M4, [page])
    assert check(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_whole_level_passes_and_keeps_to_the_parts(fixture_content):
    plan = gen.build_plan(M4)
    for page in range(1, M4.pages + 1):
        sheet = gen.build_sheet(M4, page, plan)
        assert check(sheet) == [], (sheet.id, check(sheet))
        r = resolve_page(M4, page).rules
        assert all("," not in str(a) for a in sheet.answer_key)   # the answers PDF joins entries with ", "
        if sheet.sheet_type == "column_arithmetic":
            assert all(1 <= column_answer(p["op"], p["numbers"]) <= 9999 and p["numbers"][0] >= 1000
                       for p in sheet.items)
        if sheet.sheet_type == "long_multiplication":
            for p in sheet.items:
                assert r["a"][0] <= p["a"] <= r["a"][1] and r["b"][0] <= p["b"] <= r["b"][1]
                assert sum(p["partials"] or [p["a"] * p["b"]]) == p["a"] * p["b"]
        if sheet.sheet_type == "division_house":
            for p in sheet.items:
                assert p["quotient"] * p["divisor"] + p["remainder"] == p["dividend"]
                assert 0 <= p["remainder"] < p["divisor"] <= 9
                assert len(str(p["dividend"])) <= 4
        if sheet.sheet_type == "factor_pairs":
            nums = [n for i in sheet.items for n in i.get("numbers", [i.get("n", 1)])]
            assert all(1 <= n <= 100 for n in nums)
        if sheet.sheet_type == "fraction_bars":
            for i in sheet.items:
                if i["kind"] == "equiv":
                    (a, b), (c, d) = i["left"], i["right"]
                    assert a * d == b * c and {b, d} <= {2, 3, 4, 5, 6, 8, 10, 12, 100}
                if i["kind"] == "op":
                    total = i["a"] + i["c"] if i["op"] == "add" else i["a"] - i["c"]
                    assert 1 <= total <= i["den"]


def test_neighboring_factor_pages_use_different_numbers(fixture_content):
    plan = gen.build_plan(M4)
    seen = [tuple(i["n"] for i in gen.build_sheet(M4, p, plan).items if i["kind"] == "pairs") for p in range(151, 171)]
    for a, b in zip(seen, seen[1:]):
        assert not set(a) & set(b)


def test_verify_catches_bad_multiplication(fixture_content):
    plan = gen.build_plan(M4)
    sheet = gen.build_sheet(M4, 81, plan)   # two-by-two, zero shown
    assert check(sheet) == []
    bad = copy.deepcopy(sheet)
    bad.items[0]["partials"][1] += 10
    assert any("lines" in m for m in check(bad))
    bad = copy.deepcopy(sheet)
    bad.items[0]["b"] = 30
    assert any("0 in the ones" in m for m in check(bad))
    bad = copy.deepcopy(sheet)
    bad.items[0]["cols"] = 3
    assert any("line up" in m for m in check(bad))
    bad = copy.deepcopy(sheet)
    bad.items[0]["zero_shown"] = False
    assert any("printed 0" in m for m in check(bad))
    bad_key = sheet.model_copy(update={"answer_key": list(reversed(sheet.answer_key))})
    assert any("answer key" in m for m in check(bad_key))
    carry = gen.build_sheet(M4, 31, plan)
    bad = copy.deepcopy(carry)
    bad.items[0].update(a=12, b=2, partials=[], carry_cols=[1])
    assert any("no carry" in m for m in check(bad))


def test_verify_catches_bad_division(fixture_content):
    plan = gen.build_plan(M4)
    sheet = gen.build_sheet(M4, 131, plan)   # three-digit, remainders, a 0 inside one answer
    assert check(sheet) == []
    bad = copy.deepcopy(sheet)
    bad.items[0]["quotient"] += 1
    assert any("isn't" in m for m in check(bad))
    bad = copy.deepcopy(sheet)
    item = bad.items[0]
    item.update(quotient=item["quotient"] - 1, remainder=item["remainder"] + item["divisor"])
    assert any("smaller than" in m for m in check(bad))
    bad = copy.deepcopy(sheet)
    bad.items[0]["start"] += 1
    assert any("start over" in m or "line up" in m for m in check(bad))
    bad = copy.deepcopy(sheet)
    for i in bad.items:
        if zero_inside(i["quotient"]):
            i["quotient"] += 10
            i["dividend"] += 10 * i["divisor"]
    assert any("0 inside" in m for m in check(bad))
    even = gen.build_sheet(M4, 101, plan)
    bad = copy.deepcopy(even)
    bad.items[0]["remainder"] = 1
    bad.items[0]["dividend"] += 1
    assert any("divides evenly" in m for m in check(bad))


def test_verify_catches_bad_factors(fixture_content):
    plan = gen.build_plan(M4)
    sheet = gen.build_sheet(M4, 161, plan)   # pairs, prime, circle, pairs
    assert check(sheet) == []
    bad = copy.deepcopy(sheet)
    bad.items[0]["pairs"] = bad.items[0]["pairs"][:-1]
    assert any("factor pairs of" in m for m in check(bad))
    bad = copy.deepcopy(sheet)
    prime = next(i for i in bad.items if i["kind"] == "prime")
    prime["numbers"] = [4, 6, 8]
    assert any("both primes and composites" in m for m in check(bad))
    bad = copy.deepcopy(sheet)
    circle = next(i for i in bad.items if i["kind"] == "circle")
    circle["numbers"] = [circle["base"] * k for k in range(2, 10)]
    assert any("to circle" in m for m in check(bad))


def test_verify_catches_bad_fractions(fixture_content):
    plan = gen.build_plan(M4)
    bars = gen.build_sheet(M4, 171, plan)
    bad = copy.deepcopy(bars)
    bad.items[0]["n"] = 7
    assert any("bar" in m or "bottom numbers" in m for m in check(bad))
    equiv = gen.build_sheet(M4, 181, plan)
    bad = copy.deepcopy(equiv)
    bad.items[0]["right"][0] += 1
    assert any("aren't equal" in m for m in check(bad))
    ops = gen.build_sheet(M4, 191, plan)
    bad = copy.deepcopy(ops)
    add = next(i for i in bad.items if i["kind"] == "op" and i["op"] == "add")
    add["c"] = add["den"]
    assert any("more than one whole" in m for m in check(bad))
    bad = copy.deepcopy(ops)
    bad.items[-1]["bar"] = True
    assert any("show a bar" in m for m in check(bad))
    bad_key = ops.model_copy(update={"answer_key": list(reversed(ops.answer_key))})
    assert any("answer key" in m for m in check(bad_key))
