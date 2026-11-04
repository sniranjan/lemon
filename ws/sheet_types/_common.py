"""Helpers shared by several sheet types (not a sheet type itself)."""

from __future__ import annotations

import random

from ..content import math_objects, vocab_by_word
from ..models import Issue, Sheet

NUMBER_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]


def word_items(words: list[str], kind: str) -> list[dict]:
    bank = vocab_by_word()
    return [{"kind": kind, "word": w, "picture": bank[w].picture} for w in words]


def pick_numbers(rng: random.Random, rules: dict, count: int) -> list[int]:
    """`count` distinct numbers from [min, max]; the part's `new` number is always one of them."""
    lo, hi, new = rules["min"], rules["max"], rules.get("new")
    pool = [n for n in range(lo, hi + 1) if n != new]
    if count > len(pool) + (new is not None):
        raise ValueError(f"cannot pick {count} distinct numbers from {lo}–{hi}")
    picked = rng.sample(pool, count - (new is not None))
    if new is not None:
        picked.insert(rng.randrange(count), new)
    return picked


def pick_objects(rng: random.Random, count: int) -> list[dict]:
    """A different countable object for each row (repeats only if there are too few)."""
    objs = list(math_objects())
    rng.shuffle(objs)
    return [objs[i % len(objs)] for i in range(count)]


def error(sheet: Sheet, message: str) -> Issue:
    return Issue(sheet_id=sheet.id, severity="error", message=message)
