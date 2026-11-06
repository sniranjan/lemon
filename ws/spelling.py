"""Puppies Reading (3A) spelling: patterns, word endings, syllables, copy sentences (Kittens Reading letter teams are in ws/phonics.py).

The hand-checked tables live in `content/phonics/english.yaml`. This module finds where a pattern sits
in a word, derives endings from the spelling rules (so verify can check the hand-written forms), and
checks copy sentences against the words the child knows.
"""

from __future__ import annotations

import re

VOWELS = "aeiou"
TOKEN = re.compile(r"[A-Za-z']+")
ENDINGS = ("plural", "ing", "ed")


# --- spelling patterns ---------------------------------------------------------------------

def pattern_letters(data: dict, code: str) -> str:
    return data["patterns"][code]["letters"]


def pattern_span(word: str, code: str, data: dict) -> list[int] | None:
    """Indexes of the pattern's letters in the word (the gaps the child fills), or None if the
    word doesn't have the pattern. Magic e (`a_e`): the vowel, one consonant, then a final e."""
    letters = pattern_letters(data, code)
    if letters.endswith("_e"):
        m = re.search(rf"({letters[0]})[^aeiou]e$", word)
        return [m.start(1), len(word) - 1] if m else None
    i = word.find(letters)
    return list(range(i, i + len(letters))) if i >= 0 else None


def gapped(word: str, span: list[int]) -> list[list]:
    """[[letter, is_gap], ...] for the template."""
    return [[ch, i in span] for i, ch in enumerate(word)]


# --- endings ---------------------------------------------------------------------------------

def _vowel_groups(word: str) -> int:
    return len(re.findall(r"[aeiouy]+", word.lower()))


def _cvc(word: str) -> bool:
    """One short vowel between consonants at the end of a one-syllable word: hop, clap, swim."""
    return (len(word) >= 3 and word[-1] not in VOWELS + "wxy" and word[-2] in VOWELS
            and word[-3] not in VOWELS and _vowel_groups(word) == 1)


def by_rule(base: str, ending: str) -> str:
    """The regular form: plural / third-person -s, -ing, -ed."""
    if ending == "plural":
        if base.endswith(("s", "x", "z", "ch", "sh")):
            return base + "es"
        if base.endswith("y") and base[-2] not in VOWELS:
            return base[:-1] + "ies"
        return base + "s"
    if ending == "ing":
        if base.endswith("ie"):
            return base[:-2] + "ying"
        if base.endswith("e") and not base.endswith(("ee", "ye", "oe")):
            return base[:-1] + "ing"
        return base + base[-1] + "ing" if _cvc(base) else base + "ing"
    if ending == "ed":
        if base.endswith("e"):
            return base + "d"
        if base.endswith("y") and base[-2] not in VOWELS:
            return base[:-1] + "ied"
        return base + base[-1] + "ed" if _cvc(base) else base + "ed"
    raise ValueError(f"unknown ending {ending!r}")


def tail(base: str, ending: str, form: str) -> str:
    """What is added, as shown on the sheet: s / es, ing, ed."""
    if ending == "plural":
        return "es" if form == base + "es" else "s"
    return ending


def spelling_rule(base: str, ending: str, form: str) -> str:
    """plain / es / drop_e / double: the rule a form follows (for variety on a page)."""
    if ending == "plural":
        return tail(base, ending, form)
    if form.startswith(base + base[-1]) and _cvc(base):
        return "double"
    if base.endswith("e") and not form.startswith(base):
        return "drop_e"
    return "plain"


def check_endings(data: dict) -> list[str]:
    """Every hand-written form matches the spelling rules, or is listed under `irregular`."""
    problems = []
    irregular = data.get("irregular") or {}
    for base, forms in data["endings"].items():
        for ending, form in (forms or {}).items():
            if ending not in ENDINGS:
                problems.append(f"{base}: unknown ending {ending!r}")
                continue
            expected = (irregular.get(base) or {}).get(ending) or by_rule(base, ending)
            if form != expected:
                problems.append(f"{base} + {ending}: table says {form!r}, the spelling rules give {expected!r}")
    return problems


# --- syllables ---------------------------------------------------------------------------------

def syllable_table(data: dict) -> dict[str, tuple[str, list[str]]]:
    """word -> (kind, syllables)."""
    return {w: (kind, syls) for kind, words in data["syllables"].items() for w, syls in words.items()}


def check_syllables(word: str, syls: list[str], kind: str) -> list[str]:
    problems = []
    if "".join(syls) != word:
        problems.append(f"syllables {syls} don't spell {word!r}")
    for s in syls:
        if not re.search(r"[aeiouy]", s):
            problems.append(f"syllable {s!r} of {word!r} has no vowel")
    want = {"one": 1, "three": 3}.get(kind, 2)
    if len(syls) != want:
        problems.append(f"{word!r} is listed as {kind} but has {len(syls)} syllables")
    return problems


# --- copy sentences ------------------------------------------------------------------------------

def allowed_tokens(data: dict, words: set[str]) -> set[str]:
    """Sight words, known words, and their regular endings (wheels, flies, plays)."""
    base = {w.lower() for w in data["sight_words"]} | {w.lower() for w in words}
    out = set(base)
    for w in base:
        for ending in ENDINGS:
            out.add(by_rule(w, ending))
    for forms in (data.get("irregular") or {}).values():
        out.update(forms.values())
    return out


def sentence_tokens(text: str) -> list[str]:
    return TOKEN.findall(text)


def check_sentence(text: str, word: str, data: dict, words: set[str],
                   length: tuple[int, int] | None = None, marks: list[str] | None = None) -> list[str]:
    problems = []
    tokens = sentence_tokens(text)
    allowed = allowed_tokens(data, words)
    unknown = [t for t in tokens if t.lower() not in allowed]
    if unknown:
        problems.append(f"uses words the child hasn't met {unknown}: {text!r}")
    if not text[:1].isupper() or text[-1:] not in ".?!":
        problems.append(f"not a complete sentence (capital letter, end mark): {text!r}")
    forms = {word} | {by_rule(word, e) for e in ENDINGS}
    if not any(t.lower() in forms for t in tokens):
        problems.append(f"doesn't use its word {word!r}: {text!r}")
    if length and not length[0] <= len(tokens) <= length[1]:
        problems.append(f"{len(tokens)} words, the part asks for {length[0]}–{length[1]}: {text!r}")
    if marks and text[-1:] not in marks:
        problems.append(f"ends with {text[-1:]!r}, the part asks for {marks}: {text!r}")
    return problems
