"""English 6A (Ducklings reading): review grids, phrase cards, sentence recite, and its planner."""

from collections import Counter

import pytest

from ws import generate as gen
from ws import registry
from ws.content import phrases, vocab, vocab_by_word
from ws.models import VocabEntry
from ws.phrases import fillings, render
from ws.plan import plan_new_words, plan_phrases, plan_review
from ws.syllabus import load_level

EN6A = load_level("english", "6A")


@pytest.mark.parametrize("page", [1, 31, 101])   # review_grid_4, phrase_card, sentence_recite
def test_golden(page, out_dir, fixture_content, golden):
    (sheet, path), = gen.generate_pages(EN6A, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_page_range_matches_full_run(out_dir, fixture_content):
    alone = {s.id: s for s, _ in gen.generate_pages(EN6A, [45, 46, 120])}
    full = {s.id: s for s, _ in gen.generate_pages(EN6A, list(range(31, 71)) + list(range(101, 141)))}
    for sid, sheet in alone.items():
        assert sheet == full[sid]


def test_real_content_pages_pass_type_checks():
    """Every page today's word bank can build: true phrases, known words, no repeats on a page."""
    plan = gen.build_plan(EN6A)
    built = [p for p in range(1, 201) if p in plan.pages]
    assert set(range(1, 71)) | set(range(101, 141)) <= set(built)
    for page in built:
        sheet = gen.build_sheet(EN6A, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id


def test_review_grids_cover_every_earlier_word_once():
    plan = gen.build_plan(EN6A)
    words = [w for p in range(1, 31) for w in plan.pages[p].review_words]
    earlier = [w.word for w in vocab() if w.level == "7A"]
    assert len(set(words)) == len(words) == min(120, len(earlier))


def test_color_phrases_match_the_picture():
    data, known = phrases(), vocab_by_word()
    for frame in data["phrase_groups"]["color_thing"] + data["sentence_groups"]["colors"]:
        for fill in fillings(frame, data, known):
            noun = next(w for k, w in fill.items() if k != "color")
            assert data["picture_colors"][noun] == fill["color"]


def test_animals_only_do_what_they_can():
    data, known = phrases(), vocab_by_word()
    texts = {render(f, fill, known, data) for f in data["sentence_groups"]["can"]
             for fill in fillings(f, data, known)}
    assert "The fish can swim." in texts and "The dog can run." in texts
    assert "The fish can run." not in texts and "The cat can clap." not in texts


def test_articles_and_plurals():
    data, known = phrases(), vocab_by_word()
    say = lambda frame, **fill: render(frame, fill, known, data)
    assert say("{a} {color} {colored}", color="red", colored="apple") == "a red apple"
    assert say("{a} {color} {colored}", color="blue", colored="pants") == "blue pants"
    assert say("I see {a} {thing}.", thing="egg") == "I see an egg."
    assert say("I eat {a} {eatable}.", eatable="bread") == "I eat some bread."
    assert say("{person} can {action}.", person="mom", action="run") == "Mom can run."
    assert not any("pants" in fill.values() for fill in fillings("The {colored} is {color}.", data, known))


def test_new_words_slot_in():
    """Once 6A words are approved, every page is planned, each new word is new once (on a page
    that uses it) and seen at least 3 times across the level."""
    # toys fit "my ___" phrases and "This is a ___." sentences, so they can be introduced in B and C
    bank = list(vocab()) + [VocabEntry(word=f"zz{i:02d}", picture="apple", category="toys", level="6A")
                            for i in range(80)]
    plan = plan_phrases(EN6A, bank, plan_review(EN6A, plan_new_words(EN6A, bank), bank), phrases())
    assert sorted(plan.pages) == list(range(1, 201))
    new = [w for p in plan.pages.values() for w in p.new_words]
    assert len(new) == len(set(new)) == 80
    seen = Counter(w for p in plan.pages.values() for w in p.new_words + p.review_words)
    assert min(seen[w] for w in new) >= 3
    for p in plan.pages.values():
        if p.new_words:
            assert set(p.new_words) <= {w for ph in p.extra["phrases"] for w in ph["words"]}


def test_6A_text_never_shows_internal_codes():
    from ws.verify import banned_words

    plan = gen.build_plan(EN6A)
    for page in (1, 31, 101):
        sheet = gen.build_sheet(EN6A, page, plan)
        assert banned_words(" ".join([sheet.title, sheet.parent_tip] + [str(i) for i in sheet.items])) == []
