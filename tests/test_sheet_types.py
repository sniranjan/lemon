"""Every sheet type: golden output, type checks on whole levels, worst-case renders."""

from collections import Counter

import pytest

from ws import generate as gen
from ws import registry
from ws.models import VocabEntry
from ws.plan import plan_new_words, plan_review
from ws.syllabus import all_levels, load_level

EN7A, MA6A, ZI = load_level("english", "7A"), load_level("math", "6A"), load_level("pencil", "ZI")

# (level, page, sheet type override) → one golden file per sheet type
GOLDEN_PAGES = [
    (EN7A, 4, "word_picture_sentence"),
    (EN7A, 101, None),   # review_grid_4
    (EN7A, 143, None),   # word_story, 4 sentences
    (MA6A, 75, None),    # count_and_say, part with 10
    (MA6A, 81, None),    # count_and_point
    (MA6A, 131, None),   # number_read
    (MA6A, 181, None),   # dots_to_number
    (ZI, 11, None),      # colouring, two shapes
    (ZI, 100, None),     # line_path, mixed curves
]


def test_every_syllabus_sheet_type_is_implemented():
    used = {t for lvl in all_levels() for s in lvl.sections
            for t in s.sheet_types + [t for p in s.parts for t in (p.sheet_types or [])]}
    assert used <= set(registry.implemented())


@pytest.mark.parametrize("level,page,sheet_type", GOLDEN_PAGES,
                         ids=lambda v: getattr(v, "level", None) or str(v))
def test_golden(level, page, sheet_type, out_dir, fixture_content, golden):
    variant = 2 if sheet_type else 1
    (sheet, path), = gen.generate_pages(level, [page], variant=variant, sheet_type=sheet_type)
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


