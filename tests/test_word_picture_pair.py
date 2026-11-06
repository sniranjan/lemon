import re
import pytest

from ws import generate as gen
from ws.content import licenses, picture_path, tips, vocab
from ws.models import VocabEntry
from ws.plan import plan_new_words
from ws.registry import get
from ws.syllabus import ROOT, load_level

EN7A = load_level("english", "7A")


def _bank(n: int) -> list[VocabEntry]:
    return [VocabEntry(word=f"w{i:03d}", picture="apple", category="test", level="7A") for i in range(n)]


# --- planner -----------------------------------------------------------------------------

def test_full_section_plan_rules():
    plan = plan_new_words(EN7A, _bank(200))
    assert sorted(plan.pages) == list(range(1, 101))
    new = [w for p in plan.pages.values() for w in p.new_words]
    assert len(new) == 200 and len(set(new)) == 200          # each word new exactly once
    new_on = {w: page for page, p in plan.pages.items() for w in p.new_words}
    for page, p in plan.pages.items():
        assert len(p.new_words) == 2
        if page <= 3:
            assert p.review_words == []                       # nothing old enough yet
        else:
            assert len(p.review_words) == 2
            for w in p.review_words:
                assert 3 <= page - new_on[w] <= 10, (page, w)


def test_strip_spreads_words():
    plan = plan_new_words(EN7A, _bank(200))
    shown = [w for p in plan.pages.values() for w in p.review_words]
    # 194 strip slots over 200 words: no word should be shown more than twice
    assert max(shown.count(w) for w in set(shown)) <= 2


def test_plan_stops_where_bank_runs_out():
    plan = plan_new_words(EN7A, _bank(7))
    assert sorted(plan.pages) == [1, 2, 3]
    with pytest.raises(KeyError, match="page 4 isn.t planned yet"):
        plan.for_page(4)


# --- content -------------------------------------------------------------------------------

def test_every_content_picture_exists_and_is_licensed():
    from ws.content import line_targets, math_objects

    slugs = [w.picture for w in vocab("english") if w.picture] + [o["picture"] for o in math_objects()] + list(line_targets())
    for slug in slugs:
        assert picture_path(slug).exists(), slug
        assert slug in licenses(), f"{slug} has no LICENSES.yaml entry"


def test_tips_are_short():
    for sheet_type, lines in tips("english").items():
        for t in lines:
            assert len(t) <= 220, (sheet_type, t)


# --- generate + render ---------------------------------------------------------------------

def test_sheet_contents_page_4(fixture_content):
    plan = gen.build_plan(EN7A)
    sheet = gen.build_sheet(EN7A, 4, plan)
    assert sheet.id == "EN-7A-A-004" and sheet.sheet_type == "word_picture_pair"
    assert sheet.new_words == ["fish", "rainbow"] and sheet.review_words == ["apple", "ball"]
    assert get("word_picture_pair").verify(sheet) == []


def test_html_is_deterministic(out_dir, fixture_content):
    first = {p.name: p.read_bytes() for _, p in gen.generate_pages(EN7A, [1, 2, 3, 4])}
    second = {p.name: p.read_bytes() for _, p in gen.generate_pages(EN7A, [4, 3, 2, 1])}
    assert first == second
    html = first["EN-7A-A-004.html"].decode()
    assert "Chicks · 4" in html and "Chicks · Reading · page 4" in html and 'class="strip"' in html
    assert not re.search(r"\b(7A|EN-7A)\b", html)       # internal codes never printed (CLAUDE.md §15)
    assert str(ROOT) not in html and 'src="../../../../../assets/pictures/fish.svg"' in html
    assert 'class="strip"' not in first["EN-7A-A-001.html"].decode()


def test_pages_render_cleanly(out_dir, fixture_content):
    pytest.importorskip("playwright")
    from ws.render import render_pngs

    made = gen.generate_pages(EN7A, [1, 4])
    results = render_pngs([p for _, p in made])
    for r in results:
        assert r.problems == [], (r.html.name, r.problems)
        assert r.png.stat().st_size > 10_000


def test_golden_page_4(out_dir, fixture_content, golden):
    (sheet, path), = gen.generate_pages(EN7A, [4])
    golden("EN-7A-A-004.html", path.read_text())
    golden("EN-7A-A-004.json", sheet.model_dump_json(indent=2) + "\n")


def test_section_tips_override_subject_tips(fixture_content):
    import random

    from ws.content import tips
    from ws.registry import GenContext
    from ws.syllabus import resolve_page

    spec = resolve_page(EN7A, 5)
    custom = spec.model_copy(update={"rules": {**spec.rules, "tips": {"word_picture_pair": ["Part tip."]}}})
    ctx = GenContext(spec=custom, rng=random.Random(1), banks={"tips": tips("english")})
    assert ctx.tip("word_picture_pair") == "Part tip."
    ctx = GenContext(spec=spec, rng=random.Random(1), banks={"tips": tips("english")})
    assert ctx.tip("word_picture_pair") in tips("english")["word_picture_pair"]


def test_syllabus_tips_are_short():
    from ws.syllabus import all_levels, resolve_page

    for lvl in all_levels():
        for page in range(1, lvl.pages + 1):
            for sheet_type, lines in resolve_page(lvl, page).rules.get("tips", {}).items():
                assert all(len(t) <= 220 for t in lines), (lvl.level, page, sheet_type)
