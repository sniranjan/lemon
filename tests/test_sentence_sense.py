"""Sentences that are grammatical but make no sense: "I eat a pumpkin.", "I have a koala.".

The hand-checked lists live in content/phrases/english.yaml (`eatable`, `ownable`, `the_only`, ...).
The scan at the bottom reads every sentence and phrase the Chicks and Ducklings Reading plans can
print, and every Cubs Reading card sentence, fill-in sentence and passage sentence (story sentences, card sentences, planned phrases) and checks it against rules written here,
independently of the generator's own filters.
"""

import re

import pytest

from ws import generate as gen
from ws.content import grammar, passages, phonics, phrases, stories, vocab, vocab_by_word
from ws.reading import sentences
from ws.phrases import fillings, ownable, render, word_list
from ws.sheet_types.word_story import frame_options, story_sentences
from ws.syllabus import load_level

EN7A = load_level("english", "7A")
EN6A = load_level("english", "6A")
EN4A = load_level("english", "4A")

# Sentences that once came out of the frames and must never come back.
KNOWN_BAD = {
    "I eat a pumpkin.", "I eat a lemon.", "I eat a potato.", "I eat a tomato.", "I eat a cake.",
    "I eat a pizza.", "I have a koala.", "Here is my koala.", "I have a lion.", "I have a camel.",
    "Here is my door.", "Here is my sink.", "Here is my bathtub.", "Here is my bus.", "I have a rocket.",
    "I can cook.", "I can wash.", "I wash my foot.", "I see a sun.", "This is a sun.", "a yellow sun",
    "I like my yellow key.", "my broom", "my hose", "I eat green grapes.",
    "Look at the sun.",
    "There is a candle on my cake.", "I eat my soup with a spoon.", "First she draws a sun.",   # Cubs drafts
}


def _known():
    return {e.word: e for e in vocab()}


def test_eat_frame_uses_only_the_hand_checked_list():
    data = phrases()
    texts = {render("I eat {a} {eatable}.", f, _known(), data)
             for f in fillings("I eat {a} {eatable}.", data, _known())}
    assert {"I eat some rice.", "I eat a cookie.", "I eat an apple.", "I eat grapes.", "I eat peas."} <= texts
    assert not texts & {"I eat a pumpkin.", "I eat a lemon.", "I eat a potato.", "I eat some milk.",
                        "I eat some soup.", "I eat a cake.", "I eat a pizza."}
    assert {t.split()[-1].rstrip(".") for t in texts} == set(data["eatable"]) & set(_known())


def test_hand_checked_lists_name_real_words():
    data, bank = phrases(), vocab_by_word()
    for name in ("eatable", "ownable", "the_only", "plural", "child_cannot"):
        missing = [w for w in word_list(data, name) if w not in bank]
        assert not missing, f"{name} lists words not in the word bank: {missing}"
    assert all(bank[w].category == "food" for w in data["eatable"])


@pytest.mark.parametrize("word", ["koala", "lion", "camel", "bear", "cow", "bus", "rocket", "door",
                                  "sink", "pumpkin", "lemon", "diaper"])
def test_no_my_or_have_for_things_a_child_cannot_have(word):
    for s in story_sentences(vocab_by_word()[word], stories(), phrases()):
        assert not re.search(r"\b(my|have)\b", s), s


@pytest.mark.parametrize("word,sentence", [("dog", "I have a dog."), ("cat", "Here is my cat."),
                                           ("ball", "I have a ball."), ("cookie", "I have a cookie."),
                                           ("mom", "I hug my mom."), ("nose", "I touch my nose.")])
def test_my_and_have_for_toys_pets_family_body(word, sentence):
    assert sentence in story_sentences(vocab_by_word()[word], stories(), phrases())


def test_never_look_at_the_sun():
    sentences = story_sentences(vocab_by_word()["sun"], stories(), phrases())
    assert "Look at the sun." not in sentences and "I see the sun." in sentences
    data = phrases()
    look = {render("Look at the {thing}.", f, _known(), data) for f in fillings("Look at the {thing}.", data, _known())}
    assert "Look at the sun." not in look and "Look at the moon." in look


