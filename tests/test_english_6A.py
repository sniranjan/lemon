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


# --- Ducklings word batch 1: describing words, animal-only pictures, Word Hunt order -------------

def _phrase(frame, **fill):
    from ws.phrases import picture_size, pictures_for

    data, known = phrases(), vocab_by_word()
    p = {"frame": frame, "slots": fill, "text": render(frame, fill, known, data),
         "words": list(fill.values()), "pictures": pictures_for(fill, data)}
    if picture_size(fill):
        p["picture_size"] = picture_size(fill)
    return p


@pytest.mark.parametrize("name, page, new, phrases_", [
    ("big-little", 141, ["big"], [_phrase("The {sized} is {size}.", sized="dog", size="big"),
                                  _phrase("I see {a} {size} {sized}.", size="little", sized="mouse"),
                                  _phrase("The {animal} can {action}.", animal="mouse", action="eat")]),
    ("hot-cold", 143, ["hot"], [_phrase("The {temp_thing} is {temp}.", temp_thing="soup", temp="hot"),
                                _phrase("I like {temp} {temp_food}.", temp="cold", temp_food="milk"),
                                _phrase("The {temp_thing} is {temp}.", temp_thing="snow", temp="cold")]),
])
def test_golden_describing_words(name, page, new, phrases_, out_dir, golden):
    """big/little draw the noun's picture large/small; hot/cold show the thing only; an animal doing
    an action shows the animal only. A fixed plan entry, so the golden doesn't move as words are added."""
    from ws.plan import LevelPlan, PagePlan
    from ws.render import write_html

    plan = LevelPlan(subject="english", level="6A")
    plan.pages[page] = PagePlan(page=page, new_words=new, extra={"phrases": phrases_},
                                review_words=sorted({w for p in phrases_ for w in p["words"]} - set(new)))
    sheet = gen.build_sheet(EN6A, page, plan)
    assert registry.get(sheet.sheet_type).verify(sheet) == []
    path = out_dir / f"{name}.html"
    write_html(sheet, EN6A, path)
    html = path.read_text()
    if name == "big-little":
        assert 'class="size-big"' in html and 'class="size-little"' in html
        assert sheet.items[2]["pictures"] == ["mouse"]          # not the child eating
    else:
        assert 'class="size-' not in html
        assert [i["text"] for i in sheet.items] == ["The soup is hot.", "I like cold milk.", "The snow is cold."]
    golden(f"{sheet.id}-{name}.html", html)
    golden(f"{sheet.id}-{name}.json", sheet.model_dump_json(indent=2) + "\n")


def test_describing_phrases_stay_true():
    data, known = phrases(), vocab_by_word()
    for frame in data["sentence_groups"]["describe"]:
        for fill in fillings(frame, data, known):
            noun = next(w for k, w in fill.items() if k not in ("size", "temp"))
            if "size" in fill:
                assert noun in data["sizes"][fill["size"]]
            if "temp" in fill:
                assert noun in data["temperatures"][fill["temp"]]
    texts = {render(f, fill, known, data) for f in data["sentence_groups"]["describe"] for fill in fillings(f, data, known)}
    assert {"The dog is big.", "I see a little mouse.", "The sun is hot.", "The snow is cold."} <= texts
    assert not {"The whale is little.", "The bee is big.", "The sun is cold.", "The snow is hot."} & texts


def test_animal_action_sentences_show_the_animal_only():
    from ws.phrases import pictures_for

    data, known = phrases(), vocab_by_word()
    for fill in fillings("The {animal} can {action}.", data, known):
        assert pictures_for(fill, data) == [fill["animal"]]
    assert pictures_for({"person": "dad", "action": "wave"}, data) == ["dad", "wave"]
    assert pictures_for({"action": "hop"}, data) == ["hop"]


def test_read_is_only_something_mom_and_dad_can_do():
    data, known = phrases(), vocab_by_word()
    texts = {render(f, fill, known, data) for g in ("can_do",) for f in data["phrase_groups"][g]
             for fill in fillings(f, data, known)}
    texts |= {render(f, fill, known, data) for g in ("can", "daily") for f in data["sentence_groups"][g]
              for fill in fillings(f, data, known)}
    reads = {t for t in texts if t.rstrip(".").endswith(" read")}
    assert reads == {"mom can read", "dad can read", "Mom can read.", "Dad can read.", "I like to read."}


def test_size_must_match_the_picture():
    from ws.phrases import check_phrase

    data, known = phrases(), vocab_by_word()
    item = _phrase("The {sized} is {size}.", sized="dog", size="big")
    assert check_phrase(item, data, known, 6) == []
    assert any("drawn big" in p for p in check_phrase({**item, "picture_size": None}, data, known, 6))
    animal = _phrase("The {animal} can {action}.", animal="dog", action="run")
    assert any("pictures" in p for p in check_phrase({**animal, "pictures": ["dog", "run"]}, data, known, 6))
    # the manifest stores slots with sorted keys: pictures are checked in the frame's slot order
    person = _phrase("{person} can {action}.", person="dad", action="wave")
    assert check_phrase({**person, "slots": dict(sorted(person["slots"].items()))}, data, known, 6) == []


def test_word_hunt_favors_least_seen_chicks_words():
    from ws.plan import level_exposures

    seen = level_exposures("english", ["7A"], vocab())
    plan = gen.build_plan(EN6A)
    counts = [seen[w] for p in range(1, 31) for w in plan.pages[p].review_words]
    assert counts == sorted(counts)            # least seen in Chicks first
    assert counts[0] == min(seen[w.word] for w in vocab() if w.level == "7A")


def test_batch1_words_are_new_on_their_pages_with_their_picture():
    """Words 1–30 fill pages 71–100, words 31–40 pages 141–150, each used and pictured on its page."""
    plan = gen.build_plan(EN6A)
    new6a = [w.word for w in vocab() if w.level == "6A"]
    pages = list(range(71, 101)) + list(range(141, 151))
    assert [plan.pages[p].new_words for p in pages] == [[w] for w in new6a[:40]]
    bank = vocab_by_word()
    for p in pages:
        (w,) = plan.pages[p].new_words
        if bank[w].picture:
            assert w in {pic for ph in plan.pages[p].extra["phrases"] for pic in ph["pictures"]}, (p, w)
