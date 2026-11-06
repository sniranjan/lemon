"""Penguins math (M7, grade 7): signed numbers, rational numbers, proportions and percents, tidy
expressions, two-step equations and inequalities. These pages are modes of the Pandas types
(signed_numbers, rational_story, ratio_table, expression_eval, equation_solve)."""

import copy
import re
from fractions import Fraction

import pytest

from ws import generate as gen
from ws import registry
from ws.sheet_types._linear import (MINUS, compute, decimal_text, fmt_lin, lin, read_lin, repeating, show_fact,
                                    tokens)
from ws.sheet_types._rational import evaluate
from ws.syllabus import load_level, resolve_page, sheet_id
from ws.verify import banned_words

M7 = load_level("math", "M7")


def check(sheet):
    return [i.message for i in registry.get(sheet.sheet_type).verify(sheet)]


def test_M7_shape():
    assert [s.code for s in M7.sections] == list("ABCDEF")
    assert [s.pages for s in M7.sections] == [(1, 40), (41, 70), (71, 100), (101, 140), (141, 170), (171, 200)]
    assert all(s.public_name and s.standards and s.source == "ours" for s in M7.sections)
    codes = {c for s in M7.sections for c in s.standards}
    assert all(c.startswith("7.") for c in codes)          # grade 7 work (content_grade 7)
    assert {"7.NS.1a", "7.NS.2d", "7.NS.3", "7.RP.1", "7.RP.2b", "7.RP.3", "7.EE.1", "7.EE.2", "7.EE.4a",
            "7.EE.4b"} <= codes
    assert M7.public_name == "Penguins" and len(M7.preview_pages) == 4
    assert all(len(p.pages) == 2 and p.pages[1] - p.pages[0] == 9 for s in M7.sections for p in s.parts)
    assert sheet_id(M7, M7.section("D"), 111) == "MA-M7-D-011"
    assert resolve_page(M7, 191).rules["inequality"] is True
    assert banned_words("Penguins M7 page") == ["m7"]


def test_linear_expressions():
    e = lin("-2*(x - 4) + 3*x")
    assert fmt_lin(e) == "x + 8" and read_lin("x + 8") == e
    assert fmt_lin(lin("1/2*n + 3/4*n - 1/3")) == f"5/4n {MINUS} 1/3"
    assert fmt_lin(lin("t + 0.05*t"), "decimal") == "1.05t"
    assert fmt_lin(lin("-x + 0")) == f"{MINUS}x"
    assert read_lin("3(2x + 3)") == lin("6*x + 9")
    with pytest.raises(ValueError):
        lin("x*x")


def test_signed_numbers_and_decimals():
    assert compute(["-12", "3", "-5"], ["/", "+"]) == -9            # × ÷ before + −
    assert show_fact(["5", "-3"], ["-"]) == f"5 {MINUS} ({MINUS}3)"
    assert repeating(Fraction(5, 6)) == ("0", "8", "3")
    assert decimal_text(Fraction(-1, 3)) == f"{MINUS}0.(3) repeating"
    assert decimal_text(Fraction(3, 8)) == "0.375"
    assert tokens(f"{MINUS}3/4 + x/4") == [MINUS, {"n": 3, "d": 4}, " + ", {"n": "x", "d": 4}]
    assert evaluate("floor((m - f) / c)", {"m": 30, "f": 5, "c": "2"}) == 12
    assert evaluate("ceil(7 / 2)") == 4


# one golden per kind of page: number-line adding, adding the opposite, the sign pattern, three-number
# chains, signed fractions, fractions as decimals, negatives in stories, unit rates, proportional tables,
# percent change, money percents, like terms, factoring, two-step equations, brackets and x/p,
# inequalities, inequality stories
@pytest.mark.parametrize("page", [1, 11, 41, 61, 71, 91, 92, 101, 111, 121, 131, 141, 161, 171, 181, 191, 193])
def test_golden(page, out_dir, fixture_content, golden):
    (sheet, path), = gen.generate_pages(M7, [page])
    assert check(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def _printed(sheet) -> str:
    """The text a child reads: story text and the plain pieces of printed math (tokens)."""
    out = []

    def walk(v):
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    for i in sheet.items:
        walk(i.get("text"))
        walk(i.get("show"))
    return " ".join(out)


def test_whole_level_passes(fixture_content):
    plan = gen.build_plan(M7)
    types = set()
    for page in range(1, M7.pages + 1):
        sheet = gen.build_sheet(M7, page, plan)
        assert check(sheet) == [], (sheet.id, check(sheet))
        types.add(sheet.sheet_type)
        printed = _printed(sheet) + " " + " ".join(map(str, sheet.answer_key or []))
        assert not re.search(r"(^|[\s(=+×÷$])-\s?[\d(]", printed), (sheet.id, printed)   # real minus signs only
        assert not banned_words(printed + " " + sheet.title + " " + sheet.parent_tip), sheet.id
        assert sheet.answer_key
    assert types == {"signed_numbers", "rational_story", "ratio_table", "expression_eval", "equation_solve"}


def test_verify_catches_wrong_answers(fixture_content):
    plan = gen.build_plan(M7)

    signed = gen.build_sheet(M7, 21, plan)
    bad = copy.deepcopy(signed)
    bad.items[0]["answer"] = "999"
    assert any("wrong" in m for m in check(bad))
    no_neg = copy.deepcopy(signed)
    no_neg.items[0].update(operands=["3", "4"], ops=["+"])
    assert any("no negative" in m for m in check(no_neg))

    tidy = gen.build_sheet(M7, 141, plan)
    bad = copy.deepcopy(tidy)
    bad.items[0]["answer"] = bad.items[0]["answer"].replace(MINUS, "+", 1) + " + 1"
    assert any("tidy form" in m for m in check(bad))

    factor = gen.build_sheet(M7, 161, plan)
    item = next(i for i in factor.items if i["task"] == "factor")
    g = int(item["answer"].split("(")[0])
    if g % 2 == 0:
        bad = copy.deepcopy(factor)
        k = next(i for i, x in enumerate(bad.items) if x is not None and x["task"] == "factor" and x["n"] == item["n"])
        inner = lin(item["src"]).scale(Fraction(2, g))
        bad.items[k]["answer"] = f"2({fmt_lin(inner)})"
        assert any("greatest common factor" in m for m in check(bad))

    ineq = gen.build_sheet(M7, 191, plan)
    bad = copy.deepcopy(ineq)
    neg = next(i for i in bad.items if int(i["p"]) < 0)
    neg["solved"] = neg["symbol"]                         # forgot to turn the sign around
    assert any("solving gives" in m for m in check(bad))

    table = gen.build_sheet(M7, 111, plan)
    bad = copy.deepcopy(table)
    t = next(t for t in bad.items if t["proportional"])
    t["y"][0] = f"{float(t['y'][0]) + 1:.2f}" if "." in t["y"][0] else str(int(t["y"][0]) + 1)
    assert any("isn't always" in m for m in check(bad))

    story = gen.build_sheet(M7, 121, plan)
    bad = copy.deepcopy(story)
    bad.items[0]["answer"] = "1%"
    assert any("wrong" in m for m in check(bad))
