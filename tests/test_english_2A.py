"""Cubs Reading (english 2A): picture puzzles, kinds of words, read-aloud passages, and their planner.

Uses the real content (word bank, content/grammar, content/passages): the 2A plan only reads the
hand-checked lists and this level's own words, so other levels' new words don't change it.
"""

from collections import Counter

import pytest

from ws import generate as gen
from ws import registry
from ws.content import grammar, passages, vocab, vocab_by_word
from ws.reading import KINDS, in_text, kind_of, mentions, sentences, word_count
from ws.syllabus import load_level
from ws.verify import verify_sheets

EN2A = load_level("english", "2A")


@pytest.mark.parametrize("page", [1, 41, 61, 91, 111, 151])   # missing letters, crossword, pick, sort, fill, passage
def test_golden(page, out_dir, golden):
    (sheet, path), = gen.generate_pages(EN2A, [page])
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    golden(f"{sheet.id}.html", path.read_text())
    golden(f"{sheet.id}.json", sheet.model_dump_json(indent=2) + "\n")


@pytest.fixture(scope="module")
def all_sheets():
    plan = gen.build_plan(EN2A)
    return plan, [gen.build_sheet(EN2A, p, plan) for p in range(1, EN2A.pages + 1)]


def test_whole_level_verifies(all_sheets):
    _, sheets = all_sheets
    assert [i for i in verify_sheets(sheets) if i.severity == "error"] == []
    assert [i for i in verify_sheets(sheets) if i.severity == "warning"] == []


def test_page_range_matches_full_run(out_dir):
    alone = {s.id: s for s, _ in gen.generate_pages(EN2A, [45, 99, 140, 177])}
    full = {s.id: s for s, _ in gen.generate_pages(EN2A, list(range(1, 201)))}
    for sid, sheet in alone.items():
        assert sheet == full[sid]


def test_every_new_word_new_once_and_seen_three_times(all_sheets):
    plan, _ = all_sheets
    new = [w for p in plan.pages.values() for w in p.new_words]
    level_words = [e.word for e in vocab() if e.level == "2A"]
    assert new == level_words and len(new) == 40
    seen = Counter(w for p in plan.pages.values() for w in p.new_words + p.review_words)
    assert min(seen[w] for w in new) >= 3


def test_kinds_lists_are_disjoint_known_and_cover_the_new_words():
    g, bank = grammar(), vocab_by_word()
    lists = {k: g["kinds"][k] for k in KINDS}
    for k, words in lists.items():
        assert len(set(words)) == len(words), k
        assert not [w for w in words if w not in bank], k
    assert not (set(lists["naming"]) & set(lists["doing"]) | set(lists["naming"]) & set(lists["describing"])
                | set(lists["doing"]) & set(lists["describing"]))
    for e in vocab():
        if e.level == "2A":
            assert kind_of(e.word, g) is not None, e.word
    # pictured only as crayons: color words stay out of the describing list
    assert not [w for w in lists["describing"] if bank[w].needs_color]


def test_fill_sentences_have_one_blank_and_an_answer_of_their_kind():
    g = grammar()
    for kind, group in g["fill"].items():
        texts = [f["text"] for f in group]
        assert len(set(texts)) == len(texts)
        for f in group:
            assert f["text"].count("___") == 1, f
            assert kind_of(f["answer"], g) == kind, f


def test_puzzle_words_are_pictured_earlier_words():
    bank = vocab_by_word()
    for w in grammar()["puzzle_words"]:
        assert w in bank and bank[w].picture and bank[w].level in ("7A", "6A"), w
        assert w.isalpha() and w.islower()


def test_passages_are_original_short_and_answerable():
    data, bank = passages(), vocab_by_word()
    ids = [p["id"] for p in data["passages"]]
    assert len(ids) == len(set(ids)) == 25   # 50 Read Aloud pages, each passage read twice
    for p in data["passages"]:
        text = " ".join(p["text"].split())
        assert 40 <= word_count(text) <= 60, p["id"]
        assert max(word_count(s) for s in sentences(text)) <= 16, p["id"]
        assert p["picture"] in {e.picture for e in bank.values()}, p["id"]
        assert all(w in bank and mentions(text, w) for w in p["words"]), p["id"]
        for q in p["questions"]:
            assert in_text(q["a"], text), (p["id"], q["q"])
            assert len(q["wrong"]) == 2 and q["a"] not in q["wrong"], (p["id"], q["q"])


def test_mentions_matches_inflections():
    assert mentions("Ben carries the blanket.", "carry")
    assert mentions("They take turns jumping in it.", "jump")
    assert mentions("Leo stirs it.", "stir") and mentions("She stirred it.", "stir")
    assert not mentions("The robin sings.", "rob")


def test_verify_catches_broken_sheets(all_sheets):
    _, sheets = all_sheets
    by_page = {s.page_number: s for s in sheets}

    def issues(sheet):
        return [i.message for i in registry.get(sheet.sheet_type).verify(sheet)]

    # a puzzle that shows the wrong number of empty boxes
    s = by_page[1].model_copy(deep=True)
    s.items[0]["letters"] = [[ch, True] for ch, _ in s.items[0]["letters"]]
    assert any("empty boxes" in m for m in issues(s))
    # a row with two naming words
    s = by_page[61].model_copy(deep=True)
    row = next(i for i in s.items if i["kind"] == "pick")
    row["words"] = [row["answer"], "cat", "dog"]
    assert any("exactly one naming" in m for m in issues(s))
    # a fill-in with two choices of the right kind
    s = by_page[111].model_copy(deep=True)
    s.items[0]["choices"] = [s.items[0]["answer"], "cat"]
    assert any("exactly one" in m for m in issues(s))
    # an answer that isn't in the passage, and a wrong word count
    s = by_page[151].model_copy(deep=True)
    s.items[1]["answer"] = s.items[1]["choices"][0] = "a purple whale"
    s.items[0]["words"] = 3
    msgs = issues(s)
    assert any("not in the passage" in m for m in msgs) and any("word count printed" in m for m in msgs)


def test_passages_are_read_twice_with_different_questions(all_sheets):
    _, sheets = all_sheets
    reads = [s for s in sheets if s.sheet_type == "read_aloud"]
    for a, b in zip(reads[::2], reads[1::2]):
        assert a.items[0]["id"] == b.items[0]["id"]
        assert {q["q"] for q in a.items[1:]}.isdisjoint(q["q"] for q in b.items[1:])
