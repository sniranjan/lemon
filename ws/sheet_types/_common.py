"""Helpers shared by several sheet types (not a sheet type itself)."""

from __future__ import annotations

import random

from ..content import math_objects, vocab_by_word
from ..models import Issue, Sheet

NUMBER_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]


def word_items(words: list[str], kind: str) -> list[dict]:
    bank = vocab_by_word()
    return [{"kind": kind, "word": w, "picture": bank[w].picture} for w in words]


def new_numbers(rules: dict) -> list[int]:
    """The part's `new` number(s): null, one number, or a list (5A parts add two numbers each)."""
    new = rules.get("new")
    return [] if new is None else [new] if isinstance(new, int) else list(new)


def pick_numbers(rng: random.Random, rules: dict, count: int) -> list[int]:
    """`count` distinct numbers from [min, max]; the part's `new` number(s) are always among them."""
    lo, hi, news = rules["min"], rules["max"], new_numbers(rules)
    pool = [n for n in range(lo, hi + 1) if n not in news]
    if count > len(pool) + len(news) or len(news) > count:
        raise ValueError(f"cannot pick {count} distinct numbers from {lo}–{hi}")
    picked = rng.sample(pool, count - len(news))
    for n in news:
        picked.insert(rng.randrange(len(picked) + 1), n)
    return picked


def pick_objects(rng: random.Random, count: int) -> list[dict]:
    """A different countable object for each row (repeats only if there are too few)."""
    objs = list(math_objects())
    rng.shuffle(objs)
    return [objs[i % len(objs)] for i in range(count)]


def error(sheet: Sheet, message: str) -> Issue:
    return Issue(sheet_id=sheet.id, severity="error", message=message)