def test_wild_animals_keep_see_look_this():
    assert set(story_sentences(vocab_by_word()["koala"], stories(), phrases())) == {
        "I see a koala.", "Look at the koala.", "This is a koala.", "I like the koala."}


def test_my_slot_is_ownable_body_or_family():
    data, bank = phrases(), vocab_by_word()
    for frame in ("my {mine}", "Here is my {mine}.", "my {color} {colored_mine}", "I like my {color} {colored_mine}."):
        for f in fillings(frame, data, _known()):
            w = f.get("mine") or f["colored_mine"]
            assert w in ownable(data) or bank[w].category in ("body", "family"), (frame, w)


def test_story_frames_never_fall_back_to_banned_frames():
    """A word left with no frame is an error, not a silent return to every frame."""
    bank = vocab_by_word()
    data = dict(stories(), frames_by_category={"animals": ["I have {a} {w}."]})
    with pytest.raises(ValueError, match="no story frame fits 'koala'"):
        frame_options(bank["koala"], data, phrases())


# ---- full scan -------------------------------------------------------------------------------

def all_texts() -> list[tuple[str, str]]:
    """(where, text) for every sentence or phrase Chicks and Ducklings Reading can print today."""
    bank, sd, pd = vocab(), stories(), phrases()
    out = []
    for e in bank:
        if e.level == "7A":
            out += [(f"story:{e.word}", s) for s in story_sentences(e, sd, pd)]
            out += [(f"card:{e.word}", s) for s in e.sentences]
    plan = gen.build_plan(EN7A)
    for page in plan.pages:
        sheet = gen.build_sheet(EN7A, page, plan)
        out += [(sheet.id, i["text"]) for i in sheet.items if i.get("kind") == "sentence"]
    plan = gen.build_plan(EN6A)
    for page, p in plan.pages.items():
        out += [(f"6A p{page}", ph["text"]) for ph in p.extra.get("phrases", [])]
    plan = gen.build_plan(EN4A)   # Kittens Reading: traced sentences
    for page, p in plan.pages.items():
        out += [(f"4A p{page}", ph["text"]) for ph in p.extra.get("phrases", [])]
    # Cubs Reading: word-card sentences, fill-in sentences with their answer, every passage sentence
    out += [(f"card:{e.word}", s) for e in bank if e.level == "2A" for s in e.sentences]
    out += [(f"2A fill:{f['answer']}", f["text"].replace("___", f["answer"]))
            for group in grammar()["fill"].values() for f in group]
    out += [(f"2A passage:{p['id']}", s) for p in passages()["passages"] for s in sentences(" ".join(p["text"].split()))]
    return out


def puppies_texts() -> list[tuple[str, str]]:
    """Every copy sentence Puppies Reading can print (all of its words' sentences), and the planned ones."""
    out = [(f"3A:{e.word}", s) for e in vocab() if e.level == "3A" for s in e.sentences]
    plan = gen.build_plan(load_level("english", "3A"))
    out += [(f"3A p{page}", c["text"]) for page, p in plan.pages.items() for c in p.extra.get("cards", []) if "text" in c]
    return out


def with_puppies_facts(data: dict) -> dict:
    """The phrases file's hand-checked lists plus the Puppies words' facts (content/phonics/english.yaml `sense`)."""
    extra = phonics()["sense"]
    merged = dict(data)
    merged["picture_colors"] = {**data["picture_colors"], **extra["picture_colors"]}
    merged["can_do"] = {k: list(data["can_do"].get(k, [])) + list(extra["can_do"].get(k, []))
                        for k in set(data["can_do"]) | set(extra["can_do"])}
    for name in ("eatable", "plural"):
        merged[name] = word_list(data, name) + list(extra[name])
    merged["ownable"] = word_list(data, "ownable") + list(extra["ownable"])
    return merged


