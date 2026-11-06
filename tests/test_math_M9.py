"""Whales math (M9, Algebra 1): exponents and radicals, lines and inequalities, polynomials, factoring and
quadratics, all checked with the exact algebra kit in ws/algebra.py."""

import copy
from fractions import Fraction

import pytest

from ws import generate as gen
from ws import registry
from ws.algebra import Mono, html_expr, parse, pretty, quadratic_roots, rational_power, root_parts, roots_text
from ws.sheet_types.polynomial_factoring import canonical, split
from ws.syllabus import load_level, resolve_page, sheet_id
from ws.verify import banned_words

M9 = load_level("math", "M9")


def check(sheet):
    return [i.message for i in registry.get(sheet.sheet_type).verify(sheet)]


def test_M9_shape():
    assert [s.code for s in M9.sections] == list("ABCDE")
    assert [s.pages for s in M9.sections] == [(1, 30), (31, 70), (71, 110), (111, 150), (151, 200)]
    assert all(s.public_name and s.standards and s.source == "ours" for s in M9.sections)
    assert all(p.pages[1] - p.pages[0] == 9 for s in M9.sections for p in s.parts)   # 10-page parts
    codes = {c for s in M9.sections for c in s.standards}
    assert {"N-RN.A.1", "N-RN.A.2", "A-APR.A.1", "A-SSE.A.2", "A-REI.B.4b", "A-REI.D.12", "F-IF.C.7a"} <= codes
    assert all(c[0] in "NAF" and c[1] == "-" for c in codes)   # high-school codes only at section level
    assert M9.public_name == "Whales" and len(M9.preview_pages) == 4
    assert sheet_id(M9, M9.section("D"), 121) == "MA-M9-D-011"
    assert resolve_page(M9, 45).sheet_type == "coordinate_grid"
    assert banned_words("Whales M9 page") == ["m9"]


def test_polynomials_exact():
    assert parse("(2x - 3)(x + 4)").text() == "2x^2 + 5x - 12"
    assert parse("(3x^2 - 5x + 2) - (x^2 + 4x - 7)").text() == "2x^2 - 9x + 9"
    assert parse("(x + y)^2").text() == "x^2 + 2xy + y^2"
    assert parse("-3x(2x^2 - x + 4)").text() == "-6x^3 + 3x^2 - 12x"
    assert pretty("2x^2 - 9x + 9") == "2x² − 9x + 9"
    with pytest.raises(ValueError):
        parse("x^-2")


def test_exponents_and_roots():
    assert (Mono.make(3, {"x": 2}) * Mono.make(4, {"x": 5})).text() == "12x^7"
    assert (Mono.make(2, {"x": 3}) / Mono.make(6, {"x": 9})).text() == "1/(3x^6)"
    assert Mono.make(1, {"x": Fraction(5, 6)}).text() == "x^(5/6)"
    assert rational_power(Fraction(8), Fraction(2, 3)) == 4
    assert rational_power(Fraction(16), Fraction(-1, 2)) == Fraction(1, 4)
    assert rational_power(Fraction(10), Fraction(1, 2)) is None
    assert root_parts(2, 72) == (6, 2) and root_parts(3, 54) == (3, 2)
    assert pretty("6R(2|2) + R(3|2x)") == "6√2 + ∛(2x)"
    assert 'class="rexp"' in html_expr("x^(2/3)")


@pytest.mark.parametrize("abc, text", [
    ((1, -1, -6), "x = −2 or x = 3"), ((2, 3, -2), "x = −2 or x = 1/2"), ((1, -6, 9), "x = 3"),
    ((1, 0, -12), "x = ±2√3"), ((1, -2, -1), "x = 1 ± √2"), ((2, -6, -1), "x = (3 ± √11)/2"),
])
def test_quadratic_roots(abc, text):
    roots = quadratic_roots(*abc)
    assert roots_text(roots) == text
    assert all(r.satisfies(*abc) for r in roots)


def test_factoring_canonical():
    gcf, factors = split("3x^2(2x + 3)")
    assert canonical(gcf, factors) == "3x^2(2x + 3)"
    gcf, factors = split("2(x + 1)^2")
    assert len(factors) == 2 and canonical(gcf, factors) == "2(x + 1)^2"


# one golden per sheet type and layout: exponent rules, rational exponents, radicals; write the line,
# graph lines, number-line inequalities, graph inequalities; add/subtract, box (2×2), box (2×3); GCF,
# trinomials, leading numbers, squares; factoring, square roots, formula (rational), formula (radicals), mixed
@pytest.mark.parametrize("page", [1, 11, 21, 31, 41, 51, 61, 71, 92, 101, 111, 121, 131, 141, 151, 161, 171,
                                  181, 191])
def test_golden(page, out_dir, fixture_content, golden):
    (sheet, path), = gen.generate_pages(M9, [page])
    assert check(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def _printed(sheet) -> str:
    """The text a reader sees: title, tip and every item string as printed."""
    parts = [sheet.title, sheet.parent_tip] + [str(a) for a in sheet.answer_key or []]
    for i in sheet.items:
        for k in ("q", "top", "bottom", "lhs", "rhs", "eq", "text"):
            if k in i:
                parts.append(pretty(i[k]))
    return " ".join(parts)


def test_whole_level_passes(fixture_content):
    plan = gen.build_plan(M9)
    for page in range(1, M9.pages + 1):
        sheet = gen.build_sheet(M9, page, plan)
        assert check(sheet) == [], (sheet.id, check(sheet))
        assert banned_words(_printed(sheet)) == [], (sheet.id, banned_words(_printed(sheet)))
        assert sheet.answer_key and all(", " not in a or "(" in a for a in sheet.answer_key)


def test_verify_catches_wrong_answers(fixture_content):
    plan = gen.build_plan(M9)
    for page in (1, 31, 51, 61, 71, 121, 181):
        sheet = gen.build_sheet(M9, page, plan)
        bad = copy.deepcopy(sheet)
        bad.items[0]["answer"] = "x = 0"
        assert check(bad), page
    sheet = gen.build_sheet(M9, 121, plan)
    bad = copy.deepcopy(sheet)
    bad.items[0]["q"] = "x^2 + 1"
    assert any("multiply out" in m for m in check(bad))
    sheet = gen.build_sheet(M9, 181, plan)
    bad = copy.deepcopy(sheet)
    bad.items[0]["coeffs"] = [1, 0, -4]
    assert check(bad)