@pytest.mark.parametrize("level", [MA6A, ZI], ids=lambda l: l.level)
def test_whole_level_passes_type_checks(level, fixture_content):
    plan = gen.build_plan(level)
    for page in range(1, level.pages + 1):
        sheet = gen.build_sheet(level, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id


def test_7A_review_pages_pass_type_checks(fixture_content):
    plan = gen.build_plan(EN7A)
    for page in [*range(1, 5), *range(101, 141), *range(141, 201)]:
        sheet = gen.build_sheet(EN7A, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id


def test_every_word_seen_three_times_across_7A():
    bank = [VocabEntry(word=f"w{i:03d}", picture="apple", category="t", level="7A") for i in range(200)]
    plan = plan_review(EN7A, plan_new_words(EN7A, bank))
    assert sorted(plan.pages) == list(range(1, 201))
    seen = Counter(w for p in plan.pages.values() for w in p.new_words + p.review_words)
    assert len(seen) == 200 and min(seen.values()) >= 3
    for page in range(101, 201):
        assert not plan.pages[page].new_words


def test_6A_part_ranges_respected(fixture_content):
    plan = gen.build_plan(MA6A)
    sheets = [gen.build_sheet(MA6A, p, plan) for p in range(1, 31)]
    assert max(i["n"] for s in sheets[:10] for i in s.items) <= 3
    assert all(any(i["n"] == 3 for i in s.items) for s in sheets[:10])   # the part's new number


def test_line_paths_grow_within_a_part(fixture_content):
    plan = gen.build_plan(ZI)
    first, last = gen.build_sheet(ZI, 21, plan), gen.build_sheet(ZI, 30, plan)
    length = lambda s: s.items[0]["end"][0] - s.items[0]["start"][0]
    assert length(last) > 1.8 * length(first)


def test_line_paths_flow_and_directions(fixture_content):
    plan = gen.build_plan(ZI)
    seen = set()
    for page in range(21, 101):
        for item in gen.build_sheet(ZI, page, plan).items:
            (x0, y0), (x1, y1) = item["start"], item["end"]
            assert x1 >= x0 and y1 >= y0
            seen.add(item["direction"])
    assert seen == {"horizontal", "vertical", "diagonal"}


def test_select_pages_continues_and_completes(out_dir, fixture_content):
    assert gen.select_pages(MA6A, section="A", count=5) == [1, 2, 3, 4, 5]
    gen.generate_pages(MA6A, [1, 2, 3, 4, 5])
    assert gen.select_pages(MA6A, section="A", count=3) == [6, 7, 8]
    assert gen.select_pages(MA6A, section="B", part=6) == list(range(81, 91))
    gen.generate_pages(MA6A, list(range(6, 31)))
    with pytest.raises(ValueError, match="6A-A is complete: pages 1–30"):
        gen.select_pages(MA6A, section="A", count=1)
    assert gen.select_pages(MA6A, section="A", count=2, variant=2) == [1, 2]


WORST_CASES = [
    (EN7A, [4], "word_picture_sentence"), (EN7A, [101, 141, 142, 143], None),
    (MA6A, [75, 81, 131, 132, 190], None), (ZI, [1, 11, 30, 42, 50, 90, 100], None),
]


@pytest.mark.parametrize("level,pages,sheet_type", WORST_CASES, ids=lambda v: getattr(v, "level", None) or str(v))
def test_worst_case_pages_render_cleanly(level, pages, sheet_type, out_dir, fixture_content):
    pytest.importorskip("playwright")
    from ws.render import render_pngs

    made = gen.generate_pages(level, pages, variant=2 if sheet_type else 1, sheet_type=sheet_type)
    for r in render_pngs([p for _, p in made]):
        assert r.problems == [], (r.html.name, r.problems)


@pytest.mark.parametrize("level", [MA6A, ZI, EN7A], ids=lambda l: l.level)
def test_no_duplicate_sheets_in_level(level, fixture_content):
    plan = gen.build_plan(level)
    seen = {}
    for s in level.sections:
        last = max((p for p in plan.pages if s.pages[0] <= p <= s.pages[1]), default=s.pages[1]) \
            if level.subject == "english" else s.pages[1]
        for page, sheet in gen.build_section(level, s.code, last, plan).items():
            key = (sheet.sheet_type, repr(sheet.items))
            if level.subject == "english" and s.code == "B":
                continue   # 8-word fixture bank: grids repeat word sets by necessity (order still differs)
            assert key not in seen, f"{sheet.id} repeats {seen[key]}"
            seen[key] = sheet.id


def test_page_range_matches_full_run(out_dir, fixture_content):
    alone = {s.id: s for s, _ in gen.generate_pages(ZI, [5, 6, 7])}
    full = {s.id: s for s, _ in gen.generate_pages(ZI, list(range(1, 21)))}
    for sid, sheet in alone.items():
        assert sheet == full[sid]


def test_story_frames_suit_the_word():
    import random

    from ws.content import stories, vocab_by_word
    from ws.sheet_types.word_story import article, pick_frames

    bank = vocab_by_word()
    data = stories()
    for _ in range(20):
        mom, nose, milk = bank["mom"], bank["nose"], bank["milk"]
        f_mom, f_nose = pick_frames(random.Random(_), [mom, nose], data)
        assert f_mom in data["frames_by_category"]["family"] and "{a}" not in f_mom
        assert f_nose in data["frames_by_category"]["body"]
    assert article(bank["milk"]) == "some" and article(bank["egg"]) == "an" and article(bank["dog"]) == "a"
    frames = pick_frames(random.Random(1), [bank["dog"], bank["cat"], bank["cup"], bank["ball"]], data)
    assert len(set(frames)) == 4


def test_story_allowed_words_cover_every_frame():
    import re

    from ws.content import stories

    data = stories()
    allowed = {w.lower() for w in data["allowed_words"]} | {"some", "a", "an"}
    frames = data["frames"] + [f for fs in data["frames_by_category"].values() for f in fs]
    for f in frames:
        for token in re.findall(r"[A-Za-z]+", f.replace("{w}", "").replace("{a}", "")):
            assert token.lower() in allowed, (f, token)
