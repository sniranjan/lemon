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
PICTURELESS_KINDS = {"color"}   # slot kinds shown as a word only (the noun's picture carries the color)


def slot_words(kind: str, data: dict, known: dict[str, VocabEntry]) -> list[str]:
    """Known words that may fill a slot of this kind, in word-bank order."""
    spec = data["slots"][kind]
    cats, extra, skip = set(spec.get("categories", [])), set(spec.get("words", [])), set(spec.get("except", []))
    words = [w for w, e in known.items() if (e.category in cats or w in extra) and w not in skip]
    if spec.get("colored"):
        colors = data["picture_colors"]
        words = [w for w in words if w in colors] if (cats or extra) else [w for w in known if w in colors]
    return words


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
    if "color" in filling:
        noun = next((w for k, w in filling.items() if k != "color"), None)
        if noun is None or colors.get(noun) != filling["color"]:
            return False
    if "action" in filling:
        subject_kind = next((k for k in filling if data["slots"].get(k, {}).get("subject")), None)
        if subject_kind and filling[subject_kind] not in data["can_do"].get(filling["action"], []):
            return False
    if " is " in frame:
        if any(w in data.get("plural", []) for w in filling.values()):
            return False
    return True


def pictures_for(filling: dict[str, str]) -> list[str]:
    return [w for k, w in filling.items() if k not in PICTURELESS_KINDS][:2]


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
    if not is_true(filling, item["frame"], data):
        problems.append(f"doesn't match its pictures: {item['text']!r}")
    if render(item["frame"], filling, known, data) != item["text"]:
        problems.append(f"text doesn't match its frame: {item['text']!r}")
    return problems
