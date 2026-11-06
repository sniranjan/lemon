"""Phrases (6A-B) and sentences (6A-C) from frames with slots: `content/phrases/english.yaml`.

`fillings()` lists every way to fill a frame with known words that keeps the content true
(a color matches the picture, an animal can do the action). The planner chooses among them;
the sheet types' verify re-checks the result with `check_phrase()`.
"""

from __future__ import annotations

import itertools
import re
from collections.abc import Iterable

from .models import VocabEntry

SLOT = re.compile(r"\{(\w+)\}")
TOKEN = re.compile(r"[A-Za-z']+")
# Describing slot kinds, shown as a word only: the noun's picture carries them. Each names the
# hand-checked table in content/phrases/english.yaml that says which nouns it is true of.
PICTURELESS_KINDS = {"color", "size", "temp"}
DESCRIBED_BY = {"size": "sizes", "temp": "temperatures"}   # adjective -> [nouns it fits]


def slot_words(kind: str, data: dict, known: dict[str, VocabEntry]) -> list[str]:
    """Known words that may fill a slot of this kind, in word-bank order."""
    spec = data["slots"][kind]
    cats, extra, skip = set(spec.get("categories", [])), set(spec.get("words", [])), set(spec.get("except", []))
    for name in spec.get("lists", []):
        extra |= set(word_list(data, name))
    words = [w for w, e in known.items() if (e.category in cats or w in extra) and w not in skip]
    if spec.get("colored"):
        colors = data["picture_colors"]
        words = [w for w in words if w in colors] if (cats or extra) else [w for w in known if w in colors]
    if spec.get("described_by"):
        fits = {n for nouns in data[spec["described_by"]].values() for n in nouns}
        words = [w for w in words if w in fits] if (cats or extra) else [w for w in known if w in fits]
    return words


def word_list(data: dict, name: str) -> list[str]:
    """A hand-checked word list from the phrases file: a plain list, or a mapping of headings to lists."""
    value = data.get(name, [])
    if isinstance(value, dict):
        return [w for words in value.values() for w in words]
    return list(value)


def ownable(data: dict) -> set[str]:
    """Things a child can call "my ..." / "I have a ...": the `ownable` list plus `eatable`."""
    return set(word_list(data, "ownable")) | set(word_list(data, "eatable"))


def _article(next_word: str, noun: VocabEntry | None, data: dict) -> str:
    if noun is not None and noun.word in data.get("plural", []):
        return ""          # "blue pants", "I see purple grapes."
    if noun is not None and noun.mass:
        return "some"
    return "an" if next_word[:1].lower() in "aeiou" else "a"


def render(frame: str, filling: dict[str, str], known: dict[str, VocabEntry], data: dict) -> str:
    """Fill the frame's slots; `{a}` takes its article from the next word and the phrase's noun."""
    nouns = [known[w] for k, w in filling.items() if k not in PICTURELESS_KINDS and w in known]
    out = SLOT.sub(lambda m: "{a}" if m.group(1) == "a" else filling[m.group(1)], frame)
    while "{a}" in out:
        after = out.split("{a}", 1)[1].split()
        noun = next((n for n in nouns if n.word in (t.strip(".") for t in after)), None)
        art = _article(after[0], noun, data)
        out = out.replace("{a}", art, 1) if art else out.replace("{a} ", "", 1)
    return out[0].upper() + out[1:] if frame.endswith(".") else out


def _slots(frame: str) -> list[str]:
    return [s for s in SLOT.findall(frame) if s != "a"]


def fillings(frame: str, data: dict, known: dict[str, VocabEntry]) -> Iterable[dict[str, str]]:
    """Every true filling of the frame from known words (slot kind -> word), in a fixed order."""
    kinds = _slots(frame)
    if kinds == ["x", "y"]:
        for x, y in data["pairs"]:
            if x in known and y in known:
                yield {"x": x, "y": y}
        return
    options = [slot_words(k, data, known) for k in kinds]
    for combo in itertools.product(*options):
        filling = dict(zip(kinds, combo))
        if len(set(combo)) == len(combo) and is_true(filling, frame, data):
            yield filling


def is_true(filling: dict[str, str], frame: str, data: dict) -> bool:
    """The phrase says something true about its pictures."""
    colors = data["picture_colors"]
    noun = next((w for k, w in filling.items() if k not in PICTURELESS_KINDS), None)
    if "color" in filling:
        if noun is None or colors.get(noun) != filling["color"]:
            return False
    for kind, table in DESCRIBED_BY.items():   # "a big dog", "The soup is hot."
        if kind in filling and (noun is None or noun not in data.get(table, {}).get(filling[kind], [])):
            return False
    if "action" in filling:
        subject_kind = next((k for k in filling if data["slots"].get(k, {}).get("subject")), None)
        if subject_kind and filling[subject_kind] not in data["can_do"].get(filling["action"], []):
            return False
        # things a 3-year-old can't truthfully say he can do ("I can read"), and who can
        if frame.startswith("I can ") and filling["action"] in data.get("child_cannot", []):
            return False
        people = data.get("people_can", {}).get(filling["action"])
        person = next((w for k, w in filling.items() if data["slots"].get(k, {}).get("people")), None)
        if people is not None and person is not None and person not in people:
            return False
    if " is " in frame:
        if any(w in data.get("plural", []) for w in filling.values()):
            return False
    if "{a}" in frame and noun in data.get("the_only", []):   # "the sun", never "a sun"
        return False
    if "look at" in frame.lower() and noun in data.get("dont_look_at", []):   # never "Look at the sun."
        return False
    return True


def pictures_for(filling: dict[str, str], data: dict) -> list[str]:
    """The pictures shown with a phrase: its nouns and actions, at most two. An animal doing an
    action ("The mouse can eat.") shows the animal only: the action pictures show a child."""
    subject = next((w for k, w in filling.items() if data["slots"].get(k, {}).get("subject")), None)
    if subject is not None:
        return [subject]
    return [w for k, w in filling.items() if k not in PICTURELESS_KINDS][:2]


def picture_size(filling: dict[str, str]) -> str | None:
    """big / little: the noun's picture is drawn large or small to match."""
    return filling.get("size")


def check_phrase(item: dict, data: dict, known: dict[str, VocabEntry], max_words: int | None) -> list[str]:
    """Problems with one planned phrase/sentence item (empty when it is fine)."""
    problems = []
    allowed = {w.lower() for w in data["allowed_words"]}
    known_lower = {w.lower() for w in known}
    unknown = [t for t in TOKEN.findall(item["text"]) if t.lower() not in allowed and t.lower() not in known_lower]
    if unknown:
        problems.append(f"uses words the child hasn't met {unknown}: {item['text']!r}")
    if max_words is not None and len(item["text"].split()) > max_words:
        problems.append(f"longer than {max_words} words: {item['text']!r}")
    filling = item["slots"]
    in_frame_order = {k: filling[k] for k in _slots(item["frame"]) if k in filling}   # the manifest sorts keys
    if not is_true(in_frame_order, item["frame"], data):
        problems.append(f"doesn't match its pictures: {item['text']!r}")
    if render(item["frame"], filling, known, data) != item["text"]:
        problems.append(f"text doesn't match its frame: {item['text']!r}")
    if item["pictures"] != pictures_for(in_frame_order, data):
        problems.append(f"pictures {item['pictures']} don't match the phrase: {item['text']!r}")
    if item.get("picture_size") != picture_size(filling):
        problems.append(f"picture should be drawn {picture_size(filling) or 'normal size'}: {item['text']!r}")
    return problems
