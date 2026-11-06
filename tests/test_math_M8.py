"""Lions math (M8): exponents and roots, scientific notation, multi-step equations, lines and slope,
two equations at once, right triangles."""

import copy
from decimal import Decimal
from fractions import Fraction

import pytest

from ws import generate as gen
from ws import registry
from ws.sheet_types import _systems
from ws.sheet_types._algebra import clip, equation_tokens, lattice, root_one_decimal, solve
from ws.sheet_types.sci_notation import normal, standard
from ws.syllabus import load_level, resolve_page, sheet_id
from ws.verify import banned_words

M8 = load_level("math", "M8")


def check(sheet):
    return [i.message for i in registry.get(sheet.sheet_type).verify(sheet)]


def test_M8_shape():
    assert [s.code for s in M8.sections] == list("ABCDEF")
    assert [s.pages for s in M8.sections] == [(1, 30), (31, 50), (51, 100), (101, 150), (151, 180), (181, 200)]
    assert all(s.public_name and s.standards and s.source == "ours" for s in M8.sections)
    codes = {c for s in M8.sections for c in s.standards} | {c for s in M8.sections for p in s.parts for c in p.standards}
    assert {"8.EE.1", "8.EE.2", "8.EE.3", "8.EE.4", "8.EE.7a", "8.EE.7b", "8.EE.8c", "8.F.4", "8.G.7", "8.G.8"} <= codes
    assert all(c.startswith("8.") for c in codes)   # grade 8 work (content_grade 8)
    assert all(len(p.pages) == 2 and p.pages[1] - p.pages[0] == 9 for s in M8.sections for p in s.parts)
    assert M8.public_name == "Lions" and len(M8.preview_pages) == 4
    assert sheet_id(M8, M8.section("C"), 51) == "MA-M8-C-001"
    assert banned_words("Lions M8 page") == ["m8"]
    assert {resolve_page(M8, p).sheet_type for p in (51, 101, 151)} == {"equation_solve", "coordinate_grid"}


def test_exact_helpers():
    assert root_one_decimal(65) == "8.1" and root_one_decimal(2) == "1.4" and root_one_decimal(85) == "9.2"
    assert root_one_decimal(30) == "5.5"     # √30 = 5.477…
    assert clip(Fraction(1, 2), 1, 6) == [[-6, -2], [6, 4]]
    assert lattice(2, -1, 3) == [[-1, -3], [0, -1], [1, 1], [2, 3]]
    left = [{"k": "3", "in": [{"c": "1", "v": "x"}, {"c": "-4", "v": ""}]}]
    right = [{"c": "2", "v": "x"}, {"c": "1", "v": ""}]
    assert solve(left, right) == 13
    assert equation_tokens(left, right, "n") == ["3(n − 4) = 2n + 1"]
    assert normal(Decimal("24E5")) == ("2.4", 6)
    assert standard("4.05", -4) == "0.000405" and standard("3.2", 9) == "3,200,000,000"
    e1, e2 = _systems.std(2, 1, 7), _systems.std(1, -1, 2)
    assert _systems.solve(e1, e2) == (3, 1)
    assert _systems.solve(_systems.std(2, 1, 4), _systems.std(4, 2, 8)) == "all"
    assert _systems.solve(_systems.si(2, 1), _systems.si(2, -3)) == "none"


# one golden per sheet type and mode
@pytest.mark.parametrize("page", [1, 11, 31, 41, 51, 91, 111, 131, 151, 171, 181, 192])
def test_golden(page, out_dir, fixture_content, golden):
    (sheet, path), = gen.generate_pages(M8, [page])
    assert check(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_whole_level_passes(fixture_content):
    plan = gen.build_plan(M8)
    seen = set()
    for page in range(1, M8.pages + 1):
        sheet = gen.build_sheet(M8, page, plan)
        assert check(sheet) == [], (sheet.id, check(sheet))
        text = " ".join(str(i) for i in sheet.items) + " ".join(map(str, sheet.answer_key))
        assert not banned_words(text), (sheet.id, banned_words(text))
        seen |= {i.get("task") or i.get("form") for i in sheet.items}
    assert {"power", "rule_value", "between", "to_sci", "times_bigger", "like_terms", "distribute_both",
            "fraction_coef", "points", "read_mb", "draw_line", "from_table", "graph_read", "substitution",
            "elimination", "inspect", "story", "hypotenuse", "leg", "is_right", "distance"} <= seen


def _page(page):
    return gen.build_sheet(M8, page, gen.build_plan(M8))


def test_verify_catches_bad_powers_and_notation(fixture_content):
    s = _page(11)
    bad = copy.deepcopy(s)
    bad.answer_key[0] = "2^99"
    assert any("answer key" in m for m in check(bad))
    s = _page(41)
    bad = copy.deepcopy(s)
    bad.items[0]["coef"] = "12"
    assert any("tidy" in m for m in check(bad))
    s = _page(31)
    bad = copy.deepcopy(s)
    bad.items[0]["standard"] = "1,000"
    assert any("printed number" in m for m in check(bad))


def test_verify_catches_bad_equations(fixture_content):
    s = _page(71)
    bad = copy.deepcopy(s)
    bad.items[0]["tokens"] = ["x = 1"]
    assert any("printed equation" in m for m in check(bad))
    bad = copy.deepcopy(s)
    bad.items[0]["right"][-1]["c"] = str(int(bad.items[0]["right"][-1]["c"]) + 1)
    bad.items[0]["tokens"] = equation_tokens(bad.items[0]["left"], bad.items[0]["right"], bad.items[0]["letter"])
    msgs = check(bad)
    assert any("answer key" in m or "outside" in m or "fraction" in m for m in msgs)
    s = _page(91)
    bad = copy.deepcopy(s)
    k = next(n for n, i in enumerate(bad.items) if i["special"] == "none")
    bad.items[k]["special"] = None
    assert check(bad)


def test_verify_catches_bad_lines(fixture_content):
    s = _page(111)
    bad = copy.deepcopy(s)
    bad.items[0]["ends"][0][1] += 1
    assert any("drawn line" in m for m in check(bad))
    bad = copy.deepcopy(s)
    bad.items[0]["dots"][0][1] += 1
    assert any("isn't on the line" in m for m in check(bad))
    s = _page(112)
    bad = copy.deepcopy(s)
    bad.items[0]["ys"][2] += 1
    assert any("table row" in m for m in check(bad))


def test_verify_catches_bad_systems(fixture_content):
    s = _page(151)
    bad = copy.deepcopy(s)
    bad.items[0]["x"] += 1
    assert any("solution" in m for m in check(bad))
    s = _page(171)
    story = next(i for i in s.items if i["task"] == "story")
    bad = copy.deepcopy(s)
    next(i for i in bad.items if i["task"] == "story")["x"] = story["x"] + 1
    assert any("story" in m for m in check(bad))


def test_verify_catches_bad_triangles(fixture_content):
    s = _page(181)
    bad = copy.deepcopy(s)
    h = next(i for i in bad.items if i["task"] == "hypotenuse")
    h["a"] += 1
    assert check(bad)
    s = _page(191)
    bad = copy.deepcopy(s)
    bad.answer_key[0] = "c = 9"
    assert any("answer key" in m for m in check(bad))
