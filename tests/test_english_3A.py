"""English 3A (Puppies Reading): word patterns, word endings, syllables, sentence copying, and the planner.

The golden pages use the real content, not tests/fixtures: the Puppies plan only draws on its own words,
the `known_levels` (Chicks and Ducklings words) and the hand-checked tables in content/phonics/english.yaml,
so words other strands add to the word bank never change these pages.
"""

from collections import Counter

import pytest

from ws import generate as gen
from ws import registry
from ws.content import phonics, vocab, vocab_by_word
from ws.models import VocabEntry
from ws.phonics import (by_rule, check_endings, check_sentence, check_syllables, pattern_span,
                        spelling_rule, syllable_table)
from ws.plan import plan_new_words, plan_phrases, plan_review, plan_spelling
from ws.sheet_types.sentence_copy import known_words
from ws.syllabus import load_level, resolve_page

EN3A = load_level("english", "3A")
MINE = [e.word for e in vocab() if e.level == "3A"]


@pytest.mark.parametrize("page", [1, 6, 71, 81, 101, 111, 131, 141, 161])
def test_golden(page, out_dir, golden):
    (sheet, path), = gen.generate_pages(EN3A, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_page_range_matches_full_run(out_dir):
    alone = {s.id: s for s, _ in gen.generate_pages(EN3A, [15, 88, 125, 177])}
    full = {s.id: s for s, _ in gen.generate_pages(EN3A, list(range(1, 201)))}
    for sid, sheet in alone.items():
        assert sheet == full[sid]


def test_every_page_passes_its_type_checks():
    plan = gen.build_plan(EN3A)
    assert set(plan.pages) == set(range(1, 201))
    for page in range(1, 201):
        sheet = gen.build_sheet(EN3A, page, plan)
        assert [i for i in registry.get(sheet.sheet_type).verify(sheet) if i.severity == "error"] == [], sheet.id


def test_every_word_is_new_once_and_seen_three_times():
    plan = gen.build_plan(EN3A)
    new = [w for p in plan.pages.values() for w in p.new_words]
    assert new == MINE and len(MINE) == EN3A.vocab_target
    seen = Counter(w for p in plan.pages.values() for w in p.new_words + p.review_words)
    assert min(seen[w] for w in MINE) >= 3


def test_new_word_has_its_parts_pattern_and_comes_first():
    plan = gen.build_plan(EN3A)
    data = phonics()
    for page in range(1, 71):
        codes = resolve_page(EN3A, page).rules["patterns"]
        first = plan.pages[page].extra["cards"][0]
        assert first["word"] == plan.pages[page].new_words[0]
        assert first["pattern"] in codes and pattern_span(first["word"], first["pattern"], data)


def test_no_two_pages_have_the_same_words():
    plan = gen.build_plan(EN3A)
    sets = [frozenset(c["word"] for c in plan.pages[p].extra["cards"]) for p in range(1, 201)]
    assert len(set(sets)) == len(sets)


def test_other_strands_words_never_change_the_plan():
    """Words other strands add to the bank (Bunnies, Kittens) never change a Puppies page."""
    bank = list(vocab())
    more = bank + [VocabEntry(word="ship", picture="boat", category="vehicles", level="4A", sentences=["I see a ship."]),
                   VocabEntry(word="chip", picture="cookie", category="food", level="5A")]

    def plan_with(b):
        plan = plan_review(EN3A, plan_new_words(EN3A, b), b)
        return plan_spelling(EN3A, b, plan_phrases(EN3A, b, plan, {}), phonics())

    assert plan_with(more).pages == plan_with(bank).pages


# --- the hand-checked tables -------------------------------------------------------------------

def test_endings_follow_the_spelling_rules():
    assert check_endings(phonics()) == []
    cases = {("run", "ing"): "running", ("bake", "ing"): "baking", ("see", "ing"): "seeing",
             ("box", "plural"): "boxes", ("peach", "plural"): "peaches", ("cry", "ed"): "cried",
             ("play", "ed"): "played", ("hop", "ed"): "hopped", ("pour", "ed"): "poured",
             ("smile", "ed"): "smiled", ("yawn", "ing"): "yawning", ("fly", "plural"): "flies", ("tie", "ing"): "tying"}
    for (base, ending), form in cases.items():
        assert by_rule(base, ending) == form
    assert spelling_rule("clap", "ing", "clapping") == "double"
    assert spelling_rule("dance", "ing", "dancing") == "drop_e"
    assert spelling_rule("bus", "plural", "buses") == "es"


def test_a_misspelled_ending_is_caught():
    bad = dict(phonics(), endings={"hop": {"ing": "hoping"}, "bake": {"ed": "bakeed"}})
    assert len(check_endings(bad)) == 2


def test_endings_bases_are_pictured_words_of_known_levels():
    bank = vocab_by_word()
    for base in phonics()["endings"]:
        assert base in bank and bank[base].picture and bank[base].level in ("7A", "6A", "3A"), base


def test_syllables_are_hand_checked():
    table = syllable_table(phonics())
    bank = vocab_by_word()
    for word, (kind, syls) in table.items():
        assert check_syllables(word, syls, kind) == [], word
        assert word in bank and bank[word].picture, word
    assert check_syllables("rabbit", ["rab", "bt"], "closed")   # no vowel in "bt"


def test_pattern_words_really_have_their_patterns():
    data, bank = phonics(), vocab_by_word()
    for word, codes in data["pattern_words"].items():
        assert word in bank and bank[word].picture, word
        for code in codes:
            assert pattern_span(word, code, data), (word, code)
    assert pattern_span("gate", "a_e", data) == [1, 3]
    assert pattern_span("rain", "ai", data) == [1, 2]
    assert pattern_span("light", "igh", data) == [1, 2, 3]
    assert pattern_span("cake", "i_e", data) is None


def test_every_copy_sentence_uses_known_words():
    data, words = phonics(), known_words("3A")
    for e in vocab():
        if e.level == "3A":
            assert len(e.sentences) == 2, e.word
            for s in e.sentences:
                assert check_sentence(s, e.word, data, words) == [], s
    assert check_sentence("The goat eats a pizza pie.", "goat", data, words)   # "pie" is not known


def test_copy_parts_have_enough_sentences():
    """Each Copy a Sentence part can fill its pages without one sentence twice."""
    from ws.phonics import sentence_tokens

    bank = vocab_by_word()
    sentences = [s for w in MINE for s in bank[w].sentences]
    for part in EN3A.section("D").parts:
        lo, hi = part.rules["sentence_words"]
        fits = [s for s in sentences if lo <= len(sentence_tokens(s)) <= hi and s[-1] in part.rules["end_marks"]]
        assert len(fits) >= 20, part.part
