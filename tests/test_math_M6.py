"""Pandas math (M6): dividing fractions, ratio tables, rate/percent/equation word problems, percents,
negative numbers, the coordinate plane, expressions and one-step equations."""

import copy
from fractions import Fraction

import pytest

from ws import generate as gen
from ws import registry
from ws.sheet_types._rational import evaluate, fmt, parse, pretty
from ws.sheet_types.coordinate_grid import pixel
from ws.syllabus import load_level, resolve_page, sheet_id
from ws.verify import banned_words, _strings

M6 = load_level("math", "M6")


def check(sheet):
    return [i.message for i in registry.get(sheet.sheet_type).verify(sheet)]


def test_M6_shape():
    assert [s.code for s in M6.sections] == list("ABCDEF")
    assert [s.pages for s in M6.sections] == [(1, 30), (31, 70), (71, 100), (101, 130), (131, 170), (171, 200)]
    assert [s.public_name for s in M6.sections] == [
        "Dividing Fractions", "Ratios and Rates", "Percents", "Below Zero", "Letters for Numbers",
        "One-Step Equations"]
    assert all(s.standards and s.source == "ours" for s in M6.sections)
    for s in M6.sections:
        assert all(p.pages[1] - p.pages[0] == 9 for p in s.parts)   # 10-page parts
    codes = {c for s in M6.sections for c in s.standards}
    assert {"6.NS.1", "6.RP.1", "6.RP.2", "6.RP.3c", "6.NS.5", "6.NS.8", "6.EE.1", "6.EE.2c", "6.EE.7"} <= codes
    assert all(c.startswith("6.") for c in codes)   # grade 6 work (content_grade 6)
    assert M6.public_name == "Pandas" and len(M6.preview_pages) == 4
    assert sheet_id(M6, M6.section("D"), 121) == "MA-M6-D-021"
    assert banned_words("Pandas M6 page") == ["m6"]


def test_exact_numbers():
    assert parse("2 1/2") == Fraction(5, 2) and parse("−3") == -3 and parse("1.25") == Fraction(5, 4)
    assert fmt(Fraction(7, 3)) == "2 1/3" and fmt(Fraction(3, 4)) == "3/4" and fmt(Fraction(6)) == "6"
    assert fmt(Fraction(5, 2), "money") == "2.50" and fmt(Fraction(3), "money") == "3"
    assert fmt(Fraction(1, 8), "decimal") == "0.125"
    with pytest.raises(ValueError):
        fmt(Fraction(1, 3), "decimal")
    assert evaluate("p / 100 * w", {"p": "25", "w": "80"}) == 20
    assert evaluate("a / b", {"a": "3/4", "b": "1/8"}) == 6
    with pytest.raises(ValueError):
        evaluate("__import__('os')", {})
    assert pretty("3*n + 4") == "3n + 4"
    assert pretty("2*(l + w)") == "2(l + w)"
    assert pretty("l*w*h") == "lwh"
    assert pretty("(4 + 5)**2") == "(4 + 5)²"
    assert pretty("7 + 3 * 4") == "7 + 3 × 4"
    assert pretty("x / 4 + 2") == "x ÷ 4 + 2"
    assert pretty("12 - (x - 3)") == "12 − (x − 3)"


# one golden per sheet type and layout
@pytest.mark.parametrize("page", [1, 11, 23, 31, 41, 51, 71, 81, 101, 111, 121, 131, 141, 151, 161, 171, 191, 192])
def test_golden(page, out_dir, fixture_content, golden):
    (sheet, path), = gen.generate_pages(M6, [page])
    assert check(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_whole_level_passes_and_keeps_to_the_parts(fixture_content):
    plan = gen.build_plan(M6)
    types = set()
    for page in range(1, M6.pages + 1):
        sheet = gen.build_sheet(M6, page, plan)
        assert check(sheet) == [], (sheet.id, check(sheet))
        types.add(sheet.sheet_type)
        text = " ".join([sheet.title, sheet.parent_tip, *_strings(sheet.items), *map(str, sheet.answer_key)])
        assert not banned_words(text), (sheet.id, banned_words(text))
        r = resolve_page(M6, page).rules
        if sheet.sheet_type == "equation_solve":
            assert all(parse(e["x"]) > 0 and parse(e["q"]) <= r["max_q"] for e in sheet.items)
        if sheet.sheet_type == "fraction_ops":
            assert all(i["op"] == "div" for i in sheet.items)
        if page > 130 or page <= 100:   # negatives only in Below Zero
            assert not any(str(a).lstrip("$").startswith(("−", "-")) for a in sheet.answer_key), sheet.id
    assert types == {"fraction_ops", "ratio_table", "rational_story", "percent_problem", "signed_numbers",
                     "coordinate_grid", "expression_eval", "equation_solve"}


def test_verify_catches_wrong_answers(fixture_content):
    plan = gen.build_plan(M6)

    def broken(page, change):
        sheet = gen.build_sheet(M6, page, plan)
        assert check(sheet) == []
        bad = copy.deepcopy(sheet)
        change(bad)
        return " ".join(check(bad))

    def frac(b):
        b.answer_key[0] = "99"
    assert "answer key" in broken(11, frac)

    def bar(b):
        b.items[0]["bar"]["shaded"] += 1
    assert "bar" in broken(1, bar)

    def table(b):
        b.items[0]["bottom"][2] += 1
    assert "times its multiplier" in broken(31, table)

    def story(b):
        b.items[0]["answer"] = "1"
    assert "wrong" in broken(51, story)

    def percent(b):
        b.items[0]["part"] += 1
    assert "not" in broken(81, percent)

    def compare(b):
        i = next(i for i in b.items if i["task"] == "compare")
        i["answer"] = "<" if i["answer"] == ">" else ">"
    assert "wrong" in broken(111, compare)

    def point(b):
        b.items[0]["px"] += 38    # drawn one square to the right of its coordinates
    assert "drawn at" in broken(121, point)

    def expr(b):
        b.items[0]["answer"] = str(int(b.items[0]["answer"]) + 1)
    assert "wrong" in broken(131, expr)

    def eq(b):
        b.items[0]["x"] = str(int(b.items[0]["x"]) + 1)
        b.items[0]["answer"] = f"{b.items[0]['letter']} = {b.items[0]['x']}"
    assert "the answer is" in broken(171, eq)


def test_points_are_drawn_at_their_coordinates(fixture_content):
    sheet = gen.build_sheet(M6, 121, gen.build_plan(M6))
    for i in sheet.items:
        if i["kind"] in ("read", "plot"):
            assert (i["px"], i["py"]) == pixel(i["x"], i["y"], 6)
    assert pixel(0, 0, 6)[0] < pixel(1, 0, 6)[0] and pixel(0, 1, 6)[1] < pixel(0, 0, 6)[1]