def problems(text: str, data: dict, free: bool = False) -> list[str]:
    """Rule breaks in one text. `free` (card sentences, written by hand and read to the child, so not
    built from frames): only the known-bad list and picture colors."""
    bank = vocab_by_word()
    cat = {w: e.category for w, e in bank.items()}
    plural = set(data["plural"])
    eatable, own = set(data["eatable"]), ownable(data)
    found = []
    t = text.rstrip(".")
    if text in KNOWN_BAD or t in KNOWN_BAD:
        found.append("known bad")
    for m in re.finditer(r"\b[Ll]ook at (?:the |my )?(\w+)", t):
        if m.group(1) in ("sun",):
            found.append(f"look at the {m.group(1)}")
    colors = data["picture_colors"]   # a color named with a pictured noun must match its picture
    for m in re.finditer(r"\b(red|blue|yellow|green|pink|purple) (\w+)\b|\bThe (\w+) is (red|blue|yellow|green|pink|purple)\b", t):
        color, noun = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3))
        if noun in colors and colors[noun] != color:
            found.append(f"{noun} is {colors[noun]}, not {color}")
    if free:
        return found
    for m in re.finditer(r"\bI eat (?:an? |some )?(\w+)", t):
        if m.group(1) not in eatable:
            found.append(f"eats {m.group(1)}")
    for m in re.finditer(r"\b(?:my|I have (?:an?|some)) (?:(?:red|blue|yellow|green|pink|purple|brown|black) )?(\w+)", t):
        w = m.group(1)
        if w in bank and w not in own and cat[w] not in ("body", "family"):
            found.append(f"owns {w}")
    for m in re.finditer(r"\b(?:a|an) (?:\w+ )?(\w+)", t):
        if m.group(1) in plural or m.group(1) in data["the_only"]:
            found.append(f"'a' with {m.group(1)}")
    for m in re.finditer(r"\b(\w+) is\b", t):
        if m.group(1) in plural:
            found.append(f"{m.group(1)} is")
    for m in re.finditer(r"^The (\w+) can (\w+)$", t):
        animal, action = m.groups()
        if animal not in data["can_do"].get(action, []):
            found.append(f"{animal} can't {action}")
    for m in re.finditer(r"^I can (\w+)$", t):
        if m.group(1) in data["child_cannot"] or m.group(1) in ("wash", "ride"):
            found.append(f"child can't say I can {m.group(1)}")
    for m in re.finditer(r"^(?:Mom|Dad|Grandma|Grandpa|mom|dad|grandma|grandpa) can (\w+)$", t):
        if m.group(1) in ("crawl", "roll", "wash", "ride"):
            found.append(f"grown-up can {m.group(1)}")
    for m in re.finditer(r"\bI wash my (\w+)", t):
        if m.group(1) not in ("hand", "hair", "face"):
            found.append(f"washes {m.group(1)}")
    return found


def test_scan_every_chicks_and_ducklings_sentence():
    data = phrases()
    texts = all_texts()
    assert len(texts) > 1000
    bad = [(where, text, p) for where, text in texts for p in problems(text, data, free=where.startswith("card:"))]
    assert not bad, "\n".join(f"{w}: {t!r} ({p})" for w, t, p in bad[:40])


def test_scan_every_puppies_copy_sentence():
    """Puppies Reading copy sentences are hand-written and copied, not read to the child: full rules."""
    data = with_puppies_facts(phrases())
    texts = puppies_texts()
    assert len(texts) >= 140
    bad = [(where, text, p) for where, text in texts for p in problems(text, data)]
    assert not bad, "\n".join(f"{w}: {t!r} ({p})" for w, t, p in bad[:40])


@pytest.mark.parametrize("text", ["I have a shark.", "I eat a lime.", "The shark can run.", "The toad can fly.",
                                  "I have a jeans.", "Mom has a blue purse."])
def test_scan_catches_bad_puppies_sentences(text):
    assert problems(text, with_puppies_facts(phrases()))


@pytest.mark.parametrize("text", sorted(KNOWN_BAD))
def test_scan_catches_known_bad(text):
    assert problems(text, phrases())
