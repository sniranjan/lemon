"""Factors and multiples (Owls math, 4.OA.4): factor pairs, counting in multiples, spotting multiples,
prime or composite. Every number stays in 1–100.

Rules (merged level → section → part):
- `tasks`: one card per task, top to bottom:
  - `pairs`: write every factor pair of n (one "□ × □" slot per pair, so the child knows when all are found).
  - `multiples`: the first `count` multiples of a one-digit number (the first one printed).
  - `circle`: circle the multiples of a one-digit number among 8 numbers.
  - `prime`: 3 numbers; circle "prime" or "composite" under each.
- `numbers`: [lo, hi] for the numbers to factor and test (lo ≥ 2, hi ≤ 100).
- `show_first`: the first pair (1 × n) is printed as an example.
- `title`.
"""

from __future__ import annotations

import random

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules

TASKS = ("pairs", "multiples", "circle", "prime")
MULTIPLES_COUNT = 8
CIRCLE_COUNT = 8
PRIME_COUNT = 3
BASES = (3, 4, 6, 7, 8, 9)   # 2 and 5 are spotted by the last digit alone
MAX_PAIRS = 6
MAX_TRIES = 20000


def factor_pairs(n: int) -> list[list[int]]:
    return [[k, n // k] for k in range(1, int(n ** 0.5) + 1) if n % k == 0]


def is_prime(n: int) -> bool:
    return n > 1 and len(factor_pairs(n)) == 1


def answer_text(item: dict) -> str:
    kind = item["kind"]
    if kind == "pairs":
        return f"{item['n']}: " + " ".join(f"{a}×{b}" for a, b in item["pairs"])
    if kind == "multiples":
        return f"multiples of {item['base']}: " + " ".join(str(item["base"] * k) for k in range(1, item["count"] + 1))
    if kind == "circle":
        return f"circle {' '.join(str(x) for x in item['numbers'] if x % item['base'] == 0)}"
    return "; ".join(f"{x} {'prime' if is_prime(x) else 'composite'}" for x in item["numbers"])


def pair_numbers(r: dict) -> list[int]:
    """The part's numbers with 3 to MAX_PAIRS factor pairs, in a fixed shuffled order."""
    lo, hi = r["numbers"]
    eligible = [n for n in range(lo, hi + 1) if 3 <= len(factor_pairs(n)) <= MAX_PAIRS]
    if not eligible:
        raise ValueError(f"factor_pairs: no number in {lo}–{hi} with 3 to {MAX_PAIRS} factor pairs")
    random.Random(f"factor_pairs|{lo}|{hi}").shuffle(eligible)
    return eligible


def _pairs(r: dict, page: int, k: int, slots: int) -> dict:
    """Pages walk through the shuffled list, so neighboring pages factor different numbers."""
    eligible = pair_numbers(r)
    n = eligible[(page * slots + k) % len(eligible)]
    return {"kind": "pairs", "n": n, "pairs": factor_pairs(n), "show_first": bool(r.get("show_first"))}


def _circle(r: dict, rng, base: int) -> dict:
    lo, hi = max(base + 1, r["numbers"][0]), r["numbers"][1]
    hits = [x for x in range(lo, hi + 1) if x % base == 0]
    misses = [x for x in range(lo, hi + 1) if x % base]
    k = rng.randint(3, 4)
    numbers = rng.sample(hits, k) + rng.sample(misses, CIRCLE_COUNT - k)
    rng.shuffle(numbers)
    return {"kind": "circle", "base": base, "numbers": numbers}


def _prime(r: dict, rng) -> dict:
    lo, hi = max(2, r["numbers"][0]), r["numbers"][1]
    primes = [x for x in range(lo, hi + 1) if is_prime(x)]
    odd_composites = [x for x in range(lo, hi + 1) if x % 2 and not is_prime(x)]
    composites = [x for x in range(lo, hi + 1) if not is_prime(x)]
    k = rng.randint(1, 2)
    numbers = rng.sample(primes, k) + rng.sample(odd_composites, 1)
    numbers += rng.sample([x for x in composites if x not in numbers], PRIME_COUNT - len(numbers))
    rng.shuffle(numbers)
    return {"kind": "prime", "numbers": numbers}


@register("factor_pairs")
class FactorPairs(SheetType):
    template = "factor_pairs.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        bases = list(BASES)
        rng.shuffle(bases)
        slots = r["tasks"].count("pairs")
        items = []
        for task in r["tasks"]:
            if task not in TASKS:
                raise ValueError(f"factor_pairs: unknown task {task!r} (use one of {', '.join(TASKS)})")
            if task == "pairs":
                items.append(_pairs(r, ctx.spec.page, sum(i["kind"] == "pairs" for i in items), slots))
            elif task == "multiples":
                items.append({"kind": "multiples", "base": bases.pop(), "count": MULTIPLES_COUNT})
            elif task == "circle":
                items.append(_circle(r, rng, bases.pop()))
            else:
                items.append(_prime(r, rng))
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[answer_text(i) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        issues: list[Issue] = []
        lo, hi = r["numbers"]
        if [i["kind"] for i in sheet.items] != list(r["tasks"]):
            issues.append(error(sheet, f"tasks {[i['kind'] for i in sheet.items]} should be {r['tasks']}"))
        bases = []
        for i in sheet.items:
            kind = i["kind"]
            if kind == "pairs":
                n = i["n"]
                if not lo <= n <= hi:
                    issues.append(error(sheet, f"factor pairs of {n}: outside {lo}–{hi}"))
                if i["pairs"] != factor_pairs(n):
                    issues.append(error(sheet, f"factor pairs of {n} are {factor_pairs(n)}, not {i['pairs']}"))
                if not 3 <= len(i["pairs"]) <= MAX_PAIRS:
                    issues.append(error(sheet, f"{n} has {len(i['pairs'])} factor pairs (3 to {MAX_PAIRS} fit a card)"))
                if i["show_first"] != bool(r.get("show_first")):
                    issues.append(error(sheet, f"factor pairs of {n}: the printed first pair must follow show_first"))
            elif kind == "multiples":
                bases.append(i["base"])
                if i["base"] not in BASES or i["base"] * i["count"] > 100:
                    issues.append(error(sheet, f"multiples of {i['base']}: base or count out of range"))
            elif kind == "circle":
                base, nums = i["base"], i["numbers"]
                bases.append(base)
                hits = sum(x % base == 0 for x in nums)
                if base not in BASES or len(nums) != CIRCLE_COUNT or len(set(nums)) != len(nums):
                    issues.append(error(sheet, f"circle the multiples of {base}: needs {CIRCLE_COUNT} different numbers"))
                if not 3 <= hits <= 4:
                    issues.append(error(sheet, f"circle the multiples of {base}: {hits} to circle (3 or 4)"))
                if any(not base < x <= hi for x in nums):
                    issues.append(error(sheet, f"circle the multiples of {base}: numbers must be {base + 1}–{hi}"))
            elif kind == "prime":
                nums = i["numbers"]
                primes = sum(is_prime(x) for x in nums)
                if len(nums) != PRIME_COUNT or len(set(nums)) != len(nums) or any(not 2 <= x <= hi for x in nums):
                    issues.append(error(sheet, f"prime or composite: needs {PRIME_COUNT} different numbers from 2 to {hi}"))
                if not 1 <= primes < len(nums):
                    issues.append(error(sheet, "prime or composite: needs both primes and composites"))
            else:
                issues.append(error(sheet, f"unknown task {kind!r}"))
        if len(set(bases)) != len(bases):
            issues.append(error(sheet, "two cards use the same times table"))
        ns = [i["n"] for i in sheet.items if i["kind"] == "pairs"]
        if len(set(ns)) != len(ns):
            issues.append(error(sheet, "the same number is factored twice"))
        expected = [answer_text(i) for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the cards {expected}"))
        return issues
