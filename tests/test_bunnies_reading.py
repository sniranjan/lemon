"""English 5A (Bunnies Reading): letter tracing, sound pieces, word tracing, and the letters planner."""

from collections import Counter
from pathlib import Path

import pytest

from ws import content
from ws import generate as gen
from ws import registry
from ws.content import sounds, vocab, vocab_by_word
from ws.plan import plan_letters, rime_split
from ws.syllabus import load_level
from ws.trace_font import GLYPHS, andika_has, svg

EN5A = load_level("english", "5A")
FIXTURES_5A = Path(__file__).parent / "fixtures" / "content_5A"


@pytest.fixture
def content_5A(monkeypatch):
    """A small fixed word bank, tips and sound lists (the shared fixture bank stays untouched)."""
    monkeypatch.setattr(content, "CONTENT_DIR", FIXTURES_5A)
    content.clear_caches()
    yield
    content.clear_caches()


@pytest.mark.parametrize("page", [10, 71, 151, 161])   # letter_trace, sound_parts, letter pairs, word_trace
def test_golden(page, out_dir, content_5A, golden):
    (sheet, path), = gen.generate_pages(EN5A, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


def test_trace_font_has_every_lowercase_letter():
    assert set(GLYPHS) == set("abcdefghijklmnopqrstuvwxyz")
    assert andika_has("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    assert "<path" in svg("cat", 1.0)
    with pytest.raises(KeyError):
        svg("Cat", 1.0)


# Words that start with the letter but not with its usual sound: never on a letter page as a "starts" word.
NOT_FIRST_SOUND = {"eye", "ear", "ice", "owl", "orange", "oven", "acorn", "apron", "arm", "giraffe", "knee",
                   "chair", "cheese", "cherry", "chin", "chick", "shoe", "sheep", "shell", "shirt", "shovel",
                   "shorts", "thumb", "whale", "whistle", "phone"}


def test_hand_checked_letter_lists():
    data, bank = sounds(), vocab_by_word()
    for letter, words in data["letter_words"].items():
        for w in words:
            assert w in bank and bank[w].picture, w
            assert w.startswith(letter), (letter, w)
            assert w not in NOT_FIRST_SOUND, w
            assert not bank[w].needs_color, w
    for letter, words in data["letter_inside"].items():
        assert all(w in bank and letter in w[1:] for w in words), letter


def test_rimes_are_short_vowel_onset_rime_splits():
    bank = vocab_by_word()
    for w, (onset, rime) in rime_split(sounds()).items():
        assert w in bank and bank[w].picture, w
        assert onset and onset + rime == w and rime[0] in "aeiou" and not set(onset) & set("aeiou"), w
        assert not w.endswith("s") or w in {"bus", "dress"}, f"{w}: no plurals"


def test_real_plan_pages_pass_type_checks_and_wait_only_for_new_words():
    plan = gen.build_plan(EN5A)
    assert len(plan.pages) == 200
    assert set(plan.pages) | set(plan.waiting) == set(range(1, 201))
    for page in plan.pages:
        sheet = gen.build_sheet(EN5A, page, plan)
        assert registry.get(sheet.sheet_type).verify(sheet) == [], sheet.id
    texts = [repr(gen.build_sheet(EN5A, p, plan).items) for p in plan.pages]
    assert len(set(texts)) == len(texts), "two pages with the same items"


def test_page_range_matches_full_run(out_dir):
    alone = {s.id: s for s, _ in gen.generate_pages(EN5A, [21, 75, 165])}
    full = {s.id: s for s, _ in gen.generate_pages(EN5A, list(range(1, 52)) + list(range(71, 81))
                                                   + list(range(161, 171)))}
    for sid, sheet in alone.items():
        assert sheet == full[sid]


def test_new_words_fill_every_page():
    """With word batch 1 (q, z and 20 short-vowel words) every page is planned; each new word is new
    once, on a page that shows it, and seen at least 3 times."""
    plan = gen.build_plan(EN5A)
    assert plan.waiting == {} and sorted(plan.pages) == list(range(1, 201))
    new = [w.word for w in vocab() if w.level == "5A"]
    introduced = [w for p in plan.pages.values() for w in p.new_words]
    assert len(new) == 23 and sorted(introduced) == sorted(new)
    seen = Counter(w for p in plan.pages.values() for w in p.new_words + p.review_words)
    assert min(seen[w] for w in new) >= 3, {w: seen[w] for w in new if seen[w] < 3}
    assert max(len(p.new_words) for p in plan.pages.values()) <= EN5A.rules["max_new_words"]
    # new short-vowel words arrive one a page on Sound Pieces 131-150, next to a rhyming mate where there is one
    for page in range(131, 151):
        assert len(plan.pages[page].new_words) == 1


def test_new_words_wait_until_approved():
    """Without this level's words, the pages that need them wait (verify warns) instead of failing."""
    bank = [w for w in vocab() if w.level != "5A"]
    plan = plan_letters(EN5A, bank, sounds())
    assert set(plan.waiting) == {52, 53, 66, 67, 156} | set(range(131, 151)) | set(range(191, 201))


def test_5A_text_never_shows_internal_codes():
    from ws.verify import banned_words

    plan = gen.build_plan(EN5A)
    for page in (1, 71, 151, 161):
        sheet = gen.build_sheet(EN5A, page, plan)
        assert banned_words(" ".join([sheet.title, sheet.parent_tip] + [str(i) for i in sheet.items])) == []
