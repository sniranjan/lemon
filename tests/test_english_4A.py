"""English 4A (Kittens Reading): letter teams, rhymes, sentence tracing and their planner."""

from collections import Counter
from pathlib import Path

import pytest

from ws import content
from ws import generate as gen
from ws import registry
from ws.content import phonics, phrases, vocab, vocab_by_word
from ws.models import VocabEntry
from ws.phonics import plan_phonics, rhyme_group, shared_ending, split_team
from ws.plan import plan_new_words, plan_phrases, plan_review
from ws.syllabus import load_level

EN4A = load_level("english", "4A")
FROZEN = Path(__file__).parent / "fixtures" / "content-4A"


@pytest.fixture
def frozen_content(monkeypatch):
    """A frozen copy of the word bank, phrases, phonics and tips (2026-11-06), so the goldens stay put
    while the real bank grows."""
    monkeypatch.setattr(content, "CONTENT_DIR", FROZEN)
    content.clear_caches()
    yield
    content.clear_caches()


@pytest.mark.parametrize("page", [9, 54, 101, 121, 131, 185])   # letter_team trace/fill, rhyme pair/pick/odd, sentence_trace
def test_golden(page, out_dir, frozen_content, golden):
    (sheet, path), = gen.generate_pages(EN4A, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_every_page_builds_and_passes_type_checks():
    plan = gen.build_plan(EN4A)
    assert sorted(plan.pages) == list(range(1, 201))
    for page in plan.pages:
        sheet = gen.build_sheet(EN4A, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id


def test_page_range_matches_full_run(out_dir):
    alone = {s.id: s for s, _ in gen.generate_pages(EN4A, [46, 115, 186])}
    full = {s.id: s for s, _ in gen.generate_pages(EN4A, list(range(41, 51)) + list(range(111, 121))
                                                  + list(range(181, 191)))}
    for sid, sheet in alone.items():
        assert sheet == full[sid]


def test_new_words_carry_their_units_team_and_are_seen_three_times():
    plan = gen.build_plan(EN4A)
    data = phonics()
    new = {w: p for p, e in plan.pages.items() for w in e.new_words}
    assert len(new) == 50 == EN4A.vocab_target
    for w, page in new.items():
        teams = EN4A.sections[0].parts[(page - 1) // 10 * 3 + 1].rules["teams"]
        assert any(w in data["letter_teams"][t]["words"] for t in teams), (w, page)
    seen = Counter(w for e in plan.pages.values() for w in e.new_words + e.review_words)
    assert min(seen[w] for w in new) >= 3


def test_new_words_slot_in_by_team_not_bank_order():
    """A later team's word listed first in the bank still waits for its own unit."""
    teams = phonics()["letter_teams"]
    data = {**phonics(), "letter_teams": {**teams,
                                          "sh": {**teams["sh"], "words": teams["sh"]["words"] + ["zzsh"]},
                                          "ll": {**teams["ll"], "words": teams["ll"]["words"] + ["zzll"]}}}
    bank = [e for e in vocab() if e.level != "4A"] + [
        VocabEntry(word="zzsh", picture="fish", category="toys", level="4A"),
        VocabEntry(word="zzll", picture="ball", category="toys", level="4A")]
    plan = plan_phonics(EN4A, bank, plan_review(EN4A, plan_new_words(EN4A, bank), bank), data)
    assert plan.pages[4].new_words == ["zzll"] and plan.pages[14].new_words == ["zzsh"]
    assert 5 not in plan.pages and 15 not in plan.pages   # pages the bank can't fill wait


# --- the hand-checked tables -------------------------------------------------------------------

def test_teams_are_really_in_their_words():
    data, bank = phonics(), vocab_by_word()
    for team, spec in data["letter_teams"].items():
        for w in spec["words"]:
            assert w in bank, (team, w)
            assert split_team(w, spec["letters"], spec["where"]), (team, w)
            assert not bank[w].needs_color and bank[w].picture, (team, w)


@pytest.mark.parametrize("team, word", [("ng", "orange"), ("ng", "finger"), ("bl", "table"), ("st", "sister"),
                                        ("ll", "balloon"), ("ll", "pillow"), ("-ush", "brush"), ("gr", "green"),
                                        ("bl", "blue"), ("nk", "monkey")])
def test_letters_that_are_not_the_team(team, word):
    assert word not in phonics()["letter_teams"][team]["words"]


def test_rhyme_groups():
    data, bank = phonics(), vocab_by_word()
    words = [w for g in data["rhymes"] for w in g["words"]]
    assert len(words) == len(set(words)), "a word is in two rhyme groups"
    assert all(w in bank and bank[w].picture and not bank[w].needs_color for w in words)


@pytest.mark.parametrize("a, b", [("cow", "snow"), ("bear", "ear"), ("shoe", "toe"), ("ball", "doll"),
                                  ("dog", "frog"), ("brush", "bush"), ("sun", "drum")])
def test_not_rhymes(a, b):
    ga, gb = rhyme_group(phonics(), a), rhyme_group(phonics(), b)
    assert ga is None or gb is None or ga is not gb


def test_shared_ending():
    assert shared_ending("cat", "hat") == "at"
    assert shared_ending("bear", "pear") == "ear"
    assert shared_ending("bed", "bread") == ""      # e / ea
    assert shared_ending("bear", "chair") == ""
    assert shared_ending("slide", "ride") == "ide"


def test_kittens_text_never_shows_internal_codes():
    from ws.verify import banned_words

    plan = gen.build_plan(EN4A)
    for page in (1, 101, 141):
        sheet = gen.build_sheet(EN4A, page, plan)
        assert banned_words(" ".join([sheet.title, sheet.parent_tip] + [str(i) for i in sheet.items])) == []


def test_sections_have_public_names_and_standards():
    assert EN4A.public_name == "Kittens"
    assert all(s.public_name and s.standards for s in EN4A.sections)


def test_new_frames_stay_true():
    data, bank = phrases(), vocab_by_word()
    from ws.phrases import fillings, render
    texts = {render(f, fill, bank, data) for f in data["sentence_groups"]["more_can"]
             for fill in fillings(f, data, bank)}
    assert "The big dog can run." in texts and "The big bee can fly." not in texts
    assert not any(t.startswith("The little whale") or t.startswith("My mom can crawl") for t in texts)
