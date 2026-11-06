import copy

import pytest
import yaml
from pydantic import ValidationError

from ws.models import Level
from ws.registry import CATALOGUE
from ws.syllabus import (
    all_levels, level_path, load_level, merge_rules, page_seed, parse_pages, resolve_page, sheet_id,
)

LEVELS = [("english", "7A"), ("math", "6A"), ("pencil", "ZI"), ("pencil", "ZII")]


@pytest.mark.parametrize("subject,level", LEVELS)
def test_level_loads(subject, level):
    lvl = load_level(subject, level)
    assert lvl.sections, "level has no sections"


def test_every_syllabus_file_is_valid():
    assert {(l.subject, l.level) for l in all_levels()} >= set(LEVELS)


@pytest.mark.parametrize("lvl", all_levels(), ids=lambda l: f"{l.subject}-{l.level}")
def test_sheet_types_are_in_catalogue(lvl):
    for s in lvl.sections:
        for t in s.sheet_types + [t for p in s.parts for t in (p.sheet_types or [])]:
            assert t in CATALOGUE, f"{lvl.level}-{s.code}: unknown sheet type {t!r}"


@pytest.mark.parametrize("lvl", all_levels(), ids=lambda l: f"{l.subject}-{l.level}")
def test_every_page_resolves(lvl):
    for page in range(1, lvl.pages + 1):
        spec = resolve_page(lvl, page)
        s = lvl.section(spec.section)
        assert s.pages[0] <= page <= s.pages[1]


# --- structural validation rejects bad YAML ---------------------------------------------

def _raw(subject, level):
    return yaml.safe_load(level_path(subject, level).read_text())


def test_gap_between_sections_rejected():
    data = _raw("english", "7A")
    data["sections"][1]["pages"] = [102, 140]
    with pytest.raises(ValidationError, match="starting at page 101"):
        Level.model_validate(data)


def test_sections_must_reach_last_page():
    data = _raw("english", "7A")
    data["sections"][2]["pages"] = [141, 199]
    with pytest.raises(ValidationError, match="expected 200"):
        Level.model_validate(data)


def test_section_codes_in_page_order():
    data = _raw("english", "7A")
    data["sections"][0]["code"], data["sections"][1]["code"] = "B", "A"
    with pytest.raises(ValidationError, match="section codes"):
        Level.model_validate(data)


def test_parts_must_tile_section():
    data = _raw("math", "6A")
    data["sections"][0]["parts"][1]["pages"] = [11, 19]
    with pytest.raises(ValidationError, match="parts"):
        Level.model_validate(data)


def test_unknown_keys_rejected():
    data = _raw("math", "6A")
    data["sections"][0]["sheet_type"] = "count_and_say"   # typo for sheet_types
    with pytest.raises(ValidationError):
        Level.model_validate(data)


# --- rule merging and page resolution ---------------------------------------------------

def test_merge_rules_later_wins_and_nests():
    merged = merge_rules({"a": 1, "n": {"x": 1, "y": 2}}, {"a": 2, "n": {"y": 3}}, {"b": 4})
    assert merged == {"a": 2, "n": {"x": 1, "y": 3}, "b": 4}


def test_part_rules_override_section_rules():
    lvl = load_level("math", "6A")
    spec = resolve_page(lvl, 105)          # 6A-C part 1
    assert spec.rules == {"choices": 3, "min": 1, "max": 4, "new": 4}
    data = _raw("math", "6A")
    data["sections"][2]["parts"][0]["rules"]["choices"] = 2
    assert resolve_page(Level.model_validate(data), 105).rules["choices"] == 2


def test_level_rules_reach_every_section():
    lvl = load_level("english", "7A")
    for page in (1, 120, 200):
        assert resolve_page(lvl, page).rules["min_exposures_per_word"] == 3


def test_math_6A_parts_match_approved_table():
    lvl = load_level("math", "6A")
    tops = {(s.code, p.part): (p.rules["max"], p.rules["new"]) for s in lvl.sections for p in s.parts}
    assert tops == {
        ("A", 1): (3, 3), ("A", 2): (4, 4), ("A", 3): (5, 5),
        ("B", 1): (6, 6), ("B", 2): (7, 7), ("B", 3): (8, 8), ("B", 4): (9, 9), ("B", 5): (10, 10),
        ("B", 6): (10, None), ("B", 7): (10, None),
        ("C", 1): (4, 4), ("C", 2): (6, 6), ("C", 3): (8, 8), ("C", 4): (10, 10), ("C", 5): (10, None),
        ("D", 1): (5, 5), ("D", 2): (7, 7), ("D", 3): (9, 9), ("D", 4): (10, 10), ("D", 5): (10, None),
    }
    assert all(s.source == "ours" for s in lvl.sections)


def test_part_sheet_types_override_section():
    lvl = load_level("math", "6A")
    assert resolve_page(lvl, 80).sheet_type == "count_and_say"
    assert resolve_page(lvl, 81).sheet_type == "count_and_point"


def test_sheet_types_cycle_within_section():
    lvl = load_level("english", "7A")
    assert {resolve_page(lvl, p).sheet_type for p in range(1, 21)} == {"word_picture_pair"}
    assert [resolve_page(lvl, p).sheet_type for p in (21, 22, 23, 100)] == [
        "word_picture_pair", "word_picture_sentence", "word_picture_pair", "word_picture_sentence"]
    lvl6 = load_level("math", "6A")
    # cycle restarts at each part so every part opens with number_read
    assert [resolve_page(lvl6, p).sheet_type for p in (101, 102, 111, 112)] == [
        "number_read", "count_and_point", "number_read", "count_and_point"]


def test_page_outside_level_errors():
    with pytest.raises(KeyError, match="outside"):
        resolve_page(load_level("english", "7A"), 201)


def test_7A_strip_rule_present():
    rules = resolve_page(load_level("english", "7A"), 50).rules
    assert rules["new_words_per_sheet"] == 2
    assert rules["say_it_again"] == {"count": 2, "sheets_back": [3, 10]}


# --- IDs, seeds, page specs ---------------------------------------------------------------

def test_sheet_ids():
    en, ma, zi, zii = (load_level(*x) for x in LEVELS)
    assert sheet_id(en, en.section("A"), 1) == "EN-7A-A-001"
    assert sheet_id(en, en.section("B"), 101) == "EN-7A-B-001"
    assert sheet_id(ma, ma.section("B"), 44) == "MA-6A-B-014"
    assert sheet_id(zi, zi.section("A"), 3) == "ZI-A-003"
    assert sheet_id(zii, zii.section("C"), 61) == "ZII-C-001"
    assert sheet_id(en, en.section("A"), 1, variant=2) == "EN-7A-A-001-v2"


def test_seed_is_stable_and_distinct():
    a = page_seed("english", "7A", "A", 1)
    assert a == page_seed("english", "7A", "A", 1)
    assert a == 0x3012F9DA4F885A77   # pinned: if this changes, every sheet changes
    assert len({page_seed("english", "7A", "A", p, v) for p in range(1, 101) for v in (1, 2)}) == 200


def test_parse_pages():
    assert parse_pages("1-3,7") == [1, 2, 3, 7]
    with pytest.raises(ValueError):
        parse_pages("5-1")


def test_ZI_line_rules_reach_line_sections():
    lvl = load_level("pencil", "ZI")
    rules = resolve_page(lvl, 75).rules
    assert rules["flow"] == ["left_to_right", "top_to_bottom"]
    assert (rules["start_marker"], rules["end_marker"], rules["arrows"]) == ("dot", "picture", False)
    assert rules["length_frac"] == [0.4, 0.9] and rules["path"] == "wave"
